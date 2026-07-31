"""
lib/flaky.py — flaky test detection across multiple JUnit XML runs.

Provides:
    detect_flaky(all_results: list[dict]) -> list[str]
        Returns sorted list of 'classname::testname' strings for tests
        that failed in some runs but passed in others.
"""

from collections import defaultdict


def detect_flaky(all_results: list[dict]) -> list[str]:
    """
    A test is flaky if it appears as FAILED in at least one run and
    as PASSED (not failed) in at least one other run.
    """
    failed_in: dict[str, set] = defaultdict(set)

    for idx, result in enumerate(all_results):
        for f in result['failures']:
            key = f"{f['class']}::{f['name']}"
            failed_in[key].add(idx)

    # Tests that failed in SOME runs but not ALL runs are flaky
    flaky = [
        key
        for key, failed_files in failed_in.items()
        if len(failed_files) < len(all_results)
    ]
    return sorted(flaky)
