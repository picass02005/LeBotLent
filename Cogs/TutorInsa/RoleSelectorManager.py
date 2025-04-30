# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import sqlite3

import discord
from discord import Interaction

from Cogs.TutorInsa.ConfirmSelect import ConfirmSelector


class RoleSelectorManager:
    def __init__(self, db: sqlite3.Connection, guild: discord.Guild, author: discord.Member):
        self.db: sqlite3.Connection = db
        self.guild: discord.Guild = guild
        self.author: discord.Member = author

    async def add(self, inte: Interaction):
        v = discord.ui.View()
        v.add_item(ConfirmSelector(inte.user, self.add_callback))

        await inte.response.send_message(
            "Are you sure you want to add a role selector in this channel?",
            view=v,
            ephemeral=True
        )

    async def add_callback(self, inte: Interaction) -> None:
        await inte.followup.send("TODO ADD", ephemeral=True)
        # TODO: add in db + send message

    async def modify_callback(self, inte: Interaction):
        if inte.user.id != self.author.id:
            await inte.response.send_message("You do not have permission to interact here", ephemeral=True)
            return

        await inte.response.send_message("Modify", ephemeral=True)
