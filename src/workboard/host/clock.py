"""Injectable adapter to the store's single simulated-time authority."""
from __future__ import annotations


class ClockPort:
    def __init__(self, store, board_id: str, actor: dict):
        self.store, self.board_id, self.actor = store, board_id, actor

    def now(self) -> int:
        return self.store.snapshot(self.board_id, self.actor)["tick"]

    def advance_to(self, tick: int) -> None:
        self.store.advance_to(self.board_id, tick, self.actor)
