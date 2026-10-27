from pathlib import Path
import contextlib
import fcntl
import importlib.util
import io
import os
import stat
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('updater', ROOT / 'update-nebula-theme.py')
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.css = self.root / 'custom/public/assets/css'
        self.css.mkdir(parents=True)
        self.backups = self.root / 'backups'
        self.originals = {}
        for mode in ('light', 'dark', 'auto'):
            name = f'theme-nebula-{mode}.css'
            text = (ROOT / 'css' / name).read_text()
            for _, _, _, block in updater.PATCHES:
                text = text.replace(block, '')
            path = self.css / name
            path.write_text(text)
            path.chmod(0o640)
            self.originals[name] = path.read_bytes()

    def tearDown(self):
        self.temporary.cleanup()

    def run_update(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return updater.update(self.css, self.backups)

    def test_update_exact_backup_permissions_and_second_run(self):
        backup = self.run_update()
        self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o700)
        for name, original in self.originals.items():
            self.assertEqual((backup / name).read_bytes(), original)
            self.assertEqual(stat.S_IMODE((self.css / name).stat().st_mode), 0o640)
        before = {p.name: (p.read_bytes(), p.stat().st_ino) for p in self.css.iterdir()}
        self.assertIsNone(self.run_update())
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_ino) for p in self.css.iterdir()})
        self.assertEqual(len(list(self.backups.iterdir())), 1)

    def test_symlinked_input_is_rejected(self):
        path = self.css / 'theme-nebula-light.css'
        target = self.root / 'untouched.css'
        target.write_bytes(path.read_bytes())
        original = target.read_bytes()
        path.unlink()
        path.symlink_to(target)
        with self.assertRaises(OSError):
            self.run_update()
        self.assertEqual(target.read_bytes(), original)
        self.assertFalse(self.backups.exists())

    def test_backup_inside_public_assets_is_rejected(self):
        self.backups = self.css.parent / 'backups'
        with self.assertRaises(RuntimeError):
            self.run_update()
        self.assertFalse(self.backups.exists())

    def test_other_updater_holds_directory_lock(self):
        fd = updater.open_directory(self.css)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(RuntimeError, '另一个主题更新'):
                self.run_update()
        finally:
            os.close(fd)

    def test_concurrent_edit_after_backup_is_preserved(self):
        first = self.css / 'theme-nebula-light.css'
        original_backup = updater.write_backup
        changed = self.originals[first.name] + b'\n/* concurrent edit */'
        def backup_then_edit(directory, name, data):
            original_backup(directory, name, data)
            if name == 'theme-nebula-auto.css':
                first.write_bytes(changed)
        with patch.object(updater, 'write_backup', side_effect=backup_then_edit):
            with self.assertRaisesRegex(RuntimeError, '文件在检查后发生变化'):
                self.run_update()
        self.assertEqual(first.read_bytes(), changed)
        for name, original in self.originals.items():
            if name != first.name:
                self.assertEqual((self.css / name).read_bytes(), original)
        backup = next(self.backups.iterdir())
        self.assertEqual((backup / first.name).read_bytes(), self.originals[first.name])

    def test_write_failure_rolls_back_prior_changes(self):
        original_write = updater.atomic_write
        def fail_second(directory, name, data, info, expected):
            if name == 'theme-nebula-dark.css' and data != self.originals[name]:
                raise OSError('simulated disk failure')
            return original_write(directory, name, data, info, expected)
        with patch.object(updater, 'atomic_write', side_effect=fail_second):
            with self.assertRaisesRegex(RuntimeError, 'simulated disk failure'):
                self.run_update()
        for name, original in self.originals.items():
            self.assertEqual((self.css / name).read_bytes(), original)

    def test_rollback_does_not_erase_an_external_edit(self):
        first = self.css / 'theme-nebula-light.css'
        changed = self.originals[first.name] + b'\n/* later external edit */'
        original_write = updater.atomic_write
        def fail_second(directory, name, data, info, expected):
            if name == 'theme-nebula-dark.css' and data != self.originals[name]:
                first.write_bytes(changed)
                raise OSError('simulated disk failure')
            return original_write(directory, name, data, info, expected)
        with patch.object(updater, 'atomic_write', side_effect=fail_second):
            with self.assertRaisesRegex(RuntimeError, '保留当前内容'):
                self.run_update()
        self.assertEqual(first.read_bytes(), changed)

    def test_directory_replacement_does_not_redirect_writes(self):
        original_backup = updater.write_backup
        moved = self.root / 'original-css'
        outside = self.root / 'outside'
        outside.mkdir()
        sentinel = outside / 'theme-nebula-light.css'
        sentinel.write_bytes(b'KEEP')
        def backup_then_replace(directory, name, data):
            original_backup(directory, name, data)
            if name == 'theme-nebula-auto.css':
                self.css.rename(moved)
                self.css.symlink_to(outside, target_is_directory=True)
        with patch.object(updater, 'write_backup', side_effect=backup_then_replace):
            self.run_update()
        self.assertEqual(sentinel.read_bytes(), b'KEEP')
        self.assertIn(updater.INNER_PAGES_PATCH.encode(), (moved / sentinel.name).read_bytes())


if __name__ == '__main__':
    unittest.main()
