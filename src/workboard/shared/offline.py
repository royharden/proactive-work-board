"""Exact offline fixture lookup; no SDK, network or credential discovery."""

from copy import deepcopy
import json

MAX_CALLS_PER_ATTEMPT = 2
MAX_ATTEMPTS_PER_EPISODE = 2
MAX_CALLS_PER_BOARD = 48
MAX_INPUT_TOKENS = 3000
MAX_OUTPUT_TOKENS = 400


class FixtureMiss(ValueError):
    pass


class OfflineProvider:
    """Only caller-supplied public replies; bytes are never billed tokens.

    Keys are exact canonical JSON request values. Callers must explicitly begin
    attempts; a miss is charged as an attempted lookup and never retried live.
    Token accounting is unavailable, so live dispatch always refuses. This
    provider makes no claim about token use even for a successful fixture hit.
    """

    def __init__(self, board_id: str, replies: dict[str, dict]):
        self.board_id = board_id
        self._replies = deepcopy(replies)
        self._calls = 0
        self._attempts: dict[str, int] = {}
        self._attempt_calls = 0
        self._episode: str | None = None

    def begin_attempt(self, episode: str) -> None:
        if not isinstance(episode, str) or not episode:
            raise ValueError("explicit episode required")
        count = self._attempts.get(episode, 0)
        if count >= MAX_ATTEMPTS_PER_EPISODE:
            raise ValueError("offline attempt cap reached")
        self._attempts[episode] = count + 1
        self._episode = episode
        self._attempt_calls = 0

    def reply(self, board_id: str, request: dict) -> dict:
        if board_id != self.board_id or self._episode is None:
            raise ValueError("board scope or explicit attempt missing")
        if self._calls >= MAX_CALLS_PER_BOARD or self._attempt_calls >= MAX_CALLS_PER_ATTEMPT:
            raise ValueError("offline call cap reached")
        self._calls += 1
        self._attempt_calls += 1
        key = json.dumps(request, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False)
        if key not in self._replies:
            raise FixtureMiss("no exact public offline reply; dispatch refused")
        return deepcopy(self._replies[key])

    def dispatch_live(self, *_args, **_kwargs):
        raise ValueError("live dispatch disabled; no supported billed-token accounting")


def limits() -> dict:
    return {"calls_per_attempt": MAX_CALLS_PER_ATTEMPT,
            "attempts_per_episode": MAX_ATTEMPTS_PER_EPISODE,
            "calls_per_board": MAX_CALLS_PER_BOARD,
            "input_tokens": MAX_INPUT_TOKENS, "output_tokens": MAX_OUTPUT_TOKENS,
            "token_accounting": "UNAVAILABLE - live dispatch refused",
            "provider": "offline only; dependency demo makes zero model calls"}
