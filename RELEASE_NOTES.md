Server theme for **Gitea 28.2.0**, with light, dark, and system modes. / 用于 **Gitea 28.2.0** 的服务器主题，提供浅色、深色和跟随系统模式。

- **[gitea-nebula-2.1.3.zip](https://github.com/saladinxp/gitea-nebula-theme/releases/download/v2.1.3/gitea-nebula-2.1.3.zip)** — complete ZIP with three CSS themes, local fonts, updater, source, previews, and licenses. / 完整包：三份主题 CSS、本地字体、更新器、源码、预览和许可证。
- **[Download updater / 下载更新脚本](https://github.com/saladinxp/gitea-nebula-theme/releases/download/v2.1.3/update-nebula-theme.py)**
- [English installation guide](https://github.com/saladinxp/gitea-nebula-theme/blob/v2.1.3/README.md#install) · [中文首次安装](https://github.com/saladinxp/gitea-nebula-theme/blob/v2.1.3/README.zh-CN.md#首次安装)
- [English update guide](https://github.com/saladinxp/gitea-nebula-theme/blob/v2.1.3/README.md#update-an-existing-nebula-installation) · [中文更新步骤](https://github.com/saladinxp/gitea-nebula-theme/blob/v2.1.3/README.zh-CN.md#更新已有-nebula)
- [SHA-256 checksums](https://github.com/saladinxp/gitea-nebula-theme/releases/download/v2.1.3/release-SHA256SUMS.txt) — the ZIP also contains per-file `SHA256SUMS`. / ZIP 内另附逐文件校验清单。

**First install / 首次安装：** extract the ZIP, copy CSS **and fonts** to the actual Gitea CustomPath, apply the theme configuration, then restart Gitea. / 解压后将 CSS 与字体部署到实际 CustomPath，配置主题名单并重启 Gitea。

**Update / 更新：** the updater supports existing Nebula 2.0.x–2.1.2 CSS and requires explicit `--css-dir` and `--backup-dir` arguments. It backs up changed files and skips complete patches. It does not install missing fonts or change server settings. / 已有版本可用脚本更新，必须指定 CSS 与备份目录；脚本备份原文件，只更新 CSS。完成后按 Ctrl+F5。

See [Changelog](https://github.com/saladinxp/gitea-nebula-theme/blob/v2.1.3/CHANGELOG.md) for the included features.

Packaging and release checks are hardened in this patch; the theme colors and layout are unchanged. / 本次修正打包与发布校验，配色和布局保持原样。
