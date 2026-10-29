# Scripted demo source guide

**Construction source only; all invocation examples and acceptance are NOT RUN.**
Explicit owner execution authority and final combined-source review are required
before trying them. Nothing here is an empirical study or an efficacy result.

The [README](../README.md) contains PowerShell source-PYTHONPATH examples for an
already available Python 3.12+ interpreter. No installation is needed to describe
the intended source entrypoints. No command, database or service was started
while constructing these files. No keys or paid calls are used.

## Source navigation

- [CLI](../src/workboard/cli.py): `python -m workboard.cli` defaults to a read-only
  planned fixture preview. `--execute` requires `--run-dir` and either
  `--manual-approval` or `--scripted-approval approved|rejected`.
- [Driver](../src/workboard/demo.py): explicit `run_demo(...)` creates one fresh
  run directory, then uses the host, policy, approval, verifier and report APIs.
  It never mutates a database through private SQL or creates a provider fallback.
- [Public board](../fixtures/public/board.json) and
  [loader](../src/workboard/scenarios/public.py): original fictional public
  SCRIPTED records, not held-out truth. The loader projects scenario
  `depends_on_task_id` to wire `dependency_task_id` without adding hidden labels.
- [Adverse scripts](../src/workboard/sim/scripted.py): monotone explicit time,
  sourced world-comment evidence and an adverse status revert through host APIs.
- [Offline provider](../src/workboard/shared/offline.py): exact fixture replies;
  missing keys refuse. Live dispatch refuses and never discovers credentials.
  Declared 2 calls/attempt, 2 attempts/episode, 48 calls/board and 3000/400 token
  bounds do not turn byte counts into billed-token measurements. The B2 demo
  makes no model calls.
- [Acceptance source](../scripts/demo_acceptance.py): one later deterministic
  aggregate entrypoint, no shipped result artifacts. The script inspects actual
  reopened rows, outbox, intent receipts and the durable decision read seam.
- [Verifier limitations](DEMO-LIMITATIONS.md): exact observations, history,
  actor attribution, pending verification and escaped-report boundaries.

## Intended paths and observable assertions

These are public engineering assertions in source, not reported test results.

| Variant | Intended observed check |
| --- | --- |
| `happy` | Completed dependency link clears; focal task becomes ready; parked near-miss stays unchanged; exact immediate effect remains pending until the actual +8 observation. |
| `rejected` | Explicit rejected decision reaches the host as a refusal attempt; zero domain/outbox/intent changes and decision unconsumed. D2's approved-only bundle helper is not misused. |
| `expired` | Apply at the exclusive expiry boundary refuses with no domain writes or decision consumption. |
| `stale` | Scripted status change after approval invalidates the bound task version/scope; apply refuses. |
| `inserted-world-comment-evidence` | A sourced world comment inserted after approval changes evidence scope; apply refuses. No document insertion API is assumed. |
| `duplicate` | Exact same approved bundle returns the original receipt and adds no rows or outbox events. |
| `reworded` | Request exactly one cited auxiliary evidence comment via `with_evidence_comment=True`. Approve its primary body and primary+`REWORD_SUFFIX` alternate before applying either, with distinct full digests and unchanged citations/topic/domain intent. Require the primary body persisted, alternate absent, unchanged original intent receipt, no second rows/events and alternate decision unconsumed. Missing actual comment refuses; summary/ID-only changes cannot pass. Manual mode is refused. |
| `hostile` | Hostile instruction-like text remains document data, parked task stays untouched, and the report contains no active script/link. |
| `delayed-revert` | Actual scripted +4 status revert remains adverse at +8; the expected adverse flag is required instead of expecting a verified happy effect. |
| `ack-loss` | Named post-commit exception is actually observed; lookup recovers the stored exact receipt, without reapplying. |
| `precommit-abort` | Named precommit exception is actually observed; reopened domain/outbox/intent and decision consumption show rollback. Receipt stays null; none is fabricated. |

Manual mode displays the exact proposal digest and requires
`approve <exact digest>`; anything else is a rejection. The human label describes
an explicit local input, not authenticated identity. Scripted choices are marked
as scripted. Neither has scientific independence.

## Future outputs and failures

A later `run_demo` writes `board.sqlite3` (with possible SQLite sidecars),
`trace.json`, `report.html`, `report.json` and `report.txt` only into the explicitly
supplied fresh local directory. Paths must be absolute, outside OneDrive and the
source checkout; existing run directories refuse replacement. Host snapshots and
journal reads supply observations. Reports escape all values and keep links inert.
An early failure may leave a partial run folder; it does not synthesize successful
stages or replace that folder on retry.

The aggregate acceptance script uses separate variant folders and writes
`acceptance.json` from actual checks. A nonzero exit means at least one observation,
required API or assertion failed. Expected refusals/aborts/reverts pass their own
engineering assertion only when the actual adverse outcome and absence of
unauthorized durable effects are observed. This is not a scientific gate pass.

## Integration assumptions and deferred work

The final-review comment repair declares
`propose(..., with_evidence_comment=True)` and
`controller.compile.REWORD_SUFFIX` for this variant only. D2 owns that optional
producer and strict approval-body validation; they are not in the original frozen
review baseline. D3 imports the suffix only during explicit future execution,
requires exactly one real action/insert pair, changes both exact bodies together,
and recomputes the completed proposal digest. The default policy and all other
variants remain domain-only. Final joined affected review must compare the actual
repaired D2 producer; absence is a failure, never a fallback or runtime pass.

The accepted D1 producer is present in this checkout, providing durable
`reserve_read(board_id,task_id,actor)` and
`inspect_decision(board_id,decision_id,actor)` plus complete ordered,
nonrecursive observed history. These are constructed source, not executed proof.
The integrated D2 consumer reserves through the durable host API before
selection and approval reads and uses its returned host epoch. It has no
per-Store fallback ledger. Observer-only driver/verifier snapshots are outside
that selection budget. Reopening a Store must not reset the selection cap;
using one Store here is convenience, not runtime proof of that property.

D3 consumes these APIs without reimplementing either producer. Missing decision inspection fails closed;
no direct journal SQL, fallback cache or unconditional success is provided.
`before.verification_context` binds the actual proposal/decision on a copied
snapshot. D3 never sets `history_complete` or fills a canned history. Missing,
uncertain or discontinuous observation history must remain pending and cannot
pass the happy acceptance assertions. Final combined-source review is pending,
followed by explicit execution authorization and actual
SQLite/approval/rollback/history/report checks.

Original scientific G1/G2/G3 remain UNFULFILLED/out of demo scope. Public fixtures
and builder functions are delegated stand-in, not human-independent. Runtime,
tests, builds/CI, schema-instance checks, security/durability and all measurements
remain unverified. USD 0; no API-key placeholder, model service, held-out data,
real unseal, publication or deployment is needed for this source package.
