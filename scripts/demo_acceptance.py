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
    from workboard.demo import HOSTILE_TEXT, _inspect_decision

    before, after, obs = trace["before"], trace["after"], trace["observations"]
    receipt, proposal = trace["receipt"], trace["proposal"]
    variant = trace["variant"]
    require(trace["measurement"] is False, "demo must never claim a measurement")
    require(obs["parked_candidate"]["status"] == "abstained", "parked near-miss was proposed")
    require(obs["preview_snapshot"]["records"] == before["records"], "preview wrote domain rows")
    require(_row(after, "tasks", PARKED_ID) == _row(before, "tasks", PARKED_ID),
            "parked near-miss changed")
    if variant == "not-before-boundary":
        boundary = obs["boundary_case"]
        results = boundary["selection_results"]
        require(len(results) == 8 and all(
            result == {"status": "abstained", "reason": "not_before_wait"} for result in results),
            "eight actual pre-boundary selections did not truthfully abstain")
        require(boundary["unrelated_result"] == {
            "status": "abstained", "reason": "read_budget_exhausted"},
            "unrelated tick reset the exhausted selection budget")
        old_epoch, new_epoch = boundary["initial_epoch"], boundary["crossed_epoch"]
        require(type(old_epoch) is int and old_epoch >= 0 and type(new_epoch) is int
                and boundary["unrelated_epoch"] == old_epoch and new_epoch > old_epoch,
                "actual host epoch failed relevant-boundary vs unrelated-tick distinction")
        require(before["tick"] == 0 and _row(before, "tasks", TASK_ID)["not_before_tick"] == 4
                and boundary["unrelated_snapshot"]["tick"] == 1
                and boundary["crossed_snapshot"]["tick"] == 4
                and boundary["unrelated_snapshot"]["records"] == before["records"]
                and boundary["crossed_snapshot"]["records"] == before["records"],
                "clock-only boundary observations changed domain rows or used wrong ticks")
        candidate = boundary["candidate"]
        require(candidate["status"] == "proposed" and candidate["proposal"] == proposal
                and proposal["intent"]["episode_epoch"] == new_epoch
                and candidate["preview"]["episode_read_calls"] == 1
                and candidate["preview"]["episode_reads_remaining"] == 7,
                "post-boundary proposal did not consume the new host episode's first reservation")
        require(trace["decision"]["decided_tick"] == 4 and receipt["applied_tick"] == 4
                and _row(after, "tasks", TASK_ID)["not_before_tick"] == 4,
                "boundary decision/apply did not bind actual eligible tick/domain state")
    reader = scripted_actor("read")
    reopened = BoardStore(Path(trace["db_path"]))
    persisted = reopened.snapshot(BOARD_ID, reader)
    require(persisted["records"] == (trace["delayed"] or after)["records"],
            "reopened domain rows differ from observed final snapshot")
    journal = _inspect_decision(reopened, trace["decision"], reader)
    require(obs["decision_before_apply"]["decision"] == trace["decision"]
            and obs["decision_before_apply"]["consumed"] is False,
            "decision was missing/consumed before its first apply attempt")
    require(journal == obs["decision_after_apply"], "reopened decision differs from observed journal")
    events = reopened.read_events(BOARD_ID, 0, 100, reader)
    original = reopened.lookup_intent(BOARD_ID, proposal["intent"]["intent_key"], reader)
    if variant == "precommit-abort":
        require(obs.get("precommit_abort_observed") is True, "precommit fault did not occur")
        require(receipt is None, "abort unexpectedly returned an apply receipt")
        require(after["records"] == obs["pre_apply"]["records"], "abort changed domain rows")
        require(events == obs["events_before_apply"], "abort persisted outbox changes")
        require(original is None and journal["consumed"] is False,
                "abort persisted intent or consumed the decision")
        require(trace["effect_records"] == [], "receipt-free abort fabricated an effect record")
        return
    require(receipt["proposal_digest"] == proposal["digest"], "receipt exact digest mismatch")
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
        require(journal["consumed"] is False, "refused apply consumed decision")
        require(not any(e["flags"]["verified"] for e in trace["effect_records"]),
                "refusal was marked verified")
        return
    require(receipt["committed"] is True and receipt["status"] == "applied", "apply failed")
    require(journal["consumed"] is True, "committed decision not durably consumed")
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
            require(retry["actual_write_set"] == [] and retry["outbox_event_ids"] == [],
                    "reworded refusal reported second writes/events")
            alternate = obs["alternate_proposal"]
            # A summary/ID-only difference cannot satisfy the comment example.
            from workboard.demo import _comment_pair
            from workboard.controller.compile import REWORD_SUFFIX
            from workboard.schemas.canonical import proposal_digest
            primary_action, primary_write = _comment_pair(proposal)
            alternate_action, alternate_write = _comment_pair(alternate)
            primary_body, alternate_body = primary_action["body"], alternate_action["body"]
            require(primary_body != alternate_body and alternate_body == primary_body + REWORD_SUFFIX,
                    "missing actual distinct approved comment bodies")
            require(proposal["digest"] != alternate["digest"]
                    and proposal_digest(proposal) == proposal["digest"]
                    and proposal_digest(alternate) == alternate["digest"],
                    "comment proposals lack distinct complete canonical digests")
            require(alternate["intent"] == proposal["intent"]
                    and alternate["read_binding"] == proposal["read_binding"]
                    and alternate["evidence_refs"] == proposal["evidence_refs"],
                    "reworded comment changed semantic intent or evidence binding")
            require({k: v for k, v in primary_action.items() if k != "body"}
                    == {k: v for k, v in alternate_action.items() if k != "body"}
                    and {k: v for k, v in primary_write.items() if k != "body"}
                    == {k: v for k, v in alternate_write.items() if k != "body"},
                    "alternate changed comment target/citations/topic/role")
            require([w for w in proposal["compiled_write_set"] if w["kind"] != "comments"]
                    == [w for w in alternate["compiled_write_set"] if w["kind"] != "comments"],
                    "alternate changed domain permissions")
            require(trace["decision"]["status"] == "approved"
                    and obs["alternate_decision"]["status"] == "approved"
                    and trace["decision"]["actor_kind"] == "scripted"
                    and obs["alternate_decision"]["actor_kind"] == "scripted"
                    and trace["decision"]["proposal_digest"] == proposal["digest"]
                    and obs["alternate_decision"]["proposal_digest"] == alternate["digest"],
                    "both exact comment bodies were not approved")
            require(_row(after, "comments", primary_write["id"])["body"] == primary_body
                    and _row(persisted, "comments", primary_write["id"])["body"] == primary_body,
                    "primary approved body not actually persisted")
            require(not any(row["body"] == alternate_body
                            for row in persisted["records"]["comments"]),
                    "alternate comment body persisted despite conflict")
            require(obs["intent_before_retry"] == receipt
                    and obs["intent_after_retry"] == receipt and original == receipt,
                    "retry changed the original durable intent receipt")
            alternate_journal = _inspect_decision(reopened, obs["alternate_decision"], reader)
            require(alternate_journal["consumed"] is False,
                    "changed-payload refusal consumed the alternate decision")
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
            observations.append({"variant": variant, "status": "OBSERVED_CHECKS_PASSED"})
    report = {"label": LABEL, "measurement": False, "variants": observations,
              "status": "FAILED" if failed else "OBSERVED_CHECKS_PASSED",
              "scientific_gates": "UNFULFILLED / OUT OF DEMO SCOPE"}
    (root / "acceptance.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                                         encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
