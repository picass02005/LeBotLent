import sqlite3

import discord
from discord import app_commands, Interaction, InteractionResponse, TextChannel, Embed, Member
from discord.ext import commands, tasks

from GlobalModules.GetConfig import get_config
from GlobalModules.HasPerm import has_perm


class AutoThread(commands.GroupCog):
    def __init__(self, bot: commands.AutoShardedBot, database: sqlite3.Connection):
        self.bot: bot = bot
        self.database = database

        self.__config = []

        database.execute(
            "CREATE TABLE IF NOT EXISTS AUTOTHREAD_CONFIG (GUILD_ID UNSIGNED INT, CHANNEL_ID UNSIGNED INT);"
        )

        database.execute(
            "CREATE TABLE IF NOT EXISTS AUTOTHREAD_REACT_WLIST (GUILD_ID UNSIGNED INT, USER_ID UNSIGNED INT);"
        )

        self.__update_config_from_db()


    def __update_config_from_db(self):
        self.__config = []

        for i in self.database.execute("SELECT CHANNEL_ID FROM AUTOTHREAD_CONFIG;").fetchall():
            self.__config.append(i[0])

    @tasks.loop(minutes=get_config("AutoThread.UpdateConfigFromSQL"))
    async def __update_config_task(self):
        self.__update_config_from_db()

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
                "SELECT 1 FROM AUTOTHREAD_CONFIG WHERE CHANNEL_ID=?;",
                (channel.id,)).fetchall()
                 ) >= 1:

            await resp.send_message("This channel is already auto threaded.", ephemeral=True)
            return

        self.database.execute(
            "INSERT INTO AUTOTHREAD_CONFIG (GUILD_ID, CHANNEL_ID) VALUES (?, ?);",
            (channel.guild.id, channel.id)
        )

        self.__update_config_from_db()

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
                "SELECT 1 FROM AUTOTHREAD_CONFIG WHERE CHANNEL_ID=?;",
                (channel.id,)).fetchall()
                 ) == 0:

            await resp.send_message("This channel isn't already auto threaded.", ephemeral=True)
            return

        self.database.execute(
            "DELETE FROM AUTOTHREAD_CONFIG WHERE GUILD_ID=? AND CHANNEL_ID=?;",
            (channel.guild.id, channel.id)
        )

        self.__update_config_from_db()

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


    @app_commands.command(name="add_whitelist_thread")
    @app_commands.default_permissions(administrator=True)
    @has_perm()
    async def add_whitelist_thread(self, interaction: Interaction, user: Member):
        resp: InteractionResponse = interaction.response

        if len(self.database.execute(
                "SELECT 1 FROM AUTOTHREAD_REACT_WLIST WHERE GUILD_ID=? AND USER_ID=?;",
                (interaction.guild.id, user.id)).fetchall()
                 ) >= 1:

            await resp.send_message("This user is already whitelisted.", ephemeral=True)
            return

        self.database.execute(
            "INSERT INTO AUTOTHREAD_REACT_WLIST (GUILD_ID, USER_ID) VALUES (?, ?);",
            (interaction.guild.id, user.id)
        )

        await resp.send_message(f"User <@{user.id}> is now whitelisted.", ephemeral=True)

    @app_commands.command(name="remove_whitelist_thread")
    @app_commands.default_permissions(administrator=True)
    @has_perm()
    async def remove_whitelist_thread(self, interaction: Interaction, user: Member):
        resp: InteractionResponse = interaction.response

        if len(self.database.execute(
                "SELECT 1 FROM AUTOTHREAD_REACT_WLIST WHERE GUILD_ID=? AND USER_ID=?;",
                (interaction.guild.id,user.id)).fetchall()
                 ) == 0:

            await resp.send_message("This user isn't already whitelisted.", ephemeral=True)
            return

        self.database.execute(
            "DELETE FROM AUTOTHREAD_REACT_WLIST WHERE GUILD_ID=? AND USER_ID=?;",
            (interaction.guild.id, user.id)
        )

        await resp.send_message(f"User <@{user.id}> is now removed from whitelist.", ephemeral=True)

    @app_commands.command(name="list_whitelist_thread")
    @app_commands.default_permissions(administrator=True)
    @has_perm()
    async def list_whitelist_thread(self, interaction: Interaction):
        resp: InteractionResponse = interaction.response

        channels = []
        for i in self.database.execute(
                "SELECT USER_ID FROM AUTOTHREAD_REACT_WLIST WHERE GUILD_ID=?;",
                (interaction.guild.id,)
        ).fetchall():
            channels.append(f"<@{i[0]}> | {i[0]}")

        if len(channels) == 0:
            await resp.send_message("There are no whitelisted users on this server.", ephemeral=True)
            return

        msg = '\n'.join(channels)

        e = Embed(
            title="Whitelisted users",
            description=f"List of whitelisted users on this server:\n{msg}",
            color=get_config("core.base_embed_color")
        )

        await resp.send_message(embed=e, ephemeral=True)

    @staticmethod
    async def __make_thread(message: discord.Message):
        if message.content:
            name = f"Reactions: {message.content}"

        else:
            name = "Reactions"

        await message.create_thread(name=name, reason="Auto thread module")

    @staticmethod
    async def thread_react(message: discord.Message):
        for i in (127481, 127469, 127479, 127466, 127462, 127465):
            await message.add_reaction(chr(i))


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel.id in self.__config:
            if (len(message.attachments) or "http" in message.content) and not message.author.id == 312926990888075264:
                await self.__make_thread(message)

            elif len(
                    self.database.execute(
                        "SELECT 1 FROM AUTOTHREAD_REACT_WLIST WHERE GUILD_ID=? AND USER_ID=?",
                        (message.guild.id, message.author.id)).fetchall()
            ):
                await self.thread_react(message)



# === DO NOT REMOVE THE FOLLOWING OR CHANGE PARAMETERS === #

async def setup(bot: commands.AutoShardedBot, database: sqlite3.Connection):
    await bot.add_cog(AutoThread(bot, database))
