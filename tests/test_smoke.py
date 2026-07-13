from pathlib import Path
import unittest

PROJECT = Path(__file__).resolve().parent.parent

class TestProjectStructure(unittest.TestCase):

    def test_src_exists(self):
        self.assertTrue((PROJECT / "src").is_dir())

    def test_runtime_exists(self):
        self.assertTrue((PROJECT / "runtime").is_dir())

    def test_docs_exists(self):
        self.assertTrue((PROJECT / "docs").is_dir())

    def test_scan_exists(self):
        self.assertTrue((PROJECT / "src" / "scan.py").is_file())

    def test_audit_exists(self):
        self.assertTrue((PROJECT / "src" / "audit_metadata.py").is_file())

    def test_analysis_exists(self):
        self.assertTrue((PROJECT / "src" / "analyze_library.py").is_file())

    def test_preview_exists(self):
        self.assertTrue((PROJECT / "src" / "preview.py").is_file())

if __name__ == "__main__":
    unittest.main()
