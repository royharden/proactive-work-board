"""Compile the dependency-only B2 subset to exact P01 actions and writes."""

from copy import deepcopy
from typing import Any

from workboard.schemas.canonical import digest_json

REWORD_SUFFIX = " Alternate public wording."
EVIDENCE_SUBJECT = "dependency_state"
EVIDENCE_BODY = "dependency_state: cited prerequisite tasks are currently done."
# Existing P01 evidence_comment uses null, not a request_info topic. The subject
# above is a code-owned factual phrase, never a widened wire topic field.
EVIDENCE_WIRE_TOPIC = None


def compile_dependency(
    task_id: str, links: list[dict[str, Any]],
    *, with_evidence_comment: bool = False,
    evidence_refs: list[dict[str, Any]] | None = None,
    alternate_wording: bool = False, comment_id: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if type(with_evidence_comment) is not bool or type(alternate_wording) is not bool:
        raise ValueError("explicit_comment_mode_required")
    if not with_evidence_comment and (alternate_wording or comment_id is not None):
        raise ValueError("comment_arguments_without_comment")
    # All links must have been justified by current scoped evidence before here.
    # Two deletions plus ready consume the complete three-domain-write allowance.
    if not 1 <= len(links) <= 2:
        raise ValueError("dependency_write_cap")
    actions: list[dict[str, Any]] = []
    writes: list[dict[str, Any]] = []
    targets: set[str] = set()
    link_ids: set[str] = set()
    for link in sorted(links, key=lambda row: row["id"]):
        dep = link.get("dependency_task_id")
        if (link.get("task_id") != task_id or not isinstance(dep, str) or not dep
                or dep == task_id or dep in targets or link["id"] in link_ids):
            raise ValueError("contradictory_dependency")
        targets.add(dep)
        link_ids.add(link["id"])
        actions.append({
            "action_kind": "clear_dependency", "task_id": task_id,
            "dependency_link_id": link["id"], "dependency_task_id": dep,
        })
        writes.append({
            "op": "delete", "kind": "dependency_links", "id": link["id"],
            "task_id": task_id, "dependency_task_id": dep,
        })
    actions.append({"action_kind": "set_ready", "task_id": task_id})
    writes.append({
        "op": "update", "kind": "tasks", "id": task_id,
        "field": "status", "value": "ready",
    })
    if with_evidence_comment:
        expected = {
            *(('dependency_links', link['id']) for link in links),
            *(('tasks', link['dependency_task_id']) for link in links),
        }
        selected: dict[tuple[str, str], dict[str, Any]] = {}
        if not isinstance(evidence_refs, list):
            raise ValueError("bound_dependency_citations_required")
        for ref in evidence_refs:
            key = (ref["kind"], ref["id"])
            if key in expected:
                if key in selected or set(ref) != {"kind", "id", "version", "digest"}:
                    raise ValueError("ambiguous_dependency_citation")
                selected[key] = ref
        if set(selected) != expected:
            raise ValueError("missing_dependency_citation")
        cites = [deepcopy(selected[key]) for key in sorted(selected)]
        primary_id = "comment_" + digest_json([task_id, EVIDENCE_SUBJECT, cites])[:32]
        # The existing D3 clone keeps the primary ID; an explicit opaque-ID
        # alternate may append r2. Both remain exact approved payloads, never
        # new domain intent. Other caller-selected comment rows are refused.
        allowed_ids = {primary_id, primary_id + "r2"} if alternate_wording else {primary_id}
        identifier = primary_id if comment_id is None else comment_id
        if identifier not in allowed_ids:
            raise ValueError("unsupported_auxiliary_comment_id")
        body = EVIDENCE_BODY + (REWORD_SUFFIX if alternate_wording else "")
        actions.append({
            "action_kind": "evidence_comment", "task_id": task_id,
            "body": body, "cites": deepcopy(cites),
        })
        writes.append({
            "op": "insert", "kind": "comments", "id": identifier,
            "task_id": task_id, "actor_role": "rules", "body": body,
            "cites": deepcopy(cites), "topic": EVIDENCE_WIRE_TOPIC,
        })
    return actions, writes
