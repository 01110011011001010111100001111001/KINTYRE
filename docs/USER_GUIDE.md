# KINTYRE User Guide

**Version:** 1.0

## Operating model

```text
Scan → Metadata Audit → Analysis → Preview → Approval → Apply → Verification
```

The media library remains unchanged until Apply executes actions exported as `APPROVED`.

## Activate

```bash
cd /home/richard/kintyre-dam
source .venv/bin/activate
```

## 1. Run the read-only pipeline

```bash
python src/scan.py
python src/audit_metadata.py
python src/analyze_library.py
python src/preview.py
```

Review outputs under `runtime/index/`, `runtime/reports/`, `runtime/analysis/` and `runtime/preview/` before recording approvals.

## 2. Initialize Approval

```bash
python src/approve.py init
```

To discard an existing approval working copy and rebuild it from the current Preview plan:

```bash
python src/approve.py init --reset
```

Approval states are `PENDING`, `APPROVED`, `REJECTED` and `DEFERRED`.

## 3. Record decisions

One action:

```bash
python src/approve.py approve ACTION_ID
python src/approve.py reject ACTION_ID
python src/approve.py defer ACTION_ID
python src/approve.py reset ACTION_ID
```

Filtered batch, using `FIELD=VALUE` for exact matching and `FIELD~VALUE` for contains matching:

```bash
python src/approve.py approve --filter 'action=ADD_ALBUMARTIST'
python src/approve.py approve --filter 'folder~Artist Name' --filter 'action=ADD_ALBUMARTIST'
```

Multiple filters are combined with logical AND. A zero-match bulk operation is rejected.

All actions:

```bash
python src/approve.py approve --all
```

Exactly one selector may be used: an action ID, filters, or `--all`. Repeating the same decision is idempotent.

Check totals:

```bash
python src/approve.py status
```

Approval records and the approved-action export are stored under `runtime/approval/`.

## 4. Dry-run Apply

```bash
python src/apply.py
```

This validates the approved export, paths, operation, target formats, duplicate targets and current metadata without writing media. Continue only when the report shows zero blocked transactions.

## 5. Execute Apply

```bash
python src/apply.py --execute --confirm I_APPROVE_KINTYRE_APPLY
```

Live execution is refused unless both options and the exact confirmation phrase are supplied.

Apply currently writes AlbumArtist metadata for:

- `.flac`
- `.mp3`
- `.m4a`
- `.m4b`
- `.mp4`

Other formats may be scanned or audited but are not writable by Apply.

## 6. Verify

```bash
python src/scan.py
python src/audit_metadata.py
```

Then compare findings, inspect `runtime/apply/apply-report.json` and `runtime/approval/approval-audit.json`, and refresh or rebuild Music Assistant where required. A successful metadata write does not by itself remove stale Music Assistant database identities.

## Recovery

Apply creates transaction backups and verifies writes. If any transaction fails during a batch, KINTYRE attempts batch rollback of transactions already applied in that run. Stop further work, preserve the Apply report and audit log, inspect rollback fields and restore from backups if any rollback failure is reported.


## Music Assistant artwork commissioning

This optional operation works only on Music Assistant, the rebuildable consumer. It does not edit media files or manipulate the Music Assistant database directly. It enumerates library artists and albums through the supported HTTP/JSON-RPC API and reads each detail record so metadata providers and image handling are exercised proactively.

Create a user-readable token file outside the repository, for example `~/.config/kintyre/ma-token`, containing only a Music Assistant long-lived API token.

Dry-run and inventory:

```bash
python src/commission_artwork.py \
  --url http://127.0.0.1:8095 \
  --token-file ~/.config/kintyre/ma-token
```

Commission all album and artist records:

```bash
python src/commission_artwork.py \
  --url http://127.0.0.1:8095 \
  --token-file ~/.config/kintyre/ma-token \
  --execute \
  --confirm I_APPROVE_MA_ARTWORK_COMMISSIONING
```

The operation is rate-limited, resumable and idempotent from KINTYRE's perspective. Reports and resume state are written under `runtime/music-assistant/`. Use `--limit 25` for a small live trial and `--media-type albums` or `--media-type artists` to restrict scope. Delete the state file only when an intentional complete recommissioning is required.

This feature cannot guarantee that an external metadata provider has artwork for every identity. Its report distinguishes API failures from successful entity touches; remaining missing artwork must then be investigated as provider coverage, identity, local-file artwork, or Music Assistant cache behaviour.
