"""Preview-first command line. Execution requires an explicit mode and path."""

import argparse
import json

from workboard.demo import LABEL, VARIANTS, preview_demo, run_demo


def _manual(proposal: dict, preview: dict) -> str:
    print(LABEL)
    print(json.dumps(preview, indent=2, ensure_ascii=False))
    digest = proposal["digest"]
    print(f"Exact proposal digest: {digest}")
    answer = input("Type 'approve <exact digest>' to apply; anything else rejects: ")
    return "approved" if answer == f"approve {digest}" else "rejected"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=LABEL)
    parser.add_argument("--variant", choices=VARIANTS, default="happy")
    parser.add_argument("--run-dir", help="new absolute machine-local directory outside OneDrive/source")
    parser.add_argument("--execute", action="store_true", help="requires later owner execution authority")
    approval = parser.add_mutually_exclusive_group()
    approval.add_argument("--scripted-approval", choices=("approved", "rejected"))
    approval.add_argument("--manual-approval", action="store_true")
    args = parser.parse_args(argv)
    if not args.execute:
        if args.scripted_approval or args.manual_approval:
            parser.error("approval mode requires explicit --execute")
        print(json.dumps(preview_demo(args.variant), indent=2, ensure_ascii=False))
        return 0
    if not args.run_dir or not (args.scripted_approval or args.manual_approval):
        parser.error("execution requires --run-dir and an explicit approval mode")
    trace = run_demo(args.run_dir, args.variant,
                     "manual" if args.manual_approval else args.scripted_approval,
                     manual_decider=_manual if args.manual_approval else None)
    print(json.dumps({"label": LABEL, "runtime_status": trace["runtime_status"],
                      "variant": trace["variant"], "receipt": trace["receipt"],
                      "effects": trace["effect_records"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
