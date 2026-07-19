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

Artwork commissioning is an optional consumer-side operation. It works only through Music Assistant's supported authenticated API. It does not edit media files, alter the authoritative library or manipulate the Music Assistant database directly.

The command enumerates library artists and albums and requests each entity's detail record. In the validated Music Assistant implementation, those detail requests can schedule normal asynchronous metadata enrichment.

### Correct operating order

Artwork commissioning is not a substitute for metadata remediation:

```text
Scan → Metadata Audit → Analysis → Preview → Approval → Apply → Verification → Music Assistant rescan or rebuild → Artwork commissioning → Artwork verification
```

Incorrect or incomplete identity metadata can prevent Music Assistant from matching artists, albums and artwork correctly. In particular, a missing AlbumArtist may cause Music Assistant to use `Various Artists` as a fallback where the album is not genuinely a compilation.

### Credentials

Provide the Music Assistant token through either `--token-file PATH`, where the file contains only the token, or the `KINTYRE_MA_TOKEN` environment variable.

Token files must remain outside the repository. Never commit credentials, server addresses, runtime reports or commissioning state.

Define deployment-specific values before using the examples:

```bash
export KINTYRE_MA_URL='http://music-assistant-host:port'
export KINTYRE_MA_TOKEN_FILE='/path/to/token-only-file'
```

These are placeholders. Replace them before running the command; do not paste them literally.

### Dry-run inventory

```bash
python src/commission_artwork.py \
  --url "$KINTYRE_MA_URL" \
  --token-file "$KINTYRE_MA_TOKEN_FILE" \
  --media-type all \
  --page-size 250
```

Use `--limit 25` for a small trial. Use `--media-type albums` or `--media-type artists` to restrict scope.

### Execute

```bash
python src/commission_artwork.py \
  --url "$KINTYRE_MA_URL" \
  --token-file "$KINTYRE_MA_TOKEN_FILE" \
  --media-type all \
  --page-size 250 \
  --execute \
  --confirm I_APPROVE_MA_ARTWORK_COMMISSIONING
```

Live execution requires the exact confirmation phrase.

### Result semantics

- `PLANNED` — target identified during dry-run.
- `TOUCHED` — the Music Assistant entity-detail API request completed.
- `SKIPPED_COMPLETED` — the entity was already recorded in resume state.
- `FAILED` — the entity request failed.

`TOUCHED` does not mean that artwork was found, downloaded, decoded, cached or displayed. Music Assistant performs downstream metadata and image processing asynchronously according to its enabled providers and cache state.

### Resume state and deliberate recommissioning

Reports and state are written under `runtime/music-assistant/`. The state file records completed entity keys, so later runs skip completed entities.

Do not clear state merely because artwork remains missing. Recommissioning is not a substitute for correcting identity metadata or provider coverage.

For an intentional full recommissioning, archive the existing state first:

```bash
mkdir -p runtime/music-assistant/state-backups
test ! -f runtime/music-assistant/artwork-commissioning-state.json || \
mv runtime/music-assistant/artwork-commissioning-state.json \
"runtime/music-assistant/state-backups/artwork-commissioning-state.$(date +%Y%m%d-%H%M%S).json"
```

Then execute commissioning once.

### Artwork verification and troubleshooting

After commissioning, allow Music Assistant's asynchronous enrichment to proceed; inspect artist and album artwork coverage; review Music Assistant logs for provider failures, image decoding failures, cache problems and source metadata warnings; distinguish local embedded artwork, provider artwork and unresolved identities; and return unresolved identity problems to KINTYRE's normal workflow.

A successful commissioning report proves that KINTYRE completed the requested API work. It does not certify complete artwork coverage.
