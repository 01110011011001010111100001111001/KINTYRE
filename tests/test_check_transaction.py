from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src"),
)

import approve_transaction
import check_transaction
import copy_album
import fix_album
import replace_transaction
import review_album


class TestCheckTransaction(unittest.TestCase):
    def config(self, root: Path) -> dict:
        return {
            "storage": {
                "staging_dir": str(root / "staging"),
                "replacement_dir": str(
                    root / "replacement-runtime"
                ),
            },
            "libraries": {
                "contemporary": {
                    "root": str(
                        root / "music" / "CONTEMPORARY"
                    )
                }
            },
        }

    def make_completed_transaction(
        self,
        root: Path,
        *,
        txid: str = "TX-CHECK",
    ) -> tuple[Path, Path, dict]:
        production = (
            root
            / "music"
            / "CONTEMPORARY"
            / "Artist"
            / "Album"
        )
        production.mkdir(parents=True)
        (production / "01.flac").write_bytes(b"before-audio")
        (production / "booklet.pdf").write_bytes(
            b"before-booklet"
        )

        transaction = (
            root
            / "staging"
            / copy_album.TRANSACTIONS_DIRNAME
            / txid
        )
        album = transaction / "album"
        album.mkdir(parents=True)
        (album / "01.flac").write_bytes(b"after-audio")
        (album / "cover.jpg").write_bytes(b"after-cover")

        source_manifest = {
            "schema_version": copy_album.SCHEMA_VERSION,
            "transaction_id": txid,
            "library": "CONTEMPORARY",
            "source": str(production.resolve()),
            **copy_album.build_manifest(production),
        }
        copy_album.write_json(
            transaction / copy_album.SOURCE_MANIFEST,
            source_manifest,
            immutable=True,
        )

        fix_dir = transaction / fix_album.FIX_DIRNAME
        fix_dir.mkdir()
        after_manifest = {
            "schema_version": copy_album.SCHEMA_VERSION,
            "stage": "FIX",
            "transaction_id": txid,
            **copy_album.build_manifest(album),
        }
        copy_album.write_json(
            fix_dir / fix_album.AFTER_MANIFEST,
            after_manifest,
            immutable=True,
        )

        review_dir = transaction / review_album.REVIEW_DIRNAME
        review_dir.mkdir()
        copy_album.write_json(
            review_dir / review_album.REVIEW_REPORT,
            {
                "schema_version": copy_album.SCHEMA_VERSION,
                "stage": "REVIEW",
                "status": "PASS",
                "transaction_id": txid,
            },
            immutable=True,
        )
        copy_album.write_json(
            review_dir / review_album.REVIEW_FINDINGS,
            {
                "schema_version": copy_album.SCHEMA_VERSION,
                "stage": "REVIEW",
                "transaction_id": txid,
                "recommendation": "PASS",
                "blocking_conditions": [],
            },
            immutable=True,
        )
        summary = review_dir / review_album.REVIEW_SUMMARY
        summary.write_text("# Review\n", encoding="utf-8")
        summary.chmod(0o444)

        approve_transaction.run_approve(
            txid,
            "APPROVED",
            operator="Tester",
            config=self.config(root),
        )

        replacement = replace_transaction.run_replace(
            txid,
            execute=True,
            config=self.config(root),
        )
        return transaction, production, replacement

    @staticmethod
    def readable_metadata(
        *,
        artwork_present: bool = True,
    ) -> dict:
        return {
            "audio_file_count": 1,
            "readable_audio_file_count": 1,
            "unreadable_audio_files": [],
            "embedded_artwork_file_count": (
                1 if artwork_present else 0
            ),
            "external_artwork_files": (
                ["cover.jpg"] if artwork_present else []
            ),
            "artwork_present": artwork_present,
            "records": [],
        }

    def test_successful_certification_writes_immutable_report(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transaction, _production, _replacement = (
                self.make_completed_transaction(root)
            )

            with mock.patch.object(
                check_transaction,
                "_verify_metadata",
                return_value=self.readable_metadata(),
            ):
                report = check_transaction.run_check(
                    "TX-CHECK",
                    config=self.config(root),
                )

            self.assertEqual(report["stage"], "CHECK")
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(
                report["final_disposition"],
                "CERTIFIED",
            )
            self.assertEqual(
                report["checks"]["music_assistant"],
                "NOT_RUN",
            )

            evidence = (
                transaction
                / check_transaction.CHECK_DIRNAME
                / check_transaction.CHECK_REPORT
            )
            self.assertTrue(evidence.is_file())
            self.assertEqual(
                evidence.stat().st_mode & 0o222,
                0,
            )

    def test_missing_replace_report_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transaction, _production, _replacement = (
                self.make_completed_transaction(root)
            )
            report_path = (
                transaction
                / replace_transaction.REPLACE_DIRNAME
                / replace_transaction.REPLACE_REPORT
            )
            report_path.chmod(0o644)
            report_path.unlink()

            with self.assertRaisesRegex(
                FileNotFoundError,
                "REPLACE evidence",
            ):
                check_transaction.run_check(
                    "TX-CHECK",
                    config=self.config(root),
                )

    def test_modified_production_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            _transaction, production, _replacement = (
                self.make_completed_transaction(root)
            )
            (production / "01.flac").write_bytes(
                b"post-replace-corruption"
            )

            with self.assertRaisesRegex(
                ValueError,
                "Current production",
            ):
                check_transaction.run_check(
                    "TX-CHECK",
                    config=self.config(root),
                )

    def test_missing_backup_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            _transaction, _production, replacement = (
                self.make_completed_transaction(root)
            )
            backup = Path(replacement["backup_directory"])

            for child in backup.iterdir():
                child.unlink()
            backup.rmdir()

            with self.assertRaisesRegex(
                FileNotFoundError,
                "backup",
            ):
                check_transaction.run_check(
                    "TX-CHECK",
                    config=self.config(root),
                )

    def test_metadata_or_artwork_warning_is_non_blocking(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_completed_transaction(root)

            metadata = self.readable_metadata(
                artwork_present=False
            )
            metadata["readable_audio_file_count"] = 0
            metadata["unreadable_audio_files"] = ["01.flac"]

            with mock.patch.object(
                check_transaction,
                "_verify_metadata",
                return_value=metadata,
            ):
                report = check_transaction.run_check(
                    "TX-CHECK",
                    config=self.config(root),
                )

            self.assertEqual(
                report["status"],
                "PASS_WITH_WARNINGS",
            )
            self.assertEqual(
                report["final_disposition"],
                "CERTIFIED_WITH_WARNINGS",
            )
            self.assertEqual(
                report["checks"]["metadata_readability"],
                "WARNING",
            )
            self.assertEqual(
                report["checks"]["artwork"],
                "WARNING",
            )
            self.assertEqual(len(report["warnings"]), 2)

    def test_existing_check_evidence_cannot_be_overwritten(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_completed_transaction(root)

            with mock.patch.object(
                check_transaction,
                "_verify_metadata",
                return_value=self.readable_metadata(),
            ):
                check_transaction.run_check(
                    "TX-CHECK",
                    config=self.config(root),
                )

                with self.assertRaisesRegex(
                    FileExistsError,
                    "overwrite",
                ):
                    check_transaction.run_check(
                        "TX-CHECK",
                        config=self.config(root),
                    )

    def test_backup_digest_mismatch_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            _transaction, _production, replacement = (
                self.make_completed_transaction(root)
            )
            backup = Path(replacement["backup_directory"])
            (backup / "01.flac").write_bytes(
                b"changed-backup"
            )

            with self.assertRaisesRegex(
                ValueError,
                "backup digest",
            ):
                check_transaction.run_check(
                    "TX-CHECK",
                    config=self.config(root),
                )


if __name__ == "__main__":
    unittest.main()
