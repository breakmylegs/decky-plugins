# Decky plugins

Three Decky Loader plugins for handheld PCs. GPL-3.0.

| Plugin | What it does | Status |
|---|---|---|
| [qbittorrent-monitor](plugins/qbittorrent-monitor) | Monitor and control qBittorrent from the Quick Access Menu | Phase 1 build, on-device testing next |
| [sabnzbd-monitor](plugins/sabnzbd-monitor) | Monitor and control SABnzbd from the Quick Access Menu | Phase 1 build, on-device testing next |
| [tuning-advisor](plugins/tuning-advisor) | Recommend game settings for your device and tuning tools. Never changes anything | Phase 1 MVP, on-device testing next |

This monorepo is the source of truth. Each plugin is mirrored to its own repo, which hosts releases. Report issues here.

## Develop

Needs Python 3.10 or newer, Node 22 and pnpm 9.

Nothing runs on GitHub. Run the full gate locally before every push:

```bash
python tools/gate.py
```

It needs gitleaks on PATH or in `.tools/`.

```bash
python tools/vendor_shared.py
```

```bash
cd plugins/qbittorrent-monitor && pnpm install && pnpm test && pnpm build
```

```bash
python -m pytest -q shared/py/tests tools/tests plugins/*/tests
```

```bash
python tools/package_zip.py qbittorrent-monitor && python -I tools/smoke_zip.py out/qbittorrent-monitor.zip --mock-qbt
```

Run a mock server for UI work:

```bash
python tools/mock_qbittorrent.py --port 8090 --api-key test-key-for-local-use-only
```

```bash
python tools/mock_sabnzbd.py --port 8091 --api-key test-key-for-local-use-only
```

## Docs

- [Architecture](docs/ARCHITECTURE.md)
- [Verification register](docs/VERIFICATION.md)
- [Data sources](docs/DATA-SOURCES.md)
- [Privacy](docs/PRIVACY.md)
- [Build brief](CLAUDE.md)

## Release

Each plugin is released to its own public mirror repo, from this machine:

```bash
python tools/release.py qbittorrent-monitor --dry-run
```

```bash
python tools/release.py qbittorrent-monitor
```

It refuses a dirty tree, unpushed commits or a version the mirror already has. It runs the gate, builds with the mirror named in `build_info.json`, checks the mirror tree builds and passes its tests on its own, pushes it, attaches the zip to a mirror release and tags the monorepo `<plugin-id>-v<version>`. Bump `version` in the plugin's `package.json` first. The install URL is `https://github.com/<owner>/<plugin-id>/releases/latest/download/<plugin-id>.zip`.
