import sqlite3

import discord
from discord.ext import commands

from Core.CogManager import CogManager
from GlobalModules.GetConfig import get_config
from GlobalModules.Paginator import Paginator


class CogsCommands:
    def __init__(self, bot: commands.AutoShardedBot, database: sqlite3.Connection):
        self.bot = bot
        self.db = database
        self.cogManager = CogManager(bot, database)

    async def list(self, ctx: commands.Context):
        loaded = []
        unloaded = []
        disabled = []

        for name, state in self.cogManager.list_cog().items():
            if state is True:
                loaded.append(name)

            elif state is False:
                unloaded.append(name)

            else:
                disabled.append(name)

        paginator = Paginator(self.db)

        for i in [('Loaded', loaded), ('Unloaded', unloaded), ('Disabled', disabled)]:
            if len(i[1]) > 0:
                e = discord.Embed(title="Cogs list")

                if i[0] == "Loaded":
                    e.colour = 0x00FF00

                elif i[0] == "Unloaded":
                    e.colour = 0xFF0000

                else:
                    e.colour = 0xFFFF00

                e.add_field(
                    name=f"{i[0]} ({len(i[1])}/{len(loaded) + len(unloaded) + len(disabled)})",
                    value="\n".join([f"- {j}" for j in i[1]])
                )

                paginator.add_page(e, f"{i[0]} cogs")

        if len(paginator.pages) > 0:
            await paginator.send_paginator(ctx)

        else:
            await ctx.send("No cogs are loaded in this instance")

    async def unload(self, ctx: commands.Context, *args):
        if len(args) == 0:
            return await ctx.send("Please give at least 1 cog name in command (type `*` to target all cogs)")

        cog_list = list(args)
        success = {}

        for i in args:
            if i == "*":
                cog_list = [j[0] for j in self.cogManager.list_cog().items() if j[1] is True]

                if len(cog_list) == 0:
                    return await ctx.send("No cogs are currently loaded")

        for i in cog_list:
            if i in self.bot.cogs.keys():
                status = await self.cogManager.unload_cog(i)
            else:
                status = None

            if status is True:
                success.update({f"- {i}": True})

            elif status is None:
                success.update({f"- {i} [This cog isn't loaded]": False})

            else:
                success.update({f"- {i} [Check logs]": False})

        paginator = Paginator(self.db)

        for i in [("Success", True), ("Error", False)]:
            act = [j[0] for j in success.items() if j[1] is i[1]]

            if len(act) > 0:
                e = discord.Embed(title="Cogs unload")

                if i[1] is True:
                    e.colour = 0x00FF00

                else:
                    e.colour = 0xFF0000

                e.add_field(
                    name=f"{i[0]} ({len([j for j in success.values() if j is i[1]])}/{len(success)})",
                    value="\n".join([j[0] for j in success.items() if j[1] is i[1]])
                )

                paginator.add_page(e, i[0])

        await paginator.send_paginator(ctx)
        await self.bot.tree.sync()

    async def reload(self, ctx: commands.Context, *args):
        if len(args) == 0:
            return await ctx.send("Please give at least 1 cog name in command (type `*` to target all cogs)")

        cog_list = list(args)
        disabled_cogs = []
        success = {}

        for i in args:
            if i == "*":
                cog_list = [k for k in self.cogManager.list_cog().keys() if k not in get_config("core.disabled_cogs")]
                disabled_cogs = get_config("core.disabled_cogs")

                if len(cog_list) == 0:
                    return await ctx.send("You can't load any cogs")

        for i in cog_list:
            if i in self.bot.cogs.keys():
                status_unload = await self.cogManager.unload_cog(i)

            else:
                status_unload = None

            if status_unload is True or status_unload is None:
                status_load = await self.cogManager.load_cog(i)

            else:
                status_load = False

            if status_unload is True and status_load:
                success.update({f"- {i} [Reloaded]": True})

            elif status_unload is None and status_load:
                success.update({f"- {i} [Loaded]": True})

            elif status_unload is False:
                success.update({f"- {i} [Couldn't unload this cog, check logs]": False})

            elif status_unload is True and status_load is False:
                success.update({f"- {i} [Cog unloaded but couldn't be reloaded, check logs]": False})

            elif status_unload is None and status_load is False:
                success.update({f"- {i} [Couldn't load this cog, check logs]": False})

        for i in disabled_cogs:
            if i in self.bot.cogs.keys():
                status_unload = await self.cogManager.unload_cog(i)

                if status_unload:
                    success.update({f"- {i} [Cog unloaded, load disabled by config, load it manually if needed]": True})

                else:
                    success.update({f"- {i} [Couldn't unload this cog, check logs]": False})

        paginator = Paginator(self.db)

        for i in [("Success", True), ("Error", False)]:
            act = [j[0] for j in success.items() if j[1] is i[1]]

            if len(act) > 0:
                e = discord.Embed(title="Cogs reload")

                if i[1] is True:
                    e.colour = 0x00FF00

                else:
                    e.colour = 0xFF0000

                e.add_field(
                    name=f"{i[0]} ({len([j for j in success.values() if j is i[1]])}/{len(success)})",
                    value="\n".join([j[0] for j in success.items() if j[1] is i[1]])
                )

                paginator.add_page(e, i[0])

        await paginator.send_paginator(ctx)
        await self.bot.tree.sync()
