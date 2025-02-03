import json
import sqlite3
import sys
import time
import traceback
from typing import Union, Dict, Any

import discord
from discord import app_commands
from discord.ext import commands

from Core.IsTestVersion import is_test_version
from Core.UserOnCooldown import user_on_cooldown
from GlobalModules.GetConfig import get_config
from GlobalModules.Logger import Logger
from GlobalModules.Paginator import Paginator


class ErrorHandler:
    def __init__(self, db: sqlite3.Connection, bot: commands.AutoShardedBot):
        self.db = db
        self.bot = bot

        self.logger = Logger(self.db)

    def __generate_user_response(self, error, ctx: commands.Context = None) -> Union[None, str]:

        if type(error) == commands.errors.CommandNotFound or type(error) == app_commands.errors.CommandNotFound:
            return None

        elif type(error) == commands.errors.CommandOnCooldown or type(error) == app_commands.errors.CommandOnCooldown:

            if not user_on_cooldown(ctx.author.id, self.db):
                return "Command is on cooldown."

            else:
                return None

        elif type(error) == commands.errors.MissingRequiredArgument or type(error) == commands.errors.BadArgument:
            return f"Your arguments are incorrect. Please refer to `{self.bot.command_prefix}help {ctx.command}`"

        else:
            return "An unknown error happened. A ticket was automatically sent to our developers."

    @staticmethod
    def __argument_to_string(argument):
        if isinstance(argument, str):
            return argument

        elif isinstance(argument, (int, float, bool)):
            return str(argument)

        elif isinstance(argument, (discord.User, discord.Member)):
            return f"[Member] {argument.display_name} (ID: {argument.id})"

        elif isinstance(argument, discord.Role):
            return (f"[Role] {argument.name} (ID: {argument.id}) on guild {argument.guild.name} (ID: "
                    f"{argument.guild.id})")

        elif isinstance(argument, (app_commands.AppCommandChannel, app_commands.AppCommandThread)):
            return (f"[Channel / thread] {argument.name} (ID: {argument.id}) on guild {argument.guild.name} (ID: "
                    f"{argument.guild.id})")

        elif isinstance(argument, discord.Attachment):
            return f"[Attachment] Type: {argument.content_type} | Filename: {argument.filename} | URL: {argument.url}"

        else:
            try:
                return str(argument)

            except:
                return f"This type can't be converted into string: {type(argument)}"

    async def __process_error(self, error, general_data: Dict[str, Any], extra_data: Dict[str, Any]):
        brief_error = str(type(error)).split('\'')[1] + ": " + str(error)

        tb = traceback.format_tb(error.__traceback__)
        tb.append(brief_error)

        full_error = "\n".join(tb)

        if is_test_version():
            sys.stderr.write("\n".join(tb) + "\n")
            sys.stderr.flush()

        self.db.execute("DELETE FROM ERROR_REPORT WHERE DELETE_TS < ?;", (int(time.time()),))

        error_id = self.db.execute(
            "INSERT INTO ERROR_REPORT (USER_ID, USER_NAME, COMMAND, BRIEF_ERROR, FULL_ERROR, ARGS_KWARGS, "
            "EXTRA_DATA, DELETE_TS) VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING ID;",
            (
                general_data['user']['id'],
                general_data['user']['name'],
                general_data['command'],
                brief_error,
                full_error,
                json.dumps(general_data['args_kwargs']),
                json.dumps(extra_data),
                int(time.time() + get_config("core.error_report.delete_after"))
            )
        ).fetchone()[0]

        self.db.commit()

        self.logger.add_log(
            "ERROR",
            f"An error happened while executing {general_data['command']}, for more information, refer to "
            f"ERROR_REPORT id {error_id}"
        )

        channel = self.bot.get_partial_messageable(
            id=get_config("core.error_report.channel"),
            guild_id=get_config("core.error_report.guild"),
            type=discord.ChannelType.text
        )

        if 'message_link' in extra_data['message_info']:
            desc = extra_data['message_info']['message_link']

        else:
            desc = None

        e = discord.Embed(
            title=f"Error ID: `{error_id}`",
            description=desc,
            color=get_config("core.base_embed_color")
        )

        e.add_field(name="Brief error", value=f"`{brief_error}`", inline=False)
        e.add_field(name="Command", value=f"`{general_data['command']}`", inline=False)
        e.add_field(
            name="Author",
            value=f"Name: `{general_data['user']['name']}`\nID: `{general_data['user']['id']}`",
            inline=False
        )

        await channel.send(content=" ".join([f"<@{i}>" for i in get_config("core.error_report.ping")]), embed=e)

    async def app_command_error(self, interaction: discord.Interaction, exception: app_commands.AppCommandError):
        error = getattr(exception, "original", exception)
        user_message = self.__generate_user_response(error)

        if user_message:
            if interaction.response.is_done() or interaction.is_expired():
                await interaction.followup.send(content=user_message, ephemeral=True)

            else:
                await interaction.response.send_message(content=user_message, ephemeral=True)

        kwargs = {}
        for key, value in iter(interaction.namespace):
            kwargs.update({key: self.__argument_to_string(value)})

        general_data = {
            'user': {
                'name': interaction.user.name,
                'id': interaction.user.id
            },
            'command': interaction.command.name,
            'args_kwargs': {
                'args': [],
                'kwargs': kwargs
            }
        }

        extra_data = {
            'message_info': {
                'guild': {
                    'name': interaction.guild.name if interaction.guild is not None else None,
                    'id': interaction.guild.id if interaction.guild is not None else None
                },
                'channel': {
                    'name': interaction.channel.name if interaction.channel is not None else None,
                    'id': interaction.channel.id if interaction.channel is not None else None
                },
                'message_id': interaction.message.id if interaction.message is not None else None,
                'message_link': interaction.message.jump_url if interaction.message is not None else None
            }
        }

        await self.__process_error(error, general_data, extra_data)

    async def command_error(self, ctx: commands.Context, exception: commands.CommandError):
        error = getattr(exception, "original", exception)
        user_message = self.__generate_user_response(error, ctx)

        if user_message:
            await ctx.reply(content=user_message, delete_after=30)

        general_data = {
            'user': {
                'name': ctx.author.name,
                'id': ctx.author.id
            },
            'command': ctx.command.name if ctx.command is not None else "Undefined",
            'args_kwargs': {
                'args': [self.__argument_to_string(i) for i in ctx.args[2:]],
                'kwargs': [self.__argument_to_string(i) for i in ctx.kwargs]
            }
        }

        extra_data = {
            'message_info': {
                'guild': {
                    'name': ctx.guild.name if ctx.guild is not None else None,
                    'id': ctx.guild.id if ctx.guild is not None else None
                },
                'channel': {
                    'name': ctx.channel.name if ctx.channel is not None else None,
                    'id': ctx.channel.id if ctx.channel is not None else None
                },
                'message_id': ctx.message.id if ctx.message is not None else None,
                'message_link': ctx.message.jump_url if ctx.message is not None else None
            }
        }

        await self.__process_error(error, general_data, extra_data)

    async def get_tb_command(self, ctx: commands.Context, error_id: int):
        self.db.execute("DELETE FROM ERROR_REPORT WHERE DELETE_TS < ?;", (int(time.time()),))
        self.db.commit()

        temp = self.db.execute(
            "SELECT USER_ID, USER_NAME, COMMAND, BRIEF_ERROR, FULL_ERROR, ARGS_KWARGS, EXTRA_DATA FROM "
            "ERROR_REPORT WHERE ID=?;",
            (error_id,)
        ).fetchone()

        if not temp:
            return await ctx.send(f"Error report N#`{error_id}` not found.")

        data = {
            'USER_ID': temp[0],
            'USER_NAME': temp[1],
            'COMMAND': temp[2],
            'BRIEF_ERROR': temp[3],
            'FULL_ERROR': temp[4],
            'ARGS_KWARGS': json.loads(temp[5]),
            'EXTRA_DATA': json.loads(temp[6])
        }

        paginator = Paginator(self.db)

        base_embed = discord.Embed(
            title=f"Error report ID {error_id}",
            description=f"Issued on command `{data['COMMAND']}`"
        )

        e = base_embed.copy()

        e.add_field(
            name="Information",
            value=f"User: {data['USER_NAME']} ({data['USER_ID']})\n"
                  f"Brief error: {data['BRIEF_ERROR']}",
            inline=False
        )

        e.add_field(name="Arguments", value=f"```json\n{json.dumps(data['ARGS_KWARGS'], indent=4)}```", inline=False)
        e.add_field(name="Extra data", value=f"```json\n{json.dumps(data['EXTRA_DATA'], indent=4)}```", inline=False)

        paginator.add_page(e, "Basic data")

        full_error_lines = data['FULL_ERROR'].split("\n")
        full_error_parsed = [""]

        while full_error_lines:
            if len(full_error_parsed[-1]) + len(full_error_lines[0]) < 3750:  # Discord limit at 4096
                full_error_parsed[-1] += f"\n{full_error_lines.pop(0)}"

            else:
                full_error_parsed.append("")

        for i, value in enumerate(full_error_parsed):
            e = base_embed.copy()
            e.description += f"\n\nFull error ({i + 1} / {len(full_error_parsed)})```python{value}```"

            paginator.add_page(e, f"Full error page {i + 1}")

        await paginator.send_paginator(ctx, ephemeral=False)
