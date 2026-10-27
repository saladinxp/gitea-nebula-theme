from pathlib import Path
import hashlib
import shutil
import stat
import subprocess
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
REPO = 'gitea-nebula-theme' if (ROOT / 'update-nebula-theme.py').is_file() else 'github-nebula-theme'


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.package = self.root / REPO
        shutil.copytree(ROOT, self.package,
                        ignore=shutil.ignore_patterns('.git', '__pycache__', '*.zip', 'release'))
        version = (self.package / 'RELEASE_VERSION').read_text().strip()
        relative = (f'release/nebula-github-{version}.zip' if REPO.startswith('github')
                    else f'gitea-nebula-{version}.zip')
        self.output = self.package / relative

    def tearDown(self):
        self.temporary.cleanup()

    def run_package(self):
        return subprocess.run(['python3', 'package-theme.py'], cwd=self.package,
                              capture_output=True, text=True)

    def test_symlinked_input_is_not_archived(self):
        target = self.root / 'private.txt'
        target.write_bytes(b'PRIVATE_TEST_SENTINEL')
        readme = self.package / 'README.md'
        readme.unlink()
        readme.symlink_to(target)
        result = self.run_package()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())

    def test_symlinked_output_is_not_overwritten(self):
        target = self.root / 'untouched.txt'
        target.write_bytes(b'KEEP')
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.output.symlink_to(target)
        result = self.run_package()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(target.read_bytes(), b'KEEP')

    def test_symlinked_checksum_is_not_overwritten(self):
        target = self.root / 'untouched.txt'
        target.write_bytes(b'KEEP')
        checksum = self.package / 'SHA256SUMS'
        checksum.unlink()
        checksum.symlink_to(target)
        result = self.run_package()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(target.read_bytes(), b'KEEP')

    def test_archive_checksums_and_install_permissions(self):
        result = self.run_package()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with ZipFile(self.output) as archive:
            lines = archive.read(REPO + '/SHA256SUMS').decode().splitlines()
            for line in lines:
                digest, name = line.split('  ', 1)
                member = REPO + '/' + name
                self.assertEqual(hashlib.sha256(archive.read(member)).hexdigest(), digest)
                self.assertEqual(stat.S_IMODE(archive.getinfo(member).external_attr >> 16), 0o644)
            self.assertEqual(len(archive.namelist()), len(lines) + 1)


if __name__ == '__main__':
    unittest.main()
