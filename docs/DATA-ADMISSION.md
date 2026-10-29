# Data admission requirements (P01)

Status: **PENDING — needs Roy**. G1 and G2 have not passed; G3 is not authorized.
This is a blank requirements kit, with no appointments, signatures, boards,
labels, pilots, controls, audit results or sealed data. Dirty Mode construction
only; runtime unverified. The immutable PLAN-M20-v1 sections 2 D3/D4/D8/D17,
5/P01, 6 and 8 govern this kit.

## Roles, rights and timing

- [ ] Roy appoints H in a fresh session of a different harness from every builder.
- [ ] Roy appoints Q in a fresh session distinct from every builder and H, or Roy
  serves as Q. Q's identity/session is recorded, not inferred from a role label.
- [ ] Roy appoints external custodian: Roy or a folder Roy names outside the
  builder's tree. Builders never serve as H, Q or custodian, never open the
  sealed bundle and never substitute their lineage reviewer for these roles.
- [ ] Record H/Q registry callsigns, exact session IDs, harnesses and all builder
  identities/sessions. Record appointment and separation evidence durably.
- [ ] H and Q attest original fictional synthetic authorship, permission to
  redistribute and the actual repo/data licence Roy selects. MIT is a proposal,
  not a selection. No real-person list, client, partner, Gauntlet text or public
  dataset is admitted. Fictional person names use seeded syllables.
- [ ] Preserve provenance/source-rights review. Plane/Taiga/Focalboard are reading
  only; cited benchmarks supply design ideas, not copied code or records.
- [ ] Before H receives anything, INT reconciles the four P01 slices and creates
  an actual contracts pin. No dev data/generator, rules, prompt or implementation
  exists or is supplied to H. Dev generation starts only AFTER G2.

An attribution is identity + exact session + bundle SHA256 + durable statement
and UTC time. It is not cryptographic authentication or evidence that Roy
personally signed something. A schema-shaped statement is not appointment,
permission or independent evidence. All checkboxes here are unchecked.

## Schema catalog and locations

Data-only draft 2020-12 schemas are under `../schemas/admission/`, with IDs
`urn:workboard:v1:admission:<basename>` (filename minus `.json`):

| Schema | Requirement it represents |
|---|---|
| common | Attributed identity, artifact reference with hash/time/visibility, exact split counts |
| attestation | Roy appointment, role/session separation, original authorship and redistribution rights |
| g1-evidence | Actual contracts pin, H/Q/custodian/rights records, all pilot attempts and raw blind agreement |
| g2-evidence | Full bundle and board/template/scenario hashes, quota/disjointness/reachability/canary reviews, raw audit and Q controls, seal |
| admission-record | Complete section 6.5 record tying actors, evidence, rights, hashes, freeze/custody and single-unseal log together |
| freeze | Separate P01 contract pin and eventual G3 study pin, without a self-referential commit |

Load all three local schema catalogs: wire, scenario AND admission. Never fetch
URNs over the network. Admission references the accepted
`urn:workboard:v1:scenario:private-split-inventory`; scenario also composes wire
evidence/topic/class definitions. Scenario-only loading is incomplete. Canonical
evidence URI: `urn:workboard:v1:wire:common#/$defs/evidence-ref`, not a nonexistent
standalone wire record-ref schema. Artifact references name
location, SHA256, visibility, attributed recorder and UTC. Locations are opaque
provenance references, not permission to read private data or send it elsewhere.

These schemas describe complete future evidence documents. They are not filled
pending evidence records. The sole instance supplied is `prereg/freeze.json`.
It separates documentary P01 source pinning from G3 study state: a P01 FROZEN
record identifies earlier contract bytes, not admitted data. At this handoff
study_status is UNFROZEN, study/seal authority is unset and all gates pending.
There is no
authored `admission.json`, seal, attestation, audit table, pilot or control here.

Keep raw H labels, private expected outcomes, audit/adjudication data, canaries,
private inventory and custody paths with their appointed external custodian or
auditor. Do not commit them to the builder repo or expose them through runtime,
provider/fixture channels, controller feedback or wire contracts. Future repo
`data/heldout/SEALED.json` contains only bundle hash, H/Q identities/sessions,
date and family counts. It is a projection of the private seal, never the whole
admission record. Public pilot/control publication occurs only under the actual
rights and role procedure, not by this builder authoring substitutes.

## G1 — admission, after P01 and before any product code

- [ ] Four P01 slices reconciled, actual file hashes/earlier commit pinned, frozen
  handoff given to H. `freeze.json` today does not satisfy this.
- [ ] H/Q/custodian appointments and rights attestations complete and distinct.
- [ ] H delivers exactly three pilot boards from contracts only. Actual shape
  validation results are preserved. Pilots later retire as public pilot data,
  outside both 20-board study splits.
- [ ] Q labels the pilots blind; preserve raw (`should_act`, `action_type`)
  comparisons, numerator, denominator and raw pre-adjudication agreement.
- [ ] Raw agreement is at least 80%. If it fails, one revised FAMILY-GUIDE retry
  is allowed. Preserve both attempts, their guide hashes, raw results and all
  adjudications. No repeated retries or replacement of a bad raw result.
- [ ] Custodian records the actual disposition and attribution. A numeric result
  must be rederived from the raw observations, not copied from a claim.

Missing required roles/rights, invalid pilots or a failed final threshold means
NO-GO: M20 execution skipped. Never downgrade to builder truth. PASS cannot be
inferred from the schema's threshold constants. No product code starts at G1;
G2 is also required.

## G2 — held-out readiness, before P02 or dev generation

- [ ] H delivers twenty originally authored boards and their exogenous scripts,
  acceptable outcome sets, forbidden effects, validity windows, eligibility and
  private canary per board; randomized opaque IDs and original phrasing/graphs.
- [ ] Preserve bundle, per-board observable/script/outcome, template and scenario
  hashes; source/author attestations, freeze UTC and external custody location.
- [ ] Validate the actual held-out inventory against these shared split-contract
  requirements: 20 boards; 30 tasks, 2–3 projects,
  4–6 people, 8–12 DAG links, 3–6 documents per board. Seven–ten focal opportunities
  per board, 160 per split; all other 440 tasks are background no-action.
- [ ] Verify actual held-out family totals: dependency 32, semantic evidence
  40, delegate 24 (96 resolution-eligible); missing-info ask 12, decoy 40,
  duplicate restraint 12 (64 restraint). Total 600 tasks. Every board has at
  least two decoys and at least one near-miss decoy; forty decoys thus means
  exactly two per board. Do not resize after exposure.
- [ ] Record the dev contract only at G2: seeds 20000–20019, the same fixed totals
  above and a reserved schedule-salt namespace disjoint from held-out. No actual
  dev inventory, generated counts or dev comparisons exist yet and none is a G2
  prerequisite. Held-out is H-authored. Review its independent origin and bounded
  visible decidability now. After G2, the authorized owner generates dev and
  validates its actual counts/seeds/salts and edition/template/scenario
  disjointness against the sealed held-out commitments without builder exposure.
- [ ] Review every background task across reachable exogenous-script states.
  None may acquire an actionable blocker without a focal label. Correct such
  errors in H's edition before exposure; do not ignore them in denominators.
- [ ] Verify canary coverage per board and absence from every runtime-visible
  channel. This checklist is not an executed leak scan.
- [ ] Draw 30 held-out situations by a recorded seed: exactly five per family.
  Q sees rendered board observations and exogenous script, not H answers,
  implementation, prompts or controller outputs. Preserve raw blind labels.
- [ ] Compute raw pre-adjudication agreement on (`should_act`, `action_type`):
  at least 80% AND Cohen's kappa at least 0.6. Store numerator/30, raw agreement,
  kappa, exact draw manifest, every changed label and all pre-seal adjudications.
  Undefined kappa is not a pass. Report raw kappa and changed labels later.
- [ ] Unsettleable cases become ambiguous, remain in denominators, receive no
  resolution credit; abstention or explicitly safe request is non-harmful.
- [ ] Q supplies six tiny public controls with independently hand-tabulated
  observations from frozen contracts BEFORE hidden audit inputs or implementation.
  Coverage includes good, wrong, decoy, reverted, duplicate, collateral and the
  mechanically-clean-but-semantically-wrong case. Six boards cover these cases;
  a case need not require a separate seventh board. Record coverage explicitly.
- [ ] Custodian seals the full twenty-board bundle, records digest and receipt,
  and completes admission.json. No builder opens or supplies its private truth.

All requirements are co-required. Failed/missing audit or evidence means NO-GO,
execution skipped, before code. Schema counts/booleans are declarations, not
proof of validation, independence, custody, reachable state or a sealed file.

## Section 6.5 completion map

| Required item | Durable field/reference |
|---|---|
| H/Q callsigns and exact sessions distinct from builders | admission-record builders/h/q, role_separation_review; common identity includes harness |
| Custodian appointment/location | attestation appointment_by_roy; admission-record custodian and seal.private_custody_location |
| Author attestations and rights | author_attestations, rights_record; attestation authorship/redistribution/licence/source review |
| Pilot results and retry provenance | g1.pilot_attempts, contracts_freeze, final_raw_agreement, pilot_retirement_record |
| Board/template/scenario hashes | g2.board_hashes, template_hash_inventory, scenario_hash_inventory, bundle |
| Disjointness review | g2.disjointness_review |
| Per-family and eligible counts | g2.split_inventory and quota_review; seal.family_counts |
| Reachable-state/background review | g2.reachable_state_background_review |
| Raw 30-case audit and kappa | g2.blind_audit raw labels/draw/counts/agreement/cohens_kappa |
| Q's six controls | g2.q_controls author/count/coverage/bundle/pre-implementation evidence |
| Every pre-seal adjudication and changed label | pilot attempts adjudications; blind_audit pre_seal_adjudications/changed_label_list/ambiguous_case_disposition |
| Freeze UTC and hash | seal.freeze_utc/bundle_sha256; admission_freeze_utc and artifact hashes |
| Custody receipt and attribution | seal.sealed_bundle_receipt/attribution, admission_record_attribution |

The complete private admission record binds all of these to one edition.
The custodian compares actors/sessions across records, attribution bundle hashes,
timestamps, content hashes and final gate evidence. Mismatches block admission.
PASS on a parent record requires matching PASS on the actual G1 and G2 evidence;
a status label cannot override a failed inner record. Cross-document arithmetic,
identity inequality, actual file/content existence, original rights and temporal
ordering require later validation; these schemas do not prove them.

## P01 freeze and later G3 single unseal

The authorized P01 closeout commits reconciled source BEFORE recording its pin.
`prereg/freeze.json` then names that earlier combined source commit and exact
contract file SHA256s in a SEPARATE later commit. contract_pin_authority records
INT's delegated documentary instruction and the recorder's identity/session;
it is NOT personally signed by Roy or independent admission evidence.
contracts_hash_basis=git_blob_bytes means exact bytes stored for each path at
contracts_commit. Materialize and deliver those bytes without automatic newline
conversion; a platform checkout with changed line endings is not the hashed
artifact. No normalization is applied while computing or checking the map.
Never put the containing
commit's hash into itself. Verify files at the earlier commit; only then hand
the pinned contracts to H. Scope is all four P01 documents (CONTRACTS,
SCENARIO-SPEC, FAMILY-GUIDE, DATA-ADMISSION) and every wire/scenario/admission
JSON Schema. Exclude the pin record itself, README navigation and the unfinished
preregistration skeleton from H's contract map. Do not declare FROZEN without
the actual earlier-commit pin. G1/G2/G3 remain PENDING - needs Roy.

P01 contract freeze is distinct from the later G3 study freeze. G3 requires
PREREG, B3 rules, agent prompt/schema/settings and call slots committed/hashed
at ONE common study commit. Agent prompts freeze even for a deterministic-only
unseal. The freeze-record commit can be later; study pins refer to that earlier
common source commit. Add no call-slot/settings/prompt implementation now.
For stage=P01_CONTRACTS, status=FROZEN means documentary source only;
study_status stays UNFROZEN. study_commit, study_pins, roy_unseal_decision and
heldout_bundle_sha256 stay null. frozen_utc is this documentary record's time,
not a dataset seal or G3 admission. A P01 pin can precede G1 without passing it.

Before opening held-out: actual G1/G2 passed, digest matches seal, study freeze
complete, and Roy's R-07 decision recorded. It must authorize funded exact slots
or explicitly choose the deterministic-only USD0 path under D17/R-14. No decision
means stop; USD0 alone is not unseal permission. Custodian logs edition digest,
freeze/authority references, mode, frozen slot ID, UTC and one-pass receipt.
Each frozen slot is used once; repeated slot IDs or another pass are prohibited.
The empty log shape is not an executed or authorized unseal. After exposure,
prompt/rule changes require a fresh H edition; bugs found after P13 go to
LIMITATIONS rather than rerunning held-out.

## Authoring from the reconciled contracts

The accepted CONTRACTS/SCENARIO-SPEC define these boundaries; this is handoff
guidance, not a second implementation or permission to change those definitions:

- Observed reference kinds are plural storage names; private scorer selectors
  use SCENARIO-SPEC's total singular-to-plural mapping. Delegation scope.kind is
  a separate task|project domain. Initial versions are >=1, observation refs may
  have version0, never an absent-row sentinel or a coerced initial record.
- Initial/exogenous depends_on_task_id maps to dependency_task_id at BOTH
  observable projection and compiled deletion, retaining exact link/task/version
  binding. These names are not aliases within either closed shape. Private
  selectors use that explicit mapping; absent fields cannot count as success.
- Evidence/citation digests hash the complete projected versioned observable
  payload using CONTRACTS' canonical serializer: sorted keys, UTF-8 without BOM,
  compact separators, unescaped Unicode, array order preserved, integer numeric
  record data. Project/rename BEFORE hashing; never reuse a preprojection digest.
  Artifact/file SHA256s (including this P01 map) instead bind EXACT bytes, with
  no newline normalization or JSON reserialization.
- Comments retain role/origin, actor_id, source_event_id/source_proposal_id,
  cites and topic. Human IDs resolve actual fictional board people; world/agent/
  rules actor IDs are null, never invented people. Initial/exogenous roles are
  human/world, and source IDs/ticks follow their actual enclosing origin. Arm
  origin binds the exact proposal/journal. Private arm means agent|rules for the
  evaluated arm only, not every similarly named comment. Initial/exogenous empty
  cites/null topic are explicit, never inferred from prose or private truth.
  Retain declared host insertion metadata; body/cites/topic/provenance are not noise.
- Tasks require nullable work_window. Null permits no automatic completion;
  nonnull uses the visible start/continuous/end conditions and tick ordering in
  CONTRACTS. Supported IDs are advance_time_only and
  complete_ready_task_after_visible_work_window; replies are explicit exogenous
  facts with provenance, never supplied by a hidden-answer transition.
- Starts are ticks0..96; half-open endpoints may reach boundary97 to contain
  close96.97 is never a clock/event tick; work windows end<=96 and new proposals
  stop before72. End96 excludes instant96. Never invent inclusive-end exceptions
  or discard close checks when authoring private within predicates.
- Finite topics and five action-equivalence classes/normalization are now
  defined in wire common and CONTRACTS, referenced by scenario definitions.
  Independent grouping uses actual primitive effects and observed epochs,
  never controller keys or public exposure of private grouping truth.
- Fixed40decoys across20boards with minimum2perboard means EXACTLY2perboard,
  including >=1near-miss. Other family mix varies inside the frozen split totals.

No admission-schema change is required for those upstream mappings. Their real
instance/semantic validation remains deferred. Frozen handoff uses the actual
earlier source commit/file map; descriptive alignment does not prove rights,
custody, data validity, code execution or any admission gate.

NOT RUN: schema dialect/instance validation, H pilots/Q controls, identity/rights
verification, cross-record/content hash and agreement/kappa calculations,
quota/DAG/reachability/canary/disjointness checks, actual seal/custody/unseal,
all tests/CI/builds/dependencies/runtime and every post-gate package. Later
authorized custodian/auditor and implementation owner must perform them using
actual independent evidence. No keys/placeholders are needed for this kit.
