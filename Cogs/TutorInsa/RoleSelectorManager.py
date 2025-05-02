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
        msg = await self.send_message(inte.channel)

        self.db.execute(
            "INSERT INTO TUTOR_ROLES_SELECTOR (MESSAGE_ID,CHANNEL_ID,GUILD_ID) VALUES (?,?,?);",
            (msg.id, inte.channel_id, inte.guild_id)
        )
        self.db.commit()

    async def modify_callback(self, inte: Interaction):
        if inte.user.id != self.author.id:
            await inte.response.send_message("You do not have permission to interact here", ephemeral=True)
            return

        await inte.response.send_message("Modify", ephemeral=True)

    @staticmethod
    async def send_message(channel: discord.TextChannel) -> discord.Message:
        return await channel.send("TODO SEND_MESSAGE")

    async def selector_callback(self):
        pass  # TODO
