"""gaplog CLI.

  python -m gaplog preregister PREREG.json --min-n 500 --rate 0.01
  python -m gaplog summarize GAPS.jsonl [--prereg PREREG.json]

Preregistration writes the adoption threshold *before* data collection:
the minimum sample size and the discrepancy rate at or above which the
verification spine is judged worth adopting. `summarize` refuses to issue
a pass/fail verdict unless the prereg file predates the first record, so
the analysis cannot be retrofitted to the result.
"""
import argparse
import datetime
import json
import sys
from collections import defaultdict

from . import read


def preregister(args):
    doc = {
        "declared_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "min_n": args.min_n,
        "adoption_rate": args.rate,
        "note": args.note,
    }
    with open(args.path, "x", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"preregistered: n>={args.min_n}, discrepancy rate>={args.rate} => adopt")
    print(f"wrote {args.path} (refuses to overwrite an existing prereg)")


def summarize(args):
    recs = list(read(args.path))
    n = len(recs)
    mismatches = [r for r in recs if not r["match"]]
    rate = (len(mismatches) / n) if n else 0.0

    print(f"records:       {n}")
    print(f"discrepancies: {len(mismatches)}")
    print(f"rate:          {rate:.4f}")

    by_verifier = defaultdict(lambda: [0, 0])
    for r in recs:
        by_verifier[r["verifier"]][0] += 1
        if not r["match"]:
            by_verifier[r["verifier"]][1] += 1
    for v, (total, bad) in sorted(by_verifier.items()):
        print(f"  {v}: {bad}/{total}")

    if not args.prereg:
        print("verdict:       none (no preregistration supplied)")
        return 0

    with open(args.prereg, encoding="utf-8") as f:
        pre = json.load(f)
    # Invalid only if the threshold was declared strictly AFTER the first
    # record. Equality (same clock tick) cannot be retrofitting and must
    # not reject the happy path on coarse-resolution clocks. Timestamps
    # are parsed, not string-compared: isoformat() drops zero microseconds,
    # so lexicographic order is not reliable across records.
    if n:
        declared = datetime.datetime.fromisoformat(pre["declared_at"])
        first = min(datetime.datetime.fromisoformat(r["ts"]) for r in recs)
        if declared > first:
            print("verdict:       INVALID — preregistration postdates first record")
            return 2
    if n < pre["min_n"]:
        print(f"verdict:       INSUFFICIENT DATA (n={n} < {pre['min_n']})")
        return 0
    if rate >= pre["adoption_rate"]:
        print(f"verdict:       THRESHOLD MET ({rate:.4f} >= {pre['adoption_rate']})")
    else:
        print(f"verdict:       THRESHOLD NOT MET ({rate:.4f} < {pre['adoption_rate']})")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="gaplog")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("preregister")
    pr.add_argument("path")
    pr.add_argument("--min-n", type=int, required=True)
    pr.add_argument("--rate", type=float, required=True)
    pr.add_argument("--note", default="")
    pr.set_defaults(fn=preregister)

    sm = sub.add_parser("summarize")
    sm.add_argument("path")
    sm.add_argument("--prereg", default=None)
    sm.set_defaults(fn=summarize)

    args = p.parse_args(argv)
    return args.fn(args) or 0


if __name__ == "__main__":
    sys.exit(main())
