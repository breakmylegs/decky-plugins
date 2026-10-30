# Data sources

Every source is credited on screen next to its data and here.

| Source | Used by | Access | Licence | Status |
|---|---|---|---|---|
| qBittorrent WebUI API | qbittorrent-monitor | Your own server | n/a | In use |
| SABnzbd API | sabnzbd-monitor | Your own server | n/a | In use |
| Deck Verified (DeckSettings) | tuning-advisor | Live API with a 7-day cache | GPL-3.0 (VERIFICATION.md item 16) | In use |
| ProtonDB data dumps | tuning-advisor | Monthly dump, indexed by `tools/protondb_index.py` on this machine, published to the monorepo release `protondb-index`, downloaded by the plugin when the source is on | ODbL 1.0 database, DbCL 1.0 contents. The index is shared under the ODbL | In use, off by default |
| PCGamingWiki | tuning-advisor | Cargo API with your own bot password, 7-day cache, two queries per game | CC BY-NC-SA. Shown with attribution and a link | In use, off by default |
| Are We Anti-Cheat Yet | tuning-advisor | Whole `games.json` from the project's GitHub repo, at most weekly, looked up on the device | MIT. Notice shown on screen. The site's logos come from SteamGridDB and are not used | In use, on by default |
| SteamDeckHQ, ShareDeck | tuning-advisor | Link out only | No reuse licence | Never scraped or cached |
| Handheld Daemon, InputPlumber | tuning-advisor device registry | DMI match strings | See each repo | Credited per entry in `sources` |

## Checked and left out

These were looked at for tuning-advisor on 30 October 2026 and not used.

- ProtonDB per-game summaries (`protondb.com/api/v1/reports/summaries/<appid>.json`). Undocumented, with no published terms. The ODbL covers only the monthly dumps, which the plugin already uses.
- Valve's Deck compatibility report (`store.steampowered.com/saleaction/ajaxgetdeckappcompatibilityreport`). Undocumented, and the Steam Web API terms cover only the documented APIs.
- Deck Verified game search (`search_games`). Allowed, but its results were too loose to be useful. A search for "cyberpunk" did not return Cyberpunk 2077.
- HowLongToBeat, SteamDB, SteamGridDB art, and the OptiScaler and lsfg-vk compatibility lists. No API or no reuse licence that fits.
