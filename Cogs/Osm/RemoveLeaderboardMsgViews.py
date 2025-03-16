import datetime
import sqlite3
from typing import Any

import discord
from discord import Interaction

from Cogs.Osm.TimeUtils import transform_str_to_datetime_args


class RemoveLeaderboardSelector(discord.ui.Select):
    def __init__(self, author: discord.Member, guild: discord.Guild, database: sqlite3.Connection):
        self.author = author
        self.guild = guild
        self.db = database

        placeholder = "Select the automatic message you want to remove"

        super().__init__(placeholder=placeholder, options=self.__make_options())

    def __make_options(self):
        ret = []
        for channel_id, last_update, update_every in self.db.execute(
                "SELECT CHANNEL_ID,LAST_UPDATE,UPDATE_EVERY FROM OSM_LEADERBOARD_AUTO_MSG WHERE GUILD_ID=?;",
                (self.guild.id,)).fetchall():
            update_every_human = ' '.join([f"{v} {k}" for k, v in transform_str_to_datetime_args(update_every).items()])

            channel_name = self.guild.get_channel(channel_id)

            ret.append(
                discord.SelectOption(
                    label=f"In #{channel_name} | {channel_id}",
                    value=f"{channel_id},{last_update},{update_every},{update_every_human}",
                    description=f"Every {update_every_human}, last update was on "
                                f"{datetime.datetime.fromtimestamp(last_update).strftime('%d/%m')} [DD/MM]"
                )
            )

        return ret

    async def callback(self, inte: Interaction) -> Any:
        if inte.user.id != self.author.id:
            return await inte.response.send_message("Only the author can answer this", ephemeral=True)

        channel_id = int(inte.data['values'][0].split(",")[0])
        last_update = int(inte.data['values'][0].split(",")[1])
        update_every = inte.data['values'][0].split(",")[2]
        update_every_human = inte.data['values'][0].split(",")[3]

        self.db.execute(
            "DELETE FROM OSM_LEADERBOARD_AUTO_MSG WHERE GUILD_ID=? AND CHANNEL_ID=? AND LAST_UPDATE=? AND "
            "UPDATE_EVERY=?;",
            (self.guild.id, channel_id, last_update, update_every)
        )
        self.db.commit()

        self.disabled = True
        view = discord.ui.View()
        view.add_item(self)

        await inte.response.edit_message(view=view)

        await inte.followup.send(
            f"Successfully removed leaderboard send in <#{channel_id}> every {update_every_human} and which was last "
            f"sent on <t:{last_update}:F>",
            ephemeral=True
        )
