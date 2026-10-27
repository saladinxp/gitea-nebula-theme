#!/usr/bin/env python3
"""Build a release archive from the explicit public file manifest."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / 'PUBLIC_FILES.txt'


def package():
    names = [line.strip() for line in MANIFEST.read_text(encoding='utf-8').splitlines()
             if line.strip() and not line.lstrip().startswith('#')]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate path in public file manifest')
    files = []
    for name in names:
        path = ROOT / name
        if (path.is_symlink() or not path.is_file() or
                path.resolve().parent != path.parent or
                not path.resolve().is_relative_to(ROOT)):
            raise ValueError(f'Invalid public file path: {name}')
        files.append(path)
    checksums = ''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' +
                        path.relative_to(ROOT).as_posix() + '\n' for path in files)
    (ROOT / 'SHA256SUMS').write_text(checksums, encoding='utf-8')
    target = ROOT / 'gitea-nebula-2.1.2.zip'
    with ZipFile(target, 'w', ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in [*files, ROOT / 'SHA256SUMS']:
            bundle.write(path, 'gitea-nebula-theme/' + path.relative_to(ROOT).as_posix())
    with ZipFile(target) as bundle:
        bad = bundle.testzip()
        if bad:
            raise RuntimeError('Archive verification failed: ' + bad)
    print(f'{target.name}: {len(files)+1} files, {target.stat().st_size:,} bytes; verified.')


if __name__ == '__main__':
    package()
