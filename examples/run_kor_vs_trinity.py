"""Reproduce the Kor vs Trinity finding from the encoded data.

    python examples/run_kor_vs_trinity.py
"""

from __future__ import annotations

from meaning_assay import analyze, compare, render_pair_summary, receipt, verify
from meaning_assay.cases import get as get_case


def main() -> None:
    kor = get_case("kor")
    trinity = get_case("trinity")

    for case in (kor, trinity):
        a = analyze(case)
        w = "n/a" if a.warrant is None else f"{a.warrant:+.3f}"
        print(f"{case.key:<8} significance={a.significance:+.3f}  warrant={w}  -> {a.quadrant}")

    print()
    print(render_pair_summary(compare(kor, trinity)))

    r = receipt(trinity)
    print(f"trinity receipt {r['receipt_sha256'][:16]}...  verifies={verify(r)}")


if __name__ == "__main__":
    main()
