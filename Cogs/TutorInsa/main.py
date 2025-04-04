# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import sqlite3

from discord import app_commands
from discord.ext import commands

from GlobalModules.HasPerm import has_perm


# === DO NOT CHANGE CLASS NAME OR __init__ PARAMETERS === #
class TutorInsa(commands.GroupCog):
    def __init__(self, bot: commands.AutoShardedBot, database: sqlite3.Connection):
        self.bot: bot = bot
        self.database = database


# === DO NOT REMOVE THE FOLLOWING OR CHANGE PARAMETERS === #

async def setup(bot: commands.AutoShardedBot, database: sqlite3.Connection):
    await bot.add_cog(TutorInsa(bot, database))

