"""Bounded, board-scoped observation helpers for the private keyless demo.

Every controller/approval domain read requires the host's durable reservation.
No local cache, inferred epoch, reset or fallback peek exists. Observer-only
driver/verifier snapshots are outside this bounded policy selection stream.
No application I/O on import.
"""

from copy import deepcopy
from typing import Any

from workboard.host import store as host_module
from workboard.schemas.canonical import digest_json
from workboard.schemas.records import validate_graph

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


def reserve_read(
    store: Any, board_id: str, task_id: str, actor: dict[str, Any],
) -> dict[str, int]:
    """Obtain durable metadata permission BEFORE the next policy domain read.

    The producer owns actor-independent counters across reopen and canonical
    observed transitions. Missing/old hosts refuse without a domain read. The
    reservation itself returns metadata only, not a second policy observation.
    """
    require_actor(actor, board_id, "read")
    method = getattr(store, "reserve_read", None)
    budget_error = getattr(host_module, "ReadBudgetExceeded", None)
    if (not callable(method) or not isinstance(budget_error, type)
            or not issubclass(budget_error, RuntimeError)):
        raise PolicyRefusal("unsupported_host_read_reservation")
    try:
        result = method(board_id, task_id, actor)
    except budget_error:
        raise PolicyRefusal("read_budget_exhausted") from None
    if not isinstance(result, dict) or set(result) != {
        "episode_epoch", "reads_used", "reads_remaining",
    }:
        raise PolicyRefusal("malformed_host_read_reservation")
    epoch = integer(result["episode_epoch"], maximum=2**63 - 1)
    used = integer(result["reads_used"], minimum=1, maximum=MAX_READS)
    remaining = integer(result["reads_remaining"], maximum=MAX_READS - 1)
    if used + remaining != MAX_READS:
        raise PolicyRefusal("malformed_host_read_reservation")
    return {"episode_epoch": epoch, "reads_used": used, "reads_remaining": remaining}


def read_snapshot(
    store: Any, board_id: str, task_id: str, actor: dict[str, Any],
    *, expected_epoch: int | None = None,
) -> tuple[dict[str, Any], dict[str, int]]:
    require_actor(actor, board_id, "read")
    reservation = reserve_read(store, board_id, task_id, actor)
    if expected_epoch is not None and reservation["episode_epoch"] != expected_epoch:
        # Charge failed preflight conservatively; do not peek into domain rows.
        raise PolicyRefusal("stale_host_epoch")
    snapshot = deepcopy(store.snapshot(board_id, actor))
    if not isinstance(snapshot, dict) or snapshot.get("board_id") != board_id:
        raise PolicyRefusal("cross_board_snapshot")
    integer(snapshot.get("tick"))
    integer(snapshot.get("evidence_scope_revision"), maximum=2**63 - 1)
    index_records(snapshot)
    # Accepted closed records/FKs: absent fields are never silently treated null,
    # and document/task project consistency is checked before producing evidence.
    validate_graph(snapshot["records"])
    return snapshot, reservation


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
    """Accepted host records are already projected; never relabel their digest."""
    result = deepcopy(record)
    if kind == "dependency_links" and "depends_on_task_id" in result:
        raise PolicyRefusal("unprojected_dependency_record")
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
