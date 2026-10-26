# Privacy

What each plugin stores, sends and logs.

## All plugins

- Settings live in `~/homebrew/settings/<plugin-id>/settings.json`. Keys and passwords live in `secrets.json` in the same folder. Both files are readable by your user only (mode 600).
- Secret values never leave the backend. The panel shows whether a secret is set and its last four characters when it is long enough.
- Secrets never appear in logs, error messages or events.
- Import from file reads `~/Documents/decky-import/<plugin-id>.json`. After a successful import the plugin asks you to delete the file. Delete it, because it holds your credentials in plain text.
- Uninstalling keeps your settings unless you turn on "Remove settings on uninstall".

### Update check

Once a day each plugin asks `api.github.com` for the latest release of its own mirror repo. GitHub sees your IP address and a standard request. Nothing about your setup is sent. Turn it off with "Check for updates daily".

## qbittorrent-monitor

Talks only to the qBittorrent address you enter. It sends your API key or password to that server and nowhere else. It reads torrent names, sizes, states and speeds and shows them in the panel. Nothing is stored apart from settings and secrets.

## sabnzbd-monitor

Talks only to the SABnzbd address you enter, with your API key. Same rules as above.

## tuning-advisor

As of 0.5.0:

- Reads device facts from `/sys/class/dmi/id/`, `/proc/cpuinfo` and `/etc/os-release`. Serial numbers and UUIDs are never read.
- Reads other Decky plugins' `plugin.json` files to detect your tuning tools, and the settings files of SimpleDeckyTDP, PowerControl, LeGoTDP, Legion Go 2 Companion and Decky LSFG-VK to show your current values. It never writes to them, and nothing from them leaves the device.
- Sends the Steam app ID of the selected game to Deck Verified to fetch community reports. Responses are cached for 7 days.
- ProtonDB, off by default. When on, downloads one index file (about 2 MB) from this project's GitHub release, then again after 31 days. Lookups happen on the device. Nothing about you or your game is sent.
- PCGamingWiki, off by default. When on, signs in with your own bot password and sends the game's Steam app ID (or its name for non-Steam games) to pcgamingwiki.com. Answers are cached for 7 days. The bot password lives in `secrets.json` with the AI keys and never reaches the panel.
- Your current launch options and compatibility tool are read from the Steam client to show and merge. They stay on the device.
- AI recommendations are optional and off until you pick a provider and add your own API key. Nothing is sent until you press Generate AI recommendation.
- Each request sends the game name, Steam app ID, the device profile (model, chip, screen, TDP range), your selected tools, and up to 6 short report excerpts. Home folder paths and links in report text are removed first. No host names, no other plugins' secrets, no user identifiers, no API keys of other providers.
- Requests go straight from the plugin's backend to the provider: api.openai.com, api.anthropic.com or generativelanguage.googleapis.com. There is no proxy. The provider's own data terms apply.
- Keys live in `~/homebrew/settings/tuning-advisor/secrets.json` (mode 600). The panel only sees whether a key is set and its last four characters.
- Replies are cached on the device for 7 days. An optional daily limit caps how many requests are sent.
- Use a dedicated API key with a spending limit.
