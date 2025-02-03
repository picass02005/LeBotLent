# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import sqlite3
import time

from discord.ext import commands, tasks

from Cogs.OSM.Py_OSM_API import PyOSM, py_osm_builder
from GlobalModules.GetConfig import get_config


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
            "TRACES_NB INTEGER,"
            "BLOCKS_NB INTEGER,"
            "BLOCKS_ACTIVE INTEGER);"
        )

        self.database.commit()

    @tasks.loop(minutes=get_config("OSM.Leaderboard.UpdateTimeMin"))
    async def update_data(self):
        uids = [i[0] for i in self.database.execute("SELECT OSM_UID FROM OSM_LEADERBOARD_USERS;").fetchall()]

        users = await self.py_osm.fetch_users_info(uids)

        if users is None:
            return

        ts = int(time.time())

        for i in users:
            self.database.execute(
                "INSERT INTO OSM_LEADERBOARD_DATA (TIMESTAMP, OSM_UID, CHANGESET_NB, TRACES_NB, BLOCKS_NB, "
                "BLOCKS_ACTIVE) VALUES (?, ?, ?, ?, ?, ?);",
                (
                    ts,
                    i.uid,
                    i.changesets_count,
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

# TODO: When adding a user in DB, also fetch old changeset count
