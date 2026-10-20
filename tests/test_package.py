import hashlib
from pathlib import Path
import tarfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'releases/0.1.11/virtualmin-ftps-0.1.11.wbm.gz'


class Package(unittest.TestCase):
    def test_archive_checksum(self):
        expected = Path(str(ARCHIVE) + '.sha256').read_text().split()[0]
        self.assertEqual(hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(), expected)

    def test_structure_and_permissions(self):
        with tarfile.open(ARCHIVE) as archive:
            names = archive.getnames()
            self.assertIn('virtualmin-ftps/module.info', names)
            self.assertEqual(len(names), len(set(names)))
            for info in archive.getmembers():
                self.assertTrue(info.isfile())
                self.assertTrue(info.name.startswith('virtualmin-ftps/'))
                self.assertNotIn('..', Path(info.name).parts)
                self.assertNotIn('__pycache__', info.name)
                if info.name.endswith(('.py', '.pl', '.cgi')):
                    self.assertEqual(info.mode, 0o755)
            info = archive.extractfile('virtualmin-ftps/module.info').read()
            self.assertIn(b'version=0.1.11', info)
            self.assertIn(b'(Beta)', info)

    def test_manifest_complete_and_valid(self):
        with tarfile.open(ARCHIVE) as archive:
            manifest = archive.extractfile('virtualmin-ftps/MANIFEST.sha256').read().decode()
            entries = {}
            for line in manifest.splitlines():
                digest, relative = line.split('  ', 1)
                name = 'virtualmin-ftps/' + relative
                self.assertNotIn(name, entries)
                entries[name] = digest
                data = archive.extractfile(name).read()
                self.assertEqual(hashlib.sha256(data).hexdigest(), digest)
            self.assertEqual(set(entries), set(archive.getnames()) - {'virtualmin-ftps/MANIFEST.sha256'})

    def test_packaged_sources_match_repository(self):
        with tarfile.open(ARCHIVE) as archive:
            for name in archive.getnames():
                self.assertEqual(archive.extractfile(name).read(), (ROOT / name).read_bytes(), name)
            compile(archive.extractfile('virtualmin-ftps/engine.py').read(), 'engine.py', 'exec')


if __name__ == '__main__':
    unittest.main()
