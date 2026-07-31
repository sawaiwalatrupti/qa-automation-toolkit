#!/usr/bin/env python3
"""
report_generator.py — JUnit XML test result analyser (entry point)

Usage (from tests/junit-report/):
    python3 report_generator.py results.xml
    python3 report_generator.py run1.xml run2.xml run3.xml
    python3 report_generator.py results.xml -o summary.txt
    python3 report_generator.py results.xml --no-color

Usage (from repo root):
    python3 run.py results.xml
"""

import os
import sys
import argparse
from pathlib import Path

# ── locate testlib-core ───────────────────────────────────────────────────────
# Search order:
#   1. TESTLIB_CORE env var  (export TESTLIB_CORE=/path/to/testlib-core)
#   2. sibling of this repo  (../../../testlib-core relative to this script)
#   3. one level up sibling  (../../testlib-core    relative to this script)
#   4. two levels up sibling (../../../../testlib-core)

_HERE = Path(__file__).resolve().parent

_env = os.environ.get("TESTLIB_CORE")
_CANDIDATES = [
    Path(_env) if _env else None,
    (_HERE / "../../../testlib-core").resolve(),
    (_HERE / "../../testlib-core").resolve(),
    (_HERE / "../../../../testlib-core").resolve(),
]

_SHARED_LIB = next(
    (p / "python" for p in _CANDIDATES if p and (p / "python").exists()),
    None,
)

if _SHARED_LIB is None:
    print(
        "ERROR: testlib-core not found.\n"
        "  Clone it alongside this repo:\n"
        "    git clone https://github.com/sawaiwalatrupti/testlib-core.git\n"
        "  Or set the TESTLIB_CORE environment variable:\n"
        "    export TESTLIB_CORE=/path/to/testlib-core",
        file=sys.stderr,
    )
    sys.exit(1)

# Insert shared lib first, then local lib/
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_SHARED_LIB))

from colors import Colors        # from testlib-core/python/colors.py
from lib.reporter import build_report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse JUnit XML test results and produce a human-readable report."
    )
    parser.add_argument(
        "files", nargs="+", type=Path,
        help="One or more JUnit XML result files",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=None,
        help="Write plain-text report to FILE",
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="Disable ANSI colour output",
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
        args.output.write_text("\n".join(clean) + "\n", encoding="utf-8")
        print(f"\nReport saved to: {args.output}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
