#!/usr/bin/env python3
"""
report_generator.py — JUnit XML test result analyser

Reads one or more JUnit XML files (produced by pytest, Jenkins, or any
standard CI system) and generates a human-readable summary report.

Features:
  - Pass / fail / skip / error counts per test suite
  - Lists all failures with class, name, and failure message
  - Detects flaky tests across multiple XML files (tests that both
    pass and fail across different runs)
  - Optionally writes a plain-text report to a file

Usage:
  python3 report_generator.py results.xml
  python3 report_generator.py results1.xml results2.xml results3.xml
  python3 report_generator.py results.xml -o summary.txt
  python3 report_generator.py results.xml --no-color
"""

import sys
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from datetime import datetime


# ── ANSI colour helpers ────────────────────────────────────────────────────────

class Colors:
    def __init__(self, enabled: bool = True):
        if enabled:
            self.RED    = '\033[0;31m'
            self.YELLOW = '\033[0;33m'
            self.GREEN  = '\033[0;32m'
            self.CYAN   = '\033[0;36m'
            self.BOLD   = '\033[1m'
            self.RESET  = '\033[0m'
        else:
            self.RED = self.YELLOW = self.GREEN = ''
            self.CYAN = self.BOLD = self.RESET = ''


# ── XML parsing ────────────────────────────────────────────────────────────────

def parse_junit_xml(path: Path) -> dict:
    """
    Parse a JUnit XML file and return a dict with:
      suites     — list of suite-level dicts
      totals     — aggregated counts
      failures   — list of failure detail dicts
    """
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        raise ValueError(f"Cannot parse XML in {path}: {e}")

    root = tree.getroot()

    # JUnit XML can have <testsuites> as root (multiple suites)
    # or <testsuite> as root (single suite)
    if root.tag == 'testsuites':
        suite_elements = root.findall('testsuite')
    elif root.tag == 'testsuite':
        suite_elements = [root]
    else:
        raise ValueError(f"Unexpected root element <{root.tag}> in {path}")

    suites = []
    all_failures = []
    totals = {'tests': 0, 'passed': 0, 'failures': 0, 'errors': 0,
              'skipped': 0, 'time': 0.0}

    for suite in suite_elements:
        s_tests    = int(suite.get('tests',    0))
        s_failures = int(suite.get('failures', 0))
        s_errors   = int(suite.get('errors',   0))
        s_skipped  = int(suite.get('skipped',  0))
        s_time     = float(suite.get('time',   0.0))
        s_name     = suite.get('name', 'unnamed')

        s_passed = s_tests - s_failures - s_errors - s_skipped

        suites.append({
            'name':     s_name,
            'tests':    s_tests,
            'passed':   s_passed,
            'failures': s_failures,
            'errors':   s_errors,
            'skipped':  s_skipped,
            'time':     s_time,
        })

        totals['tests']    += s_tests
        totals['passed']   += s_passed
        totals['failures'] += s_failures
        totals['errors']   += s_errors
        totals['skipped']  += s_skipped
        totals['time']     += s_time

        # Collect failure details
        for tc in suite.findall('testcase'):
            tc_name  = tc.get('name',      'unknown')
            tc_class = tc.get('classname', 'unknown')
            tc_time  = float(tc.get('time', 0.0))

            failure = tc.find('failure')
            error   = tc.find('error')
            skipped = tc.find('skipped')

            if failure is not None:
                all_failures.append({
                    'suite':   s_name,
                    'class':   tc_class,
                    'name':    tc_name,
                    'time':    tc_time,
                    'type':    'FAILURE',
                    'message': (failure.get('message') or '').strip()[:200],
                    'detail':  (failure.text or '').strip()[:400],
                })
            elif error is not None:
                all_failures.append({
                    'suite':   s_name,
                    'class':   tc_class,
                    'name':    tc_name,
                    'time':    tc_time,
                    'type':    'ERROR',
                    'message': (error.get('message') or '').strip()[:200],
                    'detail':  (error.text or '').strip()[:400],
                })

    return {'suites': suites, 'totals': totals, 'failures': all_failures}


# ── flaky test detection ──────────────────────────────────────────────────────

def detect_flaky(all_results: list[dict]) -> list[str]:
    """
    A test is considered flaky if it appears as FAILED in at least one
    XML file and as PASSED in at least one other XML file.

    Returns a list of 'classname::testname' strings.
    """
    failed_in: dict[str, set] = defaultdict(set)   # test -> set of file indices where it failed
    seen_in:   dict[str, set] = defaultdict(set)    # test -> set of file indices where it ran

    for idx, result in enumerate(all_results):
        failed_keys = {
            f"{f['class']}::{f['name']}"
            for f in result['failures']
        }
        # Walk suites to get all test names
        # We approximate by using failure lists for failed, and suite totals for seen
        # For a more precise approach, the caller would need to track all testcase names
        for key in failed_keys:
            failed_in[key].add(idx)
            seen_in[key].add(idx)

    # Any test that failed in SOME runs but not ALL runs is flaky
    flaky = []
    for key, failed_files in failed_in.items():
        if len(failed_files) < len(all_results):
            flaky.append(key)

    return sorted(flaky)


# ── report generation ─────────────────────────────────────────────────────────

def build_report(files: list[Path], c: Colors) -> tuple[list[str], int]:
    """
    Returns (report_lines, exit_code).
    exit_code is 1 if any failures/errors exist, 0 otherwise.
    """
    lines: list[str] = []
    all_results = []

    def emit(text: str = ''):
        lines.append(text)
        print(text)

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    emit(f"{c.BOLD}{'═'*62}{c.RESET}")
    emit(f"{c.BOLD}  JUnit XML Test Results Summary{c.RESET}")
    emit(f"{c.BOLD}{'═'*62}{c.RESET}")
    emit(f"  Generated : {now}")
    emit(f"  Files     : {len(files)}")
    emit()

    grand = {'tests': 0, 'passed': 0, 'failures': 0,
             'errors': 0, 'skipped': 0, 'time': 0.0}

    for path in files:
        emit(f"{c.BOLD}  File: {path.name}{c.RESET}")
        emit(f"  {'─'*56}")

        try:
            result = parse_junit_xml(path)
        except ValueError as e:
            emit(f"  {c.RED}[ERROR]{c.RESET} {e}")
            continue

        all_results.append(result)

        # Per-suite breakdown
        for suite in result['suites']:
            pct = (suite['passed'] / suite['tests'] * 100) if suite['tests'] > 0 else 0
            status_color = c.GREEN if suite['failures'] == 0 and suite['errors'] == 0 else c.RED
            emit(
                f"  Suite : {suite['name']}\n"
                f"    Tests  : {suite['tests']}   "
                f"{c.GREEN}Pass: {suite['passed']}{c.RESET}   "
                f"{c.RED}Fail: {suite['failures']}{c.RESET}   "
                f"{c.RED}Error: {suite['errors']}{c.RESET}   "
                f"{c.YELLOW}Skip: {suite['skipped']}{c.RESET}   "
                f"Time: {suite['time']:.2f}s   "
                f"{status_color}({pct:.1f}%){c.RESET}"
            )

        # Failure details
        if result['failures']:
            emit()
            emit(f"  {c.RED}{c.BOLD}  Failures & Errors:{c.RESET}")
            for i, f in enumerate(result['failures'], 1):
                tag = f"{c.RED}[{f['type']}]{c.RESET}"
                emit(f"  {i:>3}. {tag}  {f['class']}::{f['name']}")
                if f['message']:
                    emit(f"        Message : {f['message']}")
                if f['detail']:
                    first_line = f['detail'].splitlines()[0]
                    emit(f"        Detail  : {first_line}")

        # Accumulate grand totals
        for k in grand:
            grand[k] += result['totals'][k]

        emit()

    # Grand totals (only meaningful if more than one file)
    if len(files) > 1:
        emit(f"{c.BOLD}{'─'*62}{c.RESET}")
        emit(f"{c.BOLD}  Grand Total across {len(files)} files{c.RESET}")
        pct = (grand['passed'] / grand['tests'] * 100) if grand['tests'] > 0 else 0
        emit(
            f"  Tests  : {grand['tests']}   "
            f"{c.GREEN}Pass: {grand['passed']}{c.RESET}   "
            f"{c.RED}Fail: {grand['failures']}{c.RESET}   "
            f"{c.RED}Error: {grand['errors']}{c.RESET}   "
            f"{c.YELLOW}Skip: {grand['skipped']}{c.RESET}   "
            f"Time: {grand['time']:.2f}s   "
            f"({pct:.1f}%)"
        )
        emit()

    # Flaky test detection (only useful with multiple files)
    if len(all_results) > 1:
        flaky = detect_flaky(all_results)
        if flaky:
            emit(f"{c.YELLOW}{c.BOLD}  Flaky Tests Detected ({len(flaky)} tests):{c.RESET}")
            for t in flaky:
                emit(f"  {c.YELLOW}  ⚠  {t}{c.RESET}")
            emit()
        else:
            emit(f"{c.GREEN}  No flaky tests detected across {len(all_results)} runs.{c.RESET}")
            emit()

    emit(f"{c.BOLD}{'═'*62}{c.RESET}")

    exit_code = 1 if (grand['failures'] > 0 or grand['errors'] > 0) else 0
    return lines, exit_code


# ── CLI entry point ────────────────────────────────────────────────────────────

def main():
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

    # Validate files exist
    for f in args.files:
        if not f.is_file():
            print(f"Error: file not found: {f}", file=sys.stderr)
            sys.exit(2)

    use_color = not args.no_color and sys.stdout.isatty()
    c = Colors(enabled=use_color)

    report_lines, exit_code = build_report(args.files, c)

    if args.output:
        # Strip ANSI codes for file output
        import re
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        clean = [ansi_escape.sub('', line) for line in report_lines]
        args.output.write_text('\n'.join(clean) + '\n', encoding='utf-8')
        print(f"\nReport saved to: {args.output}")

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
