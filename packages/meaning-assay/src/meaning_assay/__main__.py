"""Command-line interface.

    python -m meaning_assay lenses
    python -m meaning_assay run kor
    python -m meaning_assay pair kor trinity
    python -m meaning_assay receipt trinity
    python -m meaning_assay render kor --out kor.md
"""

from __future__ import annotations

import argparse
import json
import sys

from .cases import REGISTRY, get as get_case
from .engine import analyze
from .lenses import LENSBOOK
from .pairs import compare
from .receipts import receipt
from .report import render_case, render_pair_summary


def _cmd_lenses(_args) -> int:
    for t in LENSBOOK:
        fns = ",".join(sorted(f.value for f in t.functions)) or "null"
        print(f"{t.numeral:>5}  {t.name:<24} [{fns}]")
    return 0


def _cmd_run(args) -> int:
    a = analyze(get_case(args.case))
    print(f"case:           {a.case_key}")
    print(f"significance:   {a.significance:+.3f} ({'high' if a.significance_high else 'low'})")
    w = "n/a" if a.warrant is None else f"{a.warrant:+.3f}"
    print(f"warrant:        {w} ({a.warrant_band})")
    print(f"quadrant:       {a.quadrant}")
    print(f"failure trips:  {len(a.failure_tripped_keys)}/{len(a.rows)} ({a.failure_trip_rate:.0%})")
    if a.warrant_lenses_condemning:
        print(f"condemned by:   {', '.join(a.warrant_lenses_condemning)}")
    if a.provisional_keys:
        print(f"provisional:    {', '.join(a.provisional_keys)}")
    return 0


def _cmd_pair(args) -> int:
    p = compare(get_case(args.a), get_case(args.b))
    print(render_pair_summary(p))
    return 0


def _cmd_receipt(args) -> int:
    print(json.dumps(receipt(get_case(args.case)), indent=2, ensure_ascii=False))
    return 0


def _cmd_render(args) -> int:
    md = render_case(get_case(args.case))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(md)
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(md)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="meaning-assay", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("lenses", help="list the 27 traditions and their functions").set_defaults(fn=_cmd_lenses)

    sp = sub.add_parser("run", help="analyze a case")
    sp.add_argument("case", choices=sorted(REGISTRY))
    sp.set_defaults(fn=_cmd_run)

    sp = sub.add_parser("pair", help="contrast two cases")
    sp.add_argument("a", choices=sorted(REGISTRY))
    sp.add_argument("b", choices=sorted(REGISTRY))
    sp.set_defaults(fn=_cmd_pair)

    sp = sub.add_parser("receipt", help="emit a deterministic receipt")
    sp.add_argument("case", choices=sorted(REGISTRY))
    sp.set_defaults(fn=_cmd_receipt)

    sp = sub.add_parser("render", help="render a case to markdown")
    sp.add_argument("case", choices=sorted(REGISTRY))
    sp.add_argument("--out", default=None)
    sp.set_defaults(fn=_cmd_render)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
