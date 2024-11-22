import json
import sqlite3
from typing import Optional, Dict, Any

import aiohttp
from discord.ext import commands, tasks

from GlobalModules.GetConfig import get_config


# class Packages(commands.GroupCog):
class Packages(commands.Cog):  # Passed under commands.cog since there is no commands inside this cog
    def __init__(self, bot: commands.AutoShardedBot, database: sqlite3.Connection):
        self.bot: bot = bot
        self.database = database

        self.version = {}

        with open("requirements.txt", "r") as file:
            for line in file:
                if "==" in line and "#" not in line:
                    self.version[line.split("==")[0]] = line.split("==")[1].replace("\n", "")

        self.notify_update.start()

    def cog_unload(self) -> None:
        self.notify_update.stop()

    @staticmethod
    async def get_package_info(package: str) -> Optional[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://pypi.org/pypi/{package}/json") as response:
                if response.status == 200:
                    return json.loads(await response.text())
                else:
                    return None

    @tasks.loop(minutes=get_config("Packages.UpdateDelayMin"))
    async def notify_update(self):
        for name, ver in self.version.items():
            desc = await self.get_package_info(name)

            if desc is not None:
                ver = desc["info"]["version"]

                if ver != self.version[name]:
                    channel = await self.bot.fetch_channel(get_config("Packages.Channel"))
                    await channel.send(
                        f"New {name} version available: {ver} (actual: {self.version[name]}) "
                        f"{get_config('Packages.Mention')}"
                    )

                    self.version[name] = ver


async def setup(bot: commands.AutoShardedBot, database: sqlite3.Connection):
    await bot.add_cog(Packages(bot, database))
