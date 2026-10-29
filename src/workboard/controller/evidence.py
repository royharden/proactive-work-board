"""Bounded, board-scoped observation helpers for the private keyless demo.

The ledger is scoped to a BoardStore object, not a durable DB budget. Reopening a
store needs a host-owned read/epoch journal before claiming a run-wide cap. The
single-session demo must keep one store object. No application I/O on import.
"""

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any
from weakref import WeakKeyDictionary

from workboard.schemas.canonical import digest_json

KINDS = (
    "projects", "tasks", "dependency_links", "comments", "documents", "people",
    "availability", "delegations",
)
MAX_READS = 8
MAX_OBSERVABLE_RECORDS = 256
MAX_SCOPED_RECORDS = 64


class PolicyRefusal(ValueError):
    """A fixed, non-truth-bearing refusal reason."""


def integer(value: Any, minimum: int = 0, maximum: int = 96) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise PolicyRefusal("invalid_integer")
    return value


def require_actor(actor: dict[str, Any], board_id: str, *caps: str) -> None:
    if not isinstance(actor, dict):
        raise PermissionError("actor_required")
    if (actor.get("kind") not in {"human", "scripted"}
            or not isinstance(actor.get("label"), str) or not actor["label"].strip()
            or not isinstance(actor.get("board_ids"), list)
            or board_id not in actor["board_ids"]
            or not isinstance(actor.get("capabilities"), list)
            or any(cap not in actor["capabilities"] for cap in caps)):
        raise PermissionError("board_capability_denied")


@dataclass
class Episode:
    reads: int = 0
    epoch: int = 0
    fingerprint: str | None = None


@dataclass
class Ledger:
    episodes: dict[tuple[str, str], Episode] = field(default_factory=dict)


_LEDGERS: WeakKeyDictionary[Any, Ledger] = WeakKeyDictionary()


def episode_for(store: Any, board_id: str, task_id: str) -> Episode:
    try:
        if store not in _LEDGERS:
            _LEDGERS[store] = Ledger()
        ledger = _LEDGERS[store]
    except TypeError as exc:
        raise PolicyRefusal("store_session_ledger_unavailable") from exc
    key = (board_id, task_id)
    if key not in ledger.episodes:
        if len(ledger.episodes) >= MAX_OBSERVABLE_RECORDS:
            raise PolicyRefusal("session_ledger_cap")
        ledger.episodes[key] = Episode()
    return ledger.episodes[key]


def read_snapshot(
    store: Any, board_id: str, task_id: str, actor: dict[str, Any],
) -> tuple[dict[str, Any], Episode]:
    require_actor(actor, board_id, "read")
    episode = episode_for(store, board_id, task_id)
    # Reserve before even a failed read. At exhaustion do not peek for a reset.
    if episode.reads >= MAX_READS:
        raise PolicyRefusal("read_budget_exhausted")
    episode.reads += 1
    snapshot = deepcopy(store.snapshot(board_id, actor))
    if not isinstance(snapshot, dict) or snapshot.get("board_id") != board_id:
        raise PolicyRefusal("cross_board_snapshot")
    integer(snapshot.get("tick"))
    integer(snapshot.get("evidence_scope_revision"), maximum=2**63 - 1)
    index_records(snapshot)
    return snapshot, episode


def index_records(snapshot: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    records = snapshot.get("records")
    if not isinstance(records, dict) or set(records) != set(KINDS):
        raise PolicyRefusal("incomplete_observable_snapshot")
    index: dict[str, dict[str, dict[str, Any]]] = {}
    total = 0
    for kind in KINDS:
        rows = records[kind]
        if not isinstance(rows, list):
            raise PolicyRefusal("malformed_observable_rows")
        total += len(rows)
        if total > MAX_OBSERVABLE_RECORDS:
            raise PolicyRefusal("observable_record_cap")
        index[kind] = {}
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"]:
                raise PolicyRefusal("malformed_observable_record")
            if row["id"] in index[kind]:
                raise PolicyRefusal("contradictory_duplicate_record")
            integer(row.get("version"), maximum=2**63 - 1)
            if "board_id" in row and row["board_id"] != snapshot["board_id"]:
                raise PolicyRefusal("cross_board_record")
            index[kind][row["id"]] = row
    return index


def projected(kind: str, record: dict[str, Any]) -> dict[str, Any]:
    """Hash the complete observable payload with the declared dependency alias."""
    result = deepcopy(record)
    if kind == "dependency_links" and "depends_on_task_id" in result:
        target = result.pop("depends_on_task_id")
        if "dependency_task_id" in result:
            raise PolicyRefusal("contradictory_dependency_alias")
        result["dependency_task_id"] = target
    return result


def evidence_ref(kind: str, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": kind, "id": row["id"], "version": row["version"],
        "digest": digest_json(projected(kind, row)),
    }


def check_binding(proposal: dict[str, Any], snapshot: dict[str, Any]) -> None:
    """Read-only preflight; D1 must repeat atomically at apply, including absence."""
    binding = proposal["read_binding"]
    tick = snapshot["tick"]
    if (snapshot["board_id"] != proposal["board_id"]
            or snapshot["evidence_scope_revision"] != binding["evidence_scope_revision"]
            or not binding["effective_from_tick"] <= tick < binding["effective_until_tick"]
            or tick >= proposal["expires_tick"]):
        raise PolicyRefusal("stale_or_expired_proposal")
    index = index_records(snapshot)
    for bound in binding["rows"]:
        row = index[bound["kind"]].get(bound["id"])
        if row is None or row["version"] != bound["version"]:
            raise PolicyRefusal("stale_read_version")
    for ref in proposal["evidence_refs"]:
        row = index[ref["kind"]].get(ref["id"])
        if row is None or evidence_ref(ref["kind"], row) != ref:
            raise PolicyRefusal("stale_evidence_digest")
