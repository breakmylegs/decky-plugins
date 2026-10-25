# Architecture

Three Decky Loader plugins in one monorepo. Each plugin builds on its own. Shared code is copied into each plugin at build time, so a mirror repo builds without this one.

## Layout

| Path | What it holds |
|---|---|
| `shared/py/plugin_core/` | Backend code shared by every plugin |
| `shared/ts/` | Frontend components and helpers shared by every plugin |
| `plugins/<id>/` | One plugin: `main.py`, `py_modules/`, `src/`, `package.json`, lockfile, tests |
| `tools/` | Vendoring, packaging, mocks, fixture tools, guards |
| `docs/` | This file, verification register, data sources, privacy |

`tools/vendor_shared.py` copies `shared/py/plugin_core` into `plugins/<id>/py_modules/plugin_core` and `shared/ts` into `plugins/<id>/src/shared`. The copies are gitignored here and committed in the mirrors. It also writes `build_info.json`, which names the mirror repo and asset for the update check. The mirror owner comes from `--owner`, `MIRROR_OWNER` or `GITHUB_REPOSITORY_OWNER`. No owner name appears in source.

## Backend

Decky runs each plugin backend in its own process (`multiprocessing.Process` in `decky_loader/plugin/plugin.py`). It appends the plugin's `py_modules` to `sys.path`. Appended, not prepended, so a module named like a standard library module loses to the standard library. That is why the shared package is `plugin_core` and plugin packages are `qbtmon`, `sabmon` and `advisor`, and why `plugin_core/http.py` can only be imported as `plugin_core.http`.

`main.py` is a thin adapter. It builds a service object with Decky's directories, `decky.emit` and `decky.logger`, then forwards each callable. All logic lives in importable modules so pytest can run it without a loader.

### plugin_core

| Module | Role |
|---|---|
| `http.py` | urllib client. Base URL parsing, timeouts, JSON, form encoding, cookie jar, TLS options, proxy bypass. Returns any HTTP status as a `Response` and raises only when no reply arrived |
| `errors.py` | Nine failure kinds, one plain-language message each. `classify()` maps any exception to a kind |
| `settings.py` | JSON store with typed defaults. Atomic write then `chmod 600` |
| `secrets.py` | Secret store. The frontend sees `set` and a masked suffix only. Import from `~/Documents/decky-import/<id>.json` |
| `poller.py` | Poll loop. 2 s while the panel is visible, 60 s otherwise, backoff from 5 s to 5 min on failure. Offline after 3 unreachable failures, reported once |
| `conntest.py` | Step report for the connection test: address, port, server, sign-in |
| `update_check.py` | Daily check of the mirror's latest release |
| `service.py` | `MonitorService`, the shared wiring for the two download-client plugins |

Every blocking call runs through `asyncio.to_thread`. The Decky event loop never waits on the network.

### Poll interval

The brief lists 2 s visible, 60 s hidden and 60 s in game. When the panel is open during a game the user is looking at it, so visible wins and the interval is 2 s. When the panel closes it drops to 60 s.

### Events

Backends push state with `decky.emit`:

| Event | Payload |
|---|---|
| `status` | `{state, error, last_success}`. Sent only when the state or error kind changes |
| `data` | The plugin's compact projection |
| `notify` | `{kind, key, title, body}`. The frontend toasts it |
| `update` | `{current, latest, available, install_url}` |

## Frontend

Built from `@decky/ui` components only, so every control is reachable by controller. The QAM panel is the primary UI. HTTP never runs in the frontend. Every call goes through a backend callable.

The plugin's `definePlugin` registers the `notify` listener and the game-running watcher for the whole session, so toasts arrive with the panel closed. The panel reports visibility with `useQuickAccessVisible` from `@decky/api`.

Game running state comes from `SteamClient.GameSessions.RegisterForAppLifetimeNotifications`, seeded from `Router.MainRunningApp`. See `shared/ts/gameState.ts`.

## Plugin 1: qbittorrent-monitor

| Module | Role |
|---|---|
| `qbtmon/client.py` | WebUI API v2 client. API key, cookie login, whitelist. Start and stop verbs gated on WebAPI 2.11.0 |
| `qbtmon/sync.py` | `sync/maindata` cache with incremental merge, the top 8 projection and completion and error transitions |
| `qbtmon/states.py` | State labels |
| `qbtmon/service.py` | Poll, actions and the connection test |

qBittorrent has no unauthenticated version endpoint. The connection test calls `app/version` without credentials first: 200 means the server skips auth for this device, 403 means it is reachable and wants credentials, 404 means the address is wrong. Then it signs in. If a stored API key is rejected, it retries without the key to tell a rejected key from a whitelist that works.

## Release

`release.yml` runs on a tag such as `qbittorrent-monitor-v0.1.0`. It checks the tag matches `package.json`, vendors, tests, builds, packages, smoke tests the zip, pushes the plugin folder to the mirror and creates a mirror release with the zip attached.

The zip root folder, the asset name and `plugin.json` name are all the plugin id. See `docs/VERIFICATION.md` item 4.

`tools/smoke_zip.py` loads the packaged zip the way Decky does, with a stand-in `decky` module, and exercises the backend against the mock server.

## Guards

| Guard | Fails when |
|---|---|
| gitleaks | Any secret pattern in history or the working tree |
| `tools/check_fixtures.py` | A fixture holds an IPv4 address outside loopback and the RFC 5737 ranges, or a key-shaped string |
| `tools/check_readonly.py` | tuning-advisor source calls a Steam setter, injects into a tab or runs a process. Refuses to pass on an empty tree |
| `tools/package_zip.py` | `plugin.json` name differs from the id, a root flag is set, or `"type": "module"` is missing |
