# CLAUDE.md

Build brief for three public Decky Loader plugins. Read this file in full before writing code.

## 0. Working rules

- Decisions in section 2 are locked. Ask the owner before changing any of them.
- Items tagged **[VERIFY]** are unconfirmed. Confirm each against the named source before coding against it. Record the result, source URL and date in `docs/VERIFICATION.md`.
- Use the GitHub account and remotes already configured in this environment. Do not hardcode owner names in code. Read them from build config.
- Never commit secrets, hostnames, IP addresses, torrent names or NZB names. This repo is public.
- Follow the documentation style rules in section 13 for all READMEs, docs, code comments and UI copy.

## 1. Context

**Goal.** Three independent Decky Loader plugins, published publicly under GPL-3.0, usable on any Decky-capable handheld.

| Working name | Purpose |
|---|---|
| `qbittorrent-monitor` | Monitor and control a qBittorrent instance from the Quick Access Menu (QAM) |
| `sabnzbd-monitor` | Monitor and control a SABnzbd instance from the QAM |
| `tuning-advisor` | Detect the running game, device and installed tuning stack, then recommend settings. Never writes settings |

- Confirm final names are free in the Decky store and on GitHub before first release. `decky-game-settings` is taken by DeckSettings and must not be used.
- Owner reference device is a Lenovo Legion Go 2, Ryzen Z2 Extreme, 32 GB, running SteamOS.
- Owner's download clients run on a separate machine on a 192.168.x.x LAN, reached by local IP or FQDN over HTTP. Other users may run them on localhost.

## 2. Locked decisions

| Area | Decision |
|---|---|
| Distribution | Public. Monorepo is the source of truth. CI mirrors each plugin to its own public repo, which hosts releases and later the store submodule |
| Licence | GPL-3.0 for all three plugins |
| Install path (phase 1) | Decky Developer Mode, Install Plugin from URL, pointing at the mirror's `releases/latest/download/<asset>.zip` |
| Store | Submit to the Decky Plugin Store in phase 2 |
| Devices | All Decky-capable handhelds. Device registry with community PRs and a generic fallback |
| Connectivity | Localhost, LAN IP and FQDN, over HTTP or HTTPS. Warn on localhost port 8080 |
| Remote access | Out of scope for now. No Tailscale or fallback URL features |
| qBittorrent auth | API key, username and password, or none (server-side IP whitelist). Send the API key whenever one is configured |
| SABnzbd auth | API key |
| Root | No plugin uses the `root` flag |
| HTTP | All network calls from the Python backend using the standard library. No frontend fetch |
| Plugin 3 writes | None. Plugin 3 never writes to Steam, other plugins, system services or game files |
| Plugin 3 launch options and Proton | Recommend only (phase 2). Show the exact value and where to set it. Never apply |
| Plugin 3 tuning stack | Auto-detect installed tools, allow manual override, tailor recommendations to the selected stack |
| AI | Optional, phase 2. User configures an OpenAI, Anthropic or Google Gemini API key. Backend calls the provider directly. Button-triggered only. Output is display-only |
| AI proxy | Not built |

## 3. Platform baseline

**Versions (October 2026)**
- Decky Loader v3.3.0 (18 October 2026).
- `@decky/api` 1.1.3. `@decky/ui` 4.16.0 **[VERIFY]** with `npm view`. `@decky/rollup` 1.0.2 **[VERIFY]**.
- Node.js 16.14 or newer and pnpm 9, as required by the official template.
- Start from `SteamDeckHomebrew/decky-plugin-template`.

**Mandatory settings**
- `package.json` must include `"type": "module"`. Without it Decky loads the bundle as an IIFE and fails.
- Remove `_root` from `plugin.json` flags. Set `api_version` to 1.
- Do not use `fetchNoCors`. Loader issue #974 reports it can hang. All HTTP goes through the backend.

**Backend model**
- `main.py` defines `class Plugin`. Public async methods are callable from the frontend via `callable()`.
- `_main()` starts the poll task. `_unload()` cancels it. `_uninstall()` removes stored data only if the user opted in.
- Push state to the frontend with `await decky.emit(event, payload)`.
- Wrap every blocking `urllib` call in `asyncio.to_thread`. Never block the shared Decky event loop.
- Use `decky.DECKY_PLUGIN_SETTINGS_DIR` for settings and secrets, `decky.DECKY_PLUGIN_RUNTIME_DIR` for caches, `decky.logger` for logs.
- Do not write outside the plugin's own settings and runtime directories.
- **[VERIFY]** that each plugin backend runs in its own interpreter, so vendored modules with the same name cannot collide. If not, namespace vendored modules per plugin.

**Frontend model**
- Build UI only from `@decky/ui` primitives (`PanelSection`, `PanelSectionRow`, `ButtonItem`, `ToggleField`, `SliderField`, `DropdownItem`, `TextField`, `ProgressBarWithInfo`, `Focusable`). These handle gamepad focus. Click handlers on plain elements are not controller reachable.
- Use the QAM panel for primary UI. Add full-screen routes via `routerHook` only for long lists. Remove routes on dismount.
- **[VERIFY]** exact exports and signatures in `SteamDeckHomebrew/loader-api` `src/index.ts`, including `callable`, `addEventListener`, `removeEventListener`, `toaster`, `definePlugin`, `routerHook` and any QAM visibility hook.

**Release artefact layout**
```
<asset>.zip
  <plugin-dir>/
    dist/index.js
    package.json
    plugin.json
    main.py
    py_modules/
    LICENSE
    README.md
```
- Decky Install from URL reportedly derives the plugin name from the URL, and installs hang when it differs from the zip contents. **[VERIFY]** the naming rule in the decky-loader install code, then align `plugin.json` name, zip root folder and asset filename to it.

## 4. Repository and release

**Monorepo layout**
```
/
  CLAUDE.md
  LICENSE
  README.md
  .gitleaks.toml
  .pre-commit-config.yaml
  .github/workflows/ci.yml
  .github/workflows/release.yml
  docs/
    VERIFICATION.md
    ARCHITECTURE.md
    DATA-SOURCES.md
    PRIVACY.md
  shared/
    py/plugin_core/        http.py, errors.py, settings.py, secrets.py, poller.py, update_check.py
    ts/                    ConnectionForm.tsx, StatusHeader.tsx, OfflineBanner.tsx, UpdateBadge.tsx,
                           useBackendEvent.ts, format.ts, toastOnce.ts
  plugins/
    qbittorrent-monitor/   standalone plugin with its own package.json and lockfile
    sabnzbd-monitor/
    tuning-advisor/
      registry/devices.json
      registry/stacks.json
  tools/
    vendor_shared.py       copies shared/py into plugins/*/py_modules and shared/ts into plugins/*/src/shared
    package_zip.py
    mock_qbittorrent.py
    mock_sabnzbd.py
    capture_fixture.py
    sanitise_fixture.py
    capture_device.sh
```

**Rules**
- Each plugin has its own `package.json` and lockfile and builds standalone. No pnpm workspace links, because mirrors must build without the monorepo.
- Shared code is vendored into each plugin by `tools/vendor_shared.py`. Vendored copies are gitignored in the monorepo and committed in mirrors.

**Release flow**
- Tag format per plugin, for example `qbittorrent-monitor-v0.1.0`.
- `release.yml` on tag: vendor shared code, run tests, build, package the zip, push the plugin directory to its mirror repo, create a release on the mirror with the zip attached.
- Mirror push uses a token stored as a repository secret. Never echo it in logs.
- Disable issues on mirrors. Mirror README links to the monorepo for issues.
- Install URL format is `https://github.com/<owner>/<mirror>/releases/latest/download/<asset>.zip`.

**Update notice**
- Each plugin checks `GET https://api.github.com/repos/<owner>/<mirror>/releases/latest` at most once per day, compares with its own version, and shows an update badge with the install URL. User can disable it.
- **[VERIFY]** loader PR #992 (new plugin update API in v3.3.0) and store policy on update checks before phase 2.

**Store submission (phase 2)**
- PR to `SteamDeckHomebrew/decky-plugin-database` adding each mirror as a git submodule, following the PR template checklist, including testing on SteamOS Stable and Beta.
- **[VERIFY]** that the store builds from the submodule root and that the mirror layout satisfies it.
- Submit plugins 1 and 2 first. Submit plugin 3 once phase 2 features are stable.

## 5. Shared core

**`plugin_core/http.py`**
- `urllib.request` wrapper with per-request timeout (default 5 s), JSON decode, form encode, optional cookie jar (`http.cookiejar.CookieJar`) and custom headers.
- TLS context built per configured connection. System CA store by default. Optional custom CA file path. Explicit "allow insecure" toggle that disables verification, shown with a warning.
- Accept base URLs of the form `http(s)://host[:port][/path-prefix]`. Host may be `localhost`, `127.0.0.1`, a LAN IP or an FQDN.

**`plugin_core/errors.py`**
- Classify every failure as `offline`, `dns`, `refused`, `timeout`, `tls`, `auth`, `forbidden`, `http_error` or `bad_response`. The UI shows one plain-language line per class.

**`plugin_core/settings.py` and `secrets.py`**
- `settings.json` holds non-secret config. `secrets.json` holds keys and passwords.
- Atomic write (temp file then `os.replace`), then `os.chmod(path, 0o600)` on both.
- The frontend never receives secret values. It receives flags such as `has_api_key` and a masked suffix.
- Secrets never appear in logs, error messages or emitted events.
- **Import from file.** A button reads `~/Documents/decky-import/<plugin-id>.json`, validates it, stores the values in `secrets.json`, then prompts the user to delete the import file. This avoids typing long keys on an on-screen keyboard.

**`plugin_core/poller.py`**
- Interval policy is 2 s when the QAM panel is visible, 60 s when hidden, 60 s while a game runs. The frontend reports visibility to the backend via a callable.
- Exponential backoff on failure, from 5 s to 5 min.
- After 3 consecutive `offline`, `dns`, `refused` or `timeout` failures, enter offline state. Emit one offline event, then stay quiet. No error toasts while offline.

**Connection test**
1. Validate URL format.
2. If the host is `localhost` or `127.0.0.1` and the port is 8080, warn. Decky needs port 8080 free, and both qBittorrent and SABnzbd default to it. Suggest another port such as 8090.
3. Call the unauthenticated version endpoint.
4. Call an authenticated endpoint.
5. Report which step failed, or which auth path succeeded.

## 6. Plugin 1: qbittorrent-monitor

**Server baseline**
- qBittorrent 5.2.0 (3 May 2026) is the latest confirmed release. Reference docs are the qBittorrent wiki pages "WebUI API (qBittorrent 5.0)" and "API Key Authentication (>=v5.2.0)".
- The wiki is stale on pause and resume. v5 uses `torrents/start` and `torrents/stop`.
- Support qBittorrent 4.6 or newer on a best-effort basis by accepting legacy `pausedDL` and `pausedUP` states. Feature-gate on `app/webapiVersion`.

**Auth modes**

| Mode | Mechanism |
|---|---|
| API key (preferred, 5.2.0+) | `Authorization: Bearer <key>` on every request. Stateless. The key cannot call `auth/login` |
| Username and password | `POST /api/v2/auth/login` with form fields `username` and `password`. Set `Referer` to the base URL. Store cookies in a `CookieJar` and replay them. Do not hardcode the cookie name `SID`, because 5.2.0 appends the port. Re-login once on 403, then fail |
| None | No credentials. Works when the server whitelists the handheld's IP. Document that a single-address whitelist with a DHCP reservation is safer than whitelisting the whole subnet |

- **[VERIFY]** behaviour when a whitelisted client sends an invalid API key. The connection test must report the path that worked.
- Use GET for reads and POST for mutations. qBittorrent returns 405 on the wrong method.

**Endpoints** (base path `/api/v2/`)

| Purpose | Call |
|---|---|
| Version gate | GET `app/version`, `app/webapiVersion` |
| Incremental state (primary poll) | GET `sync/maindata` with `rid` |
| Global speeds | GET `transfer/info` |
| Alt speed state and toggle | GET `transfer/speedLimitsMode`, POST `transfer/toggleSpeedLimitsMode` |
| Start and stop | POST `torrents/start`, `torrents/stop` with pipe-separated `hashes` or `all` |
| Recheck | POST `torrents/recheck` |
| Delete | POST `torrents/delete` with `hashes` and `deleteFiles` true or false |
| Categories and tags | GET `torrents/categories`, `torrents/tags` |

**`sync/maindata` algorithm**
1. Start with `rid=0`.
2. If `full_update` is true, replace cached state. Otherwise deep-merge each partial torrent object by hash and remove hashes in `torrents_removed`.
3. Store the returned `rid`.
4. Treat HTTP 204 as no change (5.2.0+).
5. Emit a compact projection (top 8 torrents by activity plus server state), not the full cache.
- **[VERIFY]** every field name against fixtures captured from a real 5.2 instance on day one.

**State mapping**

| `state` values | Label |
|---|---|
| `downloading`, `forcedDL` | Downloading |
| `metaDL`, `forcedMetaDL` | Fetching metadata |
| `stalledDL` | Stalled |
| `queuedDL`, `queuedUP` | Queued |
| `stoppedDL`, `pausedDL` | Stopped |
| `stoppedUP`, `pausedUP` | Completed |
| `uploading`, `forcedUP`, `stalledUP` | Seeding |
| `checkingDL`, `checkingUP`, `checkingResumeData` | Checking |
| `allocating`, `moving` | Working |
| `error`, `missingFiles` | Error |
| anything else | Unknown |

- An ETA of 8640000 means infinite. Show "No ETA".

**QAM UI**
- Header with connection status, download and upload speed, and alt-speed toggle.
- Torrent list, top 8, active first. Each row shows name, progress bar with percentage and ETA, speed and state label.
- Row press opens actions for Start or Stop, Recheck and Delete. Delete requires confirmation and a separate "delete files" toggle.
- Global Start all and Stop all actions.
- Settings section with base URL, auth mode, masked credentials, import from file, TLS options, notification toggle and connection test.
- Offline banner and update badge from shared components.

**Notifications**
- Toast once per torrent on transition from downloading into Completed or Seeding, and on transition into Error.
- Suppress toasts on the first poll after startup.
- User toggle to disable toasts while a game is running.

**Later**
- Full-screen list with category and tag filters. Global speed limit sliders. Add magnet link.

## 7. Plugin 2: sabnzbd-monitor

**Server baseline**
- SABnzbd 5.0.x is current. The official wiki carries a 5.1 API reference at `sabnzbd.org/wiki/configuration/5.1/api`.
- From 5.0.1, `nzo_id` values are GUIDs. Treat all IDs as opaque strings.

**Auth**
- All calls use `GET <base>/api?output=json&apikey=<key>&mode=<mode>`.
- `mode=version` needs no key. Use it for connection test step 3.
- Map these error strings: `API Key Required`, `API Key Incorrect`, `Configuration locked`.
- The NZB key cannot read the queue. Require the full API key and say so in the settings UI.
- Document `host_whitelist` for users who connect by FQDN.

**Endpoints**

| Purpose | Call |
|---|---|
| Queue | `mode=queue&start=0&limit=8` |
| History (incremental) | `mode=history&limit=10&last_history_update=N` |
| Global pause and resume | `mode=pause`, `mode=resume` |
| Timed pause | `mode=config&name=set_pause&value=<minutes>` |
| Job pause and resume | `mode=queue&name=pause&value=<nzo_id>`, `name=resume` |
| Delete | `mode=queue&name=delete&value=<id1,id2>`, optional `del_files=1` |
| Priority | `mode=queue&name=priority&value=<nzo_id>&value2=<p>` with p in -1, 0, 1, 2 |
| Speed limit | `mode=config&name=speedlimit&value=<percent, 400K or 5M>` |
| Warnings | `mode=warnings` **[VERIFY]** fields |

- Queue root fields used are `status`, `paused`, `speed`, `kbpersec`, `timeleft`, `mbleft`, `sizeleft`, `noofslots_total`, `speedlimit`, `have_warnings` and `pause_int`.
- Queue slot fields used are `nzo_id`, `filename`, `status`, `percentage`, `timeleft`, `sizeleft`, `priority` and `cat`.
- History slot fields used are `nzo_id`, `name`, `status`, `fail_message`, `size`, `completed`, `loaded` and `action_line`.
- Numeric values often arrive as strings. Coerce defensively.

**Status mapping**

| Source | `status` | Label |
|---|---|---|
| Queue | `Downloading` | Downloading |
| Queue | `Queued` | Queued |
| Queue | `Paused` | Paused |
| Queue | `Propagating` | Waiting for propagation |
| Queue or history | `Fetching` | Fetching extra par2 |
| History | `Queued` | Waiting for post-processing |
| History | `QuickCheck`, `Verifying` | Verifying |
| History | `Repairing` | Repairing |
| History | `Extracting` | Extracting |
| History | `Moving` | Moving |
| History | `Running` | Running script |
| History | `Completed` | Completed |
| History | `Failed` | Failed, with `fail_message` |

**QAM UI**
- Header with status, speed, time left, size left, global pause and resume, timed pause (15, 30, 60 minutes) and a speed limit dropdown (25, 50, 75, 100 percent).
- "Post-processing" group from history items with `loaded: true`, showing the current stage.
- Queue list, top 8, with name, percentage, time left, status and priority. Row actions for pause or resume, priority, and delete with confirmation.
- Last 5 completed or failed history items.
- Warnings badge when `have_warnings` is non-zero.
- Show "Configuration locked" when config calls fail for that reason.

**Notifications**
- Toast on transition to Completed and to Failed, including `fail_message`. Same suppression rules as plugin 1.

**Later**
- Full history route, retry failed jobs, server stats.

## 8. Plugin 3: tuning-advisor

### 8.1 Read-only constraint
- Plugin 3 never calls a Steam client setter, never writes another plugin's files, never calls another tool's write API and never edits game or Proton prefix files.
- Reading other plugins' `plugin.json` and settings files is allowed. Writing is not.
- **CI guard.** Fail the build if plugin 3 source contains `SetAppLaunchOptions`, `SpecifyCompatTool`, `UpdateSettings` or any `SteamClient.*.Set*` call. Extend the deny list as new setters are found.

### 8.2 Running game detection
- Primary method is `SteamClient.GameSessions.RegisterForAppLifetimeNotifications` (fields `unAppID`, `bRunning`). Unregister on dismount. **[VERIFY]**
- Fallback is reading `Router.MainRunningApp` when the panel opens. **[VERIFY]**
- When no game is running, let the user pick a recently played game.
- Non-Steam shortcuts have large synthetic app IDs. Match them by display name and mark results low confidence.
- Capture the game build ID for cache keys if the client exposes it. **[VERIFY]** Otherwise use a 7-day TTL.

### 8.3 Device registry
`registry/devices.json` holds one entry per device variant. Community PRs are welcome.

```json
{
  "id": "lenovo-legion-go-2-z2e",
  "vendor": "Lenovo",
  "model": "Legion Go 2",
  "family": "legion-go",
  "match": {
    "dmi_sys_vendor": ["LENOVO"],
    "dmi_product_name": [],
    "dmi_product_version": [],
    "dmi_board_name": []
  },
  "apu": "AMD Ryzen Z2 Extreme",
  "cpu": "8C/16T, 3x Zen 5 and 5x Zen 5c",
  "gpu": { "vendor": "amd", "name": "Radeon 890M", "arch": "RDNA 3.5", "cu": 16 },
  "ram_gb": [32],
  "display": { "width": 1920, "height": 1200, "panel": "OLED", "refresh_hz_max": 144, "vrr": true, "vrr_range_hz": [30, 144] },
  "battery_wh": 74,
  "tdp_w": { "min": 8, "max": 35 },
  "tdp_bands_w": { "light": 8, "medium": 16, "heavy": 20, "max": 30 },
  "steam_native_tdp": null,
  "report_aliases": [],
  "sources": [],
  "verified": false
}
```

**Detection**
- Read `/sys/class/dmi/id/` files `sys_vendor`, `product_name`, `product_version`, `product_family`, `board_name` and `board_vendor`. Match the most specific entry. Lenovo is reported to store the model name in `product_version`. **[VERIFY]**
- Source match strings from Handheld Daemon (`hhd-dev/hhd`) and InputPlumber device definitions, which maintain DMI lists for most handhelds. Credit them in `sources`.
- `tools/capture_device.sh` dumps the DMI files, `/proc/cpuinfo` model name, GPU details from `/sys/class/drm` and `lspci`, and `/etc/os-release`. Contributors attach the output to device PRs. Capture the owner's Legion Go 2 first and commit the sanitised dump as a test fixture.
- Unknown devices fall back to a generic profile built from CPU model, GPU vendor and CU count where readable. Show "Generic profile" and invite a device PR.
- The user can override the detected device in settings.

**TDP bands**
- Use the manufacturer's published power modes where available, for example Lenovo Quiet 8 W, Balanced 16 W and Performance 20 W on the Legion Go 2.
- Where no published modes exist, derive bands at 25, 50, 70 and 90 percent of the device TDP range and mark them derived.

**Seed entries**
Verify every field against the manufacturer spec page and record the URL in `sources`. Only the Legion Go 2 Z2 Extreme values were verified during research.

| id | APU and GPU | Display | Battery | Notes |
|---|---|---|---|---|
| `valve-steam-deck-lcd` | Aerith, Zen 2 4C, RDNA 2 8 CU | 7.0" 1280x800 LCD 60 Hz | 40 Wh | DMI product name `Jupiter`. Native TDP limit up to 15 W |
| `valve-steam-deck-oled` | Sephiroth, Zen 2 4C, RDNA 2 8 CU | 7.4" 1280x800 HDR OLED 90 Hz | 50 Wh | DMI product name `Galileo`. Native TDP limit up to 15 W |
| `asus-rog-ally` | Z1 Extreme (RDNA 3, 12 CU) or Z1 (4 CU) | 7" 1920x1080 IPS 120 Hz VRR | 40 Wh | |
| `asus-rog-ally-x` | Z1 Extreme, RDNA 3 12 CU | 7" 1920x1080 IPS 120 Hz VRR | 80 Wh | 24 GB |
| `asus-rog-xbox-ally` | Z2 A, RDNA 2 8 CU | 7" 1920x1080 IPS 120 Hz VRR | 60 Wh | |
| `asus-rog-xbox-ally-x` | Z2 Extreme, RDNA 3.5 16 CU | 7" 1920x1080 IPS 120 Hz VRR | 80 Wh | 24 GB |
| `lenovo-legion-go` | Z1 Extreme, RDNA 3 12 CU | 8.8" 2560x1600 IPS 144 Hz | 49.2 Wh | |
| `lenovo-legion-go-s` | Z2 Go or Z1 Extreme | 8" 1920x1200 IPS 120 Hz VRR | 55.5 Wh | Official SteamOS SKU exists |
| `lenovo-legion-go-2-z2` | Z2, RDNA 3 12 CU | 8.8" 1920x1200 OLED 144 Hz VRR | 74 Wh | 16 GB |
| `lenovo-legion-go-2-z2e` | Z2 Extreme, RDNA 3.5 16 CU | 8.8" 1920x1200 OLED 144 Hz VRR | 74 Wh | Verified. TDP 8 to 35 W sustained |
| `msi-claw-a8` | Z2 Extreme, RDNA 3.5 16 CU | 8" 1920x1200 IPS 120 Hz VRR | 80 Wh | |
| `msi-claw-intel` | Intel Core Ultra with Arc graphics | 7" or 8" | Varies | Intel path. XeSS, not FSR 4. Different TDP tooling |

Tier 2 devices (Zotac Zone, GPD, AYANEO, OneXPlayer and others) start on the generic profile until a contributor submits an entry.

### 8.4 Stack registry
`registry/stacks.json` holds one entry per tool, with `id`, `name`, `categories`, `repo`, `detect` rules, supported `devices`, `controls` exposed, `vocabulary` for phrasing recommendations, and `notes`. A tool can belong to more than one category.

| Category | id | Tool | Detection **[VERIFY all]** |
|---|---|---|---|
| power | `steam-native` | Steam QAM performance TDP limit | Device `steam_native_tdp` flag plus OS |
| power | `simpledeckytdp` | SimpleDeckyTDP (aarron-lee) | Decky plugin name |
| power | `powercontrol` | PowerControl (mengmeet) | Decky plugin name |
| power | `powertools` | PowerTools (NGnius) | Decky plugin name |
| power | `legotdp` | LeGoTDP (Rayekkk) | Decky plugin name |
| power, fan, input | `legiongo2companion` | LegionGo2Companion (Rayekkk) | Decky plugin name |
| power, fan, input | `hhd` | Handheld Daemon | systemd unit or local API |
| power | `powerstation` | PowerStation (ShadowBlip) | DBus service name |
| framegen | `lsfg-vk` | decky-lsfg-vk, requires the paid Lossless Scaling app | Decky plugin name and `~/lsfg` presence |
| framegen, upscaler | `optiscaler` | Decky-Framegen or decky-optiscaler | Decky plugin name |
| fan | `fantastic` | Fantastic (Steam Deck fan curves) | Decky plugin name |
| os | `steamos`, `bazzite`, `chimeraos`, `cachyos-handheld`, `other` | Operating system | `/etc/os-release` |

**Detection rules**
- Enumerate `<DECKY_HOME>/plugins/*/plugin.json` and match the `name` field against registry aliases. Folder names are not reliable.
- Exclude plugins Decky has disabled. **[VERIFY]** where Decky stores the disabled list.
- Show detected results pre-selected in settings. The user can change any category. Manual selection always wins.

**Conflict rules**
- More than one active power manager. Show a warning naming both and explaining they will override each other.
- LeGoTDP re-applies its values every 5 s. Warn that Steam native TDP changes will be reverted while it runs.
- No power manager on a device without native TDP. Suggest compatible tools from the registry.

**Vocabulary**
- Each entry defines how to phrase power recommendations, for example "Set TDP limit to 15 W in Steam Performance" for `steam-native`, or "Select the nearest preset (N W) in LeGoTDP".
- **[VERIFY]** each tool's UI labels and preset values from its README and source.

**Read-only current values (phase 2)**
- Where a tool's settings file format is documented or stable, read its per-game profile and show current against recommended. Skip silently when the format is unknown.

### 8.5 Data sources

| Source | Access | Licence | Use |
|---|---|---|---|
| Deck Verified (DeckSettings) | `GET https://deckverified.games/deck-verified/api/v1/game_details?appid=<id>` **[VERIFY]** response shape | GPL-3.0 reported **[VERIFY]** | Primary, phase 1. Reports are tagged by device. Live call with local cache and attribution |
| ProtonDB | Monthly ODbL dumps at `bdefore/protondb-data` | ODbL, share-alike | Phase 2. CI builds a per-appid index published as a release asset. The plugin downloads it on demand |
| PCGamingWiki | Cargo API. Bot password login required since August 2026. Tables renamed 30 August 2026. 60 requests per minute | CC BY-NC-SA | Phase 2, optional. User supplies bot credentials. Used for config file locations and upscaler support |
| SteamDeckHQ, ShareDeck | No public API, no reuse licence | None | Link out only. Never scrape or cache |

- Credit every source on screen next to its data and in `docs/DATA-SOURCES.md`.

### 8.6 Normalised recommendation model
All sources, fallback rules and AI output map into one schema, rendered by one UI path.

```json
{
  "source": "deckverified | protondb | pcgw | fallback | ai",
  "source_url": "",
  "report_date": "",
  "votes": 0,
  "device_reported": "",
  "device_match": "exact | variant | family | same_apu | other_handheld | steam_deck | generic",
  "confidence": "high | medium | low",
  "power": { "tdp_w": null, "gpu_clock_mhz": null },
  "display": { "refresh_hz": null, "fps_cap": null, "vrr": null },
  "scaling": { "steam_filter": null, "game_resolution": null },
  "upscaler": { "name": null, "mode": null },
  "frame_gen": { "tool": null, "mode": null },
  "in_game": { "preset": null, "settings": [{ "name": "", "value": "" }] },
  "compat": { "proton": null, "launch_options": null },
  "notes": ""
}
```

### 8.7 Ranking
1. Device match, in the order listed for `device_match`.
2. Recency, preferring the last 12 months.
3. Votes.
- Show the top result with a source and confidence line. Let the user cycle through the others.
- Show reports from other devices as reported, labelled with that device. Do not auto-scale values across devices.

### 8.8 Validation and translation
- Validate every recommendation against the device registry. Clamp TDP to the device range and flag the clamp. Drop refresh rates above the panel maximum.
- **FPS caps.** With VRR, any cap within the VRR range is valid. Without VRR, prefer caps that divide the refresh rate evenly and flag others.
- Translate power values into the selected power tool's vocabulary.
- If the user's stack lacks a tool a report relies on, such as lsfg-vk, show the recommendation with a "requires <tool>" note.
- Do not recommend FSR 4 on any device until verification item 25 is resolved.

### 8.9 Fallback rules
- When no report exists, the user picks light, medium or heavy (default medium).
- Recommend the device's matching TDP band, an FPS cap per section 8.8 and the Steam scaling filter.
- Label the result "General guidance, not game-specific".

### 8.10 Compatibility section (phase 2, recommend only)
- Show the recommended Proton version and launch options from the selected recommendation.
- Show exact strings in monospace and where to set them (Game Properties, General, Launch Options, and Game Properties, Compatibility).
- Show current values read-only where the client exposes them. **[VERIFY]** read access for launch options and compatibility tool.
- If current launch options already contain entries from the user's stack, such as `~/lsfg %command%` or OptiScaler wrappers, show a merged suggestion and explain the merge.
- Flag launch option strings that contain commands beyond environment variables and `%command%`.
- Never execute or apply any string.
- Offer copy to clipboard if it works in Game Mode. **[VERIFY]**

### 8.11 AI providers (phase 2, optional)

| Provider | Generate | Models list | Auth |
|---|---|---|---|
| OpenAI | Endpoint current docs recommend for new integrations **[VERIFY]** | `GET https://api.openai.com/v1/models` | `Authorization: Bearer <key>` |
| Anthropic | `POST https://api.anthropic.com/v1/messages` | `GET https://api.anthropic.com/v1/models` | `x-api-key: <key>` and `anthropic-version: 2023-06-01` |
| Google Gemini | `POST https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent` | `GET https://generativelanguage.googleapis.com/v1beta/models` | `x-goog-api-key: <key>` |

- **[VERIFY]** all endpoints, headers and structured output parameters against current official docs at build time. Anthropic docs start at `https://docs.claude.com/en/api/overview`.

**Rules**
- Implement with `urllib` in `advisor/ai/base.py`, `openai.py`, `anthropic.py` and `gemini.py` behind one interface. No SDKs.
- Do not hardcode model IDs. Fetch the provider's models list, filter to text generation models and let the user choose. No default model.
- Trigger only from an explicit "Generate AI recommendation" button.
- The prompt contains the device profile, selected stack, game name, appid and the normalised source reports. Instruct the model to return JSON matching section 8.6 and to use only settings the device and stack support.
- Use native JSON or schema output modes where the provider supports them. Always parse and validate locally regardless.
- Run section 8.8 validation on the output. Discard fields that fail and show what was discarded.
- Cap output at around 1,500 tokens. Timeout 60 s. Map 401, 429 and 5xx responses to plain-language errors.
- Cache per appid, build, device, stack, provider and model.
- Offer an optional daily request cap.
- Label output "AI generated, unverified" and show it next to the source reports, never in place of them.
- Community report text is untrusted input. AI output is display-only and can never trigger an action.

**Privacy**
- Only game name, appid, device profile, stack selection and report excerpts are sent to the provider. No hostnames, no other plugins' secrets, no user identifiers.
- Document this in `docs/PRIVACY.md` and the plugin README. Recommend a dedicated key with a spending limit.

### 8.12 QAM UI
- Header with game name, detected device and stack summary. Conflict banner when relevant.
- Recommendation card grouped as Power (in the selected tool's terms), Display (refresh, FPS cap, VRR), Scaling and upscaler, Frame generation, and In-game preset with key settings.
- Source line with source, device, date, votes and confidence. Previous and next controls to cycle reports.
- Compatibility section (phase 2).
- AI section (phase 2) with provider, model, generate button and result.
- Link-out buttons to the game's ProtonDB, PCGamingWiki, SteamDeckHQ and ShareDeck pages. **[VERIFY]** how to open a URL in the Steam browser from Game Mode.
- Settings for device override, stack override per category, source toggles, PCGamingWiki credentials, AI keys and model, cache clear and import from file.

### 8.13 Caching
- Cache source responses in `DECKY_PLUGIN_RUNTIME_DIR`, keyed by appid, with a 7-day TTL.
- Serve stale cache when offline and label it as cached.

## 9. Security
- No plugin uses the `root` flag.
- Secrets are stored per section 5 and never sent to the frontend, logs or events.
- TLS verification is on by default.
- gitleaks runs in pre-commit and CI. CI fails on any finding.
- All fixtures pass through `tools/sanitise_fixture.py`, which replaces names, hashes, paths, hostnames, IPs and keys with placeholders.
- CI rejects fixtures containing IPv4 addresses outside documentation ranges or strings matching key patterns.
- Plugin 3 write-call guard per section 8.1.

## 10. Testing
- **Backend.** `pytest` with sanitised fixtures and the mock servers in `tools/`. Cover auth modes, the port 8080 warning, error classification, offline transitions, incremental merge logic, state mapping, opaque ID handling and config lock.
- **Frontend.** `vitest` for formatting, mapping and recommendation rendering logic.
- **Device detection.** Tests against captured DMI dumps, starting with the owner's Legion Go 2.
- **Stack detection.** Tests against synthetic `plugins/*/plugin.json` trees, including conflicts and disabled plugins.
- **AI.** Tests with recorded provider responses, including malformed JSON and out-of-range values. No live calls in CI.

**On-device checklist (owner, Legion Go 2)**
1. Install each plugin via Developer Mode, Install Plugin from URL, using the mirror release URL.
2. qBittorrent by LAN IP with API key, then with the key removed relying on the whitelist, then by FQDN.
3. SABnzbd by LAN IP and by FQDN.
4. Disconnect Wi-Fi. Confirm a quiet offline state and recovery.
5. Plugin 3 with a demanding Steam title, a light indie title and a non-Steam shortcut.
6. Confirm the detected stack matches the installed tools.
7. Check controller navigation for every control.
8. Check battery impact over 30 minutes of play with the QAM closed.

## 11. Build order

**Phase 0**
1. Scaffold the monorepo and three plugins from the template. Apply the section 3 mandatory settings.
2. Run verification spikes for loader-api exports, the Install from URL naming rule, running game detection, qBittorrent 5.2 fixtures, SABnzbd fixtures and the Deck Verified response shape. Record results in `docs/VERIFICATION.md`.
3. Build `shared/py` and `shared/ts`, the mock servers, fixture tools and CI.

**Phase 1**
4. Plugin 1 backend, frontend and tests. Build the zip. Owner tests on device.
5. Plugin 2, reusing shared code. Owner tests on device.
6. Plugin 3 MVP covering game detection, device registry and detection, stack registry and detection, Deck Verified source, ranking, validation, translation, fallback rules and QAM UI.
7. Release workflow with mirrors. Owner installs all three from mirror URLs.

**Phase 2**
8. Plugin 3 compatibility section, recommend only.
9. Plugin 3 AI providers.
10. ProtonDB index and optional PCGamingWiki source.
11. Read-only current values from stack tools where formats are known.
12. Store submissions, plugins 1 and 2 first, then plugin 3.

## 12. Verification register
Track each item in `docs/VERIFICATION.md` with status, source URL and date.

1. `@decky/ui` and `@decky/rollup` current versions.
2. `@decky/api` exports and signatures.
3. Loader PR #992 plugin update API.
4. Install from URL naming rule.
5. Store build from submodule root, review checklist and update-check policy.
6. Running game detection APIs.
7. Game build ID access.
8. Read access to current launch options and compatibility tool.
9. Opening a URL in the Steam browser from Game Mode.
10. Clipboard write in Game Mode.
11. Decky disabled-plugin list location.
12. Decky port 8080 dependency and any other reserved ports.
13. qBittorrent 5.2 field names from live fixtures.
14. qBittorrent invalid key behaviour for whitelisted clients.
15. SABnzbd `warnings`, `status` and `fullstatus` fields.
16. Deck Verified API shape, device vocabulary and licence.
17. ProtonDB dump format and size.
18. PCGamingWiki auth flow and renamed Cargo tables.
19. DMI strings per device from hhd, InputPlumber and captured dumps.
20. Device spec seed values.
21. Stack detection identifiers for every registry entry.
22. Steam native TDP availability per device and OS.
23. Each tool's UI vocabulary and preset values.
24. AI provider endpoints, headers, structured output options and models endpoints.
25. FSR 4 availability on RDNA 3.5 under SteamOS.
26. Plugin backend process isolation for vendored module names.

## 13. Documentation and style rules
- British spelling.
- No em dashes or en dashes anywhere, including code comments, docs and UI copy.
- Avoid semicolons in prose. Use colons sparingly.
- Direct, plain sentences. No filler or marketing language.
- UI copy is short and specific. Error messages state what failed and what to do next.
- Each plugin README covers install URL, setup, screenshots, supported versions, data and privacy disclosure, source attribution and licence.

## 14. Out of scope
- Any write to Steam settings, other plugins, system services or game files from plugin 3.
- Remote access features such as Tailscale or fallback URLs.
- AI proxy or local models.
- Adding torrents or NZBs. Possible later for plugins 1 and 2.
- Windows support.
