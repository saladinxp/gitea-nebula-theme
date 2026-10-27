# Changelog

## 2.1.3 — 2026-10-28

- Reject symlinked package inputs, checksum files, and archive outputs.
- Archive the same file snapshots used for checksums.
- Check release tag targets and pin the checkout action to a fixed commit.
- Lock the installed theme directory, back up checked bytes, and stop on concurrent file changes.
- Preserve external edits during rollback.
- Theme colors, layout, and animation are unchanged.

## 2.1.2 — Initial public release

This release includes the completed Nebula theme for Gitea 28.2.0:

- Light, dark, and system color modes with complete Gitea color variable baselines.
- Blue-violet gradients, geometric outlines, and coordinated navigation and repository panels.
- Readable settings and dashboard surfaces, a solid file tree background, and bounded document reading width.
- CSS-only geometry motion with reduced-motion support and slower mobile animation.
- Locally bundled fonts and a self-contained nine-page offline preview with fictional content.
- An existing-installation updater with explicit CSS and private backup paths, validation, backups, and idempotent patches.
- Reproducible builds, component source checksums, and an explicit distribution manifest.
