from __future__ import annotations

import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mutagen import File
import apply


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
class TestRealMediaCertification(unittest.TestCase):
    def make_audio(self, path: Path) -> None:
        codec_args = {
            ".flac": ["-c:a", "flac"],
            ".mp3": ["-c:a", "libmp3lame", "-q:a", "7"],
            ".m4a": ["-c:a", "aac", "-b:a", "64k"],
        }[path.suffix]
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=0.25",
                *codec_args,
                "-metadata", "artist=Track Artist",
                "-metadata", "album=Test Album",
                "-metadata", "title=Test Track",
                str(path),
            ],
            check=True,
        )

    def assert_decodable(self, path: Path) -> None:
        subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "default=nw=1", str(path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test_real_flac_mp3_m4a_write_preserves_core_tags_and_audio(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for suffix in (".flac", ".mp3", ".m4a"):
                path = root / f"track{suffix}"
                self.make_audio(path)
                before = File(path, easy=True)
                self.assertIsNotNone(before)
                expected = {key: list(before.get(key, [])) for key in ("artist", "album", "title")}

                apply.set_albumartist(path, "Certified Artist")

                self.assertEqual(apply.read_albumartist(path), ["Certified Artist"])
                after = File(path, easy=True)
                self.assertIsNotNone(after)
                for key, values in expected.items():
                    self.assertEqual(list(after.get(key, [])), values)
                self.assert_decodable(path)

    def test_real_mixed_transaction_creates_verified_backups(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            album = root / "album"
            album.mkdir()
            files = []
            for suffix in (".flac", ".mp3", ".m4a"):
                path = album / f"track{suffix}"
                self.make_audio(path)
                files.append(path)
            transaction = {
                "id": "ACT-CERT",
                "operation": "ADD_ALBUMARTIST",
                "status": "SIMULATED",
                "validation": "PASS",
                "value": "Certified Artist",
                "files_to_update": [str(path) for path in files],
            }
            with mock.patch.object(apply, "BACKUP_ROOT", root / "backups"):
                result = apply.write_albumartist(transaction, run_id="CERT")
            self.assertEqual(result["status"], "APPLIED")
            self.assertEqual(result["files_updated_count"], 3)
            for path in files:
                self.assertEqual(apply.read_albumartist(path), ["Certified Artist"])
                self.assert_decodable(path)
            for item in result["backup_files"]:
                backup = Path(item["backup"])
                self.assertTrue(backup.is_file())
                self.assert_decodable(backup)

    def test_batch_failure_rolls_back_prior_real_write(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.mp3"
            second = root / "second.m4a"
            self.make_audio(first)
            self.make_audio(second)
            transactions = [
                {"id": "ACT-1", "operation": "ADD_ALBUMARTIST", "status": "SIMULATED", "validation": "PASS", "value": "Artist", "files_to_update": [str(first)]},
                {"id": "ACT-2", "operation": "ADD_ALBUMARTIST", "status": "SIMULATED", "validation": "PASS", "value": "Artist", "files_to_update": [str(second)]},
            ]
            original = apply.set_albumartist
            def fail_second(path: Path, value: str) -> None:
                if path == second:
                    raise RuntimeError("forced certification failure")
                original(path, value)
            with mock.patch.object(apply, "BACKUP_ROOT", root / "backups"), mock.patch.object(apply, "set_albumartist", side_effect=fail_second):
                results = apply.execute_batch(transactions)
            self.assertEqual(results[0]["status"], "ROLLED_BACK_BATCH")
            self.assertEqual(results[1]["status"], "ROLLED_BACK")
            self.assertEqual(apply.read_albumartist(first), [])
            self.assertEqual(apply.read_albumartist(second), [])
            self.assert_decodable(first)
            self.assert_decodable(second)


class TestApplyPlanSafety(unittest.TestCase):
    def test_duplicate_file_targets_block_every_affected_action(self) -> None:
        transactions = [
            {"id": "ACT-1", "validation": "PASS", "status": "SIMULATED", "files_to_update": ["/tmp/a.mp3"]},
            {"id": "ACT-2", "validation": "PASS", "status": "SIMULATED", "files_to_update": ["/tmp/a.mp3"]},
        ]
        apply.mark_duplicate_targets(transactions)
        self.assertEqual([item["validation"] for item in transactions], ["FAIL", "FAIL"])
        self.assertEqual([item["status"] for item in transactions], ["BLOCKED", "BLOCKED"])


if __name__ == "__main__":
    unittest.main()
