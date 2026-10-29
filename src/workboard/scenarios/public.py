"""Load the single original public fixture and project its dependency fields."""

from copy import deepcopy
import json
from pathlib import Path

KINDS = (
    "projects", "tasks", "dependency_links", "comments", "documents", "people",
    "availability", "delegations",
)
BOARD_ID = "b703"
TASK_ID = "t204"
PARKED_ID = "t319"
FIXTURE_NAME = "board.json"


def fixture_path() -> Path:
    return Path(__file__).resolve().parents[3] / "fixtures" / "public" / FIXTURE_NAME


def load_public() -> dict:
    """Return a fresh demo snapshot, without scorer labels or expected outcomes.

    Parsing is not JSON Schema or scientific admission validation. The source
    file uses P01 scenario records; the host sees the explicit wire projection.
    """
    raw = json.loads(fixture_path().read_text(encoding="utf-8"))
    if raw.get("designation") != "PUBLIC SCRIPTED ENGINEERING EXAMPLE":
        raise ValueError("only the public scripted fixture is supported")
    board = raw["board"]
    expected = {"schema_version", "board_id", "initial_tick", *KINDS}
    if set(board) != expected or board["schema_version"] != "1":
        raise ValueError("unsupported public fixture envelope")
    if board["board_id"] != BOARD_ID or board["initial_tick"] != 0:
        raise ValueError("unknown board or noninitial clock")
    records = {kind: deepcopy(board[kind]) for kind in KINDS}
    for kind, rows in records.items():
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError(f"malformed fixture records: {kind}")
        ids = [row["id"] for row in rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate fixture identifiers: {kind}")
        for row in rows:
            if type(row.get("version")) is not int or row["version"] < 1:
                raise ValueError("initial record version must be positive")
    for link in records["dependency_links"]:
        if "dependency_task_id" in link:
            raise ValueError("scenario links must use depends_on_task_id")
        link["dependency_task_id"] = link.pop("depends_on_task_id")
    return {"board_id": BOARD_ID, "tick": 0, "evidence_scope_revision": 0,
            "records": records}


def scripted_actor(*capabilities: str) -> dict:
    """Explicit local fixture capability attribution, not authentication."""
    return {"label": "SCRIPTED fixture operator", "kind": "scripted",
            "board_ids": [BOARD_ID], "capabilities": list(capabilities)}
