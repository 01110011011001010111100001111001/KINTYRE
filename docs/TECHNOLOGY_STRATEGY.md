# KINTYRE v2 Technology Strategy

Use mature OSS for music intelligence and write only the KINTYRE code required to execute the six-stage workflow safely.

## Intended roles

These are strategic roles, not proof of live installation:

- beets — candidate bounded FIX workflow;
- MusicBrainz Picard — expert/ambiguous FIX;
- MusicBrainz — release and recording identity;
- Chromaprint/AcoustID — supporting recording evidence;
- Cover Art Archive — preferred release-linked artwork;
- Mutagen — metadata inspection and verification;
- FFmpeg/ffprobe — readability and audio-stream verification;
- image tooling — decoded artwork validation;
- Music Assistant — downstream CHECK target.

## Build versus integrate

Integrate matching, provider queries, working-copy tag writing, artwork acquisition and fingerprints.

Build album selection and COPY, transaction evidence, isolation, REVIEW, APPROVE, verified backup, REPLACE, rollback, CHECK and audit.

No abstraction framework precedes the first proven workflow. No external tool writes production. No AI component is required for the first v2 release.
