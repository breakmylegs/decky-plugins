"""Decky entry point for sabnzbd-monitor. Scaffold only. Built in phase 1 after qbittorrent-monitor."""

import decky


class Plugin:
    async def _main(self):
        decky.logger.info("sabnzbd-monitor scaffold loaded")

    async def _unload(self):
        pass

    async def _uninstall(self):
        pass
