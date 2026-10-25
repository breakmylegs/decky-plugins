# Decky plugins

Three Decky Loader plugins for handheld PCs. GPL-3.0.

| Plugin | What it does | Status |
|---|---|---|
| [qbittorrent-monitor](plugins/qbittorrent-monitor) | Monitor and control qBittorrent from the Quick Access Menu | Phase 1 build, on-device testing next |
| [sabnzbd-monitor](plugins/sabnzbd-monitor) | Monitor and control SABnzbd from the Quick Access Menu | Scaffold |
| [tuning-advisor](plugins/tuning-advisor) | Recommend game settings for your device and tuning tools. Never changes anything | Scaffold |

This monorepo is the source of truth. Each plugin is mirrored to its own repo, which hosts releases. Report issues here.

## Develop

Needs Python 3.10 or newer, Node 22 and pnpm 9.

```bash
python tools/vendor_shared.py
```

```bash
cd plugins/qbittorrent-monitor && pnpm install && pnpm test && pnpm build
```

```bash
python -m pytest -q shared/py/tests tools/tests plugins/qbittorrent-monitor/tests
```

```bash
python tools/package_zip.py qbittorrent-monitor && python -I tools/smoke_zip.py out/qbittorrent-monitor.zip --mock-qbt
```

Run a mock server for UI work:

```bash
python tools/mock_qbittorrent.py --port 8090 --api-key test-key-for-local-use-only
```

## Docs

- [Architecture](docs/ARCHITECTURE.md)
- [Verification register](docs/VERIFICATION.md)
- [Data sources](docs/DATA-SOURCES.md)
- [Privacy](docs/PRIVACY.md)
- [Build brief](CLAUDE.md)

## Release

Tag `<plugin-id>-v<version>` matching the plugin's `package.json`. The release workflow builds the zip, pushes the plugin to its mirror and attaches the zip to a mirror release. It needs the `MIRROR_TOKEN` repository secret.
