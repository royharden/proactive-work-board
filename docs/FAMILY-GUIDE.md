# Workboard family guide (P01)

Status: documentation for contract construction only. P01 is UNFROZEN until INT
pins the combined contract commit. G1/G2 remain PENDING — needs Roy, before any
product code, dev generation, rulebook or agent prompt. Runtime and data-only
pilot/control validation are NOT RUN. This guide creates no study results.

Read [CONTRACTS.md](CONTRACTS.md) for BoardPortV1, allowed action templates,
approval/read-set bindings, intent epochs and mechanical effects. Read
[SCENARIO-SPEC.md](SCENARIO-SPEC.md) for scenario fields, schemas, exogenous scripts
and private/public projections. The latter is a provisional sibling reference at
this package's base; INT reconciles it with the scenario package before freezing.
This guide defines family meaning; it does not duplicate the scenario schema.
Immutable PLAN-M20-v1 §§2/D3–D8, 6, 7.1 and 8 remain authoritative.

## Audience, examples and independence

Independent H and Q later receive the frozen P01 contracts, not implementation,
generators, B3 rules, prompts or results. Roy appoints them and the custodian.
Builders never fill those roles or author held-out data. H supplies three pilot
boards and the twenty-board held-out edition; Q supplies the six public control
boards before seeing hidden audit inputs or implementation. No such data is
provided here. Fresh builder-child review is not independent study review.

Each example below is a deliberately incomplete illustrative prose vignette,
required by P01 to explain the concept. It has no board/task identifiers, event
script, label record, acceptable-outcome set, forbidden-effect set or scored truth.
It is not a pilot, fixture, control, generated board or reusable evaluation case.
The wording is not a template for H: H must use original phrasing and graph
structures. Family definitions constrain coverage, not a lexical cue or answer
lookup. Examples never prescribe a B3 decision rule or model prompt.

## Six families

| Family | Defining distinction | Eligibility class |
| --- | --- | --- |
| dependency | A task's blocker is an explicit dependency relation whose current observable state matters. | Resolution-eligible when an admitted opportunity has a genuine resolvable blocker. |
| semantic-evidence | Current task-linked business evidence establishes whether a blocker has been settled; graph state alone is insufficient. | Resolution-eligible for admitted genuine resolution opportunities. |
| delegate | A scoped delegation and effective availability determine whether reassignment can resolve the blockage. | Resolution-eligible for admitted genuine delegation opportunities. |
| missing-info ask | A required fact is unavailable within bounded visible evidence and a finite topic can be requested. | Restraint/ask-only; no resolution credit. |
| decoy | A task looks stalled but a change is unwarranted, including a plausible near-miss. | Restraint; no resolution credit. |
| duplicate-restraint | An apparently new wake or proposal refers to an already-served semantic intent in the same relevant episode. | Restraint; no additional resolution credit. |

### Dependency

A dependency opportunity concerns an explicit link to another task. Its current
state, other blockers and any wait/park restrictions are material; an old wake
hint or a historical completion message does not establish current readiness.
The family covers dependency-based resolution, with reopened/changed dependencies
available as traps in the independently authored scenario design. The allowed
wire vocabulary is `clear_dependency` and, where justified, `set_ready`, possibly
with the single allowed evidence comment. Family membership grants no writes.

**Illustrative prose example:** A preparation task is waiting on a separate review
whose current completion state is visible, while another prerequisite still needs
inspection. This illustrates the dependency relation, not an approved bundle.

### Semantic-evidence

The material evidence is observable business text such as a decision document or
comment linked to the task and project. Distinguish current, relevant evidence
from obsolete, contradictory or similarly worded evidence about a different task.
A title containing a promising word is not a hidden correctness label. H must
make a situation decidable from the bounded evidence, or explicitly ambiguous;
correctness cannot depend on private author intent or inaccessible context.

**Illustrative prose example:** A planning item awaits a business decision recorded
in a document, while an older comment describes a previous version of that
choice. This illustrates the need for task linkage and evidence currency.

### Delegate

This family concerns a blocked assignment, an explicitly scoped delegation, and
observable availability intervals. Scope may be task or project specific. The
relevant work window and effective-time conditions matter, not an unqualified
statement that a colleague is generally available. No inference about real people,
performance or suitability is allowed. `reassign_to_delegate` changes only the
admitted assignee field and cannot create authority absent from visible records.

**Illustrative prose example:** An unavailable owner has a recorded backup for one
project during a limited interval, and the work item belongs to that project.
This illustrates scoped authority and timing without declaring an outcome.

### Missing-info ask

An ask-only opportunity lacks a required fact despite the permitted bounded reads.
It separates seeking information from changing task state. `request_info` is one
policy-generated comment using a finite frozen topic; arbitrary new topics or
repeated reworded requests cannot create fresh intents. The request text is not a
model-authored instruction channel. Receiving an answer later does not turn the
original ask into a resolution; any later admitted resolution is scored on its
own actual state effect under the independent outcome definitions.

**Illustrative prose example:** A blocked item refers to a decision location that
is absent from the available task-linked records. This illustrates a missing
information topic, without supplying a request or a scored answer.

### Decoy, including near-miss

A decoy is an apparent opportunity where a change is inappropriate in the labelled
validity window. Examples of distinctions include a covered wait, a parked item,
a scheduled not-before condition, a similar-task reference, or effective evidence
that does not apply to this task. A near-miss is plausible from surface evidence
but differs in a material observable fact; it must not be decidable only from a
hidden label. Decoy labels never appear in titles, identifiers or runtime packets.
Background no-action tasks are separate from focal decoys in the denominators.

**Illustrative prose example:** An item displays a blocked status while its visible
project record says it is waiting for a scheduled external milestone. This
illustrates an apparent stall with a material waiting condition.

### Duplicate-restraint

This family tests restraint when repeated deliveries, reordered wakes, new
proposal identifiers or changed wording refer to the same semantic work. The
intent persists across the whole run. A new delivery or cosmetic text change does
not advance `episode_epoch`; a real relevant blocker/state transition can do so.
An independent observer groups actual effects from observed transitions and
predeclared equivalent-action/topic definitions, rather than trusting the
controller's key. Different keys cannot hide duplicate persisted effects.

**Illustrative prose example:** Two notifications describe the same unresolved
information topic after a request has already been recorded, with no intervening
relevant state transition. This illustrates repetition within one episode.

## Eligibility, action and outcome are different facts

`resolution_eligible` identifies whether an opportunity can earn a resolution;
`should_act` states whether an action is appropriate in a declared tick window.
They are not interchangeable. An appropriate information request can be
should_act=true while resolution_eligible=false. A resolution-eligible opportunity
may not warrant action outside its validity window. Background tasks and all
focal opportunities remain in their specified accounting units.

U requires an eligible acceptable state at immediate, +8-hour and close checks,
achieved by the arm's own applied effect, at most once per opportunity. Asks,
abstentions, summaries and natural background progress earn no U. Appropriate
abstention may be a correct decision without being a resolution. A mechanically
clean effect can still be semantically wrong; the verifier cannot adjudicate
that question. A bundle with W, C or D cannot earn U on that attempt. A later clean
recovery may earn U once but never erases earlier harm. Decision precision/recall,
proposal burden and U/W/N/C/D stay distinct; zero-denominator ratios are NA.

## Coverage and near-miss constraints

The fixed totals below describe one twenty-board split, not a per-board recipe or
controller-visible quota. Held-out data is authored by H, dev data by builders only
after G2. Both splits have thirty tasks per board and the same declared totals.

| Focal family | Split total | Resolution-eligible |
| --- | ---: | ---: |
| dependency | 32 | 32 |
| semantic-evidence | 40 | 40 |
| delegate | 24 | 24 |
| missing-info ask | 12 | 0 |
| decoy | 40 | 0 |
| duplicate-restraint | 12 | 0 |
| Total focal | 160 | 96 |

There are 64 focal restraint opportunities and 440 background no-action tasks,
600 tasks total per split. Per board: 7–10 focal opportunities, eight on average;
at least two decoys, including at least one near-miss. Composition otherwise varies
inside the fixed totals; authors must not encode family or expected action in IDs
or repeated phrasing. Because forty decoys is exactly twice twenty, the minimum
implies exactly two focal decoys per board at this edition size. Do not resize or
change quotas after held-out exposure. Every background task needs reachable-state
review across the exogenous script; an accidental unlabelled actionable blocker
fails admission until H corrects the edition before exposure.

## Ambiguity and admission

H records acceptable outcome sets, forbidden effects, validity and eligibility in
the private evaluation projection. Q labels blind from rendered visible facts and
the exogenous script, without H's answers or controller output. Do not manufacture
agreement by copying these examples into pilot/control truth. The blind audit has
thirty situations, five per family; pass requires raw pre-adjudication agreement
on (should_act, action_type) >=80% and Cohen's kappa >=0.6. G1's three pilots have
the separate raw-agreement requirement in the admission contract. Keep raw results
and every changed label; do not present adjudicated agreement as raw agreement.

Unsettleable cases are labelled ambiguous rather than silently forced into an
answer. Abstention or the explicitly safe request is non-harmful for such a case;
neither earns resolution credit. Ambiguous cases stay in denominators. The private
admission record must identify the adjudication and permitted safe request, if
any; a builder must not invent it. One revised-family-guide retry is allowed at
G1, preserving both results. G1/G2 failure means NO-GO and execution skipped, not
builder-authored replacement truth or a softer pass. Actual appointments, rights,
pilot validation, sealing and audit evidence remain pending Roy.

## Public and private data flow

Family names, quotas, focal identifiers/counts, should_act, resolution_eligible,
acceptable outcomes, forbidden effects, latent causes and canaries are evaluation
metadata, not controller inputs. Publicly readable contracts can describe them;
that does not authorize embedding them in runtime board records or packets.
World/colleague scheduling receives only exogenous script, observable state and
public transition rules. It never branches on expected answers or latent cause.

Controllers and B3 receive the same screened evidence and candidate interface,
without hidden labels. No labels/canaries enter provider requests, fixture keys or
replies, candidate IDs, errors, feedback, operational controller logs or installed
product files. The mechanical verifier receives snapshots, compiled writes and
receipts, without scorer truth or controller intent logic. Only evaluation and
authorized custody may hold private truth. Human supersession is attribution and
never erases harm; mechanical feedback cannot reveal semantic correctness.

The future scenario compiler must enforce those projection boundaries and the
reachable-state review; this guide does not implement them. Authoring rights,
H/Q/custodian independence, data-only schema validation, real data-flow/canary
checks and all runtime behavior remain unverified. No app, test, model, network,
service or container execution is authorized by this document.
