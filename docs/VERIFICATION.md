# Verification register

Each **[VERIFY]** item from the build brief (CLAUDE.md section 12), with status, finding, source and date. Checked 25 October 2026 unless stated. Sources were read at the commit or tag named.

## Corrections that change the brief

- The Decky store rejects plugins built with LLM-written code, with no appeals. These plugins cannot go on the store. They stay on the mirror releases (item 5).
- qBittorrent 5.3.0 (20 October 2026) is the latest release, not 5.2.0. WebAPI 2.16.2.
- qBittorrent 5.2.0 and later answer a successful `auth/login` with 204 and an empty body, and bad credentials with 401. The client handles both styles.
- `sync/maindata` always returns JSON with a new `rid`. The 204 path never fires for it. The client still copes with a 204.
- With an API key sent, qBittorrent ignores the IP whitelist. A stale key from a whitelisted device gets 403 on every call. The connection test detects this and says to clear the key.
- qBittorrent 5.3.0 caps WebUI sessions at 15 and evicts the oldest. The client logs in once and reuses the cookie.
- SABnzbd 5.1.3 (8 September 2026) is current. 5.2.0 is in beta and moves to Starlette.
- SABnzbd key errors are HTTP 403 with a plain-text body, empty when `api_warnings` is off. Only "Configuration locked" is JSON. Branch on status, not text.
- SABnzbd queue slots can be `Checking` (pre-check). The brief's mapping lacks it.
- Lenovo puts the machine type in `product_name` (for example `83N0`) and the model name in `product_version`. Confirmed.
- Steam native TDP exists on every target device on current SteamOS, through steamos-manager. Not Steam Deck only.
- LeGoTDP lives at Rayekkk/LeGoTDP, is archived and superseded by Legion Go 2 Companion. Its 5 s reapply is confirmed.
- ProtonDB has no TDP or frame rate fields. It feeds compatibility and notes only.
- PCGamingWiki Cargo needs a bot password since August 2026, and `Infobox_game` is now `Game`.
- Deck Verified has no ROG Xbox Ally device label yet. Its data is GPL-3.0 and its API allows 120 requests per 2 minutes per IP.
- Anthropic API version 2026-10-21 removes temperature, top_p and top_k. Gemini deprecates responseSchema. Recheck both at phase 2.
- FSR 4.1 is official on Z2 chips under Windows only, not under Proton.

## 1. `@decky/ui` and `@decky/rollup` versions

**Status:** confirmed. Checked 25 October 2026.

`npm view`: `@decky/ui` 4.16.0 (modified 20 October 2026), `@decky/rollup` 1.0.2, `@decky/api` 1.1.3. The template pins `@decky/ui` ^4.11.0. The plugins pin ^4.16.0.

Source: https://www.npmjs.com/package/@decky/ui, https://www.npmjs.com/package/@decky/rollup

## 2. `@decky/api` exports and signatures

**Status:** confirmed. Checked 25 October 2026 against `SteamDeckHomebrew/loader-api` `src/index.ts`.

Exports: `call`, `callable<Args, Return>(route)`, `addEventListener<Args>(event, listener)` (returns the listener), `removeEventListener(event, listener)`, `routerHook`, `toaster`, `openFilePicker`, `executeInTab`, `injectCssIntoTab`, `removeCssFromTab`, `fetchNoCors`, `getExternalResourceURL`, `useQuickAccessVisible(): boolean`, `definePlugin(fn)`. The client requests API version 2 and falls back to 1 with a warning.

`useQuickAccessVisible` is the QAM visibility hook. The plugins use it to report visibility to the poller.

Source: https://github.com/SteamDeckHomebrew/loader-api/blob/main/src/index.ts

## 3. Loader PR #992

**Status:** confirmed, no plugin-facing API. Checked 25 October 2026.

"Implement new plugin update API", merged 18 October 2026, changes only `frontend/src/store.tsx`. It moves the loader's own store update check to a lighter endpoint (`UpdateEndpointVersions`). It gives plugins nothing to call. Each plugin keeps its own daily GitHub check. Store policy on self update checks stays open under item 5.

Source: https://github.com/SteamDeckHomebrew/decky-loader/pull/992


**Update now, 26 October 2026.** Decky only shows its own update button for store plugins: `checkForPluginUpdates` in `frontend/src/store.tsx` compares installed plugins with the store's version list by name. A custom store URL replaces the official store, so it is not used. Install Plugin from URL calls the backend route `utilities/install_plugin` (`backend/decky_loader/utilities.py`) with artifact, name, version, hash and install type. The route asks the frontend to show Decky's install prompt (`request_plugin_install` in `browser.py`), and on confirm `_install` downloads the zip, removes the copy whose `plugin.json` name matches, and installs the new one. The frontend connection is `window.DeckyBackend` (`frontend/src/index.ts`), and `InstallType.UPDATE` is 2 (`frontend/src/plugin.ts`). The plugins call that route from Update now. It is a loader internal, not the public API, so `shared/ts/selfUpdate.ts` checks for it and the badge falls back to the link with a Copy link button.

Source: https://github.com/SteamDeckHomebrew/decky-loader/tree/v3.3.0 (files above, read 26 October 2026)
## 4. Install from URL naming rule

**Status:** confirmed. Checked 25 October 2026 against decky-loader `main` at 00cd202 (20 October 2026).

- Frontend `installFromURL(url)` takes the last URL segment, strips `.zip` and passes it as the name with version `dev` (`frontend/src/store.tsx`).
- Backend `_install` (`backend/decky_loader/browser.py`): when version is `dev`, it requires exactly one `*/plugin.json` at depth one, and replaces the name with `plugin.json` `name`. The zip root folder becomes the plugin folder.
- Before v3.0.4 there was no `plugin.json` lookup, and a URL name that differed from `plugin.json` name hung the install. Fixed by PR #706 (commit 8d2b252, 13 October 2024), first released in v3.0.4.

Decision, revised 26 October 2026: asset `<id>.zip` and root folder `<id>/` are the plugin id, and `plugin.json` `name` is the display name, such as "qBittorrent Monitor". Decky's plugin list shows `plugin.json` `name`, so the id looked like a file name there. The minimum loader is v3.0.4. `find_plugin_folder` matches installed plugins by `plugin.json` `name`, so a copy installed under the old id name is not replaced in place. Uninstall it first. Settings survive, because `DECKY_PLUGIN_SETTINGS_DIR` is keyed by folder, and the folder is still the id (`sandboxed_plugin.py`, v3.3.0).

Source: https://github.com/SteamDeckHomebrew/decky-loader/blob/main/backend/decky_loader/browser.py, https://github.com/SteamDeckHomebrew/decky-loader/pull/706

## 5. Store build, review checklist and policy

**Status:** confirmed. Checked 26 October 2026. **The store does not accept these plugins.**

- **Policy, decisive.** The wiki page "Submitting Plugins" says: "No. We do not accept any plugin that uses any LLM based code as these models do not comply with the GPL license ... Any LLM focused plugins will be rejected outright and there will be no appeals." All three plugins were written with an LLM, and tuning-advisor also has an optional AI feature. The plugin addition PR template asks the author to confirm "Generative AI was NOT used to write a majority of the code I am submitting", and warns that PRs not following it "may be denied for suspected AI usage". These plugins cannot honestly meet either, so no store submission was prepared. Distribution stays on the mirror releases and Install Plugin from URL. On 26 October 2026 the owner dropped the store step from the brief.
- **How submission works.** A PR to SteamDeckHomebrew/decky-plugin-database adds the plugin repo as a git submodule under `plugins/`, using the `plugin_addition.md` template: authorship and licence confirmations, the AI statement above, testing on SteamOS Stable or Beta for Python backends, and optionally testing two other plugins' PRs. Plugins must be public, include `LICENSE`, and have no unused `backend`, `assets` or `defaults` folders.
- **How the store builds.** Its own GitHub Actions (in its repo, at its cost) build each submodule in `builder/Dockerfile`: `node:26-alpine` with `pnpm@12`, then `pnpm i --frozen-lockfile` and `pnpm run build` at the submodule root, then copy everything except `src/`, `node_modules` and `__pycache__`. Lockfiles must be `lockfileVersion: 9.0`. Ours are.
- **What would fail today.** Tested with pnpm 12.15.0 on a mirror copy: the lockfile is accepted, but install exits 1 with `ERR_PNPM_IGNORED_BUILDS` for `esbuild` (pulled in by vitest), because pnpm 12 blocks dependency build scripts by default. pnpm 12 also no longer reads the `pnpm` field in `package.json`. A `pnpm-workspace.yaml` with `packages: ["."]`, `allowBuilds: { esbuild: false }` and the `peerDependencyRules` fixes it, and still works with pnpm 9 with the lockfile unchanged. Rollup's `@rollup/rollup-linux-x64-musl` for the Alpine image is already in the lockfiles. Mirrors also carry an empty `plugin.json` `author` and no `publish.image`. None of this is applied, because the policy above rules the store out.
- **Update checks.** No store rule on self update checks was found in the database README, the PR templates or the two wiki pages.

Source: https://github.com/SteamDeckHomebrew/wiki/blob/main/plugin-dev/submitting-plugins.md , https://github.com/SteamDeckHomebrew/wiki/blob/main/plugin-dev/review-and-testing.md , https://github.com/SteamDeckHomebrew/decky-plugin-database/blob/main/.github/PULL_REQUEST_TEMPLATE/plugin_addition.md , https://github.com/SteamDeckHomebrew/decky-plugin-database/blob/main/builder/Dockerfile , https://github.com/SteamDeckHomebrew/decky-plugin-database/blob/main/builder/entrypoint.sh (database commit 7d5cd9b, 23 October 2026)

## 6. Running game detection

**Status:** confirmed from typings. Checked 25 October 2026 against `@decky/ui` 4.16.0.

- `SteamClient.GameSessions.RegisterForAppLifetimeNotifications(cb)` returns `Unregisterable` (`unregister()`). The callback gets `AppLifetimeNotification` with `unAppID`, `nInstanceID` and `bRunning`.
- `Router.MainRunningApp` (`SteamAppOverview | undefined`), `Router.MainRunningAppID` and `Router.RunningApps` exist on `CSteamUIStore`.
- Used in `shared/ts/gameState.ts`: seed from `Router.MainRunningApp`, then track lifetime notifications. Not yet exercised on a device.

Source: `@decky/ui` 4.16.0 `dist/globals/steam-client/GameSessions.d.ts`, `dist/globals/stores/steamuistore/index.d.ts`

## 7. Game build ID

Status: confirmed from @decky/ui 4.16.0 typings.

- `window.appDetailsStore.GetAppDetails(appid)` returns `AppDetails | null`, with `nBuildID: number`. It can be null until loaded: call `await appDetailsStore.RequestAppDetails(appid)` first, or subscribe with `SteamClient.Apps.RegisterForAppDetails(appId, cb)` (returns `Unregisterable`). Also on `AppDetails`: `strSelectedBeta`, `rtLastUpdated`, `vecBetas`.
- `appStore.GetAppOverviewByAppID(appid)` returns `SteamAppOverview | null` (display name, icon, no build ID).

Source: https://github.com/SteamDeckHomebrew/decky-frontend-lib/blob/main/src/globals/steam-client/App.ts , .../src/globals/stores/appdetailsstore.ts , .../src/globals/stores/appstore.ts (commit 10b929d, 20 October 2026).

## 8. Launch options and compatibility tool

Status: confirmed.

- Same `AppDetails` object: `strLaunchOptions`, `strCompatToolName` (internal name, for example `proton_experimental`), `strCompatToolDisplayName`, `nCompatToolPriority`, `strResolutionOverride`. For non-Steam shortcuts: `strShortcutExe`, `strShortcutLaunchOptions`, `strShortcutStartDir`.
- Read only is possible. Writers exist (`SteamClient.Apps.SetAppLaunchOptions(appId, launchOptions)`, `SteamClient.Apps.SpecifyCompatTool(appId, strToolName)`) but the advisor must not call them. `SteamClient.Apps.GetAvailableCompatTools(appId)` returns `Promise<CompatibilityTool[]>`.

Source: as item 7.

## 9. Opening a URL from Game Mode

Status: confirmed.

- `Navigation.NavigateToExternalWeb(url)` from `@decky/ui` opens the Steam overlay browser. Decky Loader itself uses it (`frontend/src/components/settings/pages/developer/index.tsx`). Call `Navigation.CloseSideMenus()` after it if the Quick Access menu is open (the typings say to call it after navigating).
- `SteamClient.System.OpenInSystemBrowser(url)` exists ("Open a URL in the default web browser") and is the desktop choice. In Game Mode prefer `NavigateToExternalWeb`.
- `Navigation.NavigateToSteamWeb(url)` exists for Steam web pages.

Source: https://github.com/SteamDeckHomebrew/decky-frontend-lib/blob/main/src/modules/Router.ts , .../src/globals/steam-client/system/index.ts , decky-loader commit 00cd202 (20 October 2026).

## 10. Clipboard write

Status: unresolved as an API. No helper exists.

- @decky/ui 4.16.0 has no text clipboard helper. `SteamClient.System` has only `CopyFilesToClipboard(paths)`. There is no `SteamClient.System.CopyToClipboard`. Decky Loader's own frontend has no clipboard code.
- What plugins do: `navigator.clipboard.writeText(text)` with a hidden `textarea` plus `document.execCommand("copy")` fallback (for example xXJSONDeruloXx/omfg-deck `src/components/NerdStuffModal.tsx`). GitHub code search finds the same pattern in about a dozen plugins. Not verified on a device here. Build both paths and show the text on screen as a final fallback.

Source: decky-frontend-lib as above, https://github.com/xXJSONDeruloXx/omfg-deck/blob/main/src/components/NerdStuffModal.tsx .

## 11. Decky disabled-plugin list

**Status:** confirmed. Checked 25 October 2026.

The loader keeps a list of plugin names under the `disabled_plugins` key of its settings, read with `utilities.get_setting("disabled_plugins", [])` (`backend/decky_loader/loader.py`, `utilities.py`). The settings file is `SettingsManager("loader", <privileged path>/settings)`, which is `~/homebrew/settings/loader.json` on a standard install. Entries are `plugin.json` names, not folder names.

Source: https://github.com/SteamDeckHomebrew/decky-loader/blob/main/backend/decky_loader/loader.py

## 12. Reserved ports

**Status:** confirmed. Checked 25 October 2026.

- Decky's own server listens on `localhost:1337` (`helpers.py` loads the frontend from `http://localhost:1337/frontend/...`).
- Decky injects into Steam through the CEF remote debugger at `http://localhost:8080` (`injector.py` `BASE_ADDRESS`). A qBittorrent or SABnzbd WebUI on port 8080 on the handheld itself breaks Decky. The connection test warns on localhost or 127.0.0.1 with port 8080.
- No other reserved port was found in the loader.

Source: https://github.com/SteamDeckHomebrew/decky-loader/blob/main/backend/decky_loader/injector.py, https://github.com/SteamDeckHomebrew/decky-loader/blob/main/backend/decky_loader/helpers.py

## 13. qBittorrent: release, sync/maindata, 204, start/stop, cookie

Status: corrected (version), confirmed (rest), with one new behaviour to plan for.

- Latest stable is **5.3.0, published 20 October 2026**, not 5.2. The 5.2 line ended at 5.2.4 (28 September 2026). 5.2.0 was 3 May 2026. WebAPI version: 2.16.2 in 5.3.0 (`API_VERSION {2, 16, 2}` in `src/webui/webapplication.h`), 2.15.1 in 5.2.4.
- `sync/maindata` top level keys: `rid`, `full_update`, `torrents`, `torrents_removed`, `categories`, `categories_removed`, `tags`, `tags_removed`, `trackers`, `trackers_removed`, `server_state`. Removed lists use the `_removed` suffix (`KEY_SUFFIX_REMOVED`).
- `server_state` keys (5.3.0 `synccontroller.cpp`): `connection_status` (`connected`, `firewalled`, `disconnected`), `dht_nodes`, `dl_info_data`, `dl_info_speed`, `dl_rate_limit`, `up_info_data`, `up_info_speed`, `up_rate_limit`, `alltime_dl`, `alltime_ul`, `global_ratio`, `free_space_on_disk`, `queueing`, `use_alt_speed_limits`, `refresh_interval`, `last_external_address_v4`, `last_external_address_v6`, `average_time_queue`, `queued_io_jobs`, `queued_tracker_announces`, `read_cache_hits`, `read_cache_overload`, `request_latency`, `total_buffers_size`, `total_peer_connections`, `total_queued_size`, `total_wasted_session`, `write_cache_overload`, plus new `session_state` in 5.3.0 (BitTorrent session pause and resume, release notes #24269).
- Torrent object keys (`serialize_torrent.h`): `hash`, `infohash_v1`, `infohash_v2`, `name`, `magnet_uri`, `size`, `total_size`, `progress`, `dlspeed`, `upspeed`, `priority`, `num_seeds`, `num_complete`, `num_leechs`, `num_incomplete`, `ratio`, `popularity`, `eta`, `state`, `seq_dl`, `f_l_piece_prio`, `category`, `tags`, `super_seeding`, `force_start`, `save_path`, `download_path`, `content_path`, `root_path`, `added_on`, `completion_on`, `tracker`, `trackers_count`, `dl_limit`, `up_limit`, `downloaded`, `uploaded`, `downloaded_session`, `uploaded_session`, `amount_left`, `completed`, `max_ratio`, `max_seeding_time`, `max_inactive_seeding_time`, `ratio_limit`, `seeding_time_limit`, `inactive_seeding_time_limit`, `share_limits_mode`, `share_limit_action`, `seen_complete`, `last_activity`, `auto_tmm`, `time_active`, `seeding_time`, `availability`, `reannounce`, `comment`, `private`, `has_metadata`, `has_tracker_warning`, `has_tracker_error`, `has_other_announce_error`, `connections_count`, `connections_limit`, `total_wasted`, `pieces_num`, `piece_size`, `pieces_have`, `created_by`, `creation_date`.
- `state` strings: `error`, `missingFiles`, `uploading`, `stoppedUP`, `queuedUP`, `stalledUP`, `checkingUP`, `forcedUP`, `downloading`, `metaDL`, `forcedMetaDL`, `stoppedDL`, `queuedDL`, `stalledDL`, `checkingDL`, `forcedDL`, `checkingResumeData`, `moving`, `unknown`. There is no `pausedUP` or `pausedDL` in 5.x.
- 204 behaviour: "Send 204 when WebAPI response contains no data" (PR #21349, shipped in 5.2.0). The rule in `webapplication.cpp` is `if (result.data.isNull()) status 204`. A controller that sets no result at all gets 204. `auth/login` success now sets no result, so **login success returns 204 with an empty body, not 200 `Ok.`**. Bad credentials return **401** (`APIErrorType::Unauthorized`), not 200 `Fails.`. An IP ban returns 403 with "Your IP address has been banned after too many failed authentication attempts." (5.1.0 still returned `Ok.` and `Fails.`.) Actions such as `torrents/start` call `setResult(QString())`. Under Qt 6 a null QString inside a QVariant is not `isNull()`, so these most likely return 200 with an empty `text/plain` body. That last point is read from source, not tested live. Treat any 2xx as success.
- `torrents/start` and `torrents/stop`: confirmed (`startAction`, `stopAction` in `torrentscontroller.h`), POST, param `hashes` split on `|`, `all` accepted. `pause` and `resume` do not exist in 5.x.
- Cookie: `SESSION_COOKIE_NAME_PREFIX = u"QBT_SID_"` plus the WebUI port, so `QBT_SID_8080` for the default port (5.2.0 change "Append port to session cookie name"). HttpOnly, SameSite=Lax when CSRF protection is on. Read the name from `Set-Cookie` rather than building it.
- New in 5.3.0, relevant to a polling plugin: a WebUI session count limit, preference `WebUI/SessionsCountLimit`, default **15**. When exceeded the oldest session is deleted. A plugin that logs in on every poll will evict the user's browser session. Log in once and reuse the cookie.
- CSRF: 5.3.0 prefers `Sec-Fetch-Site` (only `same-origin` or `none` pass), else checks `Origin` and `Referer` against `Host`. A fetch from the Steam CEF frontend is cross-site, so cookie auth from the frontend will be refused. Call qBittorrent from the plugin's Python backend.
- The wiki page "WebUI API (qBittorrent 5.0)" is stale: its changelog stops at 2.11.3, it documents login as 200, and it says nothing about API keys, 204 or `QBT_SID_`. Use source, not the wiki.

Sources: https://github.com/qbittorrent/qBittorrent/releases/tag/release-5.3.0 , https://github.com/qbittorrent/qBittorrent/blob/release-5.3.0/src/webui/webapplication.cpp , https://github.com/qbittorrent/qBittorrent/blob/release-5.3.0/src/webui/api/synccontroller.cpp , https://github.com/qbittorrent/qBittorrent/blob/release-5.3.0/src/webui/api/serialize/serialize_torrent.cpp , https://github.com/qbittorrent/qBittorrent/blob/release-5.3.0/src/webui/api/authcontroller.cpp , https://github.com/qbittorrent/qBittorrent/blob/release-5.1.0/src/webui/api/authcontroller.cpp , https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-5.0) , commit 0c48b70e5.

## 14. qBittorrent API key auth

Status: confirmed, with exact behaviour.

- Shipped in 5.2.0 ("WEBAPI: Add support for authenticating via API key", PR #23212). Header: `Authorization: Bearer <key>`. The scheme match is case-insensitive in 5.3.0. Key format (`src/base/utils/apikey.cpp`): `qbt_` plus 28 characters, 32 in total. A stored key that fails that format check is ignored.
- `X-API-Key` header support (PR #24392, 5 October 2026) is on master only. It is **not** in 5.3.0 (`grep` of the 5.3.0 tree finds nothing, and the compare with the tag is "diverged"). Do not rely on it.
- Invalid key from a whitelisted IP: the Bearer path calls `apiKeySessionInitialize()` only. That function never consults `isAuthNeeded()`, so the localhost bypass and the subnet whitelist play no part. A wrong key leaves no session, and any non-public endpoint then throws `ForbiddenHTTPError`, so the reply is **403**. The whitelist bypass only works when no `Authorization: Bearer` header is sent at all. So a plugin that sends a stale key from a whitelisted Deck gets 403 even though a keyless request would succeed. If no key is configured on the server (`m_apiKey` empty) any Bearer request also gets no session and 403.
- API key and `auth/login`: in 5.3.0 any `auth/*` endpoint with a Bearer header throws 403 (`if (isUsingApiKey && endpoint.startsWith(u"auth/")) throw ForbiddenHTTPError()`). In 5.2.x the 403 fires when no session controller handles `auth`. Do not call `auth/login` with a key. With a key, non-API paths (the WebUI files) return 404.
- Bearer requests skip the CSRF check, so they are the one auth form that works from a cross-site origin. 5.3.0 also stops setting cookies for API key sessions (PR #24748).
- Basic auth (`Authorization: Basic`) is also accepted on the cookie path in 5.2 and 5.3. A bad Basic credential returns 401.

Sources: https://github.com/qbittorrent/qBittorrent/blob/release-5.3.0/src/webui/webapplication.cpp (processRequest, apiKeySessionInitialize, cookieSessionInitialize, isAuthNeeded), https://github.com/qbittorrent/qBittorrent/blob/release-5.2.4/src/webui/webapplication.cpp (doProcessRequest), https://github.com/qbittorrent/qBittorrent/blob/release-5.3.0/src/base/utils/apikey.cpp , commits 312e914ad, 374c06fbb, 926d96111.

## 15. SABnzbd

Status: corrected in part.

- Latest stable is **5.1.3 (8 September 2026)**. 5.2.0Beta2 came out 6 October 2026 (Beta1 on 22 September). No 5.2.0 final yet.
- Big change on the 5.2 line: SABnzbd 5.2.0 betas replace CherryPy with **Starlette and uvicorn** (`sabnzbd/interface.py` imports `starlette`, `uvicorn`). The API shape is kept, but test against both 5.1.3 and the 5.2 beta.
- Error strings, exact: `API Key Required`, `API Key Incorrect`, `Missing authentication`, `Access denied - Configuration locked`, `External internet access denied - https://sabnzbd.org/access-denied` (all in `interface.py`), and `Configuration locked` (`_MSG_CONFIG_LOCKED` in `api.py`).
- How they arrive: the key errors are **HTTP 403 with a `text/plain` body**, not JSON. In both 5.1.3 (`cherrypy.response.status = 403`) and 5.2 beta (`forbidden()` returns `PlainTextResponse(..., status_code=403)`) the body is the message only when `api_warnings` is on (default `True`, `cfg.py`), otherwise it is empty. Branch on the status code, not the text. 5.2 beta adds a 401 "session expired" path that only applies to browser sessions.
- `Configuration locked` is different: it is an in-band API reply via `report()`, so JSON `{"status": false, "error": "Configuration locked"}` with HTTP 200. In 5.1.3 it guards `set_config`, `set_config_default`, `del_config` and `mode=config`. In 5.2 beta it is a `config_locked=True` flag on those plus `config` `speedlimit` and `set_pause`, so a locked config also blocks speed limit and timed pause from a plugin.
- NZB key and the queue: no. Access levels in the API table: `queue` 2, `history` 2, `warnings` 2, `fullstatus` 2, `pause`/`resume` 2, `addurl`/`addfile` 1, `version` 1, `get_config` 3. The NZB key is accepted only when the level is 1. A monitor needs the full API key. `mode=version` and `mode=auth` need no key.
- `mode=warnings` returns `{"warnings": [ {"type", "text", "time", "origin"} ]}`. `type` is the log level name (`WARNING`, `ERROR`), `time` is Unix seconds (int), `origin` is source file plus line, for example `downloader.py123`. `name=clear` empties the list. `name=show` is the same as no name.
- `mode=fullstatus` returns `{"status": {...}}`. Contents are `build_header()` keys (`version`, `paused`, `paused_all`, `pause_int`, `speedlimit`, `speedlimit_abs`, `diskspace1`, `diskspace2`, `diskspacetotal1`, `diskspacetotal2`, `diskspace1_norm`, `diskspace2_norm`, `have_warnings`, `have_quota`, `quota`, `left_quota`, `uptime`, `finishaction`, `pp_pause_event`, `new_release`, `new_rel_url` and others) plus `logfile`, `weblogfile`, `loglevel`, `folders`, `configfn`, `servers`, and dashboard data unless `skip_dashboard=1`. Optional `calculate_performance=1` runs pystone and disk speed tests, so do not send it on a poll.
- Status strings (`constants.py` class `Status`): `Idle`, `Completed`, `Checking`, `Downloading`, `Extracting`, `Failed`, `Fetching`, `Grabbing`, `Moving`, `Paused`, `Queued`, `QuickCheck`, `Repairing`, `Running`, `Verifying`, `Deleted`, `Propagating`. Queue top level `status` is `Idle`, `Paused` or `Downloading`. History adds the post-processing ones.

Sources: https://github.com/sabnzbd/sabnzbd/releases , https://github.com/sabnzbd/sabnzbd/blob/5.1.3/sabnzbd/interface.py , https://github.com/sabnzbd/sabnzbd/blob/5.1.3/sabnzbd/api.py , https://github.com/sabnzbd/sabnzbd/blob/develop/sabnzbd/interface.py (commit d162e0f, 24 October 2026), https://github.com/sabnzbd/sabnzbd/blob/develop/sabnzbd/api.py , https://github.com/sabnzbd/sabnzbd/blob/develop/SABnzbd.py (GUI log handler), https://github.com/sabnzbd/sabnzbd/blob/develop/sabnzbd/constants.py .

## 16. Deck Verified / DeckSettings API

Status: confirmed, with shape below.

- `GET https://deckverified.games/deck-verified/api/v1/game_details?appid=1091500` returned 200 `application/json`, 24.5 KB, 6 reports. `appid=620` returned 200 with `reports: []`.
- Top level: `reports` (array), `external_reviews` (array), `gameName`, `appId` (int), `projectNumber` (int or null), `metadata` {`poster`, `hero`, `banner`, `background`}, `reports_summary` (null in both samples).
- Each report: `id`, `number`, `title`, `html_url` (a GitHub issue in DeckSettings/game-reports-steamos), `data`, `metadata`, `reactions` {`reactions_thumbs_up`, `reactions_thumbs_down`}, `comments`, `labels` [{`name`, `color`, `description`}], `user` {`login`, `avatar_url`, `report_count`}, `current_user_reaction`, `created_at`, `updated_at`.
- `report.data` fields: `summary`, `game_name`, `app_id`, `launcher`, `target_framerate`, `average_battery_power_draw` (string), `device`, `os_version`, `steam_play_compatibility_tool_used`, `compatibility_tool_version`, `game_resolution`, `custom_launch_options`, `frame_limit`, `disable_frame_limit`, `enable_vrr`, `allow_tearing`, `half_rate_shading`, `tdp_limit`, `manual_gpu_clock`, `scaling_mode`, `scaling_filter`, `game_display_settings` (Markdown), `game_graphics_settings` (Markdown), `additional_notes`, `performance_rating` (for example "★★★★★ (5/5)"), `calculated_battery_life_minutes` (int). Many values are strings or null, so parse defensively.
- Other parameters: `name=<game name>` instead of `appid`, and `include_external=true`. Returns 400 `{"error": "No valid query parameter"}` with neither, and **204** for an app ID above Steam's highest known ID. Optional `x-github-token` header.
- Rate limit: 120 requests per IP per 2 minutes on all routes (`express-rate-limit`, standard `RateLimit` headers). Cache results.
- Device vocabulary, current form dropdown (`GAME-REPORT.yml`): `ASUS ROG Ally Z1`, `ASUS ROG Ally Z1 Extreme`, `ASUS ROG Ally X`, `GPD Win 4`, `Lenovo Legion Go`, `Lenovo Legion Go 2`, `Lenovo Legion Go S Z1E`, `Lenovo Legion Go S Z2Go`, `MSI Claw`, `MSI Claw A8 Plus`, `Valve Steam Deck LCD (64GB)`, `Valve Steam Deck LCD (256GB/512GB)`, `Valve Steam Deck OLED`. Older reports carry other strings ("Steam Deck LCD (256GB/512GB)", "Lenovo Legion Go S"). Normalise through the `labels`, whose `description` is a regex. `GET /deck-verified/api/v1/issue_labels` returns them, for example `DEVICE: Valve Steam Deck` = `^(Valve )?Steam Deck( OLED| LCD.*)?$`, `DEVICE: Lenovo Legion Go S Z1E` = `^(Lenovo Legion Go S|Lenovo Legion Go S Z1E)$`, plus `DEVICE: Zotac Zone`. There is **no ROG Xbox Ally or Xbox Ally X** device yet, and no Intel Claw split.
- Licences: `DeckSettings/game-reports-steamos` (the report data, as GitHub issues) is **GPL-3.0**, `DeckSettings/deck-verified-site` (front and back end) is **GPL-3.0**, `DeckSettings/decky-game-settings` (their own Decky plugin) is BSD-3-Clause. No separate data licence or API terms were found in the README. Reports are user-written GitHub issues, so attribute and link each report (`html_url`) and do not bulk copy. Note the existing plugin "decky-game-settings" already browses this data.

Sources: https://deckverified.games/deck-verified/api/v1/game_details?appid=1091500 , https://deckverified.games/deck-verified/api/v1/game_details?appid=620 , https://deckverified.games/deck-verified/api/v1/issue_labels , https://github.com/DeckSettings/deck-verified-site/blob/master/packages/backend/src/index.ts , https://github.com/DeckSettings/deck-verified-site/blob/master/packages/backend/src/rateLimiter.ts , https://github.com/DeckSettings/game-reports-steamos/blob/master/.github/ISSUE_TEMPLATE/GAME-REPORT.yml , https://github.com/orgs/DeckSettings/repositories .

## 17. ProtonDB dump format and size

**Status:** confirmed. Checked 26 October 2026 by downloading and streaming the latest dump.

- Monthly dumps at https://github.com/bdefore/protondb-data, `reports/reports_<mon><n>_<year>.tar.gz`. Latest is `reports_oct1_2026.tar.gz`, 71.5 MB, pushed 1 October 2026.
- One member, `reports_piiremoved.json`, about 530 MB: a single JSON array of 395,467 reports across 40,587 apps. It is too big to load in one go, so `tools/protondb_index.py` streams it.
- Each report: `app.steam.appId`, `app.title`, `timestamp` (Unix seconds), `systemInfo` (`cpu`, `gpu`, `gpuDriver`, `kernel`, `os`, `ram`), and `responses`.
- `responses` fields that matter: `verdict` (`yes` or `no`), `variant` (`official`, `ge`, `experimental`, `native`, `notListed`, `older`), `protonVersion` (official builds, for example `9.0-4`), `customProtonVersion` (for example `GE-Proton10-34`), `launchOptions` (for example `~/lsfg %command%`), `notes.verdict`, `concludingNotes`, `batteryPerformance`, `tinkerOverride`, `launcher`.
- There is no TDP, frame rate or graphics preset field. ProtonDB feeds compatibility, launch options and notes, not power settings.
- Handheld share since January 2025: 16,563 Steam Deck reports, 398 Ryzen Z1 Extreme, 41 Z2 Go, 33 Z2 Extreme, 10 Z1, 1 Z2. The Steam Deck LCD reports itself as `AMD Custom APU 0405`, the OLED as `AMD Custom APU 0932`.
- Licence: ODbL 1.0 for the database and DbCL 1.0 for contents (repo README). The derived index is shared under the ODbL with attribution.
- Index built from it: 16,299 apps with handheld reports, 1.6 MB gzipped.

Source: https://github.com/bdefore/protondb-data , https://opendatacommons.org/licenses/odbl/

## 18. PCGamingWiki auth flow and renamed Cargo tables

**Status:** confirmed. Checked 26 October 2026 against the live API and the wiki's API page.

- Anonymous `cargoquery` returns `permissiondenied`: "You don't have permission to run arbitrary Cargo queries." Since 23 August 2026 it needs a bot password made at Special:BotPasswords with the grant "Create, query and delete data through the Cargo extension", and the MediaWiki `action=login` flow: GET `action=query&meta=tokens&type=login`, then POST `action=login` with `lgname`, `lgpassword` and `lgtoken`, keeping the session cookie.
- Renamed on 25 August 2026: `Infobox_game` is now `Game`, `Infobox_game_engine` is `GameEngine`, `VR_support` is `VR`, internal tables are `PCGW_<name>`. On 30 August the `Availability` columns were renamed (`Available_from` to `Present` and so on) and store keys moved to `StoreKeys`.
- New on 22 August: `GameData` with `Type`, `Platform` and `Paths` for config and save file locations.
- `Video` has `Upscaling` and `Frame_gen` (lists), `HDR`, `Ray_tracing`, `60_FPS`, `120_FPS`, `Ultrawidescreen` and more. `Game` has `Steam_AppID` (list), so filter with `Game.Steam_AppID HOLDS "<id>"`.
- Rate limit 60 requests a minute. Going over returns HTTP 429 and blocks the IP for 60 seconds. A descriptive User-Agent with contact details is required, or requests may get 403.
- Licence: CC BY-NC-SA. Show with attribution and a link. The plugin caches answers for 7 days.

Source: https://www.pcgamingwiki.com/wiki/PCGamingWiki:API , https://www.pcgamingwiki.com/wiki/Special:CargoTables/Video , https://www.pcgamingwiki.com/wiki/Special:CargoTables/GameData , https://www.pcgamingwiki.com/w/api.php

## 19. DMI strings

Status: confirmed. Paths are `/sys/devices/virtual/dmi/id/<field>` (same as `/sys/class/dmi/id/`).

| Device | Field | Match | Source |
|---|---|---|---|
| Steam Deck LCD | `product_name` | `Jupiter` (`sys_vendor` `Valve`) | InputPlumber 50-steam_deck.yaml, SimpleDeckyTDP |
| Steam Deck OLED | `product_name` | `Galileo` (`sys_vendor` `Valve`) | same |
| ROG Ally (Z1, Z1 Extreme) | `board_name` `RC71L`, or `product_name` contains `ROG Ally RC71L` | `sys_vendor` `ASUSTeK COMPUTER INC.` | InputPlumber, hhd |
| ROG Ally X | `board_name` `RC72LA`, or `product_name` contains `ROG Ally X RC72LA` | | same |
| ROG Xbox Ally | `board_name` `RC73YA`, or `product_name` contains `ROG Xbox Ally RC73Y` | | same |
| ROG Xbox Ally X | `board_name` `RC73XA`, or `product_name` contains `ROG Xbox Ally X RC73X` | | same |
| ROG Xbox Ally X20 (newer) | `board_name` `RC74XA`, `sys_vendor` `ASUS`, `product_name` contains `ROG XBOX Ally X RC74X` | | same |
| Legion Go | `product_name` `83E1` | `sys_vendor` `LENOVO`. hhd falls back to `bios_version` `N3CN..WW` for units with a blank product name | hhd, InputPlumber |
| Legion Go S | `product_name` `83L3` (Z2 Go), `83N6` (Z1 Extreme), `83Q2`, `83Q3` | | same |
| Legion Go 2 | `product_name` `83N0`, `83N1` | | same |
| MSI Claw A8 (Ryzen Z2 Extreme) | `board_name` `MS-1T8K` | `board_vendor` `Micro-Star International Co., Ltd.` | InputPlumber, hhd claw/const.py |
| MSI Claw (Intel, Meteor Lake, A1M) | `board_name` `MS-1T41` | | same |
| MSI Claw 7 AI+ A2VM (Intel Lunar Lake) | `board_name` `MS-1T42` | | same |
| MSI Claw 8 AI+ A2VM (Intel Lunar Lake) | `board_name` `MS-1T52` | | same |
| MSI Claw 8 EX AI+ CG3EM (Intel) | `board_name` `MS-1T91` | | same |

- Lenovo: confirmed that **`product_name` holds the machine type code** (`83E1` and so on) and **`product_version` holds the model name**: `Legion Go 8APU1` (Go), `Legion Go 8ASP2` (Go 2, 83N0), `Legion Go 8AHP2` (Go 2, 83N1), and strings starting `Legion Go S ` for the Go S (Legion Go 2 Companion `controller_firmware.py`, `module_runtime.py`, `fan_ec.py`).
- Asus `product_name` carries a suffix (`ROG Ally RC71L_RC71L`, `ROG Ally X RC72LA_RC72LA_000123206`, `ROG Xbox Ally RC73YA_RC73YA`), so use contains or `board_name`.
- "Intel Claw" is ambiguous: there are four Intel board names above. Prefer `board_name` for all MSI. SimpleDeckyTDP matches only `Claw 8 AI+ A2VM` in `product_name`.

Sources: https://github.com/ShadowBlip/InputPlumber/tree/main/rootfs/usr/share/inputplumber/devices (commit 4ed1f50, 21 October 2026), https://github.com/hhd-dev/hhd/tree/master/src/hhd/device (commit ae908f9, 24 October 2026), https://github.com/aarron-lee/SimpleDeckyTDP/blob/main/py_modules/device_utils.py , https://github.com/Rayekkk/LegionGo2Companion .

## 20. Device spec seed values

Status: partly confirmed. Steam Deck, the first two Ally models, Legion Go and Legion Go S are confirmed from the makers' pages. Lenovo PSREF sheets were read on 26 October 2026. The rest are from secondary launch coverage, AMD's chip page, or reference knowledge, and are marked as such. MSI's spec pages refuse automated requests (HTTP 403), so the Claw rows stay unconfirmed.

Key: C = confirmed on the maker's page today. S = secondary coverage agrees. R = reference value, not rechecked today.

| Device | Display | Refresh, VRR | Battery | APU, GPU | TDP | RAM | Basis |
|---|---|---|---|---|---|---|---|
| Steam Deck LCD | 7.0 in, 1280x800 | 60 Hz, no VRR | 40 Wh | Van Gogh, Zen 2 4c/8t, 8 RDNA 2 CU, 1.6 GHz | 4 to 15 W | 16 GB LPDDR5-5500 | C |
| Steam Deck OLED | 7.4 in, 1280x800 HDR OLED, 1000 nits HDR peak | up to 90 Hz, no VRR stated | 50 Wh | 6 nm, 8 RDNA 2 CU, 1.6 GHz | 4 to 15 W | 16 GB LPDDR5-6400 | C |
| ROG Ally (RC71L), Z1 Extreme | 7 in, 1920x1080 | 120 Hz, FreeSync Premium | 40 Wh | Z1 Extreme, 12 RDNA 3 CU, up to 2.7 GHz | 9 to 30 W | 16 GB LPDDR5-6400 | C. Z1 (non Extreme) SKU: 4 RDNA 3 CU, R |
| ROG Ally X (RC72LA) | 7 in, 1920x1080 | 120 Hz, FreeSync Premium | 80 Wh | Z1 Extreme, 12 RDNA 3 CU | 9 to 30 W | 24 GB LPDDR5 (12 GB x2) | C |
| ROG Xbox Ally (RC73YA) | 7 in, 1920x1080 | 120 Hz, VRR R | 60 Wh | Ryzen Z2 A, Zen 2 4c/8t, 8 RDNA 2 CU R | 6 to 20 W R (Steam's own range is 4 to 20 W, item 22) | 16 GB LPDDR5-6400 | battery and RAM C (ASUS eShop), rest S or R |
| ROG Xbox Ally X (RC73XA) | 7 in, 1920x1080 | 120 Hz, VRR R | 80 Wh | Ryzen AI Z2 Extreme, 16 RDNA 3.5 CU, up to 2.9 GHz | 15 to 35 W cTDP, 28 W default (AMD chip page) | 24 GB LPDDR5X-8000 | S, chip values C (amd.com) |
| Legion Go (83E1) | 8.8 in, 2560x1600 IPS | 144 Hz, no VRR listed | 49.2 Wh | Z1 Extreme (8c/16t) or Z1 (6c/12t). CU counts from AMD, R | up to 30 W R | 16 GB LPDDR5X-7500 | C (PSREF, 22 January 2025 sheet). The Z1 version was missing from the registry and is added as `lenovo-legion-go-z1` |
| Legion Go S (83L3 Z2 Go, 83N6 Z1E) | 8 in, 1920x1200 IPS | 48 to 120 Hz VRR | 55.5 Wh | Z2 Go (4c/8t, 8ARP1 sheet) or Z1 Extreme (8c/16t, 8APU1 sheet). CU counts from AMD, R | firmware ceiling SPL 40, SPPT 43, FPPT 53 W (LeGoTDP, read from firmware) | 16 or 32 GB. Z2 Go: LPDDR5 or LPDDR5X-6400. Z1 Extreme: LPDDR5X-7500 | C (PSREF, sheets of 25 May and 6 May 2026), TDP from source |
| Legion Go 2 (83N0 Z2E, 83N1 Z2) | 8.8 in, 1920x1200 OLED, HDR TrueBlack 1000 | 144 Hz, VRR 30 to 144 Hz | 74 Wh | Z2 Extreme (16 RDNA 3.5 CU) or Z2 (Zen 4, 12 RDNA 3 CU) | firmware range 5 to 35 W (SimpleDeckyTDP comment), up to 50 W with ryzenadj (LeGoTDP) | up to 32 GB LPDDR5X-8000 | S, TDP from source |
| MSI Claw A8 (MS-1T8K) | 8 in, 1920x1200 | 120 Hz, VRR | 80 Wh | Z2 Extreme, 16 RDNA 3.5 CU | 15 to 35 W (chip) | 24 GB LPDDR5X-8000 | R |
| MSI Claw A1M (MS-1T41) | 7 in, 1920x1080 | 120 Hz, VRR | 53 Wh | Core Ultra 7 155H or 5 135H, Arc 8 Xe (7 Xe on 135H) | up to 35 to 40 W R | 16 GB LPDDR5-6400 | R |
| MSI Claw 7 AI+ and 8 AI+ (MS-1T42, MS-1T52) | 7 in 1920x1080 and 8 in 1920x1200 | 120 Hz, VRR | 80 Wh | Core Ultra 7 258V, Arc 140V, 8 Xe2 cores | up to 30 W R | 16 or 32 GB LPDDR5X-8533 | R |

- CU counts are AMD compute units. Intel parts have Xe cores, so the advisor should not compare them with CU counts.
- Sources disagree on the Legion Go 2 iGPU name (890M versus 780M). By chip, Z2 Extreme is RDNA 3.5 and Z2 is RDNA 3.

Sources: https://www.steamdeck.com/en/tech/deck , https://www.steamdeck.com/en/tech , https://rog.asus.com/gaming-handhelds/rog-ally/rog-ally-2023/spec/ , https://rog.asus.com/gaming-handhelds/rog-ally/rog-ally-x-2024/spec/ , https://eshop.asus.com/ca-en/rog-xbox-ally-cnf.html , https://www.amd.com/en/products/processors/handhelds/ryzen-z-series/z2-series/z2-extreme.html , https://www.pcworld.com/article/2899101/lenovos-legion-go-2-adds-a-big-oled-screen-to-battle-the-steam-deck.html , https://insider-gaming.com/?p=144499 , https://liliputing.com/?p=175098 , https://psref.lenovo.com/syspool/Sys/PDF/Legion/Legion_Go_8APU1/Legion_Go_8APU1_Spec.pdf , https://psref.lenovo.com/syspool/Sys/PDF/Legion/Legion_Go_S_8APU1/Legion_Go_S_8APU1_Spec.PDF , https://psref.lenovo.com/syspool/Sys/PDF/Legion/Legion_Go_S_8ARP1/Legion_Go_S_8ARP1_Spec.PDF .

## 21. Stack detection identifiers

Status: confirmed, two repos moved owner.

`plugin.json` `name`, exact:

| Plugin | Repo | `name` | Notes |
|---|---|---|---|
| SimpleDeckyTDP | aarron-lee/SimpleDeckyTDP | `SimpleDeckyTDP` | not in the Decky store database |
| PowerControl | mengmeet/PowerControl | `PowerControl` | not in the store database |
| PowerTools | NGnius/PowerTools | `PowerTools` | GitHub repo archived (last push 9 August 2023), in the store |
| LeGoTDP | **Rayekkk/LeGoTDP** (not aarron-lee) | `LeGoTDP` | archived, superseded by Legion Go 2 Companion. Fork iLordel/LEGOTDP uses `LTDP` |
| Legion Go 2 Companion | Rayekkk/LegionGo2Companion | `Legion Go 2 Companion` | note the spaces |
| decky-lsfg-vk | xXJSONDeruloXx/decky-lsfg-vk | `Decky LSFG-VK` | in the store |
| Decky-Framegen | xXJSONDeruloXx/Decky-Framegen | `Decky-Framegen` | in the store |
| decky-optiscaler | xXJSONDeruloXx/decky-optiscaler | `decky-optiscaler` | last push July 2025 |
| Fantastic | NGnius/Fantastic | `Fantastic` | archived, in the store |

Match on a normalised name. Legion Go 2 Companion's own `conflict_guard.py` does `casefold()` and keeps only alphanumerics before comparing, then reads each sibling `plugin.json` under the plugins folder.

- Handheld Daemon: systemd units `hhd.service` (system, `ExecStart=/usr/bin/hhd`), `hhd@<user>.service` (`/usr/bin/hhd --user %i`, the one the FAQ uses: `systemctl status hhd@$(whoami)`), and `hhd_local@<user>.service` (the `install.sh` local install). Check all three. Local API: **port 5335**, bound to 127.0.0.1 by default (`hhd.http.localhost` default True), path prefix `/api/v1/` (`settings`, `state`, `profile`, `version`, `sections`, `event`, `image`). Bearer token on by default (`hhd.http.token` default True), stored in `/etc/hhd/.token` and copied 0644 to `/tmp/hhd/token`. Unauthenticated calls get 401 with `WWW-Authenticate: Bearer`.
- PowerStation: DBus well known name **`org.shadowblip.PowerStation`** on the system bus (`src/constants.rs` `BUS_NAME`), unit `powerstation.service`.
- InputPlumber unit: `inputplumber.service` (as used by Legion Go 2 Companion).

Sources: each repo's `plugin.json` on its default branch, https://github.com/SteamDeckHomebrew/decky-plugin-database/tree/main/plugins , https://github.com/Rayekkk/LegionGo2Companion/blob/main/conflict_guard.py , https://github.com/hhd-dev/hhd/blob/master/src/hhd/__main__.py , https://github.com/hhd-dev/hhd/blob/master/src/hhd/settings.yml , https://github.com/hhd-dev/hhd/tree/master/usr/lib/systemd/system , https://github.com/ShadowBlip/PowerStation/blob/main/src/constants.rs .

## 22. Steam native TDP limit per device

Status: corrected and made precise. The answer is not "Steam Deck only". Valve's `steamos-manager` (the service behind the Steam client's Performance panel) carries a per-device `[tdp_limit]` table, and the brief should read support from there.

From `data/devices/*.toml` in steamos-manager master (commit 61786e2, 23 October 2026, latest tag v26.4.1 of 22 July 2026):

| Device (DMI match used by Valve) | `tdp_limit.method` | Detail |
|---|---|---|
| Steam Deck LCD and OLED (`sys_vendor` Valve, `board_name` `Jupiter` or `Galileo`) | `amdgpu_hwmon` | range 3 to 15 W, `download_mode_limit = 6` |
| Legion Go S (`product_name` `83L3`, `83N6`, `83Q2`, `83Q3`) | `firmware_attribute` | `lenovo-wmi-other-0`, profile `custom` |
| Legion Go and Legion Go 2 (`83E1`, `83N0`, `83N1`) | `firmware_attribute` | `lenovo-wmi-other-0`, profile `custom` |
| ROG Ally, Ally X, Xbox Ally X, Xbox Ally X20 (`board_name` `RC71L`, `RC72LA`, `RC73XA`, `RC74XA`) | `firmware_attribute` | `asus-armoury`, profile `performance` ("until custom mode is added") |
| ROG Xbox Ally, non X (`RC73YA`) | `amdgpu_hwmon` | range 4 to 20 W |
| MSI Claw A8 (`MS-1T8K`) | `firmware_attribute` | `msi-wmi-platform`, profile `performance` |
| MSI Claw Intel A1M, 7 AI+, 8 AI+ (`MS-1T41`, `MS-1T42`, `MS-1T52`) | `firmware_attribute` | `msi-wmi-platform`, profile `performance` |
| MSI Claw 8 EX AI+ (`MS-1T91`) | `firmware_attribute` | `msi-wmi-platform`, profile `custom` |

- Also listed with a TDP method: Zotac Gaming Zone. Other device files (Ayaneo, GPD, OneXPlayer and others) have no `[tdp_limit]` block.
- So on current SteamOS every target device has a Steam native TDP control, provided the kernel exposes the named firmware attribute driver. On the Ally family Steam forces the `performance` platform profile when it sets a limit. On Legion it switches to `custom`.
- Which SteamOS build ships which steamos-manager is not confirmed here. Stable SteamOS was 3.8.10 (17 June 2026) per press coverage, with a 3.8.27 beta and a 3.9.1 preview on 14 September 2026. Valve's own release notes page was not reached. Only the Steam Deck, Steam Machine and Legion Go S are "Powered by SteamOS". The others run SteamOS without official support.
- Steam's DMI match for the Steam Deck uses `board_name`, while InputPlumber and SimpleDeckyTDP use `product_name`. Both fields hold `Jupiter` or `Galileo`.
- Advice for the tuning advisor: if a third-party TDP plugin (item 21) is also active, Steam's slider and the plugin will fight. LeGoTDP's 5 s enforce loop exists for exactly that reason.

Sources: https://gitlab.steamos.cloud/holo/steamos-manager/-/tree/master/data/devices , https://phoronix.com/news/SteamOS-3.8.10-Stable , https://tbreak.com/steamos-3-8-steam-machine-handheld-support/ , https://www.warp2search.net/story/steamos-391-preview-and-3827-beta-everything-new-in-the-latest-update/ , https://tech-insider.org/steamos-3-8-third-party-handhelds-2026/ (secondary, used only for the support tiers).

## 23. TDP plugin labels and presets

Status: confirmed for all four. Only LeGoTDP has named presets.

- LeGoTDP 1.7.0 (Rayekkk, archived). Preset labels: `Minimum`, `Silent`, `Balanced`, `Performance`, `Max`, `Custom`. Sliders: `SPL  (Sustained)`, `SPPT (Slow)`, `FPPT (Fast)`, plus `Package draw`, `CPU Boost`, EPP.
- Values (SPL/SPPT/FPPT in W). Legion Go and Go 2 default ladder: Minimum 5/5/10, Silent 8/10/15, Balanced 15/18/25, Performance 25/28/35, Max 35/37/45. Legion Go S ladder: Minimum 5/8/10, Silent 8/10/15, Balanced 18/20/25, Performance 33/33/35, Max 40/43/53.
- The 5 s reapply claim is **confirmed**: README "Re-applies your settings every 5 s if the system overrides them", backend "enforce loop every 5 seconds", and it gives up after a few attempts on targets the hardware refuses. Limits are written through Lenovo WMI (`/sys/class/firmware-attributes/lenovo-wmi-other-0/attributes/ppt_pl1_spl`, `ppt_pl2_sppt`, `ppt_pl3_fppt`) with `ryzenadj` only for the Go 2 extended range up to 50 W.

- SimpleDeckyTDP (aarron-lee, main, last push 25 September 2026): **no named presets**. One slider `TDP (Watts)`, default start TDP 12 W (`DEFAULT_START_TDP`), slider minimum 3 W (`MIN_TDP_RANGE`), maximum per device (`DEFAULT_MAX_TDP` 40, `STEAM_DECK_MAX_TDP` 20, fallback 15). Reapply is `Poll TDP` with `Poll Rate` ("Set TDP every N seconds"), default **15 s** (`DEFAULT_POLL_RATE = 15000`), range 5 to 60 s, and `Enable Background Polling` ("Polling sets TDP every few seconds"). Other labels: `Enable per-game profiles`, `Enable Desktop Profile`, `Minimum TDP`, `Max TDP`, `GPU Mode` (values `BATTERY`, `BALANCE`, `RANGE`, `FIXED`), `Enable CPU Boost`, `Enable SMT`, `CPU Power Governor`, `CPU Energy Performance Preference`, `Always use Max TDP on AC power`, `Lenovo Custom TDP Mode` ("Use WMI for TDP control").
- PowerControl (mengmeet, last push 23 October 2026): **no named presets**. Labels: `Thermal Power (TDP) Limit`, `TDP Backend` (`System Interface`, `System Interface (Legacy)`, `PowerStation`, `RyzenAdj`, `Intel RAPL`), `CPU Boost`, `SMT`, `Number Of CPU Cores`, `GPU Clock Frequency Mode`, `Use per-game Profile`, `Fan Speed`, `Enable Fan Control`. Defaults `DEFAULT_TDP_MIN = 3`, `DEFAULT_TDP_MAX = 25` (custom range), real maximum from the backend `get_tdpMax`. Running app read from `Router.MainRunningApp` every 100 ms.
- PowerTools (NGnius): the GitHub copy is archived (last commit 1 July 2023). Upstream is https://git.ngni.us/NG-SD-Plugins/PowerTools , latest release **v2.0.3 (18 June 2024)**, so it is effectively unmaintained. **No named presets**. Labels: `PowerPlay Limits`, `SlowPPT (W)`, `FastPPT (W)`, `SMT`, `Threads`, `Frequency Limits`, `Minimum (MHz)`, `Maximum (MHz)`, `Governor`, `Charge Limit`, `Charge Mode`, `Downclock Memory`, `Persistent Profile`, `Reapply settings` (a manual button, not a timer).

Sources: https://github.com/aarron-lee/SimpleDeckyTDP/blob/main/src/utils/constants.tsx , https://github.com/aarron-lee/SimpleDeckyTDP/blob/main/defaults/i18n/en.json , https://github.com/mengmeet/PowerControl/blob/main/src/i18n/english.json , https://github.com/mengmeet/PowerControl/blob/main/src/util/settings.ts , https://github.com/NGnius/PowerTools , https://git.ngni.us/api/v1/repos/NG-SD-Plugins/PowerTools/releases , https://github.com/Rayekkk/LeGoTDP/blob/main/README.md , https://github.com/Rayekkk/LeGoTDP/blob/main/main.py , https://github.com/Rayekkk/LeGoTDP/blob/main/src/index.tsx .

### 23b. Settings file formats, for read-only current values

**Status:** confirmed from each tool's source on its default branch. Checked 26 October 2026. tuning-advisor 0.5.0 reads these and never writes them. `<settings>` is `~/homebrew/settings/<plugin folder>`, Decky's `DECKY_PLUGIN_SETTINGS_DIR` for that plugin.

| Tool | File | Per-game entry | Values |
|---|---|---|---|
| SimpleDeckyTDP (commit 2026-09-25) | `<settings>/settings.json` | `tdpProfiles.<appid>`, `default` otherwise. Used only when `enableTdpProfiles` is true | `tdp` in watts. App ID is `Router.MainRunningApp.appid` as text |
| PowerControl (2026-10-23) | `<settings>/config.json`, key `PowerControl` | `perApp.<appid>`, `"0"` otherwise. Used only when `overwrite` is true | `defaultSettig.tdp` in watts with `tdpEnable`. `acStateOverwrite` adds `acStting` and `batSetting` |
| LeGoTDP (2026-09-06) | `<settings>/settings.json` | `game_profiles.<appid>` | `spl`, `sppt`, `fppt` in milliwatts, `preset`, `ac_separate` and `ac_*`. Global values under `settings` |
| Legion Go 2 Companion (2026-10-22) | `<settings>/tdp_settings.json` | `game_profiles.<appid>` | Same as LeGoTDP. Paused profiles under `inactive_game_profiles` |
| Decky LSFG-VK (2026-09-17) | `~/.config/lsfg-vk/conf.toml`, `version = 2` | `[[profile]]` whose `active_in` lists the app ID | `multiplier`, `flow_scale`, `performance_mode`, `pacing_mode` |

Not read, because the format is not stable or not plain: PowerTools (unmaintained), Handheld Daemon (YAML state behind a token), Fantastic (fan curves only), Steam's own TDP limit (no documented store).

Source: https://github.com/aarron-lee/SimpleDeckyTDP/blob/main/py_modules/plugin_settings.py , https://github.com/mengmeet/PowerControl/blob/main/src/util/settings.ts , https://github.com/Rayekkk/LeGoTDP/blob/main/main.py , https://github.com/Rayekkk/LegionGo2Companion/blob/main/tdp_backend.py , https://github.com/xXJSONDeruloXx/decky-lsfg-vk/blob/main/py_modules/lsfg_vk/config_schema.py

## 24. AI provider APIs

Status: confirmed for OpenAI. Corrected for Anthropic (new API version four days ago) and Gemini (`responseSchema` is deprecated).

OpenAI
- Recommended surface: the **Responses API**, `POST https://api.openai.com/v1/responses`. Migration guide: "While Chat Completions remains supported, Responses is recommended for all new projects." The Assistants API "was officially sunset on August 26, 2026".
- Structured output: `text.format` (moved from Chat Completions `response_format`). Shape: `"text": {"format": {"type": "json_schema", "name": "<name>", "schema": {...}, "strict": true}}`.
- Auth: `Authorization: Bearer <key>`. Models list: `GET https://api.openai.com/v1/models`.
- The docs examples now use `gpt-6-astra` ("For new projects, start with gpt-6-astra"). Do not hard-code a model, read the list.

Anthropic
- `POST https://api.anthropic.com/v1/messages`. Headers: `x-api-key: <key>` (or `Authorization: Bearer <key>`, which the API now accepts too), `anthropic-version`, `content-type: application/json`.
- **New API version `2026-10-21`** (released 21 October 2026). It removes `temperature`, `top_p` and `top_k` (400 on every model), and rejects `document` blocks in `assistant` messages and `citations` on user `text` blocks. `2023-06-01` is still accepted ("keep that request on 2023-06-01"). The new SDK majors send `Authorization: Bearer` instead of `X-Api-Key`. Recommendation: send `anthropic-version: 2026-10-21`, and never send sampling parameters.
- Structured output is GA, no beta header: `"output_config": {"format": {"type": "json_schema", "schema": {...}}}`. The old `output_format` is deprecated and needs the beta header `structured-outputs-2025-11-13` or it returns 400. Strict tool use: `"strict": true` on a tool definition.
- Models list: `GET https://api.anthropic.com/v1/models`, params `limit` (default 20, max 1000), `after_id`, `before_id`, `lifecycle` (`active`, `deprecated`, `retired`). Response `data[]` with `id`, `display_name`, `created_at`, `lifecycle`, `line`, `max_input_tokens`, `max_tokens`, `capabilities.structured_outputs.supported`, plus `has_more`, `first_id`, `last_id`. Filter on `capabilities.structured_outputs.supported`.

Google Gemini
- `POST https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent`, header `x-goog-api-key: <key>`. Still documented, with no deprecation notice.
- Correction: in the current API reference **`generationConfig.responseSchema` is marked deprecated** ("Deprecated. Use responseFormat instead"), and so is `_responseJsonSchema`. `responseMimeType` is still there. The new field is `generationConfig.responseFormat`: `{"text": {"mimeType": "APPLICATION_JSON", "schema": {...JSON Schema...}}}`. Deprecated fields still work for now. Send `responseFormat`, and fall back to `responseMimeType: "application/json"` plus `responseJsonSchema` if a model rejects it.
- The structured output guide now leads with a new **Interactions API** (`POST https://generativelanguage.googleapis.com/v1beta/interactions`, body `response_format` with `mime_type: "application/json"`). `generateContent` is listed beside it as a core API.
- `temperature` "is no longer supported and is silently ignored on Gemini 3.6 Flash and newer models".
- Models list: `GET https://generativelanguage.googleapis.com/v1beta/models` (same header). Doc examples use `gemini-3.8-flash`.

All three should be called from the plugin's Python backend, not the CEF frontend, so the key never sits in the Steam client's JS context.

Sources: https://developers.openai.com/api/docs/guides/migrate-to-responses , https://developers.openai.com/api/docs/guides/structured-outputs , https://platform.claude.com/docs/en/build-with-claude/structured-outputs , https://platform.claude.com/docs/en/api/versioning , https://platform.claude.com/docs/en/api/migration-2026-10-21 , https://platform.claude.com/docs/en/api/models/list , https://ai.google.dev/api/generate-content , https://ai.google.dev/gemini-api/docs/structured-output , https://ai.google.dev/api/models .

## 25. FSR 4 on RDNA 3.5 under SteamOS and Proton

Status: corrected on the Windows side, unresolved on the Linux side.

- AMD officially extended **FSR Upscaling 4.1** on 20 October 2026 to RDNA 2 (RX 6000), Ryzen AI Max, Ryzen AI 9 laptops, and handhelds with **Ryzen AI Z2 Extreme, Ryzen Z2 Extreme and Ryzen Z2 A**. Xbox Series X|S is "coming soon". Vulkan support comes with "AMD FSR SDK 2.4", no date. This is a Windows driver announcement. Earlier in 2026 (VideoCardz, about June) AMD had said 4.1 would skip RDNA 3.5 iGPUs, so the brief may hold the old position.
- Not named by AMD: Z1 and Z1 Extreme (RDNA 3, ROG Ally, Legion Go, Legion Go S Z1E), Steam Deck (RDNA 2). Z2 A uses Steam Deck class RDNA 2 silicon, so "Z2 A supported" does not prove the Deck is.
- Linux: Valve shipped FSR 4 for **discrete** RDNA 3 and the Steam Machine through Proton Experimental in June 2026, with no word on iGPUs. FSR 4.1 files for RDNA 3 and 3.5 then surfaced in the Proton Experimental depot (igor'sLAB, TechPowerUp, about June to July 2026), with user reports of it running on the Radeon 890M. No Valve statement or Proton changelog confirming RDNA 3.5 iGPU support was found as of 25 October 2026. `PROTON_FSR4_UPGRADE`, `PROTON_FSR4_RDNA3_UPGRADE` and `PROTON_FSR4_INDICATOR` appear in community builds (Proton-CachyOS, Proton-EM) per forum posts, not in Valve's notes.
- Advice: the advisor should say "FSR 4 on this device under Proton is unofficial" for every target handheld today, offer the OptiScaler route (Decky-Framegen, item 21) as the community path, and recheck the Proton Experimental changelog before release.

Sources: https://www.gamingonlinux.com/2026/10/amd-fsr-upscaling-4-1-expands-support-to-older-desktops-laptops-handhelds-consoles-and-vulkan/ , https://www.gamingonlinux.com/2026/06/amd-fsr-4-lands-on-rdna3-dgpus-for-linux-steamos-and-steam-machine-via-proton-experimental/ , https://videocardz.com/newz/amd-fsr-4-1-to-skip-rdna-3-5-integrated-graphics , https://www.techpowerup.com/350170/leaked-fsr-4-1-int8-model-confirms-compatibility-with-rdna-3-5 , https://www.igorslab.de/en/valve-fsr-4-1-proton-experimental-rdna-3-3-5/ , https://discuss.cachyos.org/t/fsr4-on-rdna3-with-proton-cachyos-env-vars-4-0-0-vs-4-0-2-and-where-the-dlls-are-cached/19391 .

## 26. Plugin backend process isolation

**Status:** confirmed, with a caveat. Checked 25 October 2026.

Each plugin backend runs in its own `multiprocessing.Process` (`backend/decky_loader/plugin/plugin.py`, `sandboxed_plugin.py`), so two plugins' `plugin_core` copies never share an interpreter. The caveat: the loader appends `py_modules` to `sys.path`. A vendored module named like a standard library or loader module would lose. All vendored packages use unique names (`plugin_core`, `qbtmon`, `sabmon`, `advisor`) and modules inside them are imported by package path. The loader is built with Python 3.14.8 and declares `>=3.10,<3.15`. CI tests on 3.10 and 3.14.

Source: https://github.com/SteamDeckHomebrew/decky-loader/blob/main/backend/decky_loader/plugin/sandboxed_plugin.py, https://github.com/SteamDeckHomebrew/decky-loader/blob/main/backend/pyproject.toml

## Name checks

Status: partly confirmed.

- GitHub: `breakmylegs/qbittorrent-monitor`, `breakmylegs/sabnzbd-monitor` and `breakmylegs/tuning-advisor` all return 404, so all three are free.
- Decky Plugin Store: `https://plugins.deckbrew.xyz/plugins` is **blocked by the corporate web filter** here ("Elevated Exposure"), so the live store JSON could not be read. Fallback: the store's source database (SteamDeckHomebrew/decky-plugin-database, `plugins/`, 127 entries, last push 23 October 2026) has no entry matching qbit, torrent, sab, nzb, usenet, tuning or advis. GitHub repo search for "decky qbittorrent" and "decky sabnzbd" returns nothing. Recheck the live JSON from an unfiltered network before submission.
- Suggestion: "tuning-advisor" is generic. Consider `handheld-tuning-advisor` or `decky-tuning-advisor` for search clarity.

## Still open

| Item | What is left |
|---|---|
| 13 | Capture fixtures from a live 5.3 server with `tools/capture_fixture.py` and test against them. Source review is done |
| 15 | Capture fixtures from a live 5.1.3 server. Confirm `have_warnings` and `speedlimit` sit in the queue root |
| 20 | MSI Claw rows are reference values (marked R). MSI's spec pages return HTTP 403 to automated requests. Check them in a browser |
| 24 | Built in tuning-advisor 0.3.0 from these findings. Test replies are shaped from each provider's documented format, not recorded live. Capture one real reply per provider with a spending-limited key and add it as a fixture |
| 25 | FSR 4.1 is official on Z2 chips under Windows only. Under Proton it stays unofficial, so FSR 4 is still never recommended |
| 10 | No clipboard API. tuning-advisor 0.2.0 tries `navigator.clipboard`, then the `execCommand` fallback, and says when both fail. Confirm which works on a device |
