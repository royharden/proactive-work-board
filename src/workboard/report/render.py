"""Render shared m20-demo-trace-v1 to HTML/JSON/text strings only.

Input: JSON-compatible trace with schema_version='m20-demo-trace-v1',
mode='SCRIPTED', measurement=False, variant, board_id, stages (name/status/detail),
before/proposal/decision/receipt/after/delayed, effect_records, limits and optional
runtime_status. Actual driver stages are shown verbatim as untrusted data; no
stage or measurement is upgraded by this renderer. EffectRecords are unchanged
P01 records. Snapshot verification_context/history requirements live in effects.py.
All content, including URLs, remains plain escaped text: no active links/scripts.
No file creation, imports of driver/controller, environment or provider access.
"""

from __future__ import annotations

from html import escape
import json

LABEL = "SYNTHETIC / SCRIPTED / NO PAID CALLS / NOT A MEASUREMENT"


def render_report(demo_trace: dict, effect_records: list[dict]) -> dict[str, str]:
    """Return three inert artifacts; invalid trace envelopes refuse rendering."""
    if not isinstance(demo_trace, dict) or demo_trace.get("schema_version") != "m20-demo-trace-v1":
        raise ValueError("unsupported demo trace version")
    if demo_trace.get("mode") != "SCRIPTED" or demo_trace.get("measurement") is not False:
        raise ValueError("only explicitly scripted nonmeasurement traces supported")
    if not isinstance(effect_records, list) or any(not isinstance(e, dict) for e in effect_records):
        raise ValueError("effect records must be JSON objects")
    if not isinstance(demo_trace.get("stages"), list):
        raise ValueError("stage observations required")
    # JSON rejects unsupported objects/nonfinite values rather than executable repr.
    payload = {"label": LABEL, "qualification": "delegated stand-in, not human-independent",
               "scientific_gates": "UNFULFILLED / outside DEMO exception",
               "semantic_usefulness": "NOT MEASURED", "trace": demo_trace,
               "effect_records": effect_records}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
    runtime = demo_trace.get("runtime_status", "Observed stages as supplied; no independent runtime certification")
    text = LABEL + "\nRuntime: " + str(runtime) + "\n\n" + raw + "\n"
    html = ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; "
            "base-uri 'none'; form-action 'none'\"><title>Workboard scripted demo</title>"
            "</head><body><h1>Workboard scripted demo</h1><p>" + escape(LABEL, quote=True)
            + "</p><p>Runtime: " + escape(str(runtime), quote=True)
            + "</p><p>Mechanical observations only. Scientific gates remain unfulfilled. "
            "No efficacy, independent audit or semantic usefulness claim.</p><pre>"
            + escape(raw, quote=True) + "</pre></body></html>")
    return {"html": html, "json": raw + "\n", "text": text}
