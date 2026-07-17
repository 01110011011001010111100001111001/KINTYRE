# KINTYRE DAM Installation Guide

Version 1.0 RC1

---

# System Requirements

Operating System

    Ubuntu Desktop 24.04 LTS

Python

    3.12 or later

Git

Docker

Music Assistant (optional during Audit and Analysis)

---

# Clone Repository

git clone <repository-url>

cd kintyre-dam

---

# Create Virtual Environment

python3 -m venv .venv

source .venv/bin/activate

---

# Install Dependencies

pip install --upgrade pip

pip install -r requirements.txt

---

# Project Layout

config/

docs/

runtime/

src/

templates/

tests/

static/

---

# Music Library

The master music archive is expected at

    /data/Music

The archive contains only media.

Applications, reports, logs and caches remain on the system drive.

---

# First Run

Generate the library index

    python src/scan.py

Audit metadata

    python src/audit_metadata.py

Analyse the library

    python src/analyze_library.py

All three stages are read-only.

---

# Outputs

runtime/index/

runtime/reports/

runtime/analysis/

---

# Documentation

README.md

docs/ARCHITECTURE.md

docs/USER_GUIDE.md

docs/DEVELOPER_GUIDE.md

docs/REPORT_FORMATS.md

docs/CHANGELOG.md

docs/ROADMAP.md

---

# Upgrade

git pull

source .venv/bin/activate

pip install -r requirements.txt

---

# Safety

Only the Apply Engine may modify metadata.

No other phase writes to

    /data/Music
