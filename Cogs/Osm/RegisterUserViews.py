# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import sqlite3
from typing import Any

import discord
from discord import Interaction

from Cogs.Osm.Py_OSM_API import OSMUser
from Cogs.Osm.Py_OSM_API import PyOSM
from Cogs.Osm.RegisterUserInDB import register_user_in_db
from GlobalModules.GetConfig import get_config


class RegisterSelectSelector(discord.ui.Select):
    def __init__(self, py_osm: PyOSM, user_id: int, database: sqlite3.Connection):
        self.py_osm = py_osm
        self.user_id = user_id
        self.db = database

        placeholder = "Select which method you want to use"

        options = [
            discord.SelectOption(
                label="With your user name",
                value="name",
                description="You will have to fill your OSM user name"
            ),
            discord.SelectOption(
                label="With your user ID (UID)",
                value="uid",
                description="You will have to fill your OSM UID"
            )
        ]

        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, inte: Interaction) -> Any:
        if inte.user.id != self.user_id:
            return await inte.response.send_message("Only the author can answer this", ephemeral=True)

        if inte.data['values'][0] == "uid":
            modal = RegisterUID(self.py_osm, self.db)

        else:
            modal = RegisterUName(self.py_osm, self.db)

        self.disabled = True
        view = discord.ui.View()
        view.add_item(self)

        await inte.response.send_modal(modal)
        await inte.edit_original_response(view=view)


class RegisterUID(discord.ui.Modal):
    uid = discord.ui.TextInput(
        label="Copy and paste your Open Street Map UID here",
        style=discord.TextStyle.short,
        placeholder="123456",
        required=True,
        max_length=10
    )

    def __init__(self, py_osm: PyOSM, database: sqlite3.Connection):
        super().__init__(title="Register OSM user")
        self.py_osm = py_osm
        self.db = database

    async def on_submit(self, inte: Interaction, /) -> None:
        if not self.uid.value.isdigit():
            await inte.response.send_message(
                "Your UID consist of only digits\nPlease retry with your valid UID",
                ephemeral=True
            )
            return

        await inte.response.defer(thinking=True, ephemeral=True)

        osm_user = await self.py_osm.fetch_user_info(self.uid.value)

        if osm_user is None:
            await inte.followup.send(
                "Unable to find this account\nPlease double check you copy pasted it right and retry",
                ephemeral=True
            )
            return

        view = discord.ui.View()
        view.add_item(ConfirmationSelector(inte.user.id, self.db, osm_user, self.py_osm))

        await inte.followup.send(embed=ConfirmationSelector.make_embed(osm_user), ephemeral=True, view=view)


class RegisterUName(discord.ui.Modal):
    uname = discord.ui.TextInput(
        label="[CASE SENSITIVE] Put your OSM name below",
        style=discord.TextStyle.short,
        placeholder="Steve",
        required=True,
        max_length=100
    )

    def __init__(self, py_osm: PyOSM, database: sqlite3.Connection):
        super().__init__(title="Register OSM user")
        self.py_osm = py_osm
        self.db = database

    async def on_submit(self, inte: Interaction, /) -> None:
        uid = await self.py_osm.get_uid_with_changeset(self.uname.value)

        if uid == -1:
            await inte.response.send_message(
                "Couldn't fetch your user\nPlease check the spelling and caps\n\n"
                "This may occurs if you never have made any changesets.\n"
                "We recommend you using the register method by UID if that's the case",
                ephemeral=True
            )
            return

        await inte.response.defer(thinking=True, ephemeral=True)

        osm_user = await self.py_osm.fetch_user_info(uid)

        if osm_user is None:
            await inte.followup.send(
                "Unable to find this account\n"
                "Please double check your account name have no misspelling or missplaced caps\n"
                "If this issue keep occuring, please try to register with your UID directly",
                ephemeral=True
            )
            return

        view = discord.ui.View()
        view.add_item(ConfirmationSelector(inte.user.id, self.db, osm_user, self.py_osm))

        await inte.followup.send(embed=ConfirmationSelector.make_embed(osm_user), ephemeral=True, view=view)


class ConfirmationSelector(discord.ui.Select):
    @staticmethod
    def make_embed(user: OSMUser) -> discord.Embed:
        e = discord.Embed(
            title="Please confirm this is your account",
            description=f"User name: `{user.display_name}`\n"
                        f"UID: `{user.uid}`\n"
                        f"Account created on: <t:{int(user.account_created.timestamp())}:D>",
            color=get_config("core.base_embed_color")
        )

        e.set_footer(text=user.display_name, icon_url=user.pfp_link if user.pfp_link else None)

        return e

    def __init__(self, user_id: int, database: sqlite3.Connection, osm_user: OSMUser, py_osm: PyOSM):
        self.user_id = user_id
        self.db = database
        self.osm_user = osm_user
        self.py_osm = py_osm

        placeholder = "Yes / No"

        options = [
            discord.SelectOption(
                label="Yes",
                value="1"
            ),
            discord.SelectOption(
                label="No",
                value="0"
            )
        ]

        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, inte: Interaction) -> Any:
        if inte.user.id != self.user_id:
            return await inte.response.send_message("Only the author can answer this", ephemeral=True)

        self.disabled = True
        view = discord.ui.View()
        view.add_item(self)

        await inte.response.edit_message(view=view)

        if inte.data['values'][0] == "1":
            await inte.followup.send("Adding yourself into database, this can take up to 2 minute...", ephemeral=True)

            try:
                await register_user_in_db(self.user_id, inte.guild_id, self.osm_user, self.py_osm, self.db)
                msg = "Your OSM account was successfully linked"

            except Exception as err:
                msg = f"An error occured while adding yourself into DB: `{type(err)}: {err}`"

            await inte.followup.send(msg, ephemeral=True)


        else:
            await inte.followup.send("Cancelled", ephemeral=True)
