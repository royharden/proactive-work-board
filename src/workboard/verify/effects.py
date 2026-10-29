"""Snapshot-derived P01 EffectRecord construction, without controller imports.

The five positional arguments are the shared demo seam. Optional *demo envelope*
observations (never additions to P01 wire objects) needed for a positive verdict:

* before['verification_context'] = {'proposal': P01 Proposal, 'decision': P01 Decision}
* after/delayed['effect_history'] = ordered transitions with before/after snapshots,
  optional P01 receipt, actor_kind ('human', 'world', 'rules', 'agent') and
  actor_label. Each snapshot in a transition contains core fields only.
* after/delayed['history_complete'] = True means the supplied sequence starts at
  board seed (tick 0), covers every mutation, and ends at that observation.

Continuity is checked from actual snapshots, not intent keys or claimed writes.
Missing history/context yields pending, never a fabricated duplicate-free pass.
These are local observation claims, not authenticated or independent audit proof.
"""

from __future__ import annotations

import hashlib
from typing import Any

from workboard.schemas.canonical import digest_json, proposal_digest

KINDS = ("projects", "tasks", "dependency_links", "comments", "documents", "people",
         "availability", "delegations")
TOPICS = {"decision_record", "dependency_state", "delegation_scope",
          "availability_window", "work_window"}
NOISE = {"version", "updated_tick"}
PRECEDENCE = ("collateral", "duplicate", "reverted", "partial", "not_applied", "verified")


def _tick(value: Any) -> bool:
    return type(value) is int and 0 <= value <= 96


def _hex(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _receipt(value: Any) -> tuple[dict, str]:
    """Do not let malformed identities or non-JSON input reach a positive path."""
    try:
        if not isinstance(value, dict) or not all(isinstance(k, str) for k in value):
            raise ValueError("receipt must be a JSON object")
        identity = ("receipt_id", "board_id", "proposal_id", "decision_id")
        if not all(isinstance(value.get(k), str) and value[k] for k in identity):
            raise ValueError("missing receipt identity")
        if not all(_hex(value.get(k)) for k in ("proposal_digest", "intent_key")):
            raise ValueError("invalid receipt digest")
        if not _tick(value.get("applied_tick")) or type(value.get("committed")) is not bool:
            raise ValueError("invalid receipt time/commit")
        statuses = {"applied", "stale", "rejected", "expired", "superseded", "conflict",
                    "not_applied", "unsupported_capability"}
        if not isinstance(value.get("status"), str) or value["status"] not in statuses:
            raise ValueError("invalid receipt status")
        if not isinstance(value.get("actual_write_set"), list) or not isinstance(value.get("outbox_event_ids"), list):
            raise ValueError("missing observed writes/outbox")
        if not all(isinstance(x, str) and x for x in value["outbox_event_ids"]):
            raise ValueError("invalid outbox identities")
        for name in ("recovered_original_receipt_id", "reason_code"):
            if name not in value or (value[name] is not None and not isinstance(value[name], str)):
                raise ValueError("missing receipt fields")
        # Canonical conversion is inside protection, including cyclic/mixed keys.
        return value, digest_json(value)
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        return {}, hashlib.sha256(b"unobserved-receipt").hexdigest()


def _core(snapshot: dict) -> dict:
    """Only the documented observable core participates in snapshot identity."""
    return {k: snapshot[k] for k in ("board_id", "tick", "evidence_scope_revision", "records")}


def _rows(snapshot: Any) -> dict:
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("board_id"), str) or not snapshot["board_id"]:
        raise ValueError("missing board observation")
    if not _tick(snapshot.get("tick")) or type(snapshot.get("evidence_scope_revision")) is not int:
        raise ValueError("invalid observation time/revision")
    if snapshot["evidence_scope_revision"] < 0 or snapshot.get("truncated", False):
        raise ValueError("incomplete observation")
    records = snapshot.get("records")
    if not isinstance(records, dict) or set(records) != set(KINDS):
        raise ValueError("all observable record kinds required")
    result = {}
    for kind in KINDS:
        if not isinstance(records[kind], list):
            raise ValueError("records must be lists")
        for row in records[kind]:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"]:
                raise ValueError("invalid observable row")
            if type(row.get("version")) is not int or row["version"] < 1:
                raise ValueError("missing observed version")
            if row.get("board_id", snapshot["board_id"]) != snapshot["board_id"]:
                raise ValueError("cross-board row")
            key = (kind, row["id"])
            if key in result:
                raise ValueError("duplicate row identity")
            result[key] = row
    # The shared serializer rejects unsupported nonintegral hash-bearing values.
    digest_json(_core(snapshot))
    return result


def _changes(before: dict, after: dict) -> list[dict]:
    left, right = _rows(before), _rows(after)
    if before["board_id"] != after["board_id"] or before["tick"] > after["tick"]:
        raise ValueError("cross-board or reversed observation")
    if before["evidence_scope_revision"] > after["evidence_scope_revision"]:
        raise ValueError("reversed scope revision")
    changes = []
    for kind, ident in sorted(left.keys() | right.keys()):
        old, new = left.get((kind, ident)), right.get((kind, ident))
        if old is None or new is None:
            changes.append(dict(op="insert" if old is None else "delete", kind=kind,
                                id=ident, field=None, before=old, after=new))
        else:
            for field in sorted(old.keys() | new.keys()):
                if field not in NOISE and (field not in old or field not in new or old[field] != new[field]):
                    changes.append(dict(op="update", kind=kind, id=ident, field=field,
                                        before=old.get(field), after=new.get(field)))
            if old != new and new["version"] <= old["version"]:
                raise ValueError("changed row lacks monotone version")
    return changes


def _expected(before: dict, writes: Any, receipt: dict) -> list[dict]:
    rows = _rows(before)
    if not isinstance(writes, list) or not writes or len(writes) > 4:
        raise ValueError("compiled permissions missing or over cap")
    expected, seen = [], set()
    comments = 0
    for w in writes:
        if not isinstance(w, dict):
            raise ValueError("invalid compiled permission")
        op, kind, ident = w.get("op"), w.get("kind"), w.get("id")
        old = rows.get((kind, ident))
        field = w.get("field") if op == "update" else None
        key = (kind, ident, field)
        if key in seen:
            raise ValueError("duplicate compiled permission")
        seen.add(key)
        if op == "delete" and kind == "dependency_links" and old is not None:
            if set(w) != {"op", "kind", "id", "task_id", "dependency_task_id"}:
                raise ValueError("unknown delete permission")
            if any(old.get(k) != w[k] for k in ("task_id", "dependency_task_id")):
                raise ValueError("dependency permission mismatch")
            new = None
        elif op == "update" and kind == "tasks" and field in {"status", "assignee_id"} and old is not None:
            if set(w) != {"op", "kind", "id", "field", "value"}:
                raise ValueError("unknown update permission")
            if field == "status" and w["value"] != "ready":
                raise ValueError("unsupported status permission")
            if field == "assignee_id" and (not isinstance(w["value"], str) or not w["value"]):
                raise ValueError("unsupported assignee permission")
            old, new = old.get(field), w["value"]
        elif op == "insert" and kind == "comments" and old is None:
            comments += 1
            if set(w) != {"op", "kind", "id", "task_id", "actor_role", "body", "cites", "topic"}:
                raise ValueError("unknown comment permission")
            if w["actor_role"] not in {"agent", "rules"} or not isinstance(w["body"], str) or not w["body"]:
                raise ValueError("invalid comment permission")
            if w["topic"] is not None and w["topic"] not in TOPICS:
                raise ValueError("unknown request topic")
            if not isinstance(w["cites"], list) or (w["topic"] is None and not w["cites"]):
                raise ValueError("missing evidence citations")
            new = {k: v for k, v in w.items() if k not in {"op", "kind"}}
            new.update(version=1, occurred_tick=receipt["applied_tick"], origin="arm",
                       actor_id=None, source_event_id=None, source_proposal_id=receipt["proposal_id"])
        else:
            raise ValueError("unobservable or unsupported compiled permission")
        expected.append(dict(op=op, kind=kind, id=ident, field=field, before=old, after=new))
    if comments > 1 or len(writes) - comments > 3:
        raise ValueError("compiled caps exceeded")
    return expected


def _signature(change: dict) -> str:
    return digest_json(change)


def _binding(before: dict, after: dict, writes: list, receipt: dict) -> bool:
    context = before.get("verification_context", {})
    proposal, decision = context.get("proposal"), context.get("decision")
    if not isinstance(proposal, dict) or not isinstance(decision, dict):
        return False
    rb = proposal.get("read_binding", {})
    if not isinstance(rb, dict) or not isinstance(rb.get("rows"), list):
        return False
    if (proposal.get("board_id") != before["board_id"] or receipt.get("board_id") != before["board_id"]
            or decision.get("board_id") != before["board_id"]
            or proposal.get("proposal_id") != receipt.get("proposal_id")
            or decision.get("proposal_id") != receipt.get("proposal_id")
            or decision.get("decision_id") != receipt.get("decision_id")
            or decision.get("proposal_digest") != receipt.get("proposal_digest")
            or proposal.get("digest") != receipt.get("proposal_digest")
            or proposal_digest(proposal) != receipt.get("proposal_digest")
            or decision.get("read_binding") != rb
            or proposal.get("intent", {}).get("intent_key") != receipt.get("intent_key")
            or proposal.get("intent", {}).get("board_id") != before["board_id"]
            or proposal.get("intent", {}).get("task_id") != proposal.get("task_id")
            or proposal.get("compiled_write_set") != writes
            or rb.get("evidence_scope_revision") != before["evidence_scope_revision"]):
        return False
    tick = receipt.get("applied_tick")
    if not all(_tick(x) for x in (tick, rb.get("effective_from_tick"), rb.get("effective_until_tick"),
                                 proposal.get("expires_tick"), decision.get("expires_tick"), decision.get("decided_tick"))):
        return False
    if not (before["tick"] <= tick == after["tick"] and rb["effective_from_tick"] <= decision["decided_tick"] <= tick
            < min(rb["effective_until_tick"], proposal["expires_tick"], decision["expires_tick"])):
        return False
    rows, seen = _rows(before), set()
    for ref in rb["rows"]:
        key = (ref.get("kind"), ref.get("id"))
        if key in seen or key not in rows or rows[key]["version"] != ref.get("version"):
            return False
        seen.add(key)
    for ref in proposal.get("evidence_refs", []):
        key = (ref.get("kind"), ref.get("id"))
        if (key not in seen or rows[key]["version"] != ref.get("version")
                or digest_json(rows[key]) != ref.get("digest")):
            return False
    return bool(seen) and decision.get("status") == "approved"


def _primitive(change: dict) -> tuple | None:
    """Derive per-effect class/target from observations, never supplied intent."""
    op, kind, field = change["op"], change["kind"], change["field"]
    old, new = change["before"], change["after"]
    if kind == "dependency_links" and op == "delete":
        return old["task_id"], "clear_dependency", digest_json([old["dependency_task_id"]])
    if kind == "tasks" and op == "update" and old != new:
        if field == "status" and new == "ready":
            return change["id"], "set_ready", digest_json([change["id"], "ready"])
        if field == "assignee_id":
            return change["id"], "reassign_to_delegate", digest_json([new])
    if kind == "comments" and op == "insert" and new.get("origin") == "arm":
        if new.get("topic") in TOPICS:
            return new["task_id"], "request_info", digest_json([new["topic"]])
        if new.get("topic") is None and new.get("cites"):
            pairs = sorted({(c["kind"], c["id"]) for c in new["cites"]})
            return new["task_id"], "evidence_comment", digest_json([list(p) for p in pairs])
    return None


def _affected(change: dict, snapshot: dict) -> set[str]:
    if change["kind"] == "tasks":
        return {change["id"]}
    row = change["after"] if isinstance(change["after"], dict) else change["before"]
    if isinstance(row, dict) and row.get("task_id"):
        return {row["task_id"]}
    # Conservatively mark every board task relevant for board-wide evidence/people.
    return {r["id"] for r in snapshot["records"]["tasks"]}


def _persists(expected: list, snapshot: dict) -> bool:
    rows = _rows(snapshot)
    for e in expected:
        row = rows.get((e["kind"], e["id"]))
        if e["op"] == "delete":
            if row is not None:
                return False
        elif e["op"] == "insert":
            material = lambda r: {k: v for k, v in r.items() if k not in NOISE}
            if row is None or material(row) != material(e["after"]):
                return False
        elif row is None:
            return False
        elif e["field"] == "status" and e["after"] == "ready":
            if row.get("status") not in {"ready", "in_progress", "done"}:
                return False
        elif row.get(e["field"]) != e["after"]:
            return False
    return True


def _related_tasks(kind: str, row: dict, snapshot: dict) -> set[str]:
    """Relation from observable IDs only; display names are never blockers."""
    tasks = snapshot["records"]["tasks"]
    if kind == "tasks":
        return {row["id"]} | {r["task_id"] for r in snapshot["records"]["dependency_links"]
                               if r.get("dependency_task_id") == row["id"]}
    if kind in {"dependency_links", "comments"}:
        return {row["task_id"]} if row.get("task_id") else set()
    if kind == "documents":
        return {t["id"] for t in tasks if t["id"] in row.get("task_ids", [])
                or t.get("project_id") == row.get("project_id")}
    if kind == "availability":
        interval = row.get("effective_interval", {})
        if not (type(interval.get("start_tick")) is int and type(interval.get("end_tick")) is int
                and interval["start_tick"] <= snapshot["tick"] < interval["end_tick"]):
            return set()
        persons = {row.get("person_id")}
        return {t["id"] for t in tasks if t.get("assignee_id") in persons}
    if kind == "delegations":
        interval = row.get("effective_interval", {})
        if not (type(interval.get("start_tick")) is int and type(interval.get("end_tick")) is int
                and interval["start_tick"] <= snapshot["tick"] < interval["end_tick"]):
            return set()
        # A project-wide row for unrelated people is not a task blocker change.
        # Only an effective grant FROM its actual assignee can alter its episode.
        tasks = [t for t in tasks if t.get("assignee_id") is not None
                 and t.get("assignee_id") == row.get("from_person_id")]
        scope = row.get("scope", {})
        if scope.get("kind") == "task":
            return {t["id"] for t in tasks if t["id"] == scope.get("id")}
        if scope.get("kind") == "project":
            return {t["id"] for t in tasks if t.get("project_id") == scope.get("id")}
        return set()
    return set()


def _epoch_targets(changes: list, a: dict, b: dict) -> tuple[set, bool]:
    """Separate actual blocker transitions from broad effect attribution.

    Substantiveness of edited business prose cannot be proved mechanically. Do
    not reset an epoch for it; mark history uncertain instead of hiding repeats.
    """
    targets, uncertain = set(), False
    left, right = _rows(a), _rows(b)
    for c in changes:
        kind, ident, field = c["kind"], c["id"], c["field"]
        rows = [r for r in (left.get((kind, ident)), right.get((kind, ident))) if r is not None]
        related = set().union(*(_related_tasks(kind, r, a) | _related_tasks(kind, r, b) for r in rows))
        if kind == "tasks" and (c["op"] != "update" or field in {
                "status", "assignee_id", "wait_reason", "not_before_tick", "work_window"}):
            targets.update(related)
        elif kind == "dependency_links":
            targets.update(related)
        elif kind in {"availability", "delegations"}:
            targets.update(related)
        elif kind in {"comments", "documents"}:
            if kind == "comments" and all(r.get("origin") == "arm" for r in rows):
                continue
            # Prose changes might be substantive OR cosmetic. Neither guess is
            # accepted as a new duplicate epoch or a complete historical proof.
            uncertain |= bool(related)
        # Task title/description and person display_name never reset an epoch.
    # A timer tick matters only at an actual relevant observable boundary.
    for (kind, _), row in left.items():
        boundaries = []
        if kind == "tasks":
            boundaries.append(row.get("not_before_tick"))
            interval = row.get("work_window") or {}
        elif kind in {"availability", "delegations", "documents"}:
            interval = row.get("effective_interval") or {}
        else:
            continue
        boundaries.extend(interval.get(k) for k in ("start_tick", "end_tick"))
        for t in boundaries:
            if type(t) is not int or not a["tick"] < t <= b["tick"]:
                continue
            # A jump can cross BOTH ends of an interval while its endpoints are
            # inactive. Evaluate the relation inside the crossed interval rather
            # than guessing from endpoint activity. Mutations in this transition
            # occur at b.tick; interior boundaries use the observed pre-step rows.
            probe_tick = t - 1 if t == interval.get("end_tick") else t
            observed = b if probe_tick == b["tick"] else a
            probe = {**observed, "tick": probe_tick}
            targets.update(_related_tasks(kind, row, probe))
    return targets, uncertain


def _history(observation: dict, before: dict, after: dict, receipt: dict, expected: list) -> tuple:
    """Return complete, duplicate, reverted, human; inspect all intervening steps."""
    entries = observation.get("effect_history")
    if observation.get("history_complete") is not True or not isinstance(entries, list) or not entries:
        return False, False, False, False
    seen, epochs = set(), {}
    duplicate = reverted = human = found = uncertain = False
    current_keys = set()
    previous = None
    for entry in entries:
        a, b = entry["before"], entry["after"]
        changes = _changes(a, b)
        if a["board_id"] != before["board_id"]:
            raise ValueError("cross-board history")
        if previous is None:
            if a["tick"] != 0:
                return False, duplicate, reverted, human
        elif digest_json(_core(previous)) != digest_json(_core(a)):
            return False, duplicate, reverted, human
        current = (digest_json(_core(a)) == digest_json(_core(before))
                   and digest_json(_core(b)) == digest_json(_core(after))
                   and entry.get("receipt") == receipt)
        keys = set()
        for change in changes:
            primitive = _primitive(change)
            if primitive:
                task, cls, target = primitive
                key = (a["board_id"], task, cls, target, epochs.get(task, 0))
                if (current and (key in seen or key in keys)) or (found and key in current_keys):
                    duplicate = True
                keys.add(key)
        seen.update(keys)
        if current:
            found = True
            current_keys = keys
        elif found:
            if not _persists(expected, b):
                reverted = True
            if changes and entry.get("actor_kind") == "human":
                targets = {e["id"] for e in expected if e["kind"] == "tasks"}
                targets.update(e["after"]["task_id"] for e in expected if e["kind"] == "comments")
                targets.update(e["before"]["task_id"] for e in expected if e["kind"] == "dependency_links")
                human |= any(_affected(c, b) & targets for c in changes)
        changed_tasks, ambiguous = _epoch_targets(changes, a, b)
        uncertain |= ambiguous
        for task in changed_tasks:
            epochs[task] = epochs.get(task, 0) + 1
        previous = b
    complete = found and not uncertain and digest_json(_core(previous)) == digest_json(_core(observation))
    return complete, duplicate, reverted, human


def inspect_effect(before: Any, after: Any, delayed: Any, compiled_writes: Any, receipt: Any) -> dict:
    """Return the closed P01 EffectRecord; malformed evidence stays pending/fail.

    Unavailable wire identities use explicit 'unobserved' / zero-digest sentinels.
    They never imply a receipt exists. Detailed limitations belong in the trace,
    since the frozen EffectRecord does not permit extra diagnostic fields.
    """
    r, receipt_hash = _receipt(receipt)
    ident = lambda name: r.get(name) if isinstance(r.get(name), str) and r[name] else "unobserved"
    flags = {k: False for k in (*PRECEDENCE, "superseded_by_human")}
    checks = dict(exact_writes=False, no_collateral=False, no_duplicate=False,
                  immediate="pending", delayed="pending", delayed_tick=None)
    record = dict(effect_id="effect-" + receipt_hash,
                  board_id=ident("board_id"), proposal_id=ident("proposal_id"), receipt_id=ident("receipt_id"),
                  intent_key=r.get("intent_key") if _hex(r.get("intent_key")) else "0" * 64,
                  observed_tick=0, checks=checks, flags=flags, display_status="pending",
                  feedback="not_applied", snapshot_digests=["0" * 64], affected_task_ids=[])
    try:
        actual = _changes(before, after)
        record["board_id"] = before["board_id"]
        record["observed_tick"] = after["tick"]
        record["snapshot_digests"] = [digest_json(_core(before)), digest_json(_core(after))]
        expected = _expected(before, compiled_writes, r)
        actual_set = {_signature(c) for c in actual}
        expected_set = {_signature(c) for c in expected}
        matches = actual_set & expected_set
        checks["exact_writes"] = actual_set == expected_set and bool(actual_set)
        flags["collateral"] = bool(actual_set - expected_set)
        checks["no_collateral"] = not flags["collateral"]
        flags["partial"] = bool(matches) and matches != expected_set
        flags["not_applied"] = not matches
        record["affected_task_ids"] = sorted(set().union(*(_affected(c, after) for c in actual))) if actual else []
        receipt_writes = r.get("actual_write_set")
        receipt_matches = (isinstance(receipt_writes, list)
                           and sorted(_signature(c) for c in receipt_writes) == sorted(actual_set))
        bound = _binding(before, after, compiled_writes, r)
        committed = r.get("status") == "applied" and r.get("committed") is True
        outbox = r.get("outbox_event_ids")
        evidence = (bound and receipt_matches and committed and isinstance(outbox, list)
                    and bool(outbox) and len(set(outbox)) == len(outbox)
                    and all(isinstance(x, str) and x for x in outbox))
        checks["immediate"] = "pass" if checks["exact_writes"] and evidence else "fail"
        observation = after
        if delayed is not None:
            _rows(delayed)
            if delayed["board_id"] != before["board_id"] or delayed["tick"] < after["tick"]:
                raise ValueError("invalid delayed observation")
            record["snapshot_digests"].append(digest_json(_core(delayed)))
            checks["delayed_tick"] = delayed["tick"]
            record["observed_tick"] = delayed["tick"]
            if _tick(r.get("applied_tick")) and delayed["tick"] >= r["applied_tick"] + 8:
                flags["reverted"] = bool(matches) and not _persists(expected, delayed)
                checks["delayed"] = "fail" if flags["reverted"] else "pending"
                observation = delayed
        complete, duplicate, reverted, human = _history(observation, before, after, r, expected)
        flags["duplicate"], flags["superseded_by_human"] = duplicate, human
        flags["reverted"] |= reverted and bool(matches)
        checks["no_duplicate"] = complete and not duplicate
        if checks["delayed_tick"] is not None and checks["delayed_tick"] >= r["applied_tick"] + 8:
            checks["delayed"] = "fail" if flags["reverted"] else "pass" if complete else "pending"
        flags["verified"] = (checks["exact_writes"] and checks["no_collateral"] and checks["no_duplicate"]
                             and checks["immediate"] == checks["delayed"] == "pass"
                             and not any(flags[k] for k in PRECEDENCE[:-1]))
        if not bound and checks["exact_writes"]:
            checks["immediate"] = "pending"
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, OverflowError, RecursionError):
        # Partial observations may still retain already discovered adverse flags.
        flags["verified"] = False
        checks["immediate"] = "pending"
        checks["delayed"] = "pending"
    record["display_status"] = next((k for k in PRECEDENCE if flags[k]), "pending")
    record["feedback"] = {"verified": "applied", "reverted": "not_persisted", "pending": "not_applied"}.get(
        record["display_status"], record["display_status"])
    if r.get("status") in {"stale", "expired", "superseded"} and record["display_status"] in {"pending", "not_applied"}:
        record["feedback"] = "stale"
    return record
