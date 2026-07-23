from __future__ import annotations

import argparse
from pathlib import Path
from dataclasses import asdict

from efm_council import run_council
from report import to_markdown, save_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description='EFM Council Lite')
    parser.add_argument('decision', nargs='?', help='Decision text to evaluate')
    parser.add_argument('--file', '-f', help='Read decision from file')
    parser.add_argument('--output', '-o', help='Base output path (without extension)')
    args = parser.parse_args()

    if args.file:
        decision = Path(args.file).read_text(encoding='utf-8').strip()
    elif args.decision:
        decision = args.decision.strip()
    else:
        raise SystemExit('No decision text provided.')

    record = asdict(run_council(decision))
    print(to_markdown(record))

    if args.output:
        save_outputs(record, args.output)


if __name__ == '__main__':
    main()
