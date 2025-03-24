# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import sqlite3
from dataclasses import dataclass
from typing import List

import discord

from GlobalModules.GetConfig import get_config


@dataclass
class LeaderboardEntry:
    OSM_uid: int
    OSM_name: str

    Discord_ID: int

    Score: int  # Delta (Changes_nb + Notes_nb + Traces_nb + Blocks_nb)

    Changes_nb: int
    Notes_nb: int
    Traces_nb: int
    Blocks_nb: int


def make_leaderboard(db: sqlite3.Connection, guild_id: int, since: int) -> List[LeaderboardEntry]:
    leaderboard = []

    for i in db.execute(
            "SELECT DISC_UID, OSM_UID, OSM_NAME FROM OSM_LEADERBOARD_USERS WHERE INSTR(DISC_GUILDS, ?) >0;",
            (str(guild_id),)
    ).fetchall():

        d_id = i[0]  # discord id
        o_uid = i[1]  # osm uid
        o_name = i[2]  # osm name

        values = db.execute(
            "WITH D AS (SELECT CHANGES_NB, NOTES_NB, TRACES_NB, BLOCKS_NB, TIMESTAMP FROM OSM_LEADERBOARD_DATA "
            "WHERE OSM_UID=? AND TIMESTAMP >= ?) SELECT * FROM (SELECT * FROM D ORDER BY TIMESTAMP DESC "
            "LIMIT 1) UNION SELECT * FROM (SELECT * FROM D ORDER BY TIMESTAMP ASC LIMIT 1);",
            (o_uid, since)).fetchall()

        if len(values) == 0:
            continue

        if len(values) == 1:
            first = (0, 0, 0, 0, 0)
            last = values[0]

        else:  # len(values) == 2
            first, last = values

        changes_nb = last[0] - first[0]
        notes_nb = last[1] - first[1]
        traces_nb = last[2] - first[2]
        blocks_nb = last[3] - first[3]

        score = sum((changes_nb, notes_nb, traces_nb, blocks_nb))

        if score == 0:
            continue

        leaderboard.append(LeaderboardEntry(o_uid, o_name, d_id, score, changes_nb, notes_nb, traces_nb, blocks_nb))

    leaderboard.sort(key=lambda x: x.Score, reverse=True)

    return leaderboard


def make_leaderboard_embed(db: sqlite3.Connection, guild: discord.Guild, since: int) -> discord.Embed:
    leaderboard = make_leaderboard(db, guild.id, since)

    embed = discord.Embed(
        title=f"Open street map leaderboard",
        description=f"This is the leaderboard for `{guild.name}` which takes data since <t:{since}:F>",
        color=get_config("core.base_embed_color")
    )

    embed.set_footer(text="Developped by picasso2005")

    if len(leaderboard) == 0:
        embed.add_field(name="No data in this time period", value="Go contribute to the community!")

    else:
        values = []
        for i, e in enumerate(reversed(leaderboard[:10])):
            values.append(f"{i}. {e.OSM_name} [`{e.Score} points`] "
                          f"({', '.join([j[0] + ": `" + str(j[1]) + "`" for j in (
                              ('Changes', e.Changes_nb),
                              ('Notes', e.Notes_nb),
                              ('Traces', e.Traces_nb),
                              ('Blocks', e.Blocks_nb)
                          ) if j[1] != 0])})")

        embed.add_field(name=f"Leaderboard of {guild.name}", value="\n".join(values))

    return embed
