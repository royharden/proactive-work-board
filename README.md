# Proactive Work Board — keyless engineering demo source

A deterministic Python/stdlib SQLite demo has been constructed as source: observe
an original fictional board, propose a dependency-only change, preview it, obtain
an exact digest-bound decision, apply atomically, inspect mechanical effects and
render escaped reports. **Runtime and acceptance have NOT RUN.** This checkout
must not be described as a validated runnable journey or a measured product result.

The public fixture, operator decisions and adverse scripts are explicitly
**SYNTHETIC / SCRIPTED / NO PAID CALLS / NOT A MEASUREMENT**. Local actor capabilities
and labels are demonstration policy attribution, not production authentication.
No keys, accounts, provider network calls or paid model services are needed.
Source construction spent USD 0; no efficacy, model or independent-audit claim is made.

Read [DEMO-QUICKSTART](docs/DEMO-QUICKSTART.md) for source navigation, future
invocation examples, expected engineering checks and deferred producer integration.
[DEMO-LIMITATIONS](docs/DEMO-LIMITATIONS.md) explains mechanical verification,
complete-history requirements and the limits of builder-authored observations.

## Future invocation — NOT RUN

Only after explicit owner execution authority and final producer reconciliation,
use an already available Python 3.12+ interpreter from this repository root.
The following PowerShell examples are instructions for later use; none was executed.
They use the source import path directly and require no package installation.

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m workboard.cli
```

The CLI defaults to a fixture preview and creates no database or report. Later
execution requires an explicit fresh absolute machine-local output directory
outside OneDrive and the source checkout, plus an approval mode:

```powershell
python -m workboard.cli --execute --manual-approval --run-dir C:\WorkboardRuns\pwb-manual-new
python -m workboard.cli --execute --scripted-approval approved --variant happy --run-dir C:\WorkboardRuns\pwb-scripted-new
python scripts/demo_acceptance.py --execute --run-dir C:\WorkboardRuns\pwb-acceptance-new
```

Directories named above must not already exist; choose distinct paths for each
invocation. SQLite/WAL, trace and report files stay in these machine-local run
folders. Source imports create no database. Manual approval requires typing the
exact displayed digest; other input rejects. Scripted approval is visibly scripted.
The reworded comparison refuses manual mode rather than inventing a second human
decision. The aggregate acceptance procedure returns nonzero for failed checks,
missing APIs or incomplete verification; no successful result artifact is shipped.

## Current construction limits

D1's durable `reserve_read`/`inspect_decision` and derived complete ordered
history are present in this source checkout. D3 directly observes the persisted
decision through that API, without fallback caches or SQL. D2's matching durable
reservation consumer repair remains a separate integration package: the current
policy still counts reads per Store object. A final source comparison must confirm
that it charges the durable host reservation before policy/approval reads across
reopen. Missing/malformed decision observations fail closed; incomplete verification
history cannot be called verified. Final combined-source tracing and every runtime
check remain deferred.

## Original scientific protocol

The frozen P01 documents and schemas remain authoritative and unchanged:
[CONTRACTS](docs/CONTRACTS.md), [SCENARIO-SPEC](docs/SCENARIO-SPEC.md),
[FAMILY-GUIDE](docs/FAMILY-GUIDE.md), [DATA-ADMISSION](docs/DATA-ADMISSION.md),
[wire](schemas/wire/), [scenario](schemas/scenario/) and [admission](schemas/admission/).
Resolve schema URNs locally; JSON parsing is not semantic or schema-instance validation.

[freeze.json](prereg/freeze.json) pins earlier P01 Git-blob bytes, not an admitted
study. [PREREG](prereg/PREREG.md) is unfinished. Original scientific G1/G2/G3 remain
UNFULFILLED and no H/Q/custodian, held-out seal, rights audit or real unseal is claimed.
An explicit successor exception admits this engineering DEMO source; it does not
retroactively satisfy the original before-code scientific gates. There is no
scorer, empirical study or measured agent result in this demo.

Tests, CI/builds, setup, SQLite transaction/security/durability checks and demo
acceptance are NOT RUN. Publication, deployment, credentials, spending and real
unseal remain outside this source grant. Private plans, coordination and transcripts
stay outside this product repository.
