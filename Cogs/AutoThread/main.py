import sqlite3

from discord import app_commands, Interaction, InteractionResponse, TextChannel, Embed
from discord.ext import commands

from GlobalModules.GetConfig import get_config
from GlobalModules.HasPerm import has_perm


class AutoThread(commands.GroupCog):
    def __init__(self, bot: commands.AutoShardedBot, database: sqlite3.Connection):
        self.bot: bot = bot
        self.database = database

        database.execute(
            "CREATE TABLE IF NOT EXISTS AUTOTHREAD_CONFIG (GUILD_ID UNSIGNED INT, CHANNEL_ID UNSIGNED INT);"
        )

    @app_commands.command(name="add_channel")
    @app_commands.default_permissions(administrator=True)
    @has_perm()
    async def add_channel(self, interaction: Interaction, channel: TextChannel):
        resp: InteractionResponse = interaction.response

        if channel.guild.id != interaction.guild.id:
            await resp.send_message(
                "You can't add an auto threaded channel which doesn't belong to this server.",
                ephemeral=True
            )
            return

        elif len(self.database.execute(
                "SELECT * FROM AUTOTHREAD_CONFIG WHERE CHANNEL_ID=?;",
                (channel.id,)).fetchall()
                 ) >= 1:

            await resp.send_message("This channel is already auto threaded.", ephemeral=True)
            return

        self.database.execute(
            "INSERT INTO AUTOTHREAD_CONFIG (GUILD_ID, CHANNEL_ID) VALUES (?, ?);",
            (channel.guild.id, channel.id)
        )

        await resp.send_message(f"Channel <#{channel.id}> is now auto threaded.", ephemeral=True)

    @app_commands.command(name="remove_channel")
    @app_commands.default_permissions(administrator=True)
    @has_perm()
    async def remove_channel(self, interaction: Interaction, channel: TextChannel):
        resp: InteractionResponse = interaction.response

        if channel.guild.id != interaction.guild.id:
            await resp.send_message(
                "You can't remove an auto threaded channel which doesn't belong to this server.",
                ephemeral=True
            )
            return

        elif len(self.database.execute(
                "SELECT * FROM AUTOTHREAD_CONFIG WHERE CHANNEL_ID=?;",
                (channel.id,)).fetchall()
                 ) == 0:

            await resp.send_message("This channel isn't already auto threaded.", ephemeral=True)
            return

        self.database.execute(
            "DELETE FROM AUTOTHREAD_CONFIG WHERE GUILD_ID=? AND CHANNEL_ID=?;",
            (channel.guild.id, channel.id)
        )

        await resp.send_message(f"Channel <#{channel.id}> removed from auto threaded channels", ephemeral=True)

    @app_commands.command(name="list_channels")
    @app_commands.default_permissions(administrator=True)
    @has_perm()
    async def list_channels(self, interaction: Interaction):
        resp: InteractionResponse = interaction.response

        channels = []
        for i in self.database.execute(
                "SELECT CHANNEL_ID FROM AUTOTHREAD_CONFIG WHERE GUILD_ID=?;",
                (interaction.guild.id,)
        ).fetchall():
            channels.append(f"<#{i[0]}> | {i[0]}")

        if len(channels) == 0:
            await resp.send_message("There are no auto threaded channels on this server.", ephemeral=True)
            return

        msg = '\n'.join(channels)

        e = Embed(
            title="Auto threaded channels",
            description=f"List of auto threaded channels on this server:\n{msg}",
            color=get_config("core.base_embed_color")
        )

        await resp.send_message(embed=e, ephemeral=True)

    # TODO: Listener + keep config in RAM (self.config) updated with a task every few minutes + on admin commands


# === DO NOT REMOVE THE FOLLOWING OR CHANGE PARAMETERS === #

async def setup(bot: commands.AutoShardedBot, database: sqlite3.Connection):
    await bot.add_cog(AutoThread(bot, database))
