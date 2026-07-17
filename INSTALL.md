# KINTYRE Installation Guide

**Version:** 1.0

## Requirements

- Linux
- Python 3.12 or later
- Git
- A mounted music library

## Install

```bash
git clone https://github.com/01110011011001010111100001111001/KINTYRE.git
cd KINTYRE
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configure

Review `config/config.yaml`. Keep application data, reports, logs, caches, staging, approvals and backups on the system drive. Keep media on the media drive.

## Validate

```bash
python -m py_compile src/*.py tests/*.py
python -m unittest discover -s tests -v
```

## Read-only workflow

```bash
python src/scan.py
python src/audit_metadata.py
python src/analyze_library.py
python src/preview.py
```

## Approval and Apply

```bash
python src/approve.py --help
python src/apply.py --help
```

Always run Apply in dry-run mode before live execution.
