from __future__ import annotations

import json
import os
import stat
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import copy_album
import fix_album


class TestFixAlbum(unittest.TestCase):
    def config(self, root: Path) -> dict:
        return {
            "libraries": {
                "contemporary": {"root": str(root / "CONTEMPORARY")}
            },
            "storage": {"staging_dir": str(root / "staging")},
        }

    def make_transaction(self, root: Path, txid: str = "TX-FIX") -> Path:
        album = root / "CONTEMPORARY" / "Artist" / "Album"
        album.mkdir(parents=True)
        (album / "01.m4a").write_bytes(b"audio-packets")
        (album / "cover.jpg").write_bytes(b"image")
        copy_album.run_copy(album, transaction_id=txid, config=self.config(root))
        return root / "staging" / "transactions" / txid

    def make_tools(self, root: Path, *, exit_code: int = 0, alter_essence: bool = False) -> tuple[str, str]:
        beet = root / "beet"
        beet.write_text(
            "#!/usr/bin/env python3\n"
            "import pathlib,sys\n"
            "if sys.argv[1:] == ['version']:\n"
            " print('beets version test'); raise SystemExit(0)\n"
            f"p=pathlib.Path(sys.argv[-1])/'01.m4a'; p.write_bytes(p.read_bytes()+b'{'CHANGED' if alter_essence else '|TAG'}')\n"
            "print('fake import')\n"
            f"raise SystemExit({exit_code})\n",
            encoding="utf-8",
        )
        beet.chmod(beet.stat().st_mode | stat.S_IXUSR)

        ffprobe = root / "ffprobe"
        ffprobe.write_text(
            "#!/usr/bin/env python3\n"
            "import hashlib,json,pathlib,sys\n"
            "data=pathlib.Path(sys.argv[-1]).read_bytes().split(b'|TAG')[0]\n"
            "h=hashlib.sha256(data).hexdigest()\n"
            "print(json.dumps({'packets':[{'stream_index':0,'size':str(len(data)),'data_hash':'SHA256:'+h}]}))\n",
            encoding="utf-8",
        )
        ffprobe.chmod(ffprobe.stat().st_mode | stat.S_IXUSR)
        return str(beet), str(ffprobe)

    def test_fix_runs_only_in_transaction_and_preserves_audio_essence(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transaction = self.make_transaction(root)
            production = root / "CONTEMPORARY" / "Artist" / "Album" / "01.m4a"
            production_before = production.read_bytes()
            beet, ffprobe = self.make_tools(root)

            report = fix_album.run_fix(
                "TX-FIX",
                config=self.config(root),
                beet_executable=beet,
                ffprobe_executable=ffprobe,
            )

            self.assertEqual(report["status"], "PASS")
            self.assertTrue(report["file_hashes_changed"])
            self.assertEqual(production.read_bytes(), production_before)
            self.assertTrue((transaction / "album" / "01.m4a").read_bytes().endswith(b"|TAG"))
            self.assertEqual(
                json.loads((transaction / "fix" / fix_album.FIX_REPORT).read_text())["status"],
                "PASS",
            )
            self.assertEqual(
                (transaction / "fix" / fix_album.FIX_REPORT).stat().st_mode & 0o222,
                0,
            )

    def test_missing_transaction_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            beet, ffprobe = self.make_tools(root)
            with self.assertRaises(FileNotFoundError):
                fix_album.run_fix(
                    "MISSING",
                    config=self.config(root),
                    beet_executable=beet,
                    ffprobe_executable=ffprobe,
                )

    def test_modified_copy_evidence_rejected_before_tool_execution(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transaction = self.make_transaction(root)
            (transaction / "album" / "01.m4a").write_bytes(b"tampered")
            beet, ffprobe = self.make_tools(root)
            with self.assertRaisesRegex(ValueError, "COPY evidence"):
                fix_album.run_fix(
                    "TX-FIX",
                    config=self.config(root),
                    beet_executable=beet,
                    ffprobe_executable=ffprobe,
                )
            self.assertFalse((transaction / "fix").exists())

    def test_audio_essence_change_fails_with_retained_evidence(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transaction = self.make_transaction(root)
            beet, ffprobe = self.make_tools(root, alter_essence=True)
            with self.assertRaisesRegex(RuntimeError, "verification failed"):
                fix_album.run_fix(
                    "TX-FIX",
                    config=self.config(root),
                    beet_executable=beet,
                    ffprobe_executable=ffprobe,
                )
            report = json.loads((transaction / "fix" / fix_album.FIX_REPORT).read_text())
            self.assertEqual(report["status"], "FAIL")
            self.assertIn("FIX changed audio essence.", report["verification_errors"])

    def test_existing_fix_evidence_is_never_overwritten(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_transaction(root)
            beet, ffprobe = self.make_tools(root)
            fix_album.run_fix(
                "TX-FIX",
                config=self.config(root),
                beet_executable=beet,
                ffprobe_executable=ffprobe,
            )
            with self.assertRaises(FileExistsError):
                fix_album.run_fix(
                    "TX-FIX",
                    config=self.config(root),
                    beet_executable=beet,
                    ffprobe_executable=ffprobe,
                )


if __name__ == "__main__":
    unittest.main()
