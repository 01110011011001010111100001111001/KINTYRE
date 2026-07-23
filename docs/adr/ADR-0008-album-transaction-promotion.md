# ADR-0008: Album transaction replacement

- Status: Accepted, simplified
- Date: 2026-07-23

One album is one transaction. The approved working album replaces the production album only after before-state validation and verified complete backup. The public stage is REPLACE, not promotion. Partial per-track completion is prohibited; failure restores the complete prior album.
