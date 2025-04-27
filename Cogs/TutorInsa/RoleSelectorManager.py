# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import sqlite3

import discord
from discord import Interaction


class RoleSelectorManager:
    def __init__(self, db: sqlite3.Connection, guild: discord.Guild, author: discord.Member):
        self.db: sqlite3.Connection = db
        self.guild: discord.Guild = guild
        self.author: discord.Member = author

    async def add(self, inte: Interaction):
        pass

    async def modify_callback(self, inte: Interaction):
        if inte.user.id != self.author.id:
            await inte.response.send_message("You do not have permission to interact here", ephemeral=True)
            return

        await inte.response.send_message("Modify", ephemeral=True)
