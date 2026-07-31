#!/usr/bin/env python3
"""
report_generator.py — JUnit XML test result analyser (entry point)

Usage:
    python3 report_generator.py results.xml
    python3 report_generator.py run1.xml run2.xml run3.xml
    python3 report_generator.py results.xml -o summary.txt
    python3 report_generator.py results.xml --no-color
"""

import sys
import argparse
from pathlib import Path

# Allow imports from testlib-core/python and local lib/
_HERE = Path(__file__).resolve().parent
_SHARED_LIB = _HERE / '../../../testlib-core/python'

if not _SHARED_LIB.exists():
    print(
        f"ERROR: testlib-core not found at: {_SHARED_LIB}\n"
        "       Clone it: git clone https://github.com/sawaiwalatrupti/testlib-core.git",
        file=sys.stderr,
    )
    sys.exit(1)

sys.path.insert(0, str(_SHARED_LIB))
sys.path.insert(0, str(_HERE))

from colors import Colors       # from testlib-core/python/colors.py
from lib.reporter import build_report


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Parse JUnit XML test results and produce a human-readable report.'
    )
    parser.add_argument(
        'files', nargs='+', type=Path,
        help='One or more JUnit XML result files'
    )
    parser.add_argument(
        '-o', '--output', type=Path, default=None,
        help='Write plain-text report to FILE'
    )
    parser.add_argument(
        '--no-color', action='store_true',
        help='Disable ANSI colour output'
    )
    args = parser.parse_args()

    for f in args.files:
        if not f.is_file():
            print(f"Error: file not found: {f}", file=sys.stderr)
            sys.exit(2)

    use_color = not args.no_color and sys.stdout.isatty()
    c = Colors(enabled=use_color)

    report_lines, exit_code = build_report(args.files, c)

    if args.output:
        clean = [Colors.strip_ansi(line) for line in report_lines]
        args.output.write_text('\n'.join(clean) + '\n', encoding='utf-8')
        print(f"\nReport saved to: {args.output}")

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
