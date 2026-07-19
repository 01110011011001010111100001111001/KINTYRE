from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from common import RUNTIME_DIR, utc_timestamp

REPORT_DIR = RUNTIME_DIR / "music-assistant"
REPORT_PATH = REPORT_DIR / "artwork-commissioning-report.json"
STATE_PATH = REPORT_DIR / "artwork-commissioning-state.json"
CONFIRMATION_PHRASE = "I_APPROVE_MA_ARTWORK_COMMISSIONING"
DEFAULT_PAGE_SIZE = 250
DEFAULT_DELAY = 0.05
MEDIA_TYPES = ("artists", "albums")


class MusicAssistantError(RuntimeError):
    """Raised when the Music Assistant API rejects or cannot fulfil a request."""


@dataclass(frozen=True)
class CommissionTarget:
    media_type: str
    item_id: str
    provider: str
    name: str

    @property
    def key(self) -> str:
        return f"{self.media_type}:{self.provider}:{self.item_id}"


class MusicAssistantClient:
    """Minimal HTTP/JSON-RPC client for Music Assistant."""

    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout: float = 30.0,
        opener: Callable[..., Any] = urllib.request.urlopen,
    ) -> None:
        self.endpoint = f"{base_url.rstrip('/')}/api"
        self.token = token.strip()
        self.timeout = timeout
        self._opener = opener
        self._message_id = 0

        if not self.token:
            raise ValueError("Music Assistant API token is empty")

    def command(self, command: str, args: dict[str, Any] | None = None) -> Any:
        self._message_id += 1
        payload = json.dumps(
            {
                "message_id": str(self._message_id),
                "command": command,
                "args": args or {},
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
        )
        try:
            with self._opener(request, timeout=self.timeout) as response:
                document = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise MusicAssistantError(
                f"Music Assistant HTTP {exc.code}: {detail or exc.reason}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise MusicAssistantError(f"Cannot reach Music Assistant: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise MusicAssistantError("Music Assistant returned invalid JSON") from exc

        if not isinstance(document, dict):
            raise MusicAssistantError("Music Assistant returned an invalid response object")
        if document.get("error_code") or document.get("error_message"):
            raise MusicAssistantError(
                str(document.get("error_message") or document.get("error_code"))
            )
        return document.get("result")


def _items_from_result(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    if isinstance(result, dict):
        for key in ("items", "results"):
            value = result.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    raise MusicAssistantError("Library listing response did not contain an item list")


def _target_from_item(media_type: str, item: dict[str, Any]) -> CommissionTarget:
    item_id = str(item.get("item_id") or item.get("id") or "").strip()
    provider = str(
        item.get("provider")
        or item.get("provider_instance")
        or item.get("provider_domain")
        or "library"
    ).strip()
    name = str(item.get("name") or item.get("sort_name") or item_id).strip()
    if not item_id:
        raise MusicAssistantError(f"{media_type} library item is missing item_id")
    return CommissionTarget(media_type, item_id, provider or "library", name)


def iter_library_targets(
    client: MusicAssistantClient,
    media_type: str,
    *,
    page_size: int,
    list_command: str | None = None,
) -> Iterable[CommissionTarget]:
    command = list_command or f"music/{media_type}/library_items"
    offset = 0
    seen: set[str] = set()
    while True:
        result = client.command(
            command,
            {
                "limit": page_size,
                "offset": offset,
                "order_by": "name",
            },
        )
        items = _items_from_result(result)
        if not items:
            break
        for item in items:
            target = _target_from_item(media_type, item)
            if target.key in seen:
                continue
            seen.add(target.key)
            yield target
        if len(items) < page_size:
            break
        offset += len(items)


def touch_target(
    client: MusicAssistantClient,
    target: CommissionTarget,
    *,
    detail_command: str | None = None,
) -> None:
    singular = target.media_type[:-1]
    command = detail_command or f"music/{target.media_type}/get_{singular}"
    client.command(
        command,
        {
            "item_id": target.item_id,
            "provider_instance_id_or_domain": target.provider,
            "add_to_library": False,
        },
    )


def load_completed(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    values = data.get("completed", []) if isinstance(data, dict) else []
    return {str(value) for value in values}


def save_completed(path: Path, completed: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            {
                "updated_at": utc_timestamp(),
                "completed": sorted(completed),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def run_commissioning(
    client: MusicAssistantClient,
    *,
    execute: bool,
    media_types: tuple[str, ...] = MEDIA_TYPES,
    page_size: int = DEFAULT_PAGE_SIZE,
    delay: float = DEFAULT_DELAY,
    limit: int | None = None,
    resume: bool = True,
    report_path: Path = REPORT_PATH,
    state_path: Path = STATE_PATH,
) -> dict[str, Any]:
    started = utc_timestamp()
    completed = load_completed(state_path) if resume else set()
    targets: list[CommissionTarget] = []
    for media_type in media_types:
        targets.extend(
            iter_library_targets(client, media_type, page_size=page_size)
        )
    targets.sort(key=lambda item: (item.media_type, item.name.casefold(), item.key))
    if limit is not None:
        targets = targets[:limit]

    outcomes: list[dict[str, Any]] = []
    for target in targets:
        if target.key in completed:
            outcomes.append({"key": target.key, "name": target.name, "status": "SKIPPED_COMPLETED"})
            continue
        if not execute:
            outcomes.append({"key": target.key, "name": target.name, "status": "PLANNED"})
            continue
        try:
            touch_target(client, target)
        except Exception as exc:  # record and continue; one bad entity must not stop commissioning
            outcomes.append({"key": target.key, "name": target.name, "status": "FAILED", "reason": str(exc)})
        else:
            completed.add(target.key)
            save_completed(state_path, completed)
            outcomes.append({"key": target.key, "name": target.name, "status": "TOUCHED"})
        if delay:
            time.sleep(delay)

    counts: dict[str, int] = {}
    for outcome in outcomes:
        status = str(outcome["status"])
        counts[status] = counts.get(status, 0) + 1
    report = {
        "schema_version": 1,
        "started_at": started,
        "completed_at": utc_timestamp(),
        "mode": "EXECUTE" if execute else "DRY_RUN",
        "media_types": list(media_types),
        "target_count": len(targets),
        "counts": counts,
        "state_path": str(state_path),
        "outcomes": outcomes,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely prefetch Music Assistant album and artist details so artwork/metadata enrichment is commissioned proactively."
    )
    parser.add_argument("--url", default=os.environ.get("KINTYRE_MA_URL", "http://127.0.0.1:8095"))
    parser.add_argument("--token", default=os.environ.get("KINTYRE_MA_TOKEN"))
    parser.add_argument("--token-file", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm")
    parser.add_argument("--media-type", choices=("all", *MEDIA_TYPES), default="all")
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--no-resume", action="store_true")
    return parser


def resolve_token(args: argparse.Namespace) -> str:
    if args.token_file:
        return args.token_file.expanduser().read_text(encoding="utf-8").strip()
    if args.token:
        return str(args.token).strip()
    raise RuntimeError("Supply --token-file or set KINTYRE_MA_TOKEN")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.page_size < 1 or args.delay < 0 or (args.limit is not None and args.limit < 1):
        parser.error("page size and limit must be positive; delay cannot be negative")
    if args.execute and args.confirm != CONFIRMATION_PHRASE:
        parser.error(f"live commissioning requires --confirm {CONFIRMATION_PHRASE}")
    token = resolve_token(args)
    media_types = MEDIA_TYPES if args.media_type == "all" else (args.media_type,)
    report = run_commissioning(
        MusicAssistantClient(args.url, token),
        execute=args.execute,
        media_types=media_types,
        page_size=args.page_size,
        delay=args.delay,
        limit=args.limit,
        resume=not args.no_resume,
    )
    print("KINTYRE Music Assistant Artwork Commissioning")
    print(f"Mode: {report['mode']}")
    print(f"Targets: {report['target_count']}")
    for status, count in sorted(report["counts"].items()):
        print(f"{status}: {count}")
    print(f"Report: {REPORT_PATH}")
    return 1 if report["counts"].get("FAILED", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
