from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src"),
)

import approve_transaction
import copy_album
import fix_album
import review_album


class TestApproveTransaction(unittest.TestCase):
    def config(self, root: Path) -> dict:
        return {
            "storage": {
                "staging_dir": str(root / "staging")
            }
        }

    def make_reviewed_transaction(
        self,
        root: Path,
        *,
        txid: str = "TX-APPROVE",
        review_status: str = "PASS",
        recommendation: str = "PASS",
    ) -> Path:
        transaction = (
            root
            / "staging"
            / copy_album.TRANSACTIONS_DIRNAME
            / txid
        )
        album = transaction / "album"
        album.mkdir(parents=True)
        (album / "01.flac").write_bytes(b"audio")
        (album / "cover.jpg").write_bytes(b"image")

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
                "status": review_status,
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
                "recommendation": recommendation,
                "blocking_conditions": [],
            },
            immutable=True,
        )
        summary = review_dir / review_album.REVIEW_SUMMARY
        summary.write_text("# Review\n", encoding="utf-8")
        summary.chmod(0o444)
        return transaction

    def test_successful_review_decision_is_recorded(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transaction = self.make_reviewed_transaction(root)

            report = approve_transaction.run_approve(
                "TX-APPROVE",
                "APPROVED",
                operator="Richard",
                config=self.config(root),
            )

            self.assertEqual(report["stage"], "APPROVE")
            self.assertEqual(report["status"], "RECORDED")
            self.assertEqual(report["decision"], "APPROVED")
            self.assertEqual(report["operator"], "Richard")
            self.assertTrue(report["approval_valid"])

            evidence = (
                transaction
                / approve_transaction.APPROVAL_DIRNAME
                / approve_transaction.APPROVAL_REPORT
            )
            self.assertTrue(evidence.is_file())
            self.assertEqual(evidence.stat().st_mode & 0o222, 0)

            persisted = json.loads(
                evidence.read_text(encoding="utf-8")
            )
            self.assertEqual(
                len(
                    persisted["evidence"]["review_report"]["sha256"]
                ),
                64,
            )
            self.assertEqual(
                len(
                    persisted["evidence"]
                    ["staged_album_manifest_sha256"]
                ),
                64,
            )

    def test_non_pass_review_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_reviewed_transaction(
                root,
                review_status="BLOCK",
                recommendation="BLOCK",
            )

            with self.assertRaisesRegex(
                ValueError,
                "successful REVIEW",
            ):
                approve_transaction.run_approve(
                    "TX-APPROVE",
                    "REJECTED",
                    config=self.config(root),
                )

    def test_missing_review_evidence_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transaction = self.make_reviewed_transaction(root)
            summary = (
                transaction
                / review_album.REVIEW_DIRNAME
                / review_album.REVIEW_SUMMARY
            )
            summary.chmod(0o600)
            summary.unlink()

            with self.assertRaises(FileNotFoundError):
                approve_transaction.run_approve(
                    "TX-APPROVE",
                    "DEFERRED",
                    config=self.config(root),
                )

    def test_changed_staged_album_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transaction = self.make_reviewed_transaction(root)
            (transaction / "album" / "01.flac").write_bytes(
                b"changed"
            )

            with self.assertRaisesRegex(
                ValueError,
                "changed after REVIEW",
            ):
                approve_transaction.run_approve(
                    "TX-APPROVE",
                    "APPROVED",
                    config=self.config(root),
                )

    def test_existing_approval_is_not_overwritten(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_reviewed_transaction(root)
            approve_transaction.run_approve(
                "TX-APPROVE",
                "APPROVED",
                config=self.config(root),
            )

            with self.assertRaises(FileExistsError):
                approve_transaction.run_approve(
                    "TX-APPROVE",
                    "REJECTED",
                    config=self.config(root),
                )

    def test_invalid_decision_is_rejected_without_evidence(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transaction = self.make_reviewed_transaction(root)

            with self.assertRaises(ValueError):
                approve_transaction.run_approve(
                    "TX-APPROVE",
                    "MAYBE",
                    config=self.config(root),
                )

            self.assertFalse(
                (
                    transaction
                    / approve_transaction.APPROVAL_DIRNAME
                ).exists()
            )

    def test_review_evidence_digests_bind_exact_files(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transaction = self.make_reviewed_transaction(root)
            report = approve_transaction.run_approve(
                "TX-APPROVE",
                "PENDING",
                config=self.config(root),
            )

            review_dir = transaction / review_album.REVIEW_DIRNAME
            self.assertEqual(
                report["evidence"]["review_report"]["sha256"],
                approve_transaction.sha256_file(
                    review_dir / review_album.REVIEW_REPORT
                ),
            )
            self.assertEqual(
                report["evidence"]["review_findings"]["sha256"],
                approve_transaction.sha256_file(
                    review_dir / review_album.REVIEW_FINDINGS
                ),
            )
            self.assertEqual(
                report["evidence"]["review_summary"]["sha256"],
                approve_transaction.sha256_file(
                    review_dir / review_album.REVIEW_SUMMARY
                ),
            )


if __name__ == "__main__":
    unittest.main()
