# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import sqlite3
import time

from Cogs.Osm.GetChangesNotesNb import get_notes_nb, get_changes_nb
from Cogs.Osm.Py_OSM_API import OSMUser, PyOSM


async def register_user_in_db(disc_uid: int, guild_id: int, osm_user: OSMUser, py_osm: PyOSM, db: sqlite3.Connection):
    try:
        notes_nb = await get_notes_nb(py_osm, osm_user.uid)
        changes_nb = await get_changes_nb(py_osm, osm_user.uid)

    except Exception:
        notes_nb = None
        changes_nb = None

    db.execute(
        "INSERT INTO OSM_LEADERBOARD_USERS (DISC_UID,DISC_GUILDS,OSM_UID,OSM_NAME) VALUES (?,?,?,?);",
        (disc_uid, f"[{guild_id}]", osm_user.uid, osm_user.display_name)
    )

    if notes_nb is not None and changes_nb is not None:
        db.execute(
            "INSERT INTO OSM_LEADERBOARD_DATA (TIMESTAMP, OSM_UID, CHANGESET_NB, CHANGES_NB, NOTES_NB, "
            "TRACES_NB, BLOCKS_NB, BLOCKS_ACTIVE) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
            (
                int(time.time()),
                osm_user.uid,
                osm_user.changesets_count,
                changes_nb,
                notes_nb,
                osm_user.traces_count,
                osm_user.blocks_count,
                osm_user.blocks_active
            )
        )

    db.commit()
