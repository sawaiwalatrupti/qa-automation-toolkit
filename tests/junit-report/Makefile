# tests/junit-report/Makefile

PYTHON  := python3
SCRIPT  := report_generator.py
SAMPLE  := sample_results.xml
OUTFILE := /tmp/junit_report.txt

.PHONY: run run-sample lint clean

run:
	@test -n "$(FILES)" || (echo "Usage: make run FILES='a.xml b.xml'"; exit 1)
	$(PYTHON) $(SCRIPT) $(FILES)

run-sample:
	$(PYTHON) $(SCRIPT) $(SAMPLE) -o $(OUTFILE)
	@echo "Report written to $(OUTFILE)"

lint:
	python3 -m py_compile $(SCRIPT) lib/xml_parser.py lib/flaky.py lib/reporter.py
	@echo "Syntax OK"

clean:
	rm -f $(OUTFILE)
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
