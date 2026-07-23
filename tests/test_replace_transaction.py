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
    str(Path(__file__).resolve().parents[1] / "src"),
)

import approve_transaction
import copy_album
import fix_album
import replace_transaction
import review_album


class TestReplaceTransaction(unittest.TestCase):
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

    def make_approved_transaction(
        self,
        root: Path,
        *,
        txid: str = "TX-REPLACE",
        decision: str = "APPROVED",
    ) -> tuple[Path, Path]:
        production = (
            root
            / "music"
            / "CONTEMPORARY"
            / "Artist"
            / "Album"
        )
        production.mkdir(parents=True)
        (production / "01.flac").write_bytes(b"before-audio")
        (production / "booklet.pdf").write_bytes(b"before-booklet")

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
            decision,
            operator="Tester",
            config=self.config(root),
        )
        return transaction, production

    def test_preflight_does_not_modify_production(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            _transaction, production = (
                self.make_approved_transaction(root)
            )
            before = copy_album.build_manifest(production)

            report = replace_transaction.run_replace(
                "TX-REPLACE",
                execute=False,
                config=self.config(root),
            )

            self.assertEqual(report["status"], "READY")
            self.assertFalse(report["production_modified"])
            self.assertEqual(
                copy_album.build_manifest(production),
                before,
            )

    def test_execute_replaces_complete_album_and_keeps_backup(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transaction, production = (
                self.make_approved_transaction(root)
            )
            original = copy_album.build_manifest(production)
            staged = copy_album.build_manifest(
                transaction / "album"
            )

            report = replace_transaction.run_replace(
                "TX-REPLACE",
                execute=True,
                config=self.config(root),
            )

            self.assertEqual(report["status"], "PASS")
            self.assertEqual(
                copy_album.build_manifest(production),
                staged,
            )

            backup = Path(report["backup_directory"])
            self.assertTrue(backup.is_dir())
            self.assertEqual(
                copy_album.build_manifest(backup),
                original,
            )

            evidence = (
                transaction
                / replace_transaction.REPLACE_DIRNAME
                / replace_transaction.REPLACE_REPORT
            )
            self.assertTrue(evidence.is_file())
            self.assertEqual(
                evidence.stat().st_mode & 0o222,
                0,
            )

    def test_non_approved_decision_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_approved_transaction(
                root,
                decision="DEFERRED",
            )

            with self.assertRaisesRegex(
                ValueError,
                "APPROVED",
            ):
                replace_transaction.run_replace(
                    "TX-REPLACE",
                    execute=True,
                    config=self.config(root),
                )

    def test_changed_production_before_state_is_rejected(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            _transaction, production = (
                self.make_approved_transaction(root)
            )
            (production / "01.flac").write_bytes(b"changed")

            with self.assertRaisesRegex(
                ValueError,
                "Production before-state",
            ):
                replace_transaction.run_replace(
                    "TX-REPLACE",
                    execute=True,
                    config=self.config(root),
                )

    def test_changed_staged_album_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transaction, _production = (
                self.make_approved_transaction(root)
            )
            (transaction / "album" / "01.flac").write_bytes(
                b"changed"
            )

            with self.assertRaisesRegex(
                ValueError,
                "Staged album",
            ):
                replace_transaction.run_replace(
                    "TX-REPLACE",
                    execute=True,
                    config=self.config(root),
                )

    def test_backup_failure_leaves_production_untouched(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transaction, production = (
                self.make_approved_transaction(root)
            )
            before = copy_album.build_manifest(production)

            def fail_backup_copy(source, destination, **kwargs):
                destination.mkdir(parents=True)
                (
                    destination / "partial.tmp"
                ).write_bytes(b"partial")
                raise OSError("simulated backup failure")

            with mock.patch.object(
                replace_transaction.shutil,
                "copytree",
                side_effect=fail_backup_copy,
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "production remained unchanged",
                ):
                    replace_transaction.run_replace(
                        "TX-REPLACE",
                        execute=True,
                        config=self.config(root),
                    )

            self.assertEqual(
                copy_album.build_manifest(production),
                before,
            )

            evidence = json.loads(
                (
                    transaction
                    / replace_transaction.REPLACE_DIRNAME
                    / replace_transaction.REPLACE_REPORT
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(
                evidence["status"],
                "FAILED_PRE_REPLACE",
            )
            self.assertFalse(
                evidence["production_modified"]
            )
            self.assertIsNone(
                evidence["rollback_method"]
            )

    def test_partial_failure_rolls_back_whole_album(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transaction, production = (
                self.make_approved_transaction(root)
            )
            before = copy_album.build_manifest(production)

            real_replace = os.replace
            calls = 0

            def fail_second_replace(source, destination):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated promotion failure")
                return real_replace(source, destination)

            with mock.patch.object(
                replace_transaction.os,
                "replace",
                side_effect=fail_second_replace,
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "rollback succeeded",
                ):
                    replace_transaction.run_replace(
                        "TX-REPLACE",
                        execute=True,
                        config=self.config(root),
                    )

            self.assertEqual(
                copy_album.build_manifest(production),
                before,
            )

            evidence = json.loads(
                (
                    transaction
                    / replace_transaction.REPLACE_DIRNAME
                    / replace_transaction.REPLACE_REPORT
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(
                evidence["status"],
                "ROLLED_BACK",
            )
            self.assertEqual(
                evidence["rollback_method"],
                "DISPLACED_DIRECTORY",
            )

    def test_existing_replace_evidence_is_not_overwritten(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_approved_transaction(root)

            replace_transaction.run_replace(
                "TX-REPLACE",
                execute=True,
                config=self.config(root),
            )

            with self.assertRaises(FileExistsError):
                replace_transaction.run_replace(
                    "TX-REPLACE",
                    execute=True,
                    config=self.config(root),
                )


if __name__ == "__main__":
    unittest.main()
