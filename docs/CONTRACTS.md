# Workboard v1 contracts (P01)

Status: construction source only; runtime, schema-instance validation and P01 freeze
are unverified. G1/G2 are PENDING â€” needs Roy, before any product code. These
contracts provide neither held-out answers nor role appointments. The immutable
PLAN-M20-v1 Â§Â§4.1, 5/P01, 7.5, 8 and 10 govern this document.

## Wire catalog and interpretation

The data-only schemas in `../schemas/wire/` use JSON Schema draft 2020-12.
Each filename without `.json` has ID `urn:workboard:v1:wire:<filename>`:
`common`, `action`, `candidate-bundle`, `proposal`, `decision`, `approved-bundle`,
`apply-receipt`, `event`, `effect-record`. Resolve URNs through a local schema
registry; never fetch schemas over the network. `common` contains reusable `$defs`.
Objects are closed; opaque identifiers must not encode family, focal opportunity,
expected answer, correctness or canary data. SHA256 values are lowercase hex.

Schemas enforce structure and selected bounds. The relational invariants below are
mandatory future policy/host/verifier checks; JSON parsing is not their validation.
Schema acceptance alone never authorizes application or study admission. No product
implementation, executable predicates, generated boards or evaluation truth is here.

Ticks are integer simulated hours, not wall-clock timestamps. Script events occupy
0â€“72; proposals stop at 72; observations drain through close at 96. A delayed effect
check is scheduled at apply tick +8; a scripted revert at +4 must remain visible.

## BoardPortV1 and ClockPort

BoardPortV1 is an in-process versioned boundary, not a server. It provides:

| Operation | Contract |
| --- | --- |
| `capabilities()` | Return declared capabilities before admission; no optimistic fallback. |
| `snapshot(board_id)` | Consistent observable board snapshot, row versions, scope revision and snapshot digest, without evaluation labels. |
| `read_task(id)` | Board-scoped task or explicit missing result, including version. |
| `search_text(task_id, query, limit)` | Task/project-scoped bounded visible records, explicit truncation, no hidden labels. |
| `read_record(kind, id)` | Typed observable record plus version and digest; missing is explicit. |
| `read_events(after_seq, limit)` | Ordered board-scoped events after exclusive cursor; events are hints, never authoritative state. |
| `apply(ApprovedBundle)` | Atomically admit the exact proposal/decision or return a refusal receipt with zero domain writes. |
| `lookup_intent(key)` | Stored original durable receipt or explicit absent result, including after lost acknowledgement. |

Read calls are capped at eight per visible task/blocker episode, including packet
construction. Limits, cursor and board identity are checked, with no implicit
cross-board search or uncapped tool retries. Missing needed evidence or explicit
truncation leads to abstention, never invented evidence. At most one additional
record may be requested from the code-generated menu. No labels enter fixture keys,
provider requests, errors, operational logs, evidence or candidate IDs.

Required capabilities: `tasks`, `dependency_links`, `comments`, `documents`,
`availability`, `delegations`, `atomic_bundle_cas`, `evidence_scope_revision`,
`intent_receipts`, `virtual_clock`. A missing capability raises
`UnsupportedCapability` and refuses the operation before mutation; no lossy status
mapping or partial emulation. A future adapter must pass P02/P07/P08 controls.

ClockPort exposes `now()` and monotone `advance_to(tick)` with an injectable clock.
Reject backwards/out-of-horizon moves. Wall-clock model latency never advances it.
Task status vocabulary: `todo`, `blocked`, `ready`, `in_progress`, `done`, `parked`.
Domain tables: projects, tasks, dependency_links, comments, documents, people,
availability, delegations. Availability/delegation intervals have explicit task or
project scope and must be effective throughout the relevant work window.

## Events and candidate construction

Event fields are event_id, board_id, seq, entity_kind, entity_id, entity_version,
occurred_tick, origin and payload_digest. Sequences are monotonically increasing
within a board; event IDs are stable across duplicate delivery. Insert outbox rows
in the same transaction as domain changes. Re-read current state for drops, old
versions and reordering; an older event cannot overwrite newer state. Self-events
are audited without waking the same unchanged intent indefinitely.

Code generates the candidate menu and all IDs, versions, permissions, read bindings
and exact compiled writes. A model selects an opaque candidate ID or abstains; it
supplies no SQL, keys, versions, predicates or permissions. Free text is allowed only
inside the `evidence_comment` template and is screened as untrusted data.
`request_info` text/topics are policy generated from a finite frozen vocabulary.
All actions in a bundle refer to the same board and focal task.

| Template | Permitted effect and required evidence |
| --- | --- |
| `clear_dependency` | Delete the exact task/dependency link only when the dependency is currently satisfied; bind link and dependency versions. |
| `set_ready` | Set only the target task status to ready when all blockers are clear; bind every blocker, wait/park/not-before condition and absence scope. |
| `reassign_to_delegate` | Set only assignee_id to an explicitly scoped, effective delegate while the prior assignee is unavailable through the work window; bind availability/delegation evidence. |
| `request_info` | Insert one policy-owned comment for a missing finite information topic; no status or assignee change; one request per semantic topic/epoch. |
| `evidence_comment` | Insert one screened comment citing visible records; a comment or narration alone cannot prove a resolution. |

One bundle has at most three domain writes and one comment, at most four actions
and four compiled writes total. `request_info` and `evidence_comment` share the one
comment allowance. Compiling must produce exactly the listed effects, without due
dates, arbitrary links, labels, extra fields, SQL or implied follow-up writes.
Duplicates/no-op candidates are inadmissible. Evidence refs bind kind/id/version/
digest; the full read set includes evidence rows, dependency rows, target rows,
availability, delegation and all policy inputs, not just the written task.

## Proposal, digest, approval and intent

Proposal adds proposal_id, predicted_summary and expires_tick to CandidateBundle.
`read_binding.rows` is the full `read_set_versions`; `evidence_scope_revision` is
nested in that binding. It detects relevant inserts, updates and deletes, including
new evidence contradicting a claim of absence. Effective-time bounds are carried
in the same binding. These names are the normative v1 representation for consumers;
there is no second unbound revision at proposal top level.

Canonical digest input is the complete proposal excluding its own digest, with
stable JSON object-key ordering, UTF-8, compact separators, preserved array order
and no non-finite numbers. Candidate digest follows the same rule on candidate
content. The proposal digest is recomputed after adding proposal fields. All
embedded identities must agree; no duplicate row keys or contradictory writes.

The code-owned intent tuple is `(board_id, task_id, action_kind, semantic_target,
episode_epoch)`. Hash its canonical JSON array with SHA256 for intent_key. For a
multi-action bundle action_kind/semantic_target designate its primary semantic
change; secondary actions are inseparable compiled consequences, not a way to
bypass dedupe. Equivalent action classes and normalized request topics are frozen
policy definitions. Reworded comments, new delivery IDs, proposal IDs or retries
never advance epoch. Only a real relevant blocker/state transition does. Persist
intent receipts for the entire run. Same key and same payload returns original
receipt; same key and different payload is conflict, never a second effect.

Decision is append-only: approved, rejected, expired or superseded. Bind operator
label, actor kind, exact proposal digest, full read binding, decided tick and
expiry; scripted approvals are visibly scripted, never human judgment. Expiry is
exclusive: apply tick must be earlier than expires_tick and effective_until_tick,
and at least effective_from_tick. Reject invalid/reversed intervals and approvals
made before the bound evidence exists. A decision may approve only one exact
proposal, once; it cannot add effects or extend expiry. Supersession appends a new
journal record and invalidates the old authorization without rewriting history.

## Atomic apply and recovery

Inside one BEGIN IMMEDIATE transaction: reload proposal and journal; check all
IDs/digests, active approval, one-use decision, read versions, scope revision,
effective time, intent receipt and required capabilities; consume the decision;
write all compiled domain effects, all outbox rows and the intent receipt; commit.
Any mismatch/refusal rolls back domain effects and decision consumption together.
No half-applied bundle is success. Append-only is an application invariant, not
tamper-proof storage. A rejected/expired/superseded decision cannot be revived.

After an acknowledgement loss, lookup_intent returns the original committed
receipt and no reapply occurs, even though its decision is already consumed.
A pre-commit crash leaves zero durable effects/outbox/receipt; a post-commit crash
leaves exactly one. Actual writes in receipts are observations, not permission:
noncompiled writes and over-limit writes must be preserved for collateral review.
A same-target no-op or silent no-op is not verified application. Out-of-board
mutation invalidates the run. Refusal receipts have committed=false and no actual
domain writes; applied requires committed=true, exact writes and durable outbox.
The required receipt field `applied_tick` is the attempt/observation tick on a
refusal; it asserts an application time only when committed=true. It never
represents a successful effect merely because it is present.

## Mechanical effect records

Verifier inputs are pre/post/delayed snapshots, compiled writes and receipts only.
It cannot import agent/controller intent logic or evaluation truth. Independently
group actual effects by task, equivalent-action class, topic/target and blocker
epoch observed from transitions; two different keys do not hide a duplicate.
Only infrastructure log/outbox/attempt fields and required version/timestamp bumps
are noise. Never ignore domain status, assignee, links or comment content.

Flags coexist: collateral, duplicate, reverted, partial, not_applied, verified,
superseded_by_human. Set every applicable adverse flag even with human supersession.
Display precedence: collateral > duplicate > reverted > partial > not_applied >
verified; pending means mandatory observations are not complete and is not success.
Verified requires exact actual writes, no collateral, no duplicate, immediate and
+8-hour checks passed and no adverse flag. Delayed pending cannot be verified.
Legitimate ready â†’ in_progress â†’ done is forward progress, not failed equality;
actual revert-to-blocked is a persistence failure. Human repair/supersession is
attribution only and never erases prior harm or duplicate effects.

Controller feedback vocabulary is only applied, stale, not_applied, partial,
duplicate, collateral, not_persisted. Display `verified` maps to mechanical applied;
reverted maps to not_persisted. Approval/adapter refusal details stay operational,
without scorer labels or hidden answers. An immediate applied observation does not
promise delayed persistence. No effect field asserts semantic usefulness: outcome
scoring and U/W/N/C/D belong exclusively to evaluation, with independent truth.

## P01 boundary and later validation

D2 scenario schemas may reference these wire URNs through their local resolver;
scenario/evaluation labels must remain outside wire records. INT reconciles the
combined P01 docs and freezes their exact commit. That freeze must also name the
finite request-topic vocabulary and equivalent-action normalization vocabulary;
the present string fields intentionally do not assert membership in an unfrozen
vocabulary. Freeze those definitions before product policy implementation.
Until then P01 is UNFROZEN.
No schema-instance validation, H pilots, Q controls, runtime, tests, CI, SQLite
crash/security/isolation checks or study measurements have run in this package.
Later authorized owners must validate the schema dialect/URN registry, relational
invariants, full read-set coverage, canonical hashing and cross-document seams,
then exercise P02/P07/P08 after actual G1/G2 admission. H/Q/custodian, rights/licence,
audit/seal, model/key/spend, unseal and publication remain Roy decisions.
