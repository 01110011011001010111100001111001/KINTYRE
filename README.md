# KINTYRE

Deterministic, audit-first commissioning and metadata management for Music Assistant libraries.

## Release

Current stable release: **v1.0**

## Workflow

```text
Scan → Metadata Audit → Analysis → Preview → Approval → Apply → Verification
```

## Implemented in v1.0

- Scan Engine
- Metadata Audit Engine
- Analysis Engine
- Preview Engine
- Four-state approval model
- Generic exact and contains filtering
- Bulk approval operations
- Atomic approval persistence
- Approval audit logging
- Approved-action export
- Apply dry-run
- Controlled live execution foundations
- Backup, rollback and post-write verification
- Apply outcome audit integration
- Automated regression tests

## Safety model

The media library is authoritative and protected. Scan, Audit, Analysis, Preview and Approval are read-only with respect to media. Only Apply may modify metadata, and only for explicitly approved actions.

Applications, reports, logs, databases, caches, staging, backups and generated runtime files belong on the system drive. The media drive contains media only.

## Documentation

- [Installation](INSTALL.md)
- [Architecture](docs/ARCHITECTURE.md)
- [User Guide](docs/USER_GUIDE.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Report Formats](docs/REPORT_FORMATS.md)
- [Roadmap](docs/ROADMAP.md)
- [Changelog](docs/CHANGELOG.md)

## Repository privacy

The public repository contains source code, tests and generic documentation. Production-library inventories, collection statistics, filenames, generated reports, commissioning results, databases, caches and backups must not be committed.
