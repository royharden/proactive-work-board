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
sorted JSON object-key ordering, UTF-8 without BOM, compact separators,
unescaped Unicode, preserved array order and no non-finite numbers (v1 numeric
record values are integers). Candidate digest follows the same rule on candidate
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

Scenario schemas reference these wire URNs through their local resolver;
scenario/evaluation labels must remain outside wire records. INT reconciles the
combined P01 docs and freezes their exact commit. The finite topics, action normalization and public transitions below are
part of that combined contract pin; schema shape does not prove their relational
invariants or authorize product policy implementation.
Until then P01 is UNFROZEN.
No schema-instance validation, H pilots, Q controls, runtime, tests, CI, SQLite
crash/security/isolation checks or study measurements have run in this package.
Later authorized owners must validate the schema dialect/URN registry, relational
invariants, full read-set coverage, canonical hashing and cross-document seams,
then exercise P02/P07/P08 after actual G1/G2 admission. H/Q/custodian, rights/licence,
audit/seal, model/key/spend, unseal and publication remain Roy decisions.


## Reconciled representation boundaries

SCENARIO-SPEC defines the closed initial records and private scorer selectors.
Wire/storage entity kinds are projects, tasks, dependency_links, comments,
documents, people, availability, delegations. Private scorer singular kinds use
its total explicit mapping; type-definition names and delegation scope.kind
are separate domains, never aliases accepted in wire objects. Canonical evidence
reference: urn:workboard:v1:wire:common#/$defs/evidence-ref.

Initial records have versions >=1. Observation references allow version0 without
claiming that a row is absent or that a wire receipt is an initial board. External
refusal/recovery observations retain exact source IDs, versions and fields even
when they lie outside the initial scenario profile; never coerce them to pass it.
For the shared study profile, generated entity/proposal/candidate/decision/receipt
IDs use the scenario lexical subset (1-128 ASCII alphanumerics, underscore, hyphen,
starting alphanumeric). Wire permits broader nonempty strings. Stored comments
use body<=4000 characters in that study profile; wire observations remain lossless
if a broader adapter reports other text. Broader observations cannot be silently
inserted as narrower scenario data. Version and ID constraints apply to references
as well as records, and are not claims of arbitrary adapter compatibility.

Initial/scenario dependency depends_on_task_id projects to wire
dependency_task_id; link.id/task_id retain their values and versions. The two
field names are not aliases inside either closed shape. Canonical wire observable
dependency payloads use the latter name; other observable fields retain their
names. All evidence/citation digests are SHA256 of the complete versioned payload
after this explicit projection, with sorted JSON object keys, preserved array
order, UTF-8 (no BOM), compact separators, unescaped Unicode and no non-finite
numbers. Hashes are lowercase hex. For v1, numeric data in hash-bearing records
is integer-valued; reject unsupported floating numbers rather than guessing their
serialization. File artifact hashes instead bind exact delivered bytes, without
normalization. Proposal/candidate/intent digests use the same canonical serializer,
and only the object's own digest field is omitted when computing that object's
digest. Recompute after projection; do not relabel an old digest as a new one.

Stored comment provenance follows the closed scenario common comment shape.
Human actor_id resolves a board person; world/agent/rules use null, never a fake
person. Initial origin has no source IDs; exogenous origin binds its actual
enclosing event_id or F9 control_id; arm origin binds the exact proposal_id and
has null source_event_id. Scripted human edits stay role=human even though their
source is a simulator; world is a distinct nonperson actor role. Initial comment
occurred_tick must be0 (the initial snapshot instant); exogenous comment
occurred_tick must equal the actual enclosing event/control tick. These are
semantic admission requirements, not claims that shape validation proves them.
The host projects
compiled comment id/task_id/body/cites/topic/actor_role unchanged, adding version1,
occurred_tick=commit tick, origin=arm, actor_id=null and proposal provenance.
Those host metadata additions are declared insertion metadata, not arbitrary extra
domain permission. They must be exact and are checked; ignoring an authorized
version/tick bump never ignores body/cites/topic/provenance. The proposal's immutable
arm-run journal association supplies run/arm identity without putting it in person
IDs or model-visible text. A missing/mismatched journal source is not attributable
success. Scorer actor_role=arm matches stored agent OR rules for that evaluated
arm's proposal/receipt history only; human/world match themselves. Retain the
original role/origin/source IDs through grouping. Initial/exogenous cites and topic
are explicit (empty cites/null topic allowed), never inferred from business prose
or private answers. Existing comments cannot be edited by these templates.

## Finite topics and equivalent actions

The finite information-request vocabulary is exactly:

| Topic | Missing observable information it denotes |
| --- | --- |
| decision_record | Current task-linked business decision evidence. |
| dependency_state | Current state evidence for a linked dependency. |
| delegation_scope | Explicit task/project authority of a delegation. |
| availability_window | Effective availability of the relevant person. |
| work_window | The task's explicit visible work interval. |

A topic names an information gap, not an answer, family label or rule to act.
No catch-all/free-text topic is admitted. request_info requires one of these
values. A stored comment topic is one of them or null. evidence_comment uses null;
request_info uses its actual topic. Code owns request text/topics; model free
text remains confined to evidence_comment. Private safe_request_topic uses the
same vocabulary or null; deciding whether it is safe remains independent truth.

Equivalent-action classes are the five existing template names:
clear_dependency, set_ready, reassign_to_delegate, request_info, evidence_comment.
For each actual effect the observer derives its own class: dependency deletion,
status-to-ready change, assignee change, finite-topic request comment, or
null-topic cited evidence comment, respectively. This is classification of effects,
not a decision policy. No new action or permission is introduced. Unknown effects
are collateral observations, not dropped because they lack a valid class.

Per-action semantic targets are canonical JSON arrays: clear_dependency uses
[dependency_task_id] (not the mutable link-row ID); set_ready uses [task_id,"ready"];
reassign_to_delegate uses [delegate_id]; request_info uses [finite topic];
evidence_comment uses the sorted unique array of [kind,id] cited pairs.
For the last, versions/digests/body changes do not change semantic identity.
For every class its target digest is SHA256 of that array using the serializer
above. Task/board IDs remain in the outer intent tuple.

For a multi-action bundle, primary action_kind is the first present class in the
order clear_dependency, set_ready, reassign_to_delegate, request_info,
evidence_comment. The bundle semantic_target is SHA256 of a sorted unique JSON
array of [class, per-action-target-digest] pairs for its domain actions
(clear_dependency/set_ready/reassign_to_delegate). For a comments-only bundle it
is SHA256 of the corresponding one-element pair array. An auxiliary comment on a
domain bundle does not change the domain bundle's semantic identity. Repeated or
contradictory normalized actions fail admission, never silently disappear.
The write cap, exact approved body/citations/topic and one-comment limit still
apply. A changed auxiliary comment under the same key is payload conflict,
not a new intent. Compute intent_key from the original five-part tuple with
this normalized primary class and bundle target. Rewording, new deliveries,
proposal IDs or changed evidence versions never create a new key.

For each task/blocker episode, the public episode_epoch starts at0 and increments
only on an observed relevant change: dependency relation/state, task blocker/status,
assignee, effective delegation/availability/work-window, or substantive task-linked
business evidence changing that blocker. Timer ticks matter only where they cross
an actual relevant effective boundary. Cosmetic wording, version-only bumps,
repeated notifications and unrelated rows are not transitions. Observe pre/post
state to distinguish them; do not read a latent blocker label. Bind a proposal's
epoch to the actual observed history. Reopening a real blocker starts a new episode;
rephrasing the same unresolved fact does not.

Scorer and mechanical verifier independently group persisted effects by task,
per-effect class/target and the blocker epoch reconstructed from observable
history. They use the public definitions independently; they never call/import
controller intent code or use its key as truth. Bundle regrouping, two different
keys or a changed auxiliary comment cannot hide a repeated primitive effect.
Private equivalent_action_class names the relevant primitive class, and
information_topic_or_target is its finite topic for request_info, otherwise its
per-action target digest. Those private declarations must be checked against
actual observations, never fed to the controller or treated as a result.

## Supported public world transitions and time boundaries

Task.work_window is a required nullable half-open interval [start_tick,end_tick).
Null schedules no autonomous work. A nonnull work window is integer-valued with
0<=start<end<=96. It is observable business data, not a hidden readiness answer.

Only advance_time_only and complete_ready_task_after_visible_work_window are
supported transition IDs. Unknown IDs fail scenario admission. advance_time_only
permits monotone clock advancement and fixed exogenous facts without autonomous
mutations. It may coexist with the completion ID as the clock mechanism, not as
a second producer of completion effects. The automatic reply ID is removed:
no source-selection/reply representation was frozen. Replies must be explicit
exogenous comment facts with source provenance, never chosen from hidden answers.

For complete_ready_task_after_visible_work_window, at window start the current
task must be ready, have an existing assignee, no wait_reason, no active
not_before restriction, all remaining linked dependencies done, and consistent
availability declaring that person available for the whole interval. No matching
available interval or any overlapping unavailable interval fails the precondition.
A successful start changes status to in_progress. Otherwise no change occurs and
the single window is not retried. At window end, completion changes status to done
only if the assignee stayed the same, status stayed in_progress and the dependency, wait/not-before and
availability conditions held throughout [start,end), plus
current task/dependency/wait state still permits completion. Intervening invalidation
is remembered from observable history, so undoing a bad edit just before end is
not treated as uninterrupted work. No missing fact is supplied by a hidden answer.
Failure leaves current state unchanged; it never reverses human or exogenous edits.
No dependency deletion, reassignment or reply/comment is implied by this transition.

At each tick process fixed exogenous events first in (order,event_id) order,
then completion ends and then starts, each in task-ID order. F9 pre-apply edits
occur at their named approval/apply boundary, and revert controls at commit tick+4
before that tick's public transition checks; ties use control_id order.
Each mutation rechecks current observable state, increments its actual host version,
and emits its outbox atomically. Script replacement records supply declared
business data, not authority to overwrite host versions: on insert, declared
version must be1; on replacement, it must match the current version before the
host increments it. A mismatch is an inadmissible script/explicit fault observation,
never silent overwrite. Duplicate comment IDs cannot become comment edits.
At a work-window end, availability coverage is evaluated historically over
[start,end), so an interval ending at that boundary covered the work; current
task/dependency/wait changes at the boundary can still block completion.
Fixed script events end by72, while work progress and delayed observations may
drain through96; wall-clock latency never advances simulated time.

Observation ticks range0..96. Interval starts range0..96 and exclusive endpoints
may range1..97; 97 is a boundary sentinel, never a clock tick or scheduled event.
Thus end96 excludes instant96, and a private within window that must contain the
close snapshot may end97. Work windows still end<=96; proposal/effective-time
bindings retain wire expiry bounds and apply before both exclusive expiries.
New proposals stop before72. H must choose outcome validity/within windows
consistent with required immediate/+8/close observations; no silent inclusive-end
exception or discarded close check is allowed. All intervals require start<end,
and no endpoint value advances the clock beyond96.

These are documentary/data-schema obligations. Product world code, B3 rules,
agent prompts, scorer code and executable validators remain blocked by G1/G2.
