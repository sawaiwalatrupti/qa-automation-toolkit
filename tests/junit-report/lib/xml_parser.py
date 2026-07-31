"""
lib/xml_parser.py — JUnit XML parsing logic.

Provides:
    parse_junit_xml(path: Path) -> dict
        Returns {'suites': [...], 'totals': {...}, 'failures': [...]}
"""

import xml.etree.ElementTree as ET
from pathlib import Path


def parse_junit_xml(path: Path) -> dict:
    """
    Parse a JUnit XML file.

    Handles both <testsuites> (multiple suites) and <testsuite> (single suite) roots.

    Returns:
        suites   — list of per-suite dicts (name, tests, passed, failures, errors, skipped, time)
        totals   — aggregated counts across all suites
        failures — list of failure/error detail dicts
    """
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise ValueError(f"Cannot parse XML in {path}: {exc}") from exc

    root = tree.getroot()

    if root.tag == 'testsuites':
        suite_elements = root.findall('testsuite')
    elif root.tag == 'testsuite':
        suite_elements = [root]
    else:
        raise ValueError(f"Unexpected root element <{root.tag}> in {path}")

    suites: list[dict] = []
    all_failures: list[dict] = []
    totals = {'tests': 0, 'passed': 0, 'failures': 0, 'errors': 0,
              'skipped': 0, 'time': 0.0}

    for suite in suite_elements:
        s_tests    = int(suite.get('tests',    0))
        s_failures = int(suite.get('failures', 0))
        s_errors   = int(suite.get('errors',   0))
        s_skipped  = int(suite.get('skipped',  0))
        s_time     = float(suite.get('time',   0.0))
        s_name     = suite.get('name', 'unnamed')
        s_passed   = s_tests - s_failures - s_errors - s_skipped

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

        for tc in suite.findall('testcase'):
            tc_name  = tc.get('name',      'unknown')
            tc_class = tc.get('classname', 'unknown')
            tc_time  = float(tc.get('time', 0.0))

            failure = tc.find('failure')
            error   = tc.find('error')

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
