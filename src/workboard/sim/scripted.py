"""Adverse engineering events through the host, never direct SQL."""

from workboard.scenarios.public import BOARD_ID, TASK_ID


def advance(store, tick: int, actor: dict) -> None:
    if type(tick) is not int or not 0 <= tick <= 96:
        raise ValueError("demo tick outside the P01 observation horizon")
    store.advance_to(BOARD_ID, tick, actor)


def insert_contradiction(store, actor: dict) -> None:
    """Insert sourced WORLD comment after approval to invalidate scope binding.

    Host supplies exact exogenous source/provenance; this never broadens the
    controller's compiled comment permissions or invents document support.
    """
    store.scripted_edit(BOARD_ID, [{
        "op": "insert", "kind": "comments", "id": "c908",
        "task_id": TASK_ID, "actor_role": "world", "cites": [], "topic": None,
        "body": "A newly recorded business hold requires another review.",
    }], actor)


def revert_at_four(store, applied_tick: int, actor: dict) -> None:
    """Scripted adverse revert, not a permitted controller status template."""
    advance(store, applied_tick + 4, actor)
    store.scripted_edit(BOARD_ID, [{
        "op": "update", "kind": "tasks", "id": TASK_ID,
        "field": "status", "value": "blocked",
    }], actor)
