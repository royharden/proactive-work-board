"""D2 policy guard over the accepted D1 public P01 normalizer.

This module grants no writes and is never a mechanical grading oracle.
"""
from typing import Any

from workboard.schemas.validation import ACTIONS, TOPICS, normalized_intent

ACTION_KINDS = tuple(ACTIONS)
INFORMATION_TOPICS = frozenset(TOPICS)
DOMAIN_KINDS = frozenset(ACTION_KINDS[:3])


def semantic_intent(
    board_id: str, task_id: str, actions: list[dict[str, Any]], epoch: int,
) -> dict[str, Any]:
    if not actions or type(epoch) is not int or epoch < 0:
        raise ValueError("invalid_intent")
    singleton_kinds: set[str] = set()
    comments = 0
    for action in actions:
        kind = action.get("action_kind")
        if kind not in ACTION_KINDS or action.get("task_id") != task_id:
            raise ValueError("unsupported_or_cross_task_action")
        if kind != "clear_dependency":
            if kind in singleton_kinds:
                raise ValueError("contradictory_normalized_action")
            singleton_kinds.add(kind)
        comments += kind not in DOMAIN_KINDS
    if comments > 1 or len(actions) - comments > 3:
        raise ValueError("write_cap")
    return normalized_intent(board_id, task_id, actions, epoch)
