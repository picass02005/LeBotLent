# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import json
import sqlite3
from typing import Any, Tuple

import discord.ui
from discord import Interaction

from Cogs.Osm.Py_OSM_API import OSMUser


class UnregisterView(discord.ui.View):
    def __init__(self, db: sqlite3.Connection, osm_user: OSMUser, on_guild: bool, guild_nb: int, user_id: int):
        self.db = db
        self.osm_user = osm_user
        self.user_id = user_id

        super().__init__()

        super().add_item(UnregisterSelect(self.user_id, self.db, self.osm_user, on_guild, guild_nb))


class UnregisterSelect(discord.ui.Select):
    def __init__(self, user_id: int, database: sqlite3.Connection, osm_user: OSMUser, on_guild: bool, guild_nb: int):
        self.user_id = user_id
        self.db = database
        self.osm_user = osm_user

        placeholder = "Choose an action"

        options = []

        # G: Only this guild
        # A: From whole db
        # C: Cancel

        if on_guild:
            if guild_nb > 1:
                options.append(discord.SelectOption(label="Unregister only for this guild", value="G"))

            else:
                options.append(discord.SelectOption(label="Unregister your account", value="A"))

        if guild_nb > 1 or not on_guild:
            options.append(discord.SelectOption(label="Unregister for every guild", value="A"))

        options.append(discord.SelectOption(label="Cancel", value="C"))

        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, inte: Interaction) -> Any:
        if inte.user.id != self.user_id:
            return await inte.response.send_message("Only the author can answer this", ephemeral=True)

        self.disabled = True
        view = discord.ui.View()
        view.add_item(self)

        await inte.response.edit_message(view=view)

        match inte.data['values'][0]:
            case "G":  # Guild only
                cursor = self.db.execute(
                    "SELECT DISC_GUILDS FROM OSM_LEADERBOARD_USERS WHERE DISC_UID=? LIMIT 1;",
                    (self.user_id,)
                ).fetchone()

                if cursor is None:
                    await inte.response.send_message("An error appened", ephemeral=True)
                    return

                guilds = json.loads(cursor[0])

                print(f"{inte.guild_id=} {guilds=}")
                guilds.remove(inte.guild_id)

                view = discord.ui.View()
                view.add_item(ConfirmationSelector(
                    self.user_id,
                    self.db,
                    "UPDATE OSM_LEADERBOARD_USERS SET DISC_GUILDS=? WHERE DISC_UID=?;",
                    (json.dumps(guilds), inte.user.id),
                    f"Your account was successfully unlinked on `{inte.guild.name}`")
                )

                await inte.followup.send(
                    f"Are you sure you want to unlink your account on `{inte.guild.name}`?",
                    view=view,
                    ephemeral=True
                )

            case "A":  # All
                view = discord.ui.View()
                view.add_item(ConfirmationSelector(
                    self.user_id,
                    self.db,
                    "DELETE FROM OSM_LEADERBOARD_USERS WHERE DISC_UID=?;",
                    (inte.user.id,),
                    f"Your account was successfully unlinked on every guilds")
                )

                await inte.followup.send(
                    f"Are you sure you want to unlink your account for __**every**__ guilds?",
                    view=view,
                    ephemeral=True
                )

            case "C":  # Cancel
                await inte.followup.send("Cancelled", ephemeral=True)


class ConfirmationSelector(discord.ui.Select):
    def __init__(
            self,
            user_id: int,
            database: sqlite3.Connection,
            sql_statement: str,
            sql_param: Tuple[str | int, ...],
            success_message: str
    ):

        self.user_id = user_id
        self.db = database
        self.sql_statement = sql_statement
        self.sql_param = sql_param
        self.success_message = success_message

        placeholder = "Yes / No"

        options = [
            discord.SelectOption(
                label="Yes",
                value="Y"
            ),
            discord.SelectOption(
                label="No",
                value="N"
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

        if inte.data['values'][0] == "Y":
            try:
                self.db.execute(self.sql_statement, self.sql_param),
                self.db.commit()
                msg = self.success_message

            except Exception as err:
                msg = (f"An error occured while editing DB: `{type(err)}: {err}`\n"
                       f"Please retry later or contact <@360018891776327680>")

            await inte.followup.send(msg, ephemeral=True)


        else:
            await inte.followup.send("Cancelled", ephemeral=True)
