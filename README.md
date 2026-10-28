# Proactive Work Board — P01 contracts

This repository contains four contract documents, data-only JSON Schemas and an
unfinished preregistration skeleton. It has no product implementation, installed
CLI, runnable demo, scorer, generated boards or measured results. Runtime remains
unverified. Source construction spent USD0 and needs no keys or placeholders.

Read in order:

1. [CONTRACTS](docs/CONTRACTS.md): host/wire/action/approval boundaries, projection,
   canonical digests and supported observable transitions.
2. [SCENARIO-SPEC](docs/SCENARIO-SPEC.md): public/private data shapes, provenance,
   temporal conventions and fixed split quotas.
3. [FAMILY-GUIDE](docs/FAMILY-GUIDE.md): family meaning, independent authoring and
   the distinction between decisions, mechanical effects and useful outcomes.
4. [DATA-ADMISSION](docs/DATA-ADMISSION.md): role/rights/pilot/audit/custody gates
   and the frozen-contract handoff procedure.

Load the complete local draft2020-12 catalog: [wire](schemas/wire/),
[scenario](schemas/scenario/) and [admission](schemas/admission/). Scenario
references wire definitions; admission references scenario. Resolve URNs locally,
without network fetch. JSON parsing does not prove instance or semantic validity.

[freeze.json](prereg/freeze.json) records a documentary P01 pin against an EARLIER
source commit and exact file-byte SHA256s; the record is committed later. At
contracts_hash_basis=git_blob_bytes, hashes bind exact stored file bytes at that
commit; the H handoff must preserve those bytes without checkout newline conversion.
At
stage P01_CONTRACTS, status FROZEN refers only to the four contract documents
and all schemas. It does not admit data, appoint H/Q/custodian, approve a licence,
complete preregistration or authorize unseal. study_status remains UNFROZEN and
G1/G2/G3 remain PENDING - needs Roy. Attribution names delegated INT authority
and the recorder; it does not assert that Roy personally signed the record.

[PREREG](prereg/PREREG.md) is an unfinished skeleton, not a completed study freeze.
No model/settings/prompt/call slots, sealed data or study authority is supplied.
Actual independent role appointments, rights and G1/G2 evidence are required
BEFORE any product code or dev generation. Dev generation occurs only after G2.
Later G3 common study freeze and Roy's explicit unseal decision are separate,
even for deterministic-only USD0 execution.

Later authorized owners must validate the schema dialect/instances with real
independent pilots/controls, raw agreement/kappa, rights/identities/custody,
cross-record ID/digest/quota/interval/reachability and data-flow boundaries.
Tests, CI, builds, setup, host/security/transaction behavior and all runtime
journeys are NOT RUN. Nothing here authorizes spend, credentials, push,
publication or data exposure. Private coordination, plans and transcripts stay
outside this product repository; the adopted plan is in the private OUTER folder.
