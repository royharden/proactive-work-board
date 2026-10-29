"""Adverse engineering events through the host, never direct SQL."""

from workboard.scenarios.public import BOARD_ID, TASK_ID


def advance(store, tick: int, actor: dict) -> None:
    if type(tick) is not int or not 0 <= tick <= 96:
        raise ValueError("demo tick outside the P01 observation horizon")
    store.advance_to(BOARD_ID, tick, actor)


def insert_contradiction(store, actor: dict) -> None:
    """Insert visible evidence after approval; scope binding must reject apply.

    This is a scripted-edit extension seam, not a compiled action permission.
    The host must support document inserts in its explicit fixture capability.
    """
    store.scripted_edit(BOARD_ID, [{
        "op": "insert", "kind": "documents", "id": "d908",
        "project_id": "p107", "task_ids": [TASK_ID],
        "title": "Updated fictional work constraint",
        "body": "A newly recorded business hold requires another review.",
        "effective_interval": {"start_tick": 0, "end_tick": 97},
    }], actor)


def revert_at_four(store, applied_tick: int, actor: dict) -> None:
    """Scripted adverse revert, not a permitted controller status template."""
    advance(store, applied_tick + 4, actor)
    store.scripted_edit(BOARD_ID, [{
        "op": "update", "kind": "tasks", "id": TASK_ID,
        "field": "status", "value": "blocked",
    }], actor)
