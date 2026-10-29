"""Public P01 semantic normalization, separate from mechanical grading.

No verifier/scorer imports this module. Canonical hashing belongs to D1.
"""

from typing import Any

from workboard.schemas.canonical import digest_json

ACTION_KINDS = (
    "clear_dependency", "set_ready", "reassign_to_delegate", "request_info",
    "evidence_comment",
)
INFORMATION_TOPICS = frozenset({
    "decision_record", "dependency_state", "delegation_scope",
    "availability_window", "work_window",
})
DOMAIN_KINDS = frozenset(ACTION_KINDS[:3])


def semantic_intent(
    board_id: str, task_id: str, actions: list[dict[str, Any]], epoch: int,
) -> dict[str, Any]:
    """Normalize the five-template vocabulary without granting their effects."""
    if not actions or type(epoch) is not int or epoch < 0:
        raise ValueError("invalid_intent")
    pairs: list[list[str]] = []
    seen: set[tuple[str, str]] = set()
    singleton_kinds: set[str] = set()
    comment_count = 0
    for action in actions:
        kind = action.get("action_kind")
        if kind not in ACTION_KINDS or action.get("task_id") != task_id:
            raise ValueError("unsupported_or_cross_task_action")
        if kind != "clear_dependency":
            if kind in singleton_kinds:
                raise ValueError("contradictory_normalized_action")
            singleton_kinds.add(kind)
        if kind == "clear_dependency":
            target = [action["dependency_task_id"]]
        elif kind == "set_ready":
            target = [task_id, "ready"]
        elif kind == "reassign_to_delegate":
            target = [action["delegate_id"]]
        elif kind == "request_info":
            if action.get("topic") not in INFORMATION_TOPICS:
                raise ValueError("unknown_information_topic")
            target = [action["topic"]]
        else:
            cites = action.get("cites")
            if not isinstance(cites, list) or not cites:
                raise ValueError("missing_citation")
            target = [list(x) for x in sorted({(r["kind"], r["id"]) for r in cites})]
        pair = (kind, digest_json(target))
        if pair in seen:
            raise ValueError("duplicate_normalized_action")
        seen.add(pair)
        pairs.append(list(pair))
        comment_count += kind not in DOMAIN_KINDS
    if comment_count > 1 or len(actions) - comment_count > 3:
        raise ValueError("write_cap")
    domain = [p for p in pairs if p[0] in DOMAIN_KINDS]
    normalized = sorted(domain or pairs)
    primary = next(kind for kind in ACTION_KINDS if any(p[0] == kind for p in pairs))
    target_digest = digest_json(normalized)
    return {
        "board_id": board_id, "task_id": task_id, "action_kind": primary,
        "semantic_target": target_digest, "episode_epoch": epoch,
        "intent_key": digest_json([board_id, task_id, primary, target_digest, epoch]),
    }
