"""One future keyless acceptance procedure; NOT RUN during Dirty construction.

After owner execution authority, invoke with --execute --run-dir <new local dir>
and source package on Python's import path. No dependency installation required.
Checks inspect actual reopened host rows/receipts and observed effect records;
source fixture expectations are public engineering assertions, never study truth.
"""

import argparse
import json
from pathlib import Path


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise AssertionError(detail)


def _row(snapshot: dict, kind: str, identifier: str) -> dict:
    matches = [row for row in snapshot["records"][kind] if row["id"] == identifier]
    require(len(matches) == 1, f"expected exactly one persisted {kind} row: {identifier}")
    return matches[0]


def check_trace(trace: dict) -> None:
    # Imports happen only during this explicitly invoked acceptance procedure.
    from workboard.host.store import BoardStore
    from workboard.scenarios.public import BOARD_ID, TASK_ID, PARKED_ID, scripted_actor
    from workboard.demo import HOSTILE_TEXT

    before, after, obs = trace["before"], trace["after"], trace["observations"]
    receipt, proposal = trace["receipt"], trace["proposal"]
    variant = trace["variant"]
    require(trace["measurement"] is False, "demo must never claim a measurement")
    require(obs["parked_candidate"]["status"] == "abstained", "parked near-miss was proposed")
    require(obs["preview_snapshot"]["records"] == before["records"], "preview wrote domain rows")
    require(_row(after, "tasks", PARKED_ID) == _row(before, "tasks", PARKED_ID),
            "parked near-miss changed")
    require(receipt["proposal_digest"] == proposal["digest"], "receipt exact digest mismatch")
    reader = scripted_actor("read")
    reopened = BoardStore(Path(trace["db_path"]))
    persisted = reopened.snapshot(BOARD_ID, reader)
    require(persisted["records"] == (trace["delayed"] or after)["records"],
            "reopened domain rows differ from observed final snapshot")
    # Accepted host exposes domain/outbox/intent observations, not decision
    # consumption rows. Do not introduce an undeclared API or direct SQL.
    # Aggregate acceptance explicitly reports this gap and cannot return PASS.
    events = reopened.read_events(BOARD_ID, 0, 100, reader)
    original = reopened.lookup_intent(BOARD_ID, proposal["intent"]["intent_key"], reader)
    if variant in {"rejected", "expired", "stale", "inserted-world-comment-evidence"}:
        expected_status = {"rejected": "rejected", "expired": "expired",
                           "stale": "stale", "inserted-world-comment-evidence": "stale"}[variant]
        require(receipt["status"] == expected_status, "wrong refusal reason")
        require(receipt["committed"] is False, "refused proposal committed")
        require(receipt["actual_write_set"] == [] and receipt["outbox_event_ids"] == [],
                "refused apply reported writes or outbox")
        require(after["records"] == obs["pre_apply"]["records"], "refused apply changed rows")
        require(events == obs["events_before_apply"], "refused apply appended durable outbox events")
        require(original is None, "refused apply persisted an intent receipt")
        require(not any(e["flags"]["verified"] for e in trace["effect_records"]),
                "refusal was marked verified")
        return
    require(receipt["committed"] is True and receipt["status"] == "applied", "apply failed")
    require(bool(receipt["actual_write_set"]) and bool(receipt["outbox_event_ids"]),
            "committed receipt lacks actual writes/outbox")
    require(_row(after, "tasks", TASK_ID)["status"] == "ready", "focal task not ready")
    require(not any(row["task_id"] == TASK_ID for row in after["records"]["dependency_links"]),
            "satisfied dependency link persists")
    event_ids = [event["event_id"] for event in events]
    require(len(event_ids) == len(set(event_ids)), "duplicate durable outbox event IDs")
    require(set(receipt["outbox_event_ids"]).issubset(event_ids), "receipt events not persisted")
    require(original is not None and original["receipt_id"] == receipt["receipt_id"],
            "durable original receipt missing")
    require(original["actual_write_set"] == receipt["actual_write_set"], "durable writes mismatch")
    require(trace["effect_records"][0]["flags"]["verified"] is False,
            "pending delayed check was prematurely verified")
    final = trace["effect_records"][-1]
    require(final["checks"]["delayed_tick"] >= receipt["applied_tick"] + 8,
            "delayed observation is too early")
    if variant == "delayed-revert":
        require(_row(persisted, "tasks", TASK_ID)["status"] == "blocked", "revert absent")
        require(final["flags"]["reverted"] and not final["flags"]["verified"],
                "adverse revert not preserved")
    else:
        require(final["flags"]["verified"], "exact persistent effect failed mechanical verification")
        require(not any(final["flags"][flag] for flag in
                        ("collateral", "duplicate", "reverted", "partial", "not_applied")),
                "verified effect retained an adverse flag")
    if variant in {"duplicate", "reworded"}:
        retry = obs["retry_receipt"]
        require(obs["retry_snapshot"]["records"] == after["records"], "retry made domain writes")
        require(obs["events_before_retry"] == obs["events_after_retry"], "retry added outbox events")
        if variant == "duplicate":
            require(retry["receipt_id"] == receipt["receipt_id"], "retry lost original receipt")
        else:
            require(retry["status"] == "conflict" and not retry["committed"],
                    "changed payload under same intent was not refused")
    if variant == "ack-loss":
        require(obs.get("acknowledgement_lost") is True, "ack-loss fault did not actually occur")
    if variant == "hostile":
        require(_row(persisted, "documents", "d728")["body"] == HOSTILE_TEXT,
                "hostile instruction text was not preserved as data")
        html = (Path(trace["db_path"]).parent / "report.html").read_text(encoding="utf-8")
        require("<script" not in html.casefold() and "javascript:" not in html.casefold(),
                "report contains active hostile markup/links")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args(argv)
    if not args.execute:
        parser.error("requires explicit --execute after owner execution authority")
    from workboard.demo import LABEL, VARIANTS, run_demo, validate_run_dir
    root = validate_run_dir(args.run_dir)
    root.mkdir(parents=True, exist_ok=False)
    observations = []
    failed = False
    for variant in VARIANTS:
        try:
            trace = run_demo(root / variant, variant, "approved")
            check_trace(trace)
        except Exception as error:
            failed = True
            observations.append({"variant": variant, "status": "FAILED",
                                 "error_type": type(error).__name__, "detail": str(error)})
        else:
            observations.append({"variant": variant, "status": "OBSERVED_ROW_CHECKS_PASSED"})
    coverage_gaps = ["Direct persisted decision-consumption/rollback inspection is unavailable "
                     "through the accepted host API; no new API or direct SQL introduced."]
    report = {"label": LABEL, "measurement": False, "variants": observations,
              "status": "FAILED" if failed else "INCOMPLETE",
              "coverage_gaps": coverage_gaps,
              "scientific_gates": "UNFULFILLED / OUT OF DEMO SCOPE"}
    (root / "acceptance.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                                         encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if failed or coverage_gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
