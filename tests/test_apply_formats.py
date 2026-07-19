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

import apply


class TestApplyFormats(unittest.TestCase):
    def test_metadata_format_recognizes_writable_types(
        self,
    ) -> None:
        self.assertEqual(
            apply.metadata_format(Path("track.flac")),
            "FLAC",
        )
        self.assertEqual(
            apply.metadata_format(Path("track.MP3")),
            "MP3",
        )
        self.assertEqual(
            apply.metadata_format(Path("track.m4a")),
            "MP4",
        )
        self.assertEqual(
            apply.metadata_format(Path("track.m4b")),
            "MP4",
        )
        self.assertEqual(
            apply.metadata_format(Path("track.mp4")),
            "MP4",
        )

    def test_inspection_accepts_mixed_supported_formats(
        self,
    ) -> None:
        files = [
            Path("/music/a.flac"),
            Path("/music/b.mp3"),
            Path("/music/c.m4a"),
        ]

        with mock.patch.object(
            apply,
            "media_files",
            return_value=files,
        ), mock.patch.object(
            apply,
            "read_albumartist",
            return_value=[],
        ):
            result = apply.inspect_album(
                Path("/music"),
                "Artist",
            )

        self.assertEqual(
            result["writable_file_count"],
            3,
        )
        self.assertEqual(
            result["format_counts"],
            {
                "FLAC": 1,
                "MP3": 1,
                "MP4": 1,
            },
        )
        self.assertEqual(
            result["unsupported_audio_files"],
            [],
        )
        self.assertEqual(
            len(result["files_to_update"]),
            3,
        )

    def test_mp3_albumartist_uses_tpe2(self) -> None:
        tags = mock.Mock()
        tags.get.return_value = None

        with mock.patch.object(
            apply,
            "read_albumartist",
            side_effect=[[], ["Artist"]],
        ), mock.patch.object(
            apply,
            "ID3",
            return_value=tags,
        ), mock.patch.object(
            apply,
            "TPE2",
            return_value="FRAME",
        ):
            apply.set_albumartist(
                Path("/music/test.mp3"),
                "Artist",
            )

        tags.delall.assert_called_once_with("TPE2")
        tags.add.assert_called_once_with("FRAME")
        tags.save.assert_called_once_with(
            Path("/music/test.mp3")
        )

    def test_mp4_albumartist_uses_aart(self) -> None:
        audio = mock.MagicMock()
        audio.tags = {}

        with mock.patch.object(
            apply,
            "read_albumartist",
            side_effect=[[], ["Artist"]],
        ), mock.patch.object(
            apply,
            "MP4",
            return_value=audio,
        ):
            apply.set_albumartist(
                Path("/music/test.m4a"),
                "Artist",
            )

        audio.__setitem__.assert_called_once_with(
            "aART",
            ["Artist"],
        )
        audio.save.assert_called_once_with()

    def test_execute_rolls_back_all_formats_on_failure(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "one.mp3"
            second = root / "two.m4a"
            first.write_bytes(b"first-original")
            second.write_bytes(b"second-original")

            transaction = {
                "id": "ACT-TEST",
                "operation": "ADD_ALBUMARTIST",
                "status": "SIMULATED",
                "validation": "PASS",
                "value": "Artist",
                "files_to_update": [
                    str(first),
                    str(second),
                ],
            }

            def change_then_fail(
                path: Path,
                value: str,
            ) -> None:
                if path == first:
                    path.write_bytes(b"changed")
                    return

                raise RuntimeError("forced failure")

            with mock.patch.object(
                apply,
                "BACKUP_ROOT",
                root / "backups",
            ), mock.patch.object(
                apply,
                "set_albumartist",
                side_effect=change_then_fail,
            ):
                result = apply.write_albumartist(
                    transaction
                )

            self.assertEqual(
                result["status"],
                "ROLLED_BACK",
            )
            self.assertEqual(
                first.read_bytes(),
                b"first-original",
            )
            self.assertEqual(
                second.read_bytes(),
                b"second-original",
            )


if __name__ == "__main__":
    unittest.main()
