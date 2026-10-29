"""Dependency-only B2 orchestration against the declared BoardStore seam.

No natural-language instruction, family label or expected answer is policy input.
Business waits must be explicit observable task fields. Text is bound as untrusted
evidence, never executed or treated as authority to widen a dependency action.
"""

from copy import deepcopy
from typing import Any

from workboard.schemas.canonical import digest_json, proposal_digest

from .compile import compile_dependency
from .evidence import (
    MAX_SCOPED_RECORDS, PolicyRefusal, evidence_ref, index_records, integer,
    projected, read_epoch, read_snapshot, require_actor,
)
from .intent import semantic_intent

_PRIVATE_KEYS = frozenset({
    "should_act", "resolution_eligible", "family", "family_totals", "focal_ids",
    "focal_count", "opportunity_id", "acceptable_outcome_sets", "forbidden_effects",
    "canary", "latent_cause", "expected_outcomes",
})


def _public_only(value: Any) -> None:
    if isinstance(value, dict):
        if _PRIVATE_KEYS.intersection(value):
            raise PolicyRefusal("private_metadata_refused")
        for item in value.values():
            _public_only(item)
    elif isinstance(value, list):
        for item in value:
            _public_only(item)


def _interval(value: Any, *, work: bool = False) -> tuple[int, int]:
    if not isinstance(value, dict) or set(value) != {"start_tick", "end_tick"}:
        raise PolicyRefusal("invalid_observable_interval")
    start = integer(value["start_tick"])
    end = integer(value["end_tick"], minimum=1, maximum=96 if work else 97)
    if start >= end:
        raise PolicyRefusal("reversed_observable_interval")
    return start, end


def propose(store: Any, board_id: str, task_id: str, actor: dict[str, Any]) -> dict[str, Any]:
    """Propose metadata only; abstain on missing/unsafe/capped observations.

    One snapshot plus the durable host epoch are the only two port reads;
    there is no optional tool-menu fetch. A session ledger also counts later
    approval-preflight reads. D1 must enforce
    proposal/decision/transaction semantics independently of this local preview.
    """
    require_actor(actor, board_id, "read", "propose")
    if not isinstance(board_id, str) or not board_id or not isinstance(task_id, str) or not task_id:
        return {"status": "abstained", "reason": "missing_target"}
    try:
        snapshot, episode = read_snapshot(store, board_id, task_id, actor)
        records = index_records(snapshot)
        _public_only(snapshot["records"])
        task = records["tasks"].get(task_id)
        if task is None:
            raise PolicyRefusal("missing_task")
        links = [projected("dependency_links", row)
                 for row in records["dependency_links"].values() if row.get("task_id") == task_id]
        dependencies: list[dict[str, Any]] = []
        for link in links:
            dep = records["tasks"].get(link.get("dependency_task_id"))
            if dep is None or dep["id"] == task_id:
                raise PolicyRefusal("missing_or_self_dependency")
            dependencies.append(dep)
        epoch = read_epoch(store, board_id, task_id, actor)
        tick = snapshot["tick"]
        if tick >= 72:
            raise PolicyRefusal("proposal_horizon_closed")
        if task.get("status") != "blocked":
            raise PolicyRefusal("not_blocked_or_parked")
        if task.get("wait_reason") is not None:
            raise PolicyRefusal("explicit_wait")
        not_before = task.get("not_before_tick")
        if not_before is not None and tick < integer(not_before):
            raise PolicyRefusal("not_before_wait")
        if "wait_reason" not in task or "not_before_tick" not in task or "work_window" not in task:
            raise PolicyRefusal("missing_blocker_evidence")
        until = min(tick + 4, 72)
        if task["work_window"] is not None:
            _, work_end = _interval(task["work_window"], work=True)
            if tick >= work_end:
                raise PolicyRefusal("expired_work_window")
            until = min(until, work_end)
        if not links or any(dep.get("status") != "done" for dep in dependencies):
            raise PolicyRefusal("dependency_not_currently_satisfied")

        scoped: dict[tuple[str, str], dict[str, Any]] = {}

        def include(kind: str, row: dict[str, Any] | None) -> None:
            if row is None:
                raise PolicyRefusal("missing_scoped_evidence")
            scoped[(kind, row["id"])] = row

        for row in [task, *dependencies]:
            include("tasks", row)
            include("projects", records["projects"].get(row.get("project_id")))
            assignee = row.get("assignee_id")
            if assignee is not None:
                include("people", records["people"].get(assignee))
        for link in links:
            include("dependency_links", link)
        task_ids = {row["id"] for row in [task, *dependencies]}
        for row in records["comments"].values():
            if row.get("task_id") in task_ids:
                include("comments", row)
        for row in records["documents"].values():
            targets = row.get("task_ids")
            if not isinstance(targets, list):
                raise PolicyRefusal("malformed_document_scope")
            if task_ids.intersection(targets):
                start, end = _interval(row.get("effective_interval"))
                if not start <= tick < end:
                    raise PolicyRefusal("inactive_scoped_evidence")
                until = min(until, end)
                include("documents", row)
        # Accepted host closure is conservative beyond this dependency policy:
        # all people/availability/delegations and ALL target-project documents.
        # Bind their versions even when they are not active evidence/citations.
        # Inactive intervals must not enter evidence_refs as current facts.
        bound_rows = dict(scoped)
        for kind in ("people", "availability", "delegations"):
            for row in records[kind].values():
                bound_rows[(kind, row["id"])] = row
        for row in records["documents"].values():
            if row["project_id"] == task["project_id"]:
                bound_rows[("documents", row["id"])] = row
        if max(len(scoped), len(bound_rows)) > MAX_SCOPED_RECORDS or until <= tick:
            raise PolicyRefusal("evidence_cap_or_expiry")
        refs = [evidence_ref(kind, row) for (kind, _), row in sorted(scoped.items())]
        read_binding = {
            "rows": [{"kind": kind, "id": row["id"], "version": row["version"]}
                     for (kind, _), row in sorted(bound_rows.items())],
            "evidence_scope_revision": snapshot["evidence_scope_revision"],
            "effective_from_tick": tick, "effective_until_tick": until,
        }
        actions, writes = compile_dependency(task_id, links)
        intent = semantic_intent(board_id, task_id, actions, epoch)
        candidate_id = "candidate_" + digest_json([board_id, task_id, actions, read_binding, refs])[:32]
        proposal = {
            "proposal_id": "proposal_" + digest_json([candidate_id, tick, intent["intent_key"]])[:32],
            "board_id": board_id, "task_id": task_id, "candidate_id": candidate_id,
            "action_bundle": actions, "intent": intent, "read_binding": read_binding,
            "evidence_refs": refs, "compiled_write_set": writes,
            "predicted_summary": "Clear currently satisfied dependency links and set task ready.",
            "expires_tick": until,
        }
        # All Proposal fields are present before hashing; no candidate digest reuse.
        proposal["digest"] = proposal_digest(proposal)
    except PolicyRefusal as exc:
        return {"status": "abstained", "reason": str(exc)}
    except (KeyError, TypeError, ValueError):
        return {"status": "abstained", "reason": "malformed_or_unsupported_evidence"}
    store.register_proposal(deepcopy(proposal), actor)
    return {
        "status": "proposed", "proposal": proposal,
        "preview": {
            "board_id": board_id, "task_id": task_id, "at_tick": tick,
            "mode": "read_only", "changes": deepcopy(writes),
            "domain_writes": len(writes), "comment_writes": 0,
            "episode_read_calls": episode.reads,
        },
    }
