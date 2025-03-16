# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import datetime
import json
import sqlite3
import time

import discord
from discord import app_commands, Interaction
from discord.ext import commands, tasks

from Cogs.Osm.GetChangesNotesNb import get_notes_nb, get_changes_nb
from Cogs.Osm.Py_OSM_API import PyOSM, py_osm_builder
from Cogs.Osm.RegisterUserViews import RegisterSelectSelector
from Cogs.Osm.RemoveLeaderboardMsgViews import RemoveLeaderboardSelector
from Cogs.Osm.TimeUtils import transform_str_to_datetime_args, date_to_timestamp, compact_str_to_human
from Cogs.Osm.UnregisterUserViews import UnregisterView
from GlobalModules.GetConfig import get_config
from GlobalModules.HasPerm import has_perm


# === DO NOT CHANGE CLASS NAME OR __init__ PARAMETERS === #
class Osm(commands.GroupCog):
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

        self.database.execute(
            "CREATE TABLE IF NOT EXISTS OSM_LEADERBOARD_AUTO_MSG ("
            "GUILD_ID INTEGER,"
            "CHANNEL_ID INTEGER,"
            "LAST_UPDATE INTEGER,"
            "NEXT_UPDATE INTEGER,"
            "UPDATE_EVERY TEXT);"
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

    @app_commands.command(name="unregister_user")
    @has_perm()
    async def unregister_user(self, interaction: Interaction):
        data = self.database.execute(
            "SELECT DISC_GUILDS, OSM_UID FROM OSM_LEADERBOARD_USERS WHERE DISC_UID=? LIMIT 1;",
            (interaction.user.id,)
        ).fetchone()

        if data is None:
            await interaction.response.send_message("No OSM account are linked to you", ephemeral=True)

        else:
            guilds = json.loads(data[0])
            osm_user = await self.py_osm.fetch_user_info(data[1])

            e = discord.Embed(
                title="OpenStreetMap unresgister account",
                color=get_config("core.base_embed_color"),
                description="What would you like to do with your linked OSM account?"

            )

            e.add_field(
                name="Account details",
                value=f"User name: `{osm_user.display_name}`\n"
                      f"UID: `{osm_user.uid}`\n"
                      f"Account created on: <t:{int(osm_user.account_created.timestamp())}:D>\n\n"
                      f"Registered on following guilds:\n"
                      f"{'\n'.join(
                          [f'`{g.name}`' if (g := self.bot.get_guild(i)) is not None else f'`{i}`' for i in guilds]
                      )}"
            )

            e.set_footer(text=osm_user.display_name, icon_url=osm_user.pfp_link if osm_user.pfp_link else None)

            await interaction.response.send_message(
                embed=e,
                view=UnregisterView(
                    self.database,
                    osm_user,
                    interaction.guild_id in guilds,
                    len(guilds),
                    interaction.user.id
                ),
                ephemeral=True
            )

    @app_commands.command(name="add_leaderboard_msg")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(
        duration=[
            app_commands.Choice(name="Daily", value="1d"),
            app_commands.Choice(name="Every 2 days", value="2d"),
            app_commands.Choice(name="Every 3 days", value="3d"),
            app_commands.Choice(name="Every 4 days", value="4d"),
            app_commands.Choice(name="Every 5 days", value="5d"),
            app_commands.Choice(name="Every 6 days", value="6d"),
            app_commands.Choice(name="Weekly", value="1w"),
            app_commands.Choice(name="Every 2 weeks", value="2w"),
            app_commands.Choice(name="Monthly", value="1m"),
            app_commands.Choice(name="Every 2 months", value="2m")
        ]
    )
    @has_perm()
    async def add_leaderboard_msg(
            self,
            interaction: Interaction,
            duration: app_commands.Choice[str],
            channel: discord.TextChannel = None
    ):

        if channel is None:
            channel = interaction.channel

        self.database.execute(
            "INSERT INTO OSM_LEADERBOARD_AUTO_MSG (GUILD_ID,CHANNEL_ID,LAST_UPDATE,NEXT_UPDATE,UPDATE_EVERY) VALUES "
            "(?,?,?,?,?);",
            (
                channel.guild.id,
                channel.id,
                date_to_timestamp(datetime.date.today()),
                date_to_timestamp(
                    datetime.date.today() + datetime.timedelta(**transform_str_to_datetime_args(duration.value))
                ),
                duration.value
            )
        )

        self.database.commit()

        await interaction.response.send_message(
            f"Successfully added an automatic message which will be sent {duration.name.lower()} in <#{channel.id}>",
            ephemeral=True
        )

    @app_commands.command(name="rm_leaderboard_msg")
    @app_commands.default_permissions(administrator=True)
    @has_perm()
    async def rm_leaderboard_msg(self, interaction: Interaction):
        selector = RemoveLeaderboardSelector(interaction.user, interaction.guild, self.database)

        if len(selector.options):
            view = discord.ui.View()
            view.add_item(selector)

            await interaction.response.send_message("Select a leaderboard to delete", view=view, ephemeral=True)

        else:
            await interaction.response.send_message("You have no leaderboard message set", ephemeral=True)

    @app_commands.command(name="list_leaderboard_msg")
    @app_commands.default_permissions(administrator=True)
    @has_perm()
    async def list_leaderboard_msg(self, interaction: Interaction):
        entries = []
        for channel_id, last_update, update_every in self.database.execute(
                "SELECT CHANNEL_ID,LAST_UPDATE,UPDATE_EVERY FROM OSM_LEADERBOARD_AUTO_MSG WHERE GUILD_ID=?;",
                (interaction.guild_id,)).fetchall():
            entries.append(
                f"- In <#{channel_id}> (`{channel_id}`)\n  - Last updated was on <t:{last_update}:F>\n  - Updates every"
                f" `{compact_str_to_human(update_every)}`"
            )

        if len(entries):
            e = discord.Embed(
                title="Leaderboards in {}",
                description="\n".join(entries),
                color=get_config("core.base_embed_color")
            )

            await interaction.response.send_message(embed=e, ephemeral=True)

        else:
            await interaction.response.send_message("There are no leaderboard set in this guild.", ephemeral=True)

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

            last_timestamps = datetime.datetime.fromtimestamp(cursor[0] + 1 if cursor is not None else 0)
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
    await bot.add_cog(Osm(bot, database, py_osm))

# TODO: Leaderboard
# TODO: Search element
# TODO: show map

# TODO: admin manage users

# TODO: add brief to every commands

# TODO: When adding a user in DB, also fetch old changeset count + notes + nodes count
# print(await get_notes_nb(py_osm, 14112053))
# print(await get_changes_nb(py_osm, 14112053))
