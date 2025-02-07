# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import sqlite3
import time
from datetime import datetime

from discord.ext import commands, tasks

from Cogs.OSM.GetChangesNotesNb import get_notes_nb, get_changes_nb
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
            "CHANGES_NB INTEGER,"
            "NOTES_NB INTEGER,"
            "TRACES_NB INTEGER,"
            "BLOCKS_NB INTEGER,"
            "BLOCKS_ACTIVE INTEGER);"
        )

        self.database.commit()

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

# TODO: When adding a user in DB, also fetch old changeset count + notes + nodes count
# print(await get_notes_nb(py_osm, 14112053))
# print(await get_changes_nb(py_osm, 14112053))
