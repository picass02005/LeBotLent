# SPDX-License-Identifier: MIT
# Copyright (C) 2024 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import os
import sqlite3
import time

import discord
from discord.ext import commands
from discord.ext import tasks

from Core.CogManager import CogManager
from Core.CommandPrefix import CommandPrefix
from Core.Commands.CogsCommands import CogsCommands
from Core.Commands.Help import Help
from Core.Commands.Stop import Stop
from Core.Commands.Sync import sync_command
from Core.DatabaseChecker import check_database
from Core.ErrorHandler import ErrorHandler
from Core.GetToken import get_token
from Core.IsTestVersion import is_test_version
from GlobalModules.GetConfig import get_config
from GlobalModules.HasPerm import has_perm
from GlobalModules.Logger import Logger
from GlobalModules.Paginator import Paginator
from GlobalModules.TempManager import TempManager

commandPrefix = CommandPrefix()

# noinspection PyTypeChecker
bot = commands.AutoShardedBot(
    intents=discord.Intents.all(),
    command_prefix=commandPrefix.prefix_callback
)

if not os.path.isdir(get_config("core.data.folder")):
    os.mkdir(get_config("core.data.folder"))

database = sqlite3.connect(f"{get_config('core.data.folder')}/{get_config('core.data.database')}")
logger = Logger(database)
errorHandler = ErrorHandler(database, bot)

TEST_VERSION = is_test_version(print_message=True)

if os.name == 'nt' and not TEST_VERSION:
    print(f"\033[93mWARNING: Data folder can be found in C:{get_config('core.data.folder')}\033[0m")


@bot.event
async def on_ready():
    logger.add_log("Core", f"Bot connected: {bot.user} (ID: {bot.user.id})")

    logger.add_log("Core", f"Syncing global command tree")
    await bot.tree.sync()

    logger.add_log("Core", f"Syncing per-guild command tree")
    for i in bot.guilds:
        await bot.tree.sync(guild=i)

    logger.add_log("Core", f"Every command tree synced")


@bot.event
async def setup_hook() -> None:
    check_database(database)

    disabled_by_config = get_config("core.disabled_cogs")

    for key, value in cogManager.list_cog().items():
        if not value and key not in disabled_by_config:
            await cogManager.load_cog(key)

    remove_old_paginator.start()
    clear_temp_files.start()
    purge_logs.start()


@bot.event
async def on_interaction(inter: discord.Interaction):
    await Paginator(database).process_interaction(inter)


@bot.event
async def on_socket_event_type(event_type: str):
    if event_type == "PRESENCE_UPDATE":
        return

    elif event_type == "TYPING_START":
        return

    elif "MESSAGE" in event_type:
        return

    logger.add_log("SOCKET_EVENT", event_type.capitalize())


bot.tree.on_error = errorHandler.app_command_error


@bot.event
async def on_command_error(ctx, exception):
    if not isinstance(exception, discord.ext.commands.errors.CommandNotFound):
        await errorHandler.command_error(ctx, exception)


@bot.event
async def on_message(message):
    if message.author.id in commandPrefix.get_allowed_users() and bot.user.mentioned_in(message):
        await message.channel.send(f"My prefix is `{commandPrefix.get_prefix()}`")

    await bot.process_commands(message)


@tasks.loop(minutes=5)
async def remove_old_paginator():
    if not bot.is_ready():
        return

    query = "SELECT MESSAGE_ID, CHANNEL_ID FROM PAGINATOR WHERE DELETE_TS < ?"
    for values in database.execute(query, (int(time.time()),)).fetchall():
        msg = bot.get_channel(values[1]).get_partial_message(values[0])
        await Paginator(database).remove_paginator(msg)


@tasks.loop(minutes=30)
async def clear_temp_files():
    TempManager.purge_temp()


@tasks.loop(hours=6)
async def purge_logs():
    database.execute(
        "DELETE FROM LOGS WHERE TIMESTAMP<?;",
        (int(time.time()) - get_config("core.logs_delete_after"),)
    )
    database.commit()


cogManager = CogManager(bot, database)
cogsCommands = CogsCommands(bot, database)


@bot.command(name="cogs_list", brief="Show all cogs in this instance")
@has_perm(database)
async def cogs_list(ctx: discord.ext.commands.Context):
    await cogsCommands.list(ctx)


@bot.command(
    name="cogs_reload",
    aliases=["cogs_load"],
    brief="(Re)load every cogs given as argument (if * given, (re)load every cogs which aren't disabled)"
)
@has_perm(database)
async def cogs_reload(ctx: discord.ext.commands.Context, *args):
    await cogsCommands.reload(ctx, *args)


@bot.command(name="cogs_unload", brief="Unload every cogs given as argument (if * given, unload every cogs)")
@has_perm(database)
async def cogs_unload(ctx: discord.ext.commands.Context, *args):
    await cogsCommands.unload(ctx, *args)


@bot.command(name="sync", brief="Sync comands tree (if guild_only = True, sync only the local tree)")
@has_perm(database)
async def sync(ctx: discord.ext.commands.Context, guild_only: bool = False):
    await sync_command(bot, logger, ctx, guild_only)


@bot.command(name="get_tb", brief="Get a full traceback with its ID")
@has_perm(database)
async def get_tb(ctx: discord.ext.commands.Context, error_id: int):
    await errorHandler.get_tb_command(ctx, error_id)


@bot.command(name="stop", brief="Stop this bot instance")
@has_perm(database)
async def stop(ctx: discord.ext.commands.Context):
    await Stop(ctx).stop_command()


help_ = Help(bot, database)
bot.remove_command("help")


@bot.command(name="help", brief="Show the help of the bot")
@has_perm(database)
async def help_command(ctx: commands.Context):
    await help_.ctx_command(ctx)


@bot.tree.command(name="help", description="Show the help of the bot")
@has_perm(database)
async def help_app_command(inte: discord.Interaction):
    await help_.app_command(inte)


if TEST_VERSION:
    bot.run(token=get_token())

else:
    bot.run(token=get_token(), log_handler=None)
