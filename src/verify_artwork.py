#!/usr/bin/env python3
"""
KINTYRE DAM
Artwork Verification Engine

Read-only with respect to Music Assistant and the authoritative media library.
Verifies artwork presence from canonical Music Assistant entity-detail responses.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from commission_artwork import (
    MEDIA_TYPES,
    CommissionTarget,
    MusicAssistantClient,
    MusicAssistantError,
    iter_library_targets,
)

DEFAULT_OUTPUT = Path("runtime/music-assistant/artwork-verification.json")


@dataclass(frozen=True, slots=True)
class VerificationRecord:
    media_type: str
    item_id: str
    provider: str
    name: str
    status: str
    artwork_count: int
    thumb_count: int
    image_types: tuple[str, ...]
    image_providers: tuple[str, ...]
    reason: str | None = None


def _detail_command(media_type: str) -> str:
    return f"music/{media_type}/get_{media_type[:-1]}"


def verify_target(
    client: MusicAssistantClient,
    target: CommissionTarget,
) -> VerificationRecord:
    try:
        detail = client.command(
            _detail_command(target.media_type),
            {
                "item_id": target.item_id,
                "provider_instance_id_or_domain": target.provider,
                "add_to_library": False,
            },
        )
    except MusicAssistantError as exc:
        return VerificationRecord(
            media_type=target.media_type,
            item_id=target.item_id,
            provider=target.provider,
            name=target.name,
            status="ERROR",
            artwork_count=0,
            thumb_count=0,
            image_types=(),
            image_providers=(),
            reason=str(exc),
        )

    metadata = detail.get("metadata") if isinstance(detail, dict) else None
    raw_images = metadata.get("images") if isinstance(metadata, dict) else None
    images = [image for image in raw_images or [] if isinstance(image, dict)]

    image_types = tuple(
        sorted({str(image.get("type")) for image in images if image.get("type")})
    )
    image_providers = tuple(
        sorted({str(image.get("provider")) for image in images if image.get("provider")})
    )
    thumb_count = sum(1 for image in images if image.get("type") == "thumb")

    if thumb_count:
        status = "PRESENT"
        reason = None
    elif images:
        status = "NON_PRIMARY_ONLY"
        reason = "Image metadata exists but no thumb artwork is present."
    else:
        status = "MISSING"
        reason = "Music Assistant returned no image metadata."

    return VerificationRecord(
        media_type=target.media_type,
        item_id=target.item_id,
        provider=target.provider,
        name=target.name,
        status=status,
        artwork_count=len(images),
        thumb_count=thumb_count,
        image_types=image_types,
        image_providers=image_providers,
        reason=reason,
    )


def run_verification(
    client: MusicAssistantClient,
    *,
    media_types: Iterable[str],
    page_size: int,
    limit: int | None,
    report_path: Path,
) -> dict:
    records: list[VerificationRecord] = []

    for media_type in media_types:
        for target in iter_library_targets(client, media_type, page_size=page_size):
            records.append(verify_target(client, target))
            if limit is not None and len(records) >= limit:
                break
        if limit is not None and len(records) >= limit:
            break

    counts = dict(sorted(Counter(record.status for record in records).items()))
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_boundary": {
            "presence": "VERIFIED_FROM_MA_DETAIL_METADATA",
            "retrievability": "NOT_TESTED",
            "image_validity": "NOT_TESTED",
        },
        "counts": counts,
        "records": [asdict(record) for record in records],
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def _read_token(token_file: str | None) -> str:
    if token_file:
        return Path(token_file).read_text(encoding="utf-8").strip()
    token = os.environ.get("KINTYRE_MA_TOKEN", "").strip()
    if token:
        return token
    raise SystemExit("Provide --token-file PATH or set KINTYRE_MA_TOKEN.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify Music Assistant artwork presence without changing MA."
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("KINTYRE_MA_URL", "http://127.0.0.1:8095"),
    )
    parser.add_argument(
        "--token-file",
        default=os.environ.get("KINTYRE_MA_TOKEN_FILE"),
    )
    parser.add_argument(
        "--media-type",
        choices=("all", *MEDIA_TYPES),
        default="all",
    )
    parser.add_argument("--page-size", type=int, default=250)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--report", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    media_types = MEDIA_TYPES if args.media_type == "all" else (args.media_type,)
    client = MusicAssistantClient(args.url, _read_token(args.token_file))
    report = run_verification(
        client,
        media_types=media_types,
        page_size=args.page_size,
        limit=args.limit,
        report_path=args.report,
    )
    print(json.dumps(report["counts"], sort_keys=True))
    print(f"Wrote {args.report}")
    print("READ ONLY — Music Assistant and /data/Music were not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
