"""Dependency-only B2 demo adapter; not a measured comparator implementation."""

from typing import Any

from workboard.controller.service import propose as _propose


def propose(
    store: Any, board_id: str, task_id: str, actor: dict[str, Any],
    *, with_evidence_comment: bool = False,
) -> dict[str, Any]:
    return _propose(
        store, board_id, task_id, actor, with_evidence_comment=with_evidence_comment,
    )
