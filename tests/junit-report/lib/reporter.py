"""
lib/reporter.py — report generation for JUnit XML results.

Provides:
    build_report(files, c) -> tuple[list[str], int]
        Generates the human-readable report, prints to stdout,
        and returns (report_lines, exit_code).
"""

from pathlib import Path
from datetime import datetime

from lib.xml_parser import parse_junit_xml
from lib.flaky import detect_flaky


def build_report(files: list[Path], c) -> tuple[list[str], int]:
    """
    Build and print the test results report.

    Args:
        files:  list of JUnit XML Path objects
        c:      Colors instance

    Returns:
        (report_lines, exit_code)
        exit_code is 1 if any failures/errors exist, 0 otherwise.
    """
    lines: list[str] = []
    all_results: list[dict] = []

    def emit(text: str = '') -> None:
        lines.append(text)
        print(text)

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    emit(f"{c.BOLD}{'═' * 62}{c.RESET}")
    emit(f"{c.BOLD}  JUnit XML Test Results Summary{c.RESET}")
    emit(f"{c.BOLD}{'═' * 62}{c.RESET}")
    emit(f"  Generated : {now}")
    emit(f"  Files     : {len(files)}")
    emit()

    grand = {'tests': 0, 'passed': 0, 'failures': 0,
             'errors': 0, 'skipped': 0, 'time': 0.0}

    for path in files:
        emit(f"{c.BOLD}  File: {path.name}{c.RESET}")
        emit(f"  {'─' * 56}")

        try:
            result = parse_junit_xml(path)
        except ValueError as exc:
            emit(f"  {c.RED}[ERROR]{c.RESET} {exc}")
            continue

        all_results.append(result)

        for suite in result['suites']:
            pct          = (suite['passed'] / suite['tests'] * 100) if suite['tests'] > 0 else 0
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

        if result['failures']:
            emit()
            emit(f"  {c.RED}{c.BOLD}Failures & Errors:{c.RESET}")
            for i, f in enumerate(result['failures'], 1):
                tag = f"{c.RED}[{f['type']}]{c.RESET}"
                emit(f"  {i:>3}. {tag}  {f['class']}::{f['name']}")
                if f['message']:
                    emit(f"        Message : {f['message']}")
                if f['detail']:
                    emit(f"        Detail  : {f['detail'].splitlines()[0]}")

        for k in grand:
            grand[k] += result['totals'][k]

        emit()

    if len(files) > 1:
        emit(f"{c.BOLD}{'─' * 62}{c.RESET}")
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

    if len(all_results) > 1:
        flaky = detect_flaky(all_results)
        if flaky:
            emit(f"{c.YELLOW}{c.BOLD}  Flaky Tests Detected ({len(flaky)} tests):{c.RESET}")
            for t in flaky:
                emit(f"  {c.YELLOW}  \u26a0  {t}{c.RESET}")
            emit()
        else:
            emit(f"{c.GREEN}  No flaky tests detected across {len(all_results)} runs.{c.RESET}")
            emit()

    emit(f"{c.BOLD}{'═' * 62}{c.RESET}")

    exit_code = 1 if (grand['failures'] > 0 or grand['errors'] > 0) else 0
    return lines, exit_code
