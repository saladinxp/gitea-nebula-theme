# Nebula for Gitea

A soft blue-violet theme for Gitea, with light, dark, and system modes, subtle gradients, and floating geometric outlines.

**Version 2.1.2 · Target: Gitea 28.2.0 · CSS only**

[简体中文](README.zh-CN.md) · [Changelog](CHANGELOG.md) · [GitHub edition](https://github.com/saladinxp/github-nebula-theme)

![Nebula light document view](preview/nebula-gitea-document-light.png)

## Features

- Three installable themes: `nebula-light`, `nebula-dark`, and `nebula-auto`.
- Coordinated navigation, repository lists, settings, dashboard panels, and document surfaces.
- A solid background behind the file tree and reading panels keeps decorative motion away from text.
- Two CSS geometry layers, with slower mobile motion and support for the system's reduced-motion setting.
- Locally hosted Oxanium, Sora, and JetBrains Mono fonts. Other scripts use system font fallbacks.
- An offline preview with fictional data: download the repository and open `preview/nebula-preview.html`.

![Nebula dark document view](preview/nebula-gitea-document-dark.png)

## Compatibility

The theme targets the Gitea **28.2.0** UI. Other Gitea versions may use different markup and need adjustments. Use a current browser with CSS `color-mix()` and `:has()` support.

The production theme contains CSS and local font files. The preview's JavaScript and sample controls are only for the offline demo. Installing this theme does not change repositories, permissions, or database contents.

## Install

1. Find your instance's actual **CustomPath**, using Gitea's administration configuration page or `gitea help`. Command-line options and `GITEA_CUSTOM` can change it. With Docker, resolve the host directory corresponding to the container's CustomPath before copying files.
2. Back up any existing files with the same names to a directory outside publicly served assets.
3. Copy the files using the mapping below. Keep other themes and assets intact.

| Repository contents | Destination |
|---|---|
| `css/theme-nebula-light.css` | `{CustomPath}/public/assets/css/theme-nebula-light.css` |
| `css/theme-nebula-dark.css` | `{CustomPath}/public/assets/css/theme-nebula-dark.css` |
| `css/theme-nebula-auto.css` | `{CustomPath}/public/assets/css/theme-nebula-auto.css` |
| `fonts/nebula/` | `{CustomPath}/public/assets/fonts/nebula/` |

Gitea must be able to read the files. Typical static asset permissions are `755` for directories and `644` for files; use the ownership appropriate to your installation. The CSS refers to `../fonts/nebula/`, so copy the fonts as well.

4. If `[ui] THEMES` is explicitly restricted in `app.ini`, append `nebula-light,nebula-dark,nebula-auto` to the existing list. On the target version, an empty `THEMES` setting allows available themes. Preserve your other configuration and existing default theme.
5. Restart Gitea after first installation so it discovers the added themes. Choose Nebula in **Settings → Appearance**, then refresh the page.

Docker environment settings such as `GITEA__ui__THEMES` can override `app.ini`. Change the configuration source your deployment actually uses. If you edit Compose environment values, recreate the Gitea service to apply them.

Official references: [customizing Gitea](https://docs.gitea.com/administration/customizing-gitea/), [UI settings](https://docs.gitea.com/administration/config-cheat-sheet/#ui-ui), and [Docker configuration](https://docs.gitea.com/installation/install-with-docker/#managing-deployments-with-environment-variables).

## Update an existing Nebula installation

Download the current `update-nebula-theme.py`. It contains the visual patches for Nebula 2.0.x–2.1.2 and uses only Python's standard library. **Both paths must be supplied explicitly.** For example, after replacing these example paths with your own:

```bash
python3 update-nebula-theme.py \
  --css-dir /srv/gitea/custom/public/assets/css \
  --backup-dir /srv/backups/nebula
```

The updater checks all three existing theme files before writing, preserves their final Gitea metadata and file permissions, and creates an exact backup of changed files. Re-running it skips complete patches. Missing files, symlinks, or locally modified patch blocks cause it to stop instead of overwriting uncertain input. Backups must be outside public assets.

The updater changes CSS only; it does not install missing fonts, change `app.ini`, or restart services. After an update, use **Ctrl+F5** to refresh cached styles. For a fresh installation, use the full installation steps above.

To roll back, select your previous theme in Gitea, or restore the CSS files from the backup directory printed by the updater.

## Build and preview

Python **3.10+** is required for the build. No package installation is needed.

```bash
python3 build-theme.py
python3 build-theme.py --check
python3 package-theme.py
```

Edit `src/`, then rebuild. The builder verifies the bundled Gitea source checksums and generates all three stylesheets and the self-contained preview. The package command creates a ZIP and `SHA256SUMS` using an explicit public file manifest.

The offline demo is a visual preview, not a running Gitea server. Check the pages you use on your own instance after installation. Screenshots use fictional repositories and accounts.

## Motion

Desktop geometry cycles take 18 and 22 seconds; mobile cycles take 32 seconds. The grid and reading surfaces stay still. Your operating system's **Reduce motion** setting disables the geometry animation. The offline demo also has a motion toggle.

## Credits and licensing

Maintained by [saladinxp](https://github.com/saladinxp). This is a community theme and is not affiliated with Gitea.

Bundled Gitea reference CSS retains its MIT license, and the three bundled fonts retain their SIL Open Font License notices. These component licenses do not grant a blanket license for the Nebula-specific sources. See [LICENSING.md](LICENSING.md) for the current license status and component paths.
