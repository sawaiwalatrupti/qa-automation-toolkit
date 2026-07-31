# qa-automation-toolkit

A Python tool that parses JUnit XML test result files (produced by pytest, Jenkins, GitHub Actions, or any standard CI system) and generates a clean, human-readable pass/fail summary report with flaky test detection.

---

## Features

- Parses standard JUnit XML (`<testsuites>` and `<testsuite>` formats)
- Pass / fail / error / skip counts per test suite
- Lists every failure and error with class name, test name, and failure message
- **Flaky test detection** — when given multiple XML files from different runs, identifies tests that pass in some runs and fail in others
- Colour-coded terminal output (auto-disabled when piped)
- `--no-color` flag for CI environments
- `-o FILE` to save a plain-text report
- Exit code `1` if any failures/errors exist — suitable for CI pipeline gating

---

## Repository layout

```
qa-automation-toolkit/
├── README.md
├── Makefile
└── tests/
    └── junit-report/
        ├── report_generator.py     ← entry point
        ├── sample_results.xml      ← example JUnit XML for quick testing
        ├── Makefile
        └── lib/
            ├── xml_parser.py       ← JUnit XML parsing
            ├── flaky.py            ← flaky test detection
            └── reporter.py         ← report generation
```

> **Requires [testlib-core](https://github.com/sawaiwalatrupti/testlib-core)** cloned alongside this repo for the shared `Colors` utility.

---

## Installation

```bash
# Python 3.9+ required
python3 --version

# Clone this repo and the shared library
git clone https://github.com/sawaiwalatrupti/qa-automation-toolkit.git
git clone https://github.com/sawaiwalatrupti/testlib-core.git

# Both repos must be in the same parent directory:
# ~/your-dir/
# ├── qa-automation-toolkit/
# └── testlib-core/
```

---

## Usage

The script lives under `tests/junit-report/`. Run it from there, or pass the path explicitly:

```bash
cd tests/junit-report

# Analyse a single result file
python3 report_generator.py results.xml

# Analyse multiple runs (enables flaky test detection)
python3 report_generator.py run1.xml run2.xml run3.xml

# Save report to a file
python3 report_generator.py results.xml -o summary.txt

# Disable colours (useful for CI logs)
python3 report_generator.py results.xml --no-color

# Try it with the included sample file
python3 report_generator.py sample_results.xml
```

Or use `make` from the repo root:

```bash
# Run against the included sample
make test

# Run against your own files
make -C tests/junit-report run FILES="run1.xml run2.xml"
```

---

## Sample output

```
══════════════════════════════════════════════════════════════
  JUnit XML Test Results Summary
══════════════════════════════════════════════════════════════
  Generated : 2025-06-01 16:00:42
  Files     : 1

  File: sample_results.xml
  ────────────────────────────────────────────────────────────
  Suite : virtualization.kvm_tests
    Tests  : 10   Pass: 6   Fail: 2   Error: 1   Skip: 1   Time: 38.45s   (60.0%)

  Suite : kernel.module_tests
    Tests  : 6    Pass: 6   Fail: 0   Error: 0   Skip: 0   Time: 12.10s   (100.0%)

  Suite : networking.interface_tests
    Tests  : 5    Pass: 4   Fail: 1   Error: 0   Skip: 0   Time: 9.87s    (80.0%)

    Failures & Errors:
    1. [FAILURE]  virtualization.kvm_tests::test_vm_live_migration
         Message : AssertionError: VM did not reach running state after migration
    2. [ERROR]    virtualization.kvm_tests::test_vm_passthrough_device
         Message : RuntimeError: VFIO device /dev/vfio/0 not found
    3. [FAILURE]  virtualization.kvm_tests::test_vm_network_bridge
         Message : AssertionError: Bridge interface virbr0 not found after VM start
    4. [FAILURE]  networking.interface_tests::test_ipv6_link_local
         Message : AssertionError: IPv6 link-local address not assigned on eth0

══════════════════════════════════════════════════════════════
```

---

## Flaky test detection (multiple runs)

```bash
cd tests/junit-report
python3 report_generator.py monday.xml tuesday.xml wednesday.xml
```

If a test fails in some runs but passes in others, it is flagged:

```
  Flaky Tests Detected (2 tests):
  ⚠  virtualization.kvm_tests::test_vm_network_bridge
  ⚠  networking.interface_tests::test_ipv6_link_local
```

---

## Exit codes

| Code | Meaning |
|---|---|
| `0` | All tests passed |
| `1` | One or more failures or errors |
| `2` | Bad arguments (file not found, etc.) |

---

## Generating JUnit XML from pytest

```bash
pip install pytest
pytest tests/ --junitxml=results.xml
python3 tests/junit-report/report_generator.py results.xml
```

---

## Requirements

- Python 3.9+
- [testlib-core](https://github.com/sawaiwalatrupti/testlib-core) cloned as a sibling directory
- No other external dependencies (uses `xml.etree.ElementTree` from stdlib)
