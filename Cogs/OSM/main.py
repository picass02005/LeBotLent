# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved
import json
import sqlite3
import time
from datetime import datetime

import discord
from discord import app_commands, Interaction
from discord.ext import commands, tasks

from Cogs.OSM.GetChangesNotesNb import get_notes_nb, get_changes_nb
from Cogs.OSM.Py_OSM_API import PyOSM, py_osm_builder
from Cogs.OSM.RegisterUserViews import RegisterSelectSelector
from GlobalModules.GetConfig import get_config
from GlobalModules.HasPerm import has_perm


# === DO NOT CHANGE CLASS NAME OR __init__ PARAMETERS === #
class OSM(commands.GroupCog):
    def __init__(self, bot: commands.AutoShardedBot, database: sqlite3.Connection, py_osm: PyOSM):
        self.bot: bot = bot
        self.database = database

        self.py_osm: PyOSM = py_osm

        self.check_db()

        self.update_data.start()

    def cog_unload(self) -> None:
        self.update_data.stop()

    def check_db(self):
        self.database.execute(
            "CREATE TABLE IF NOT EXISTS OSM_LEADERBOARD_USERS ("
            "DISC_UID INTEGER UNIQUE,"
            "DISC_GUILDS JSON,"
            "OSM_UID INTEGER UNIQUE,"
            "OSM_NAME TEXT);"
        )

        self.database.execute(
            "CREATE TABLE IF NOT EXISTS OSM_LEADERBOARD_DATA ("
            "TIMESTAMP UNSIGNED INT(10),"
            "OSM_UID INTEGER,"
            "CHANGESET_NB INTEGER,"
            "CHANGES_NB INTEGER,"
            "NOTES_NB INTEGER,"
            "TRACES_NB INTEGER,"
            "BLOCKS_NB INTEGER,"
            "BLOCKS_ACTIVE INTEGER);"
        )

        self.database.commit()

    @app_commands.command(name="register_user")
    @has_perm()
    async def register_user(self, interaction: Interaction):
        data = self.database.execute(
            "SELECT DISC_GUILDS FROM OSM_LEADERBOARD_USERS WHERE DISC_UID=? LIMIT 1;",
            (interaction.user.id,)
        ).fetchone()

        if data is None:
            e = discord.Embed(
                title="OpenStreetMap resgister account",
                color=get_config("core.base_embed_color"),
                description="Choose which method you want to use to connect your OSM account"
            )

            e.add_field(
                name="By user name",
                value="You will have to give your Open Street Map user name\n"
                      "__This methos is case sensitibe__\n"
                      "**This only works if you have made at least one changeset since your account creation**",
                inline=True
            )

            e.add_field(
                name="By User ID",
                value="You will have to give your Open Street Map User ID (UID)\n"
                      "To get your UID, please follow those steps:\n"
                      "1. Log in your OSM account in any web browser\n"
                      "2. Go on [this API url](https://api.openstreetmap.org/api/0.6/user/details.json)\n"
                      "3. Search for a field named `id` located here: `{'user': {'id': YOUR_USER_ID, ...}, ...}`\n"
                      "4. Copy and paste your UID",
                inline=True
            )

            view = discord.ui.View()
            view.add_item(RegisterSelectSelector(self.py_osm, interaction.user.id, self.database))

            await interaction.response.send_message(embed=e, ephemeral=True, view=view)

        else:
            guilds = json.loads(data[0])

            if interaction.guild_id in guilds:
                await interaction.response.send_message("You are already registered on this guild", ephemeral=True)

            else:
                guilds.append(interaction.guild_id)

                self.database.execute(
                    "UPDATE OSM_LEADERBOARD_USERS SET DISC_GUILDS=? WHERE DISC_UID=?;",
                    (json.dumps(guilds), interaction.user.id)
                )
                self.database.commit()

                await interaction.response.send_message(
                    "Your linked OSM account was syccessfully added to this guild", ephemeral=True
                )

    @tasks.loop(minutes=get_config("OSM.Leaderboard.UpdateTimeMin"))
    async def update_data(self):
        uids = [i[0] for i in self.database.execute("SELECT OSM_UID FROM OSM_LEADERBOARD_USERS;").fetchall()]

        if not uids:
            return

        users = await self.py_osm.fetch_users_info(uids)

        if users is None:
            return

        ts = int(time.time())

        for i in users:
            cursor = self.database.execute(
                "SELECT TIMESTAMP, CHANGESET_NB, CHANGES_NB FROM OSM_LEADERBOARD_DATA "
                "WHERE OSM_UID=? ORDER BY TIMESTAMP DESC LIMIT 1;",
                (i.uid,)
            ).fetchone()

            last_timestamps = datetime.fromtimestamp(cursor[0] + 1 if cursor is not None else 0)
            last_changeset_nb = cursor[1] if cursor is not None else 0
            last_changes_nb = cursor[2] if cursor is not None else 0

            if i.changesets_count != last_changeset_nb:
                changes_nb = await get_changes_nb(self.py_osm, i.uid, last_timestamps)

            else:
                changes_nb = last_changes_nb

            notes_nb = await get_notes_nb(self.py_osm, i.uid, last_timestamps)

            self.database.execute(
                "INSERT INTO OSM_LEADERBOARD_DATA (TIMESTAMP, OSM_UID, CHANGESET_NB, CHANGES_NB, NOTES_NB, "
                "TRACES_NB, BLOCKS_NB, BLOCKS_ACTIVE) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                (
                    ts,
                    i.uid,
                    i.changesets_count,
                    changes_nb,
                    notes_nb,
                    i.traces_count,
                    i.blocks_count,
                    i.blocks_active
                )
            )

        self.database.execute(
            "DELETE FROM OSM_LEADERBOARD_DATA WHERE TIMESTAMP < ?;",
            (ts - get_config("OSM.Leaderboard.DeleteAfter"),)
        )

        self.database.commit()


# === DO NOT REMOVE THE FOLLOWING OR CHANGE PARAMETERS === #

async def setup(bot: commands.AutoShardedBot, database: sqlite3.Connection):
    py_osm = await py_osm_builder()
    await bot.add_cog(OSM(bot, database, py_osm))

# TODO: Leaderboard
# TODO: Search element
# TODO: show map

# TODO: admin manage users
# TODO: unregister

# TODO: When adding a user in DB, also fetch old changeset count + notes + nodes count
# print(await get_notes_nb(py_osm, 14112053))
# print(await get_changes_nb(py_osm, 14112053))
