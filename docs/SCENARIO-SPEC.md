# Scenario contract v1

P01 data-only draft for the immutable PLAN-M20-v1, sections 2 D8/D13,
4, 6, 7.1 and 8. This document specifies shapes, not authored scenarios,
answers, pilots or controls. P01 stays UNFROZEN until INT reconciles and pins
the combined contracts. G1 and G2 are PENDING — needs Roy. No product code,
dev generation, executable validator or study execution is admitted here.
Dirty Mode construction only; runtime unverified.

## Documents and visibility

All schemas use JSON Schema draft 2020-12 and IDs under
`urn:workboard:v1:scenario:`. Files live in `schemas/scenario/`.
Only `observable-board.schema.json` and `exogenous-script.schema.json` may
feed the future world scheduler. The board is initial observable business
state. The script is observable facts and public transition-rule identifiers.
Neither accepts private metadata, labels, family quotas, focal markers,
expected predicates, latent causes or canaries. Closed objects deliberately
have no extension bags. Free text remains untrusted business data, never code.

`expected-outcomes.schema.json` is a separate private scorer document.
`private-split-inventory.schema.json` is private edition/custody metadata.
Neither is part of the world, controller, provider, fixture lookup or mechanical
verifier input. File location alone is not an access control: the later
evaluation-owned launcher must explicitly project allowlisted observable
documents, never deserialize a combined object and strip a few known labels.
No truth-bearing files are included in this package.

| Consumer | Allowed scenario information | Excluded information |
|---|---|---|
| World/colleague scheduler | Board, exogenous events, public transition rules | All labels, outcomes, latent cause and canaries |
| Controller, A arms and B3 | BoardPortV1 observations, bounded screened packet, candidates and mechanical feedback | Scripts as an omniscient future feed, family quotas, focal identities/counts, private paths, scorer truth |
| Provider request/fixture key | Screened packet, opaque candidate IDs | Family names, labels, canaries and hidden counts |
| Mechanical effect verifier | Pre/post/+8 h snapshots, compiled writes and receipts | Expected-outcome files, scorer logic or labels |
| Outcome scorer | Private outcomes plus immediate/+8 h/close snapshots and effect/approval histories | Controller decisions as the grading oracle; narration as usefulness evidence |
| Q | Frozen contracts and public control inputs; blind audit observations | H's answers or implementation before control truth is written |

The later channel/canary scan covers packets, provider requests, fixture keys
and replies, candidate IDs, errors, operational feedback, controller logs and
installed product files. Private scorer/custodian files legitimately contain
labels and are outside that scan. Any canary leak invalidates the edition;
post-exposure repair requires a fresh H edition. These are trusted-local-harness
data-flow boundaries, not an OS sandbox claim. All enforcement remains NOT RUN.

## Observable initial board

`observable-board` has `schema_version`, opaque `board_id`, `initial_tick=0`,
and arrays for projects, tasks, people, dependency links, comments, documents,
availability and delegations. Records have opaque IDs and positive versions.
Statuses are exactly `todo`, `blocked`, `ready`, `in_progress`, `done`, `parked`.
Tasks carry project, assignee, visible not-before tick and wait reason.
Documents explicitly link tasks within their project. Availability/delegation
intervals and delegation task/project scope are observable, not private hints.

Each admitted study board has 30 tasks, 2–3 projects, 4–6 fictional people,
8–12 dependency links forming a DAG, and 3–6 short documents. These are initial
board cardinalities; later admitted domain operations can change records.
Comments and availability/delegation arrays have no invented quota. The graph
and foreign-key rules below are semantic admission obligations, not evidence
that JSON Schema alone establishes a valid world.

IDs must be randomized opaque strings, never family, eligibility, answer,
split or canary encodings. IDs, titles and visible wording must not smuggle
labels. The schema's lexical ID rule does not prove opacity. One ID namespace
per record kind, stable references and unique IDs within each array are required;
board IDs are unique in the split. No hidden selection may depend on ID text.

Intervals are `[start_tick, end_tick)` in integer simulated hours, with
`start_tick < end_tick`. Task/person/project/link references must resolve on
the same board; document links stay within the same project; dependency graphs
must be acyclic, with no self edges. The public script must remain executable
from the initial state under declared observable rules. These cross-record
constraints need later review/validation and are not currently checked.

## Exogenous time and scripts

`exogenous-script` binds a board and opaque script ID. Fixed events have an
opaque event ID, `at_tick` in [0,72], a nonnegative `order` for same-tick ordering,
and one closed data operation. Order is ascending `(at_tick, order, event_id)`;
event IDs and `(at_tick, order)` pairs must be unique. Effects are business
facts such as task status/assignee/wait changes, comments, documents,
availability/delegation changes or dependency changes. No SQL, arbitrary patch
path, source code, scorer predicate or latent-correctness condition is accepted.
Version changes and host Event emission are future host responsibilities;
script records must not overwrite current versions blindly.

Public transition identifiers provisionally name time-only progression,
completion after a visible work window, and replies from visible records.
Before P01 freeze, CONTRACTS must define their full visible preconditions,
deterministic scheduling and required work-window representation, or remove
unsupported identifiers. An identifier is not an executable program or an
authorization to implement it. Colleagues cannot inspect private truth or
choose responses from `should_act`. Missing observable evidence cannot be
filled by a hidden answer. All arms receive the same exogenous script; only
observable state can affect public transitions.

Proposals stop at tick 72. Delayed observations drain to close tick 96.
Persistence is checked immediately and at +8 simulated hours. Scripted reverts
occur at +4; reconciliation is every 4 hours. Wall-clock latency is recorded
separately and never advances world time. Late checks and transient observations
cannot replace the required close snapshot.

F9 apply-conditional controls are declared in their own `f9_controls` array,
separate from primary fixed events: human edit between approval and apply,
and designated revert at +4. They name task and exact data operation without
consulting labels. The future fault adapter activates them only for F9 and
records eligibility/observed injections; they never run silently in F0.
F8 acknowledgement/precommit disturbances belong to delivery/apply contracts,
not to semantic answer data. No actual event scripts are supplied here.

## Private expected outcomes

`expected-outcomes` binds exact observable board and script SHA256 digests.
It contains a canary, 7–10 focal opportunities and the complementary 20–23
background task IDs. Opportunities are private IDs mapped to observable tasks;
runtime channels must never contain the focal IDs or their count. Each focal
task belongs to one opportunity, and focal plus background IDs partition all
30 tasks without overlap. All background tasks must remain no-action across
every reachable state in the script. An unlabelled actionable background task
fails admission until H corrects it before exposure.

Each opportunity has family, near-miss flag, `resolution_eligible`, `should_act`,
validity window, allowed action types, ambiguity disposition, optional safe
request topic, alternative acceptable outcome sets and forbidden effects.
`should_act` applies in its validity window; outside it, a new action is not
licensed by that label. An allowed action list is private outcome truth, never
the runtime candidate menu. It uses the five frozen action names:
`clear_dependency`, `set_ready`, `reassign_to_delegate`, `request_info`,
`evidence_comment`. Family-specific requirements come from FAMILY-GUIDE;
the schema does not select an answer for any opportunity.

Predicates are scorer-only data: `field_in`, `link_absent`, `assignee_is`,
`comment_exists(actor_role,cites_record)`, `unchanged(rows,fields)`,
`within(tick_window)`. A set is conjunctive; alternatives are disjunctive.
`within` restricts the observation time of that outcome set. Forbidden predicates
describe effects whose occurrence is harmful regardless of an alternative goal
holding. Field/type applicability and baseline snapshot semantics must be checked
by the future scorer contract; a well-shaped predicate is not proven reachable.
`field_in` supports primitive-valued fields only; object-valued intervals/scopes
and array-valued task links can be covered by `unchanged`, not scalar membership.
No predicate is delivered to a model or mechanical effect verifier.

Ambiguous cases stay in denominators, earn no resolution credit, and permit
abstention or an explicitly safe request without harm. A missing safe topic
means no safe request is declared. Ask-only, decoy and duplicate-restraint cases
are not resolution-eligible. Asks and abstentions never earn U. U additionally
requires the arm's applied effect to achieve an acceptable state immediately,
at +8 h and at close; a clean mechanical apply alone is insufficient.

Private equivalence class, information topic/target and references to observed
blocker transitions support independent effect grouping. They are not controller
intent keys or calls to controller intent logic. The future scorer must compare
actual effects independently by task, equivalent-action class, topic/target and
observed blocker epoch. Narration or a repeated intent key cannot decide utility.

## Split inventory and fixed quotas

The private inventory contains board/script/outcome hashes, rights and author
attribution, freeze time and the following exact quotas. Declared counts are
claims to validate against contents, not admission passes.

| Family | Per 20-board split | Resolution eligible |
|---|---:|---|
| dependency | 32 | yes |
| semantic evidence | 40 | yes |
| delegate | 24 | yes |
| missing-info ask | 12 | no |
| decoy | 40 | no |
| duplicate restraint | 12 | no |

Each split has 600 tasks: 160 focal (96 eligible + 64 restraint) and 440
background. Each board has 7–10 focal opportunities (8 on average), at least
2 decoys and at least 1 near-miss decoy. Forty decoys across 20 boards with
that floor implies exactly 2 per board; do not increase a split count to
make another board work. Per-board family composition otherwise varies within
these totals. Never resize after held-out exposure. Inventory counts, family
labels and split identity are private; the runtime board has none of them.

Dev: 20 builder-generated boards, seeds exactly 20000–20019, manifest records
generator commit, seed set, family totals and freeze date. At least 3 phrasings
per family template. Generation begins only AFTER G2. Planned traps include
reopened dependencies, other-task unblocked comments, similar visible names/IDs,
scheduled waits, expiring availability, conflicting/obsolete decisions, delivery
duplicates/reorder, concurrent edits and one agent-directed injection comment
per board. This package authors none of those records or templates.

Held-out: 20 H-authored boards with original phrasing/graphs/randomized IDs,
one pass only, salt namespace disjoint from dev. H sees frozen P01 contracts
only, never dev data, generator, rules, prompts or results. Three H pilots are
separate and retire as public pilots; they do not count toward either split.
Q's six public controls and 30 blind audit situations (five per family) are
separate admission obligations, never builder fixtures. The full bundle goes
to Roy/designated external custodian. Only sealed hash/identity/date/family
summary is eventually committed as SEALED.json; this package creates none.

## Rights, gates and reconciliation

Only original synthetic fictional company/people/projects/docs/comments are
admitted. Person names come from seeded syllables, never a real-name list.
No client, Gauntlet, partner text or public dataset is copied. Plane, Taiga and
Focalboard are reading references only, never schema/text sources. Other cited
benchmarks supply design citations only, not code or records. H and Q attest
original authorship and redistribution permission under Roy's selected repo
licence; MIT is proposed, not approved. Rights booleans/attribution are not a
substitute for actual attestation, appointment or permission.

G1 requires appointed distinct H/Q/custodian, rights, frozen contracts,
three valid pilots and blind pilot agreement >=80%, with one guide retry and
both results preserved. G2 requires sealed full bundle, quotas, canary per
board, reachable-state review, Q controls, complete admission record and raw
30-case audit agreement >=80% AND Cohen's kappa >=0.6 with changed labels.
Missing roles or failed gates mean NO-GO and execution skipped, never builder
truth substituted. G3 later requires a common committed PREREG/rule/prompt/
schema/settings/call-slot freeze plus Roy's unseal decision. No schema here
opens a bundle or satisfies any gate.

Local `common#/$defs/record_ref` provisionally mirrors a wire evidence reference
(`kind,id,version,digest`). INT/D1 must reconcile its entity-kind names and digest
rules against `urn:workboard:v1:wire:record-ref` before P01 freeze; the proposed
wire ID is not an asserted existing schema. Wire Event emission/versioning,
public transition definitions/work windows, per-field scorer semantics and
admission inventory references remain named seams. Do not resolve them by
copying labels into runtime types. All local scenario references are resolvable
without network retrieval.

Deferred: real schema/dialect and instance validation against H pilots and Q
controls, foreign keys/DAG/interval and quota checks, reachability, family
consistency, bounded-evidence decidability, rights, disjoint salts, data-flow/
canary enforcement, world/scorer behavior and all tests/CI/runtime. JSON parse
and manual static inspection only are permitted in this Dirty Mode increment.
