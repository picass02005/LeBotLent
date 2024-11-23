import importlib
import inspect
import os
import sqlite3
from typing import Dict

from discord import AppCommandType
from discord.ext import commands

from GlobalModules.GetConfig import get_config
from GlobalModules.Logger import Logger


class CogManager:
    def __init__(self, bot: commands.AutoShardedBot, database: sqlite3.Connection) -> None:
        """
        :param bot: The bot instance
        """

        self.bot = bot
        self.database = database

        self.logger = Logger(self.database)

    def list_cog(self) -> Dict[str, bool]:
        """
        List all cogs and indicate if they are loaded or not
        :return: A dict with all cogs, boolean value indicate if it's loaded or not. Will be None if unloaded + disabled
        """

        ret = {}
        disabled_cogs = get_config("core.disabled_cogs")

        for cog_name in os.listdir("Cogs"):
            if cog_name in disabled_cogs:
                ret.update({cog_name: None})

            else:
                ret.update({cog_name: False})

        for cog_name in self.bot.cogs:
            ret.update({cog_name: True})

        return dict(sorted(ret.items()))

    async def load_cog(self, cog_name: str) -> bool:
        """
        Load a cog by its name
        :param cog_name: The cog to load
        :return: Boolean indicating if it was loaded successfully or not
        """

        try:
            cog = importlib.import_module(f"Cogs.{cog_name}.main")
            importlib.reload(cog)
            await eval("cog.setup")(self.bot, self.database)

            self.logger.add_log("CogManager", f"Successfully loaded cog {cog_name}")

            return True

        except Exception as err:
            self.logger.add_log("CogManager", f"Couldn't load cog {cog_name}: {type(err)} : {err}")

            return False

    async def unload_cog(self, cog_name: str) -> bool:
        """
        Unload a cog by its name
        :param cog_name: The cog to unload
        :return: Boolean indicating if it was unloaded successfully or not
        """

        try:
            if cog_name not in self.bot.cogs.keys():
                raise ValueError(f"Cog {cog_name} is not loaded")

            if isinstance(self.bot.cogs[cog_name], commands.GroupCog):
                guilds_none = list(self.bot.guilds)
                guilds_none.append(None)

                for guild in guilds_none:
                    # === Remove message and user context based commands === #

                    for cmd_type in (AppCommandType.message, AppCommandType.user):
                        for i in self.bot.tree.get_commands(type=cmd_type, guild=guild):
                            if inspect.getfile(i.callback) == inspect.getfile(self.bot.cogs[cog_name].__class__):
                                self.bot.tree.remove_command(i.name, type=i.type)

                    # === Remove cog group === #

                    for i in self.bot.tree.get_commands(guild=guild):
                        if i.name.lower().replace("-", "") == cog_name.lower():
                            self.bot.tree.remove_command(i.name, guild=guild)

            await self.bot.remove_cog(cog_name)

            self.logger.add_log("CogManager", f"Successfully unloaded cog {cog_name}")

            return True

        except Exception as err:
            self.logger.add_log("CogManager", f"Couldn't unload cog {cog_name}: {type(err)} : {err}")

            return False
