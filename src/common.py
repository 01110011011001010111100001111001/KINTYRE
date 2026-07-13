from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
CONFIG_DIR = PROJECT_ROOT / "config"
RUNTIME_DIR = PROJECT_ROOT / "runtime"
INDEX_DIR = RUNTIME_DIR / "index"
REPORTS_DIR = RUNTIME_DIR / "reports"
ANALYSIS_DIR = RUNTIME_DIR / "analysis"

DATA_ROOT = Path("/data/Music")

LIBRARIES: dict[str, Path] = {
    "CONTEMPORARY": DATA_ROOT / "CONTEMPORARY",
    "CLASSICAL": DATA_ROOT / "CLASSICAL",
}

SUPPORTED_AUDIO_EXTENSIONS = frozenset(
    {
        ".aac",
        ".aif",
        ".aiff",
        ".alac",
        ".ape",
        ".dff",
        ".dsf",
        ".flac",
        ".m4a",
        ".m4b",
        ".mp3",
        ".mp4",
        ".oga",
        ".ogg",
        ".opus",
        ".wav",
        ".wma",
        ".wv",
    }
)

DEFAULT_CONFIG: dict[str, Any] = {
    "project_root": str(PROJECT_ROOT),
    "data_root": str(DATA_ROOT),
    "libraries": {
        name: str(path)
        for name, path in LIBRARIES.items()
    },
    "runtime": {
        "index_dir": str(INDEX_DIR),
        "reports_dir": str(REPORTS_DIR),
        "analysis_dir": str(ANALYSIS_DIR),
    },
    "supported_audio_extensions": sorted(
        SUPPORTED_AUDIO_EXTENSIONS
    ),
}


def utc_now() -> datetime:
    """Return a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return (
        utc_now()
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def timestamp_slug() -> str:
    """Return a compact UTC timestamp for filenames."""
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def project_path(*parts: str) -> Path:
    return PROJECT_ROOT.joinpath(*parts)


def runtime_path(*parts: str) -> Path:
    return RUNTIME_DIR.joinpath(*parts)


def report_path(*parts: str) -> Path:
    return REPORTS_DIR.joinpath(*parts)


def analysis_path(*parts: str) -> Path:
    return ANALYSIS_DIR.joinpath(*parts)


def ensure_runtime_directories() -> None:
    """
    Create project report directories.

    These locations are all on the system drive.
    """
    for path in (
        INDEX_DIR,
        REPORTS_DIR,
        ANALYSIS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def _deep_merge(
    base: dict[str, Any],
    override: Mapping[str, Any],
) -> dict[str, Any]:
    merged = copy.deepcopy(base)

    for key, value in override.items():
        if (
            isinstance(value, Mapping)
            and isinstance(merged.get(key), dict)
        ):
            merged[key] = _deep_merge(
                merged[key],
                value,
            )
        else:
            merged[key] = copy.deepcopy(value)

    return merged


def _load_yaml(path: Path) -> Mapping[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Cannot read YAML configuration "
            f"{path}: PyYAML is not installed"
        ) from exc

    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)

    if loaded is None:
        return {}

    if not isinstance(loaded, Mapping):
        raise ValueError(
            f"Configuration root must be a mapping: {path}"
        )

    return loaded


def load_config(
    path: Path | None = None,
) -> dict[str, Any]:
    """
    Load project configuration.

    Search order when no explicit path is supplied:

    1. config/config.yaml
    2. config/config.yml
    3. config/config.json

    Missing configuration is allowed. Stable project
    defaults are returned.
    """
    selected = path

    if selected is None:
        for candidate in (
            CONFIG_DIR / "config.yaml",
            CONFIG_DIR / "config.yml",
            CONFIG_DIR / "config.json",
        ):
            if candidate.is_file():
                selected = candidate
                break

    if selected is None:
        return copy.deepcopy(DEFAULT_CONFIG)

    selected = selected.expanduser().resolve()

    if not selected.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: {selected}"
        )

    suffix = selected.suffix.lower()

    if suffix == ".json":
        with selected.open(
            "r",
            encoding="utf-8",
        ) as handle:
            loaded = json.load(handle)

        if not isinstance(loaded, Mapping):
            raise ValueError(
                "Configuration root must be a mapping: "
                f"{selected}"
            )

    elif suffix in {".yaml", ".yml"}:
        loaded = _load_yaml(selected)

    else:
        raise ValueError(
            f"Unsupported configuration format: {selected}"
        )

    return _deep_merge(
        DEFAULT_CONFIG,
        loaded,
    )
