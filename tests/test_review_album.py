from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
        / "src"
    ),
)

import copy_album
import fix_album
import review_album


class FakeEasyAudio:
    def __init__(
        self,
        tags: dict[str, object] | None = None,
    ) -> None:
        self.tags = tags or {}


class FakeRawAudio:
    def __init__(
        self,
        tags: dict[str, object] | None = None,
    ) -> None:
        self.tags = tags or {}
        self.pictures: list[object] = []


class TestReviewAlbum(unittest.TestCase):
    def config(self, root: Path) -> dict:
        return {
            "libraries": {
                "contemporary": {
                    "root": str(
                        root / "CONTEMPORARY"
                    )
                }
            },
            "storage": {
                "staging_dir": str(
                    root / "staging"
                )
            },
        }

    def make_copy(
        self,
        root: Path,
        txid: str = "TX-REVIEW",
        extension: str = ".flac",
    ) -> tuple[Path, Path]:
        album = (
            root
            / "CONTEMPORARY"
            / "Artist"
            / "Album"
        )
        album.mkdir(parents=True)
        (
            album / f"01{extension}"
        ).write_bytes(b"audio")
        (
            album / "cover.jpg"
        ).write_bytes(b"image")

        report = copy_album.run_copy(
            album,
            transaction_id=txid,
            config=self.config(root),
        )

        return (
            album,
            Path(report["transaction_directory"]),
        )

    def complete_fix_evidence(
        self,
        transaction: Path,
        txid: str = "TX-REVIEW",
        *,
        essence_matches: bool = True,
    ) -> None:
        album = transaction / "album"
        fix_dir = transaction / fix_album.FIX_DIRNAME
        fix_dir.mkdir()

        before = copy_album.build_manifest(album)
        after = copy_album.build_manifest(album)

        before_payload = {
            "schema_version": copy_album.SCHEMA_VERSION,
            "transaction_id": txid,
            "stage": "FIX",
            **before,
        }
        after_payload = {
            "schema_version": copy_album.SCHEMA_VERSION,
            "transaction_id": txid,
            "stage": "FIX",
            **after,
        }

        essence_before = {
            "schema_version": copy_album.SCHEMA_VERSION,
            "transaction_id": txid,
            "stage": "FIX",
            "files": [
                {
                    "relative_path": "01.flac",
                    "packet_count": 1,
                    "packet_data_sha256": "same",
                }
            ],
        }
        essence_after = json.loads(
            json.dumps(essence_before)
        )

        if not essence_matches:
            essence_after["files"][0][
                "packet_data_sha256"
            ] = "changed"

        copy_album.write_json(
            fix_dir / fix_album.BEFORE_MANIFEST,
            before_payload,
        )
        copy_album.write_json(
            fix_dir / fix_album.AFTER_MANIFEST,
            after_payload,
        )
        copy_album.write_json(
            fix_dir
            / fix_album.AUDIO_ESSENCE_BEFORE,
            essence_before,
        )
        copy_album.write_json(
            fix_dir
            / fix_album.AUDIO_ESSENCE_AFTER,
            essence_after,
        )
        copy_album.write_json(
            fix_dir / fix_album.FIX_REPORT,
            {
                "schema_version": (
                    copy_album.SCHEMA_VERSION
                ),
                "stage": "FIX",
                "status": "PASS",
                "transaction_id": txid,
            },
        )

    def fake_mutagen(
        self,
        path: Path,
        *,
        easy: bool,
    ) -> object:
        if easy:
            return FakeEasyAudio(
                {
                    "title": [path.stem],
                    "artist": ["Artist"],
                    "album": ["Album"],
                    "albumartist": ["Artist"],
                }
            )
        return FakeRawAudio()

    def test_successful_transaction_is_certified(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            _source, transaction = self.make_copy(
                root
            )
            self.complete_fix_evidence(transaction)

            with mock.patch.object(
                review_album.mutagen,
                "File",
                side_effect=self.fake_mutagen,
            ):
                report = review_album.run_review(
                    "TX-REVIEW",
                    config=self.config(root),
                )

            self.assertEqual(report["status"], "PASS")

            review_dir = (
                transaction
                / review_album.REVIEW_DIRNAME
            )

            self.assertTrue(
                (
                    review_dir
                    / review_album.REVIEW_REPORT
                ).is_file()
            )
            self.assertTrue(
                (
                    review_dir
                    / review_album.REVIEW_FINDINGS
                ).is_file()
            )
            self.assertTrue(
                (
                    review_dir
                    / review_album.REVIEW_SUMMARY
                ).is_file()
            )

            for evidence in review_dir.iterdir():
                self.assertEqual(
                    evidence.stat().st_mode & 0o222,
                    0,
                )

    def test_audio_essence_mismatch_blocks(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            _source, transaction = self.make_copy(
                root
            )
            self.complete_fix_evidence(
                transaction,
                essence_matches=False,
            )

            with mock.patch.object(
                review_album.mutagen,
                "File",
                side_effect=self.fake_mutagen,
            ):
                report = review_album.run_review(
                    "TX-REVIEW",
                    config=self.config(root),
                )

            self.assertEqual(report["status"], "BLOCK")
            self.assertIn(
                "FIX audio-essence evidence does not match.",
                report["verification_errors"],
            )

    def test_existing_review_is_not_overwritten(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            _source, transaction = self.make_copy(
                root
            )
            self.complete_fix_evidence(transaction)

            with mock.patch.object(
                review_album.mutagen,
                "File",
                side_effect=self.fake_mutagen,
            ):
                review_album.run_review(
                    "TX-REVIEW",
                    config=self.config(root),
                )

                with self.assertRaises(FileExistsError):
                    review_album.run_review(
                        "TX-REVIEW",
                        config=self.config(root),
                    )

    def test_missing_fix_evidence_is_rejected(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_copy(root)

            with self.assertRaises(FileNotFoundError):
                review_album.run_review(
                    "TX-REVIEW",
                    config=self.config(root),
                )

    def test_every_declared_audio_extension_is_seen(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)

            for index, extension in enumerate(
                sorted(
                    review_album
                    .SUPPORTED_AUDIO_EXTENSIONS
                ),
                start=1,
            ):
                (
                    root / f"{index:02d}{extension}"
                ).write_bytes(b"audio")

            with mock.patch.object(
                review_album.mutagen,
                "File",
                side_effect=self.fake_mutagen,
            ):
                manifest = (
                    review_album
                    .build_metadata_manifest(root)
                )

            self.assertEqual(
                set(
                    manifest[
                        "observed_formats"
                    ]
                ),
                set(
                    review_album
                    .SUPPORTED_AUDIO_EXTENSIONS
                ),
            )
            self.assertEqual(
                len(manifest["files"]),
                len(
                    review_album
                    .SUPPORTED_AUDIO_EXTENSIONS
                ),
            )

    def test_metadata_unavailable_is_warning_not_block(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            _source, transaction = self.make_copy(
                root
            )
            self.complete_fix_evidence(transaction)

            with mock.patch.object(
                review_album.mutagen,
                "File",
                return_value=None,
            ):
                report = review_album.run_review(
                    "TX-REVIEW",
                    config=self.config(root),
                )

            self.assertEqual(report["status"], "PASS")

            findings = json.loads(
                (
                    transaction
                    / review_album.REVIEW_DIRNAME
                    / review_album.REVIEW_FINDINGS
                ).read_text(encoding="utf-8")
            )

            self.assertTrue(findings["warnings"])
            self.assertFalse(
                findings["blocking_conditions"]
            )


if __name__ == "__main__":
    unittest.main()
