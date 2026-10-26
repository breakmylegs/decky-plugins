# Data sources

Every source is credited on screen next to its data and here.

| Source | Used by | Access | Licence | Status |
|---|---|---|---|---|
| qBittorrent WebUI API | qbittorrent-monitor | Your own server | n/a | In use |
| SABnzbd API | sabnzbd-monitor | Your own server | n/a | In use |
| Deck Verified (DeckSettings) | tuning-advisor | Live API with a 7-day cache | GPL-3.0 (VERIFICATION.md item 16) | In use |
| ProtonDB data dumps | tuning-advisor | Monthly dump, indexed by `tools/protondb_index.py` on this machine, published to the monorepo release `protondb-index`, downloaded by the plugin when the source is on | ODbL 1.0 database, DbCL 1.0 contents. The index is shared under the ODbL | In use, off by default |
| PCGamingWiki | tuning-advisor | Cargo API with your own bot password, 7-day cache, two queries per game | CC BY-NC-SA. Shown with attribution and a link | In use, off by default |
| SteamDeckHQ, ShareDeck | tuning-advisor | Link out only | No reuse licence | Never scraped or cached |
| Handheld Daemon, InputPlumber | tuning-advisor device registry | DMI match strings | See each repo | Credited per entry in `sources` |
