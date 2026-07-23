from __future__ import annotations
import json, os, sys, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import copy_album

class TestCopyAlbum(unittest.TestCase):
    def make_album(self, root: Path) -> Path:
        album = root/'CONTEMPORARY'/'Artist'/'Album'; album.mkdir(parents=True)
        (album/'01.flac').write_bytes(b'audio-one')
        (album/'disc').mkdir(); (album/'disc'/'02.mp3').write_bytes(b'audio-two')
        (album/'cover.jpg').write_bytes(b'image')
        return album
    def config(self, root: Path):
        return {'libraries': {'contemporary': {'root': str(root/'CONTEMPORARY')}}, 'storage': {'staging_dir': str(root/'staging')}}
    def test_copy_is_complete_verified_and_source_unchanged(self):
        with TemporaryDirectory() as d:
            root=Path(d); album=self.make_album(root); before=copy_album.build_manifest(album)
            report=copy_album.run_copy(album, transaction_id='TX-1', config=self.config(root))
            self.assertEqual(report['status'],'PASS'); self.assertEqual(copy_album.build_manifest(album),before)
            tx=Path(report['transaction_directory']); self.assertEqual(copy_album.build_manifest(tx/'album'), before)
            self.assertFalse(os.access(tx/copy_album.SOURCE_MANIFEST, os.W_OK) and (tx/copy_album.SOURCE_MANIFEST).stat().st_mode & 0o222)
            payload=json.loads((tx/copy_album.COPY_REPORT).read_text()); self.assertEqual(payload['file_count'],3)
    def test_outside_root_rejected(self):
        with TemporaryDirectory() as d:
            root=Path(d); album=root/'outside'; album.mkdir(); (album/'x.flac').write_bytes(b'x')
            with self.assertRaisesRegex(ValueError,'below CONTEMPORARY'):
                copy_album.run_copy(album, transaction_id='TX-2', config=self.config(root))
    def test_nested_symlink_rejected_and_transaction_removed(self):
        with TemporaryDirectory() as d:
            root=Path(d); album=self.make_album(root); outside=root/'secret'; outside.write_bytes(b'secret'); (album/'link').symlink_to(outside)
            with self.assertRaisesRegex(ValueError,'Symbolic links'):
                copy_album.run_copy(album, transaction_id='TX-3', config=self.config(root))
            self.assertFalse((root/'staging'/'transactions'/'TX-3').exists())
    def test_transaction_collision_rejected(self):
        with TemporaryDirectory() as d:
            root=Path(d); album=self.make_album(root); cfg=self.config(root)
            copy_album.run_copy(album, transaction_id='TX-4', config=cfg)
            with self.assertRaises(FileExistsError): copy_album.run_copy(album, transaction_id='TX-4', config=cfg)
    def test_unsafe_transaction_id_rejected(self):
        with self.assertRaises(ValueError): copy_album.validate_transaction_id('../escape')
if __name__=='__main__': unittest.main()

