# KINTYRE Installation

## Status

The repository contains the released v1 implementation and the target documentation for v2. The v2 workflow is not yet implemented.

## Existing v1 environment

```bash
cd /home/richard/kintyre-dam
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

A successful v1 installation does not prove the v2 OSS toolchain is installed or configured.

## v2 installation boundary

Before v2 implementation, perform a read-only inventory of exact versions, executable paths and configuration for proposed tools, including beets, Picard, Chromaprint/AcoustID, FFmpeg/ffprobe, Mutagen and image-validation tooling.

No external tool may receive production write, move, rename or delete access. Its writable target must be an isolated system-drive copy.

## Storage

- Production media: `/data/Music`
- Repository: `/home/richard/kintyre-dam`
- v2 working data: system drive only
- Never place workspaces, logs, caches, databases or backups on the media drive.
