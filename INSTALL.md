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

Review `config/config.yaml` before running the pipeline.

- `storage.music_root` identifies the authoritative media root.
- `libraries` defines logical libraries.
- `scan.include` defines the active discovery extensions.
- Runtime data, approvals, reports, logs, caches, staging and backups must remain on the system drive.

The common discovery constants cover AAC, AIFF/AIF, ALAC, APE, DFF, DSF, FLAC, M4A, M4B, MP3, MP4, OGA, OGG, Opus, WAV, WMA and WavPack. Apply writes only FLAC, MP3, M4A, M4B and MP4 metadata.

## Validate installation

```bash
python -m py_compile src/*.py tests/*.py
python -m unittest discover -s tests -v
```

## Run the complete workflow

```bash
python src/scan.py
python src/audit_metadata.py
python src/analyze_library.py
python src/preview.py
python src/approve.py init
python src/approve.py approve --all
python src/approve.py status
python src/apply.py
python src/apply.py --execute --confirm I_APPROVE_KINTYRE_APPLY
python src/scan.py
python src/audit_metadata.py
```

`python src/apply.py` is dry-run mode. Do not run the live command unless the dry run reports zero blocked transactions and the approved actions have been reviewed.

## Approval alternatives

Approve one action:

```bash
python src/approve.py approve ACTION_ID
```

Approve matching actions using exact or contains filters:

```bash
python src/approve.py approve --filter 'action=ADD_ALBUMARTIST'
python src/approve.py approve --filter 'folder~Artist Name' --filter 'action=ADD_ALBUMARTIST'
```

Approve every action explicitly:

```bash
python src/approve.py approve --all
```

Exactly one selector is allowed: an action ID, one or more `--filter` arguments, or `--all`.
