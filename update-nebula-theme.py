#!/usr/bin/env python3
"""Update three installed Nebula themes on Linux (updater 2.1.3).

Self-contained, Python standard library only. No network requests or service
restarts. Includes the visual patches through 2.1.2. Files are backed up
before writing; concurrent changes cause the update to stop.
"""
from datetime import datetime
import argparse
from pathlib import Path
import os
import re
import fcntl
import secrets
import stat

NAVBAR_PATCH = r"""/* NEBULA_NAVBAR_2_0_1_BEGIN */
/* Keep --color-nav-bg a color: badges and avatar rings also use it. */
#navbar {
  background-color: var(--color-nav-bg);
  background-image: linear-gradient(
    110deg,
    color-mix(in srgb, var(--color-nav-bg) 80%, var(--color-primary) 20%) 0%,
    color-mix(in srgb, var(--color-nav-bg) 95%, var(--color-primary) 5%) 50%,
    color-mix(in srgb, var(--color-nav-bg) 87%, var(--nb-cyan) 13%) 100%
  );
}
/* NEBULA_NAVBAR_2_0_1_END */"""
GEOMETRY_PATCH = r"""/* NEBULA_GEOMETRY_2_1_0_BEGIN */
/* Nebula 2.1: colored file-list surfaces and two decorative background layers.
 * The original grid, display:contents rows, loaders and content order remain native.
 * No script, remote asset, external font or template change is required.
 */
#repo-files-table {
  background-color: color-mix(in srgb, var(--color-body) 92%, var(--color-primary) 8%);
  background-image: linear-gradient(
    115deg,
    color-mix(in srgb, var(--color-body) 84%, var(--color-primary) 16%) 0%,
    color-mix(in srgb, var(--color-body) 96%, var(--color-primary) 4%) 47%,
    color-mix(in srgb, var(--color-body) 86%, var(--nb-cyan) 14%) 100%
  );
  border-color: color-mix(in srgb, var(--color-secondary) 72%, var(--color-primary) 28%);
  box-shadow: var(--nb-panel-shadow), inset 0 1px var(--nb-hairline);
}
#repo-files-table .repo-file-last-commit {
  background-color: var(--color-box-header);
  background-image: linear-gradient(
    110deg,
    color-mix(in srgb, var(--color-box-header) 88%, var(--color-primary) 12%),
    color-mix(in srgb, var(--color-box-header) 94%, var(--nb-cyan) 6%)
  );
}
#repo-files-table .repo-file-item:nth-of-type(even) > .repo-file-cell {
  background-color: color-mix(in srgb, var(--color-box-body) 15%, transparent);
}
#repo-files-table .repo-file-cell.message,
#repo-files-table .repo-file-cell.age {
  color: var(--color-text-light);
}
#repo-files-table .repo-file-item:is(:hover, :focus-within) > .repo-file-cell,
#repo-files-table .parent-link:hover {
  background: color-mix(in srgb, var(--color-body) 80%, var(--color-primary) 20%);
}

/* A body stacking context keeps negative decorative layers above the body
 * background and below normal content. Do not transform or clip the body.
 */
body {
  isolation: isolate;
}
body::before,
body::after {
  content: "";
  position: fixed;
  top: 82px;
  width: clamp(126px, 16vw, 246px);
  height: min(780px, calc(100vh - 130px));
  z-index: -1;
  pointer-events: none;
  user-select: none;
  background-color: var(--color-primary);
  opacity: .24;
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: 100% 100%;
  mask-size: 100% 100%;
  mask-mode: alpha;
  transform-origin: center;
  animation: nebula-geometry-left 38s ease-in-out infinite;
}
body::before {
  left: clamp(16px, 2vw, 34px);
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20240%20760%22%3E%3Cg%20fill%3D%22black%22%20fill-opacity%3D%22.08%22%20stroke%3D%22black%22%20stroke-width%3D%221.8%22%20stroke-linejoin%3D%22round%22%3E%3Crect%20x%3D%2232%22%20y%3D%2254%22%20width%3D%22108%22%20height%3D%22108%22%20rx%3D%229%22%20transform%3D%22rotate(17%2086%20108)%22%2F%3E%3Crect%20x%3D%22115%22%20y%3D%22318%22%20width%3D%2254%22%20height%3D%2254%22%20rx%3D%225%22%20transform%3D%22rotate(-16%20142%20345)%22%2F%3E%3Cpath%20d%3D%22M31%20595%20133%20556%20151%20665Z%22%2F%3E%3Cpath%20d%3D%22M53%20595%20123%20570%20136%20646Z%22%20fill%3D%22none%22%20stroke-opacity%3D%22.45%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20240%20760%22%3E%3Cg%20fill%3D%22black%22%20fill-opacity%3D%22.08%22%20stroke%3D%22black%22%20stroke-width%3D%221.8%22%20stroke-linejoin%3D%22round%22%3E%3Crect%20x%3D%2232%22%20y%3D%2254%22%20width%3D%22108%22%20height%3D%22108%22%20rx%3D%229%22%20transform%3D%22rotate(17%2086%20108)%22%2F%3E%3Crect%20x%3D%22115%22%20y%3D%22318%22%20width%3D%2254%22%20height%3D%2254%22%20rx%3D%225%22%20transform%3D%22rotate(-16%20142%20345)%22%2F%3E%3Cpath%20d%3D%22M31%20595%20133%20556%20151%20665Z%22%2F%3E%3Cpath%20d%3D%22M53%20595%20123%20570%20136%20646Z%22%20fill%3D%22none%22%20stroke-opacity%3D%22.45%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E");
  animation-delay: -9s;
}
body::after {
  right: clamp(16px, 2vw, 34px);
  background-color: var(--nb-cyan);
  opacity: .27;
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20240%20760%22%3E%3Cg%20fill%3D%22black%22%20fill-opacity%3D%22.07%22%20stroke%3D%22black%22%20stroke-width%3D%221.8%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M118%2058%20181%2094%20181%20166%20118%20202%2055%20166%2055%2094Z%22%2F%3E%3Cpath%20d%3D%22M118%2079%20163%20105%20163%20155%20118%20181%2073%20155%2073%20105Z%22%20fill%3D%22none%22%20stroke-opacity%3D%22.4%22%2F%3E%3Crect%20x%3D%2232%22%20y%3D%22430%22%20width%3D%22111%22%20height%3D%22111%22%20rx%3D%228%22%20transform%3D%22rotate(-23%2087%20485)%22%2F%3E%3Crect%20x%3D%22159%22%20y%3D%22640%22%20width%3D%2238%22%20height%3D%2238%22%20rx%3D%224%22%20transform%3D%22rotate(28%20178%20659)%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20240%20760%22%3E%3Cg%20fill%3D%22black%22%20fill-opacity%3D%22.07%22%20stroke%3D%22black%22%20stroke-width%3D%221.8%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M118%2058%20181%2094%20181%20166%20118%20202%2055%20166%2055%2094Z%22%2F%3E%3Cpath%20d%3D%22M118%2079%20163%20105%20163%20155%20118%20181%2073%20155%2073%20105Z%22%20fill%3D%22none%22%20stroke-opacity%3D%22.4%22%2F%3E%3Crect%20x%3D%2232%22%20y%3D%22430%22%20width%3D%22111%22%20height%3D%22111%22%20rx%3D%228%22%20transform%3D%22rotate(-23%2087%20485)%22%2F%3E%3Crect%20x%3D%22159%22%20y%3D%22640%22%20width%3D%2238%22%20height%3D%2238%22%20rx%3D%224%22%20transform%3D%22rotate(28%20178%20659)%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E");
  animation-name: nebula-geometry-right;
  animation-duration: 46s;
  animation-delay: -18s;
}
@keyframes nebula-geometry-left {
  0%, 100% { transform: translate3d(0, 8px, 0) rotate(-2deg); }
  50% { transform: translate3d(3px, -32px, 0) rotate(2deg); }
}
@keyframes nebula-geometry-right {
  0%, 100% { transform: translate3d(0, -26px, 0) rotate(2deg); }
  50% { transform: translate3d(-3px, 26px, 0) rotate(-2deg); }
}
@media (max-width: 767.98px) {
  body::before, body::after {
    width: 126px;
    opacity: .15;
    animation-duration: 54s;
  }
}
html[data-nebula-motion="off"] body::before,
html[data-nebula-motion="off"] body::after {
  animation: none !important;
  transform: none;
}
@media (prefers-reduced-motion: reduce) {
  body::before, body::after {
    animation: none !important;
    transform: none;
  }
}
@supports not (mask-image: linear-gradient(black, black)) {
  body::before, body::after { display: none; }
}
@media print {
  body::before, body::after { display: none; }
}
/* NEBULA_GEOMETRY_2_1_0_END */"""
MOTION_PATCH = r"""/* NEBULA_GEOMETRY_MOTION_2_1_1_BEGIN */
/* More visible drift on the existing two decorative layers.
 * Keep the original geometry and accessibility rules; no new layer or script.
 */
body::before {
  animation-duration: 18s;
  animation-delay: -3s;
}
body::after {
  animation-duration: 22s;
  animation-delay: -7s;
}
@keyframes nebula-geometry-left {
  0%, 100% { transform: translate3d(0, 20px, 0) rotate(-2deg); }
  50% { transform: translate3d(3px, -64px, 0) rotate(2deg); }
}
@keyframes nebula-geometry-right {
  0%, 100% { transform: translate3d(0, -44px, 0) rotate(2deg); }
  50% { transform: translate3d(-3px, 52px, 0) rotate(-2deg); }
}
@media (max-width: 767.98px) {
  body::before, body::after { animation-duration: 32s; }
}
/* NEBULA_GEOMETRY_MOTION_2_1_1_END */"""
INNER_PAGES_PATCH = r"""/* NEBULA_INNER_PAGES_2_1_2_BEGIN */
/* Nebula 2.1.2: calm, opaque reading surfaces for native Gitea 28.2.0.
 * Selectors follow the upstream settings/dashboard/file-view templates.
 * Use current palette colors so light, dark and automatic modes stay in sync.
 */
:root {
  --nb-inner-panel: color-mix(in srgb, var(--color-box-body) 93%, var(--color-primary) 7%);
  --nb-inner-reading: color-mix(in srgb, var(--color-box-body) 96%, var(--color-primary) 4%);
  --nb-inner-sidebar: color-mix(in srgb, var(--color-body) 95%, var(--color-primary) 5%);
  --nb-inner-header: color-mix(in srgb, var(--color-box-header) 92%, var(--color-primary) 8%);
  --nb-inner-border: color-mix(in srgb, var(--color-secondary) 88%, var(--color-primary) 12%);
  --nb-inner-hover: color-mix(in srgb, var(--nb-inner-panel) 94%, var(--color-primary) 6%);
  --nb-inner-selected: color-mix(in srgb, var(--nb-inner-panel) 88%, var(--color-primary) 12%);
}

/* Settings: attached headers/segments retain their native form and menu flow.
 * Leave input backgrounds, validation colors and dropdown layers to Gitea.
 */
.page-content.user.settings .user-setting-content > .ui.top.attached.header:not(.error, .warning, .red, .negative, .positive, .success) {
  background: var(--nb-inner-header);
  border-color: var(--nb-inner-border);
  border-radius: 12px 12px 0 0;
}
.page-content.user.settings .user-setting-content > .ui.attached.segment:not(.error, .warning, .red, .negative, .positive, .success) {
  background: var(--nb-inner-panel);
  border-color: var(--nb-inner-border);
  box-shadow: var(--nb-panel-shadow);
}
.page-content.user.settings .user-setting-content > .ui.attached.segment:not(.error, .warning, .red, .negative, .positive, .success):has(+ .ui.top.attached.header),
.page-content.user.settings .user-setting-content > .ui.attached.segment:not(.error, .warning, .red, .negative, .positive, .success):last-child {
  border-radius: 0 0 12px 12px;
}
.page-content.user.settings .flex-container-nav > .ui.vertical.menu {
  background: var(--nb-inner-sidebar);
  border-color: var(--nb-inner-border);
  border-radius: 12px;
  box-shadow: var(--nb-panel-shadow);
}
.page-content.user.settings .flex-container-nav > .ui.vertical.menu > .header.item {
  background: var(--nb-inner-header);
  border-radius: 11px 11px 0 0;
}
.page-content.user.settings .flex-container-nav > .ui.vertical.menu > a.item:hover {
  background: var(--nb-inner-hover);
}
.page-content.user.settings .flex-container-nav > .ui.vertical.menu > a.active.item {
  background: var(--nb-inner-selected);
  color: var(--color-text-dark);
  box-shadow: inset 3px 0 var(--color-primary);
  font-weight: 600;
}

/* Dashboard: one quiet activity panel, plus coordinated repository cards.
 * No per-entry effects, no backdrop blur and no change to list ordering.
 */
.dashboard #activity-feed {
  background: var(--nb-inner-reading);
  border: 1px solid var(--nb-inner-border);
  border-radius: 12px;
  box-shadow: var(--nb-panel-shadow);
  padding: 4px 18px;
}
.dashboard #activity-feed > .item {
  border-color: var(--color-secondary);
}
.dashboard :is(.dashboard-repos, .dashboard-orgs) > .ui.top.attached.header {
  background: var(--nb-inner-header);
  border-color: var(--nb-inner-border);
  border-radius: 12px 12px 0 0;
}
.dashboard :is(.dashboard-repos, .dashboard-orgs) > .ui.attached.segment {
  background: var(--nb-inner-panel);
  border-color: var(--nb-inner-border);
}
.dashboard :is(.dashboard-repos, .dashboard-orgs) > .ui.attached.segment:last-child {
  border-radius: 0 0 12px 12px;
  box-shadow: var(--nb-panel-shadow);
}
.dashboard #dashboard-repo-list > div > .ui.two.item.menu {
  background: var(--nb-inner-panel);
  border-color: var(--nb-inner-border);
  border-radius: 10px;
}
.dashboard #dashboard-repo-list > div > .ui.two.item.menu > .active.item {
  background: var(--nb-inner-selected);
  color: var(--color-text-dark);
}
.dashboard :is(.dashboard-repos, .dashboard-orgs) .repo-owner-name-list > li {
  background: transparent;
  border-color: var(--color-secondary);
}
.dashboard :is(.dashboard-repos, .dashboard-orgs) .repo-owner-name-list > li:is(:hover, :focus-within) {
  background: var(--nb-inner-hover);
}
.dashboard :is(.dashboard-repos, .dashboard-orgs) .repo-owner-name-list > li.active {
  background: var(--nb-inner-selected);
  box-shadow: inset 3px 0 var(--color-primary);
}

/* File tree: the native sticky container supplies a solid shield behind text.
 * Keep its display, height, flex sizing, scrolling and mobile hiding unchanged.
 */
.repository .repo-view-file-tree-container {
  background: var(--nb-inner-sidebar);
  border: 1px solid var(--nb-inner-border);
  border-radius: 12px;
  box-shadow: var(--nb-panel-shadow);
}
.repository .repo-view-file-tree-container > .repo-button-row {
  background: var(--nb-inner-header);
  border-bottom: 1px solid var(--nb-inner-border);
  border-radius: 11px 11px 0 0;
  margin-top: 0;
  margin-bottom: 4px;
  padding: 10px 8px;
}
.repository #view-file-tree {
  background: var(--nb-inner-sidebar);
}
.repository #view-file-tree .tree-item:hover {
  background: var(--nb-inner-hover);
}
.repository #view-file-tree .tree-item.selected,
.repository #view-file-tree .tree-item.selected:hover {
  background: var(--nb-inner-selected);
  color: var(--color-text-dark);
  box-shadow: inset 2px 0 var(--color-primary);
}
.repository #view-file-tree .sub-items {
  border-color: var(--nb-inner-border);
}
#repo-files-table .repo-file-item:is(:hover, :focus-within) > .repo-file-cell,
#repo-files-table .parent-link:hover {
  background: color-mix(in srgb, var(--color-body) 88%, var(--color-primary) 12%);
}

/* Standalone file commit summary, also used above rendered documents. */
.repository #repo-file-commit-box {
  background: var(--nb-inner-panel);
  border-color: var(--nb-inner-border);
  border-radius: 12px;
  box-shadow: var(--nb-panel-shadow);
}

/* Rendered documents and README: opaque paper with a bounded reading measure.
 * Scope to markup, keeping source code, media, CSV and diff layouts separate.
 */
.repository .non-diff-file-content > .file-header {
  background: var(--nb-inner-header);
  border-color: var(--nb-inner-border);
  border-radius: 12px 12px 0 0;
}
.repository .non-diff-file-content > .file-view-container:has(> .file-view.markup:not(.csv)) {
  background: var(--nb-inner-reading);
  border-color: var(--nb-inner-border);
  border-radius: 0 0 12px 12px;
  box-shadow: var(--nb-panel-shadow);
}
.repository .non-diff-file-content > .file-view-container > .file-view.markup:not(.csv) {
  background: var(--nb-inner-reading);
  color: var(--color-text);
  box-sizing: border-box;
  max-width: 72rem;
  margin-inline: auto;
  line-height: 1.85 !important;
}
.repository .non-diff-file-content > .file-view-container > .file-view.markup:not(.csv) :is(img, video) {
  background-color: var(--nb-inner-reading);
}
.repository .non-diff-file-content > .file-view-container > .file-view.markup:not(.csv) th {
  background: var(--nb-inner-header);
  color: var(--color-text-dark);
}

@media (max-width: 767.98px) {
  .dashboard #activity-feed { padding-inline: 12px; }
  .repository .non-diff-file-content > .file-view-container > .file-view.markup:not(.csv):not(:has(.file-not-rendered-prompt)) {
    padding-inline: 18px;
  }
}
/* NEBULA_INNER_PAGES_2_1_2_END */"""
PATCHES = (
    ('顶栏', '/* NEBULA_NAVBAR_2_0_1_BEGIN */', '/* NEBULA_NAVBAR_2_0_1_END */', NAVBAR_PATCH),
    ('文件列表与几何背景', '/* NEBULA_GEOMETRY_2_1_0_BEGIN */', '/* NEBULA_GEOMETRY_2_1_0_END */', GEOMETRY_PATCH),
    ('几何漂移动效', '/* NEBULA_GEOMETRY_MOTION_2_1_1_BEGIN */', '/* NEBULA_GEOMETRY_MOTION_2_1_1_END */', MOTION_PATCH),
    ('内页配色与阅读', '/* NEBULA_INNER_PAGES_2_1_2_BEGIN */', '/* NEBULA_INNER_PAGES_2_1_2_END */', INNER_PAGES_PATCH),
)
META = re.compile(r'gitea-theme-meta-info\s*\{[^{}]*\}\s*\Z')


def prepare_text(text, mode, name):
    meta = META.search(text)
    if not meta or len(re.findall(r'gitea-theme-meta-info\s*\{', text)) != 1:
        raise RuntimeError(f'主题元数据位置不符，尚未写入：{name}')
    if not re.search(r'--theme-color-scheme:\s*"' + mode + r'"', meta.group()):
        raise RuntimeError(f'主题模式不符，尚未写入：{name}')
    if any(token not in text for token in ('--nb-cyan:', '#navbar', '#repo-files-table')):
        raise RuntimeError(f'不是预期的 Nebula 主题，尚未写入：{name}')
    pending = []
    for label, begin, end, patch in PATCHES:
        begin_count, end_count = text.count(begin), text.count(end)
        if begin_count or end_count:
            if begin_count != end_count or text.count(patch) != begin_count:
                raise RuntimeError(f'{label}补丁标记存在，但内容不完整或已被修改，尚未写入：{name}')
        else:
            pending.append(patch)
    if not pending:
        return None
    return text[:meta.start()].rstrip() + '\n\n' + '\n\n'.join(pending) + '\n\n' + meta.group()


def open_directory(path, create=False):
    """Open each path component without following symlinks."""
    fd = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            if create:
                try:
                    os.mkdir(part, mode=0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def file_identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_ctime_ns, info.st_mode, info.st_uid, info.st_gid)


def read_snapshot(directory, name):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise RuntimeError(f'不是普通主题文件，尚未写入：{name}')
        data = stream.read()
        after = os.fstat(stream.fileno())
        if file_identity(before) != file_identity(after):
            raise RuntimeError(f'读取期间文件发生变化，尚未写入：{name}')
        return data, after


def require_snapshot(directory, name, expected):
    current = read_snapshot(directory, name)
    if current[0] != expected[0] or file_identity(current[1]) != file_identity(expected[1]):
        raise RuntimeError(f'文件在检查后发生变化，尚未写入：{name}')


def atomic_write(directory, name, data, info, expected):
    temporary = '.nebula-theme-' + secrets.token_hex(12) + '.tmp'
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 mode=0o600, dir_fd=directory)
    try:
        with os.fdopen(fd, 'wb') as stream:
            if (os.geteuid(), os.getegid()) != (info.st_uid, info.st_gid):
                os.fchown(stream.fileno(), info.st_uid, info.st_gid)
            os.fchmod(stream.fileno(), stat.S_IMODE(info.st_mode))
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        require_snapshot(directory, name, expected)
        os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)
    finally:
        try:
            os.unlink(temporary, dir_fd=directory)
        except FileNotFoundError:
            pass


def write_backup(directory, name, data):
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 mode=0o600, dir_fd=directory)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def update(css_dir, backup_root):
    css_dir, backup_root = Path(css_dir).expanduser(), Path(backup_root).expanduser()
    for label, path in (('CSS', css_dir), ('Backup', backup_root)):
        if not path.is_absolute() or path.resolve() != path:
            raise RuntimeError(f'{label} directory must be an absolute path without symlinks: {path}')
    if backup_root == css_dir or css_dir in backup_root.parents:
        raise RuntimeError('Backups must be outside the CSS directory.')
    public_roots = [parent for parent in css_dir.parents if parent.name == 'public']
    if any(backup_root == public or public in backup_root.parents for public in public_roots):
        raise RuntimeError('Backups must be outside the public assets directory.')
    directory = open_directory(css_dir)
    try:
        try:
            fcntl.flock(directory, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('另一个主题更新正在运行，请等它完成后再试。') from None
        changes = []
        for mode in ('light', 'dark', 'auto'):
            name = f'theme-nebula-{mode}.css'
            original, info = read_snapshot(directory, name)
            updated = prepare_text(original.decode('utf-8'), mode, name)
            if updated is not None:
                changes.append((name, original, updated.encode('utf-8'), info))
        if not changes:
            print('三个主题都已包含 Nebula 2.1.2 视觉补丁，无需重复写入。浏览器按 Ctrl+F5 刷新即可。')
            return None
        root_fd = open_directory(backup_root, create=True)
        stamp = datetime.now().astimezone().strftime('%Y%m%d-%H%M%S')
        backup_name = f'nebula-theme-backup-{stamp}-' + secrets.token_hex(8)
        try:
            os.mkdir(backup_name, mode=0o700, dir_fd=root_fd)
            backup_fd = os.open(backup_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                dir_fd=root_fd)
        finally:
            os.close(root_fd)
        backup = backup_root / backup_name
        try:
            for name, original, _, info in changes:
                require_snapshot(directory, name, (original, info))
                write_backup(backup_fd, name, original)
            os.fsync(backup_fd)
        finally:
            os.close(backup_fd)
        attempted = []
        try:
            for name, original, updated, info in changes:
                attempted.append((name, original, updated, info))
                atomic_write(directory, name, updated, info, (original, info))
        except Exception as error:
            restore_failures = []
            for name, original, updated, info in reversed(attempted):
                try:
                    current = read_snapshot(directory, name)
                    if current[0] == original:
                        continue
                    if current[0] != updated:
                        raise RuntimeError('检测到其他修改，已保留当前内容，未覆盖')
                    atomic_write(directory, name, original, info, current)
                except Exception as restore_error:
                    restore_failures.append(f'{name}: {restore_error}')
            status = ('未能自动恢复：' + '; '.join(restore_failures)) if restore_failures else '本次已写入的文件已恢复原样。'
            raise RuntimeError(f'写入失败：{error}。{status} 原文件备份：{backup}') from error
        print(f'已更新 {len(changes)} 个主题；原文件备份：{backup}')
        print('现在回到 Gitea，按 Ctrl+F5 强制刷新。')
        return backup
    finally:
        os.close(directory)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--css-dir', type=Path, required=True,
                        help='Absolute path to the installed public/assets/css directory')
    parser.add_argument('--backup-dir', type=Path, required=True,
                        help='Absolute private backup directory, outside public assets')
    args = parser.parse_args()
    try:
        update(args.css_dir, args.backup_dir)
    except (OSError, UnicodeError, RuntimeError) as error:
        raise SystemExit(f'停止更新：{error}')
