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

## Plugin 2: sabnzbd-monitor

| Module | Role |
|---|---|
| `sabmon/client.py` | API client. Every call is `GET /api?output=json&apikey=...&mode=...` |
| `sabmon/sync.py` | Queue and history cache, the projection, and completed and failed toasts |
| `sabmon/states.py` | Queue and history labels, priority names, string to number and time parsing |
| `sabmon/service.py` | Poll, actions, warnings and the connection test |

Each poll makes two calls: `queue` with `limit=8`, and `history` with `last_history_update`. When history has not changed SABnzbd answers `{"history": false}` and the cache stays.

SABnzbd reports a missing or wrong key as HTTP 403 with a plain-text body, and the body is empty when the server has `api_warnings` off. The client decides on the status code and uses the text only to choose a more specific message: NZB key used, host name not whitelisted, or access refused. "Configuration locked" is a JSON error with HTTP 200. The service remembers it, so the panel can explain why timed pause and the speed limit fail.

`PluginError` takes an optional `hint`, which replaces the standard message when a plugin knows exactly what went wrong. The poller re-reports status when the message changes, not only the kind.

## Plugin 3: tuning-advisor

Read only. It recommends and never applies. `tools/check_readonly.py` fails the gate if its source calls a Steam setter, injects into a tab or runs a process.

| Module | Role |
|---|---|
| `registry/devices.json` | One entry per device variant, with DMI match rules, specs, TDP range and bands, and Deck Verified name patterns |
| `registry/stacks.json` | One entry per tool, with detection rules, categories and the words to phrase advice in |
| `advisor/device.py` | Reads DMI, cpuinfo and the GPU vendor. The most specific matching entry wins. CPU text splits variants that share DMI strings |
| `advisor/stack.py` | Reads other plugins' `plugin.json` names, Decky's disabled list and some file paths. Picks one tool per category, manual choice first. Finds conflicts |
| `advisor/deckverified.py` | Fetches reports and normalises them into the section 8.6 model |
| `advisor/cache.py` | 7-day cache keyed by app and build. Stale entries serve when offline |
| `advisor/recommend.py` | Device match, ranking, validation, translation and the fallback |
| `advisor/service.py` | Ties it together. Recomputes when the game or settings change. There is no poller |

The frontend tracks games with `SteamClient.GameSessions.RegisterForAppLifetimeNotifications`, reads the name and build ID from `appStore` and `appDetailsStore`, and offers recent games from `collectionStore`. Non-Steam shortcuts are looked up by name and every result for them is low confidence.

Validation runs on every recommendation, including the fallback. TDP is clamped to the device range, refresh rates above the panel are dropped, and frame caps outside the VRR range, or that do not divide the refresh rate without VRR, are flagged. FSR 4 is removed wherever it appears, including the in-game settings list.

## Release

Nothing runs on GitHub. GitHub Actions is turned off for this repo, by the owner's decision, and there are no workflow files. Every check runs locally through `tools/gate.py`, and releases are made from the local machine with `gh`, which uses no Actions minutes.

`tools/release.py <plugin-id>` releases one plugin. It reads the owner from the monorepo's origin remote, refuses a dirty tree, unpushed commits or an existing mirror release, runs the gate, vendors with the mirror owner so `build_info.json` names the mirror, rebuilds, packages with the owner as author and smoke tests the zip. It then builds the mirror tree in a temp folder: the plugin folder, its vendored shared code and mocks, `LICENSE` and `.gitattributes`. That tree must install, build, typecheck and pass its tests with nothing skipped before it is pushed. The mirror is created on first release, public with issues off. The script tags the mirror `v<version>`, creates the mirror release with the zip, and tags the monorepo `<plugin-id>-v<version>`.

The zip root folder, the asset name and `plugin.json` name are all the plugin id. See `docs/VERIFICATION.md` item 4.

`tools/smoke_zip.py` loads the packaged zip the way Decky does, with a stand-in `decky` module, and exercises the backend against the mock server.

## Guards

All guards run in `tools/gate.py`, which stops at the first failure.

| Guard | Fails when |
|---|---|
| gitleaks | Any secret pattern in history or the working tree. A missing gitleaks fails the gate unless `--skip-secrets` is given |
| `tools/check_fixtures.py` | A fixture holds an IPv4 address outside loopback and the RFC 5737 ranges, or a key-shaped string |
| `tools/check_readonly.py` | tuning-advisor source calls a Steam setter, injects into a tab or runs a process. Refuses to pass on an empty tree |
| `tools/package_zip.py` | `plugin.json` name differs from the id, a root flag is set, or `"type": "module"` is missing |
