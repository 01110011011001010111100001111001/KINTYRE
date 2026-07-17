# ============================================================
# KINTYRE
# Build, Validation and Operations
# ============================================================

PYTHON := python
SRC := src
TESTS := tests

.PHONY: help check test scan audit analysis preview approve apply docs status clean

help:
	@echo
	@echo "KINTYRE"
	@echo
	@echo "Available targets:"
	@echo
	@echo "  make check      - Compile source and tests"
	@echo "  make test       - Run the complete automated test suite"
	@echo "  make scan       - Build the media index"
	@echo "  make audit      - Run the metadata audit"
	@echo "  make analysis   - Generate analysis reports"
	@echo "  make preview    - Generate proposed actions"
	@echo "  make approve    - Show Approval Engine command help"
	@echo "  make apply      - Show Apply Engine command help"
	@echo "  make docs       - List documentation"
	@echo "  make status     - Show runtime directories and files"
	@echo "  make clean      - Remove Python cache files"
	@echo

check:
	$(PYTHON) -m py_compile $(SRC)/*.py $(TESTS)/*.py

test:
	$(PYTHON) -m unittest discover -s $(TESTS) -v

scan:
	$(PYTHON) $(SRC)/scan.py

audit:
	$(PYTHON) $(SRC)/audit_metadata.py

analysis:
	$(PYTHON) $(SRC)/analyze_library.py

preview:
	$(PYTHON) $(SRC)/preview.py

approve:
	$(PYTHON) $(SRC)/approve.py --help

apply:
	$(PYTHON) $(SRC)/apply.py --help

docs:
	@ls -1 README.md INSTALL.md docs/*.md

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
