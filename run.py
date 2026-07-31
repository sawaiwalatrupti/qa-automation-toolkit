#!/usr/bin/env python3
"""
run.py — convenience wrapper to run report_generator from the repo root.

Usage (from repo root):
    python3 run.py results.xml
    python3 run.py run1.xml run2.xml -o summary.txt
    python3 run.py --no-color results.xml
    python3 run.py tests/junit-report/sample_results.xml
"""

import sys
from pathlib import Path

# Forward to the real entry point
sys.path.insert(0, str(Path(__file__).resolve().parent / "tests" / "junit-report"))

from report_generator import main

main()
