# qa-automation-toolkit

![CI](https://github.com/sawaiwalatrupti/qa-automation-toolkit/actions/workflows/ci.yml/badge.svg)

Reads JUnit XML test result files (from pytest, Jenkins, GitHub Actions) and turns them into a clean, human-readable report — so you can quickly see what passed, what failed, and why.

---

## What problem does it solve?

When automated tests run, they produce a raw XML file like this:

```xml
<testsuite name="kvm_tests" tests="10" failures="2">
  <testcase name="test_vm_migration">
    <failure message="VM did not reach running state"/>
  </testcase>
</testsuite>
```

That XML is unreadable. This tool turns it into:

```
Suite : virtualization.kvm_tests
  Tests: 10   Pass: 6   Fail: 2   Error: 1   Skip: 1   (60.0%)

  1. [FAILURE] test_vm_live_migration
       Message : VM did not reach running state after migration
```

---

## What it does

| Feature | Description |
|---|---|
| Pass / fail / error / skip counts | Per suite and grand total |
| Failure details | Test name, class, message, first line of stack trace |
| **Flaky test detection** | Give it XMLs from multiple runs — it flags tests that fail sometimes but not always |
| Colour-coded output | Auto-disabled when piped or in CI |
| Save to file | `-o report.txt` writes a plain-text version |
| CI-ready exit codes | Exit `1` if failures found — stops your pipeline automatically |

---

## Where is it useful?

- **CI/CD pipelines** — run after pytest, exit code gates the build
- **Nightly test monitoring** — readable summary without digging through XML
- **Flaky test hunting** — compare results across multiple runs
- **Cross-distro validation** — run tests on RHEL, SLES, Ubuntu, compare all three XMLs in one report

---

## Repository layout

```
qa-automation-toolkit/
├── README.md
├── Makefile
├── run.py                          ← run from repo root (start here)
└── tests/
    └── junit-report/
        ├── Makefile
        ├── report_generator.py     ← main entry point
        ├── sample_results.xml      ← example XML for quick testing
        └── lib/
            ├── xml_parser.py       ← parses JUnit XML
            ├── flaky.py            ← flaky test detection
            └── reporter.py         ← builds the report
```

---

## Installation

Requires Python 3.9+. No external packages needed.

```bash
# Clone this repo and the shared library side by side
git clone https://github.com/sawaiwalatrupti/qa-automation-toolkit.git
git clone https://github.com/sawaiwalatrupti/testlib-core.git
```

Both repos must be in the same parent directory:
```
your-folder/
├── qa-automation-toolkit/
└── testlib-core/
```

---

## Quick start

```bash
cd qa-automation-toolkit

# Run with the included sample file
python3 run.py tests/junit-report/sample_results.xml

# Run with your own XML
python3 run.py results.xml

# Save report to a file
python3 run.py results.xml -o report.txt

# Disable colours (for CI logs)
python3 run.py results.xml --no-color

# Flaky test detection across multiple runs
python3 run.py monday.xml tuesday.xml wednesday.xml
```

---

## Getting the XML from Jenkins

**From the build page:**
```
Jenkins → Your Job → Build #N → Artifacts → results.xml
```

**Via URL:**
```bash
curl -u username:API_TOKEN \
  -o results.xml \
  "http://<jenkins-url>/job/<job-name>/lastSuccessfulBuild/artifact/results.xml"
```

**Make pytest write it:**
```bash
pytest tests/ --junitxml=results.xml
python3 run.py results.xml
```

---

## Exit codes

| Code | Meaning |
|---|---|
| `0` | All tests passed |
| `1` | One or more failures or errors |
| `2` | Bad arguments (file not found, etc.) |

---

## Requirements

- Python 3.9+
- [testlib-core](https://github.com/sawaiwalatrupti/testlib-core) cloned as a sibling directory
- No other external dependencies
