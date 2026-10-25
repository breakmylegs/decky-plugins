"""Decky entry point for tuning-advisor. Scaffold only. Built in phase 1 after qbittorrent-monitor."""

import decky


class Plugin:
    async def _main(self):
        decky.logger.info("tuning-advisor scaffold loaded")

    async def _unload(self):
        pass

    async def _uninstall(self):
        pass
