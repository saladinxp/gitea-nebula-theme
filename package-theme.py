#!/usr/bin/env python3
"""Build the public release ZIP without following filesystem links."""
from pathlib import Path, PurePosixPath
import hashlib
import os
import re
import stat
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent


def safe_path(name):
    if (not name or any(c in name for c in "\r\n\\") or
            any(part in ("", ".", "..") for part in name.split("/")) or
            PurePosixPath(name).is_absolute()):
        raise ValueError(f"Invalid package path: {name!r}")
    path = ROOT / name
    if path.is_symlink() or path.resolve() != path:
        raise ValueError(f"Package paths must not use symlinks: {name}")
    return path


def read_regular(name):
    path = safe_path(name)
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(fd, "rb") as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise ValueError(f"Not a regular package file: {name}")
        return source.read()


def package():
    version = read_regular("RELEASE_VERSION").decode("ascii").strip()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("RELEASE_VERSION must contain a semantic version")
    names = [line.strip() for line in read_regular("PUBLIC_FILES.txt").decode("utf-8").splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if len(names) != len(set(names)) or "SHA256SUMS" in names:
        raise ValueError("Duplicate or reserved path in package manifest")
    for name in names:
        safe_path(name)
    checksum_path = safe_path("SHA256SUMS")
    output = safe_path(f"gitea-nebula-{version}.zip")
    if output.exists() and not output.is_file():
        raise ValueError("The release output must be a regular file")
    if checksum_path.exists() and not checksum_path.is_file():
        raise ValueError("SHA256SUMS must be a regular file")
    subprocess.run([sys.executable, str(ROOT / "build-theme.py"), "--check"], check=True)
    # Hash and archive the same snapshots, even if a source changes later.
    files = {name: read_regular(name) for name in names}
    checksums = "".join(hashlib.sha256(data).hexdigest() + "  " + name + "\n"
                        for name, data in files.items()).encode("utf-8")
    files["SHA256SUMS"] = checksums
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = []
    try:
        fd, archive_tmp = tempfile.mkstemp(prefix=".nebula-package-", suffix=".tmp", dir=output.parent)
        temporary.append(archive_tmp)
        with os.fdopen(fd, "w+b") as stream:
            with ZipFile(stream, "w", ZIP_DEFLATED, compresslevel=9) as archive:
                for name, data in files.items():
                    entry = ZipInfo("gitea-nebula-theme/" + name)
                    entry.create_system = 3
                    entry.external_attr = (stat.S_IFREG | 0o644) << 16
                    entry.compress_type = ZIP_DEFLATED
                    archive.writestr(entry, data)
            stream.flush()
            os.fsync(stream.fileno())
        with ZipFile(archive_tmp) as archive:
            if archive.testzip() is not None:
                raise ValueError("Archive integrity check failed")
        fd, checksum_tmp = tempfile.mkstemp(prefix=".nebula-checksums-", suffix=".tmp", dir=ROOT)
        temporary.append(checksum_tmp)
        with os.fdopen(fd, "wb") as stream:
            stream.write(checksums)
        # Recheck output paths and replace directory entries, never link targets.
        safe_path(checksum_path.relative_to(ROOT).as_posix())
        safe_path(output.relative_to(ROOT).as_posix())
        os.replace(archive_tmp, output)
        os.replace(checksum_tmp, checksum_path)
    finally:
        for path in temporary:
            Path(path).unlink(missing_ok=True)
    print(f"{output.name}: {len(files)} files, {output.stat().st_size:,} bytes; verified.")


if __name__ == "__main__":
    try:
        package()
    except (OSError, ValueError, UnicodeError) as error:
        raise SystemExit(f"Packaging failed: {error}")
