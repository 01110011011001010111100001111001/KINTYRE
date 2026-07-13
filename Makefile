# ============================================================
# KINTYRE DAM
# Build and Operations
# ============================================================

PYTHON := python
SRC := src

.PHONY: help check scan audit analysis preview clean docs status

help:
	@echo
	@echo "KINTYRE DAM"
	@echo
	@echo "Available targets:"
	@echo
	@echo "  make check      - Syntax check Python source"
	@echo "  make scan       - Build album index"
	@echo "  make audit      - Run metadata audit"
	@echo "  make analysis   - Generate analysis reports"
	@echo "  make preview    - Generate preview reports"
	@echo "  make docs       - List documentation"
	@echo "  make status     - Show runtime directories"
	@echo "  make clean      - Remove temporary files"
	@echo

check:
	$(PYTHON) -m py_compile $(SRC)/*.py

scan:
	$(PYTHON) $(SRC)/scan.py

audit:
	$(PYTHON) $(SRC)/audit_metadata.py

analysis:
	$(PYTHON) $(SRC)/analyze_library.py

preview:
	$(PYTHON) $(SRC)/preview.py

docs:
	@ls -1 docs

status:
	@echo
	@echo "Runtime directories"
	@find runtime -maxdepth 2 -type d | sort
	@echo
	@echo "Generated files"
	@find runtime -maxdepth 2 -type f | sort

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete


test:
	python -m unittest discover -s tests -v
