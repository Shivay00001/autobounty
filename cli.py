"""CLI: python cli.py scan <hostname> [--json]

Only scan hosts you own or that explicitly allow scanning (e.g. scanme.nmap.org).
"""

import argparse
import json
import sys

from scanner import scan


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="autobounty",
                                 description="Honest scoped web security scanner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("scan", help="scan a hostname")
    p.add_argument("target", help="bare hostname, e.g. example.com")
    p.add_argument("--json", action="store_true", help="print raw JSON")
    p.add_argument("--ports", default="",
                   help="comma-separated ports (default: common set)")
    args = ap.parse_args(argv)

    if args.cmd == "scan":
        result = scan(args.target)
        if args.json:
            print(json.dumps(result, indent=2))
            return 0
        print(f"autobounty scan: {result['target']}  ({result['scanned_at']})")
        s = result["summary"]
        print(f"checks: {s['checks_run']}  findings: {s['findings']}  {s['by_severity']}")
        for check in result["checks"]:
            print(f"\n== {check['check']}")
            for f in check["findings"]:
                print(f"  [{f['severity']}] {f['finding']}")
            if not check["findings"]:
                print("  (no findings)")
            obs = check.get("observations")
            if isinstance(obs, dict) and obs.get("note"):
                print(f"  note: {obs['note'][:200]}")
        print("\nNote: absence of findings is not a claim of safety.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
