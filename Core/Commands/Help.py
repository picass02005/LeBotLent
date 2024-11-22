import json
import sqlite3
from typing import Union, List, Dict

import discord
from discord import AppCommandType
from discord.ext import commands
from discord.ext.commands import Command

from Core.IsTestVersion import is_test_version
from GlobalModules.GetConfig import get_config
from GlobalModules.HasPerm import user_have_perm
from GlobalModules.Paginator import Paginator


class Help:
    def __init__(self, bot: commands.AutoShardedBot, database: sqlite3.Connection):
        self.bot = bot
        self.db = database

    async def app_command(self, inte: discord.Interaction):
        await self.__generate_paginator(inte).send_paginator(inte, ephemeral=True)

    async def ctx_command(self, ctx: commands.Context):
        await self.__generate_paginator(ctx).send_paginator(ctx, ephemeral=False)

    def __get_commands(self, inte_ctx: Union[discord.Interaction, commands.Context]) \
            -> Dict[str, List[Union[Command, discord.app_commands.Command, discord.app_commands.ContextMenu]]]:

        command_list = {}

        lists = [self.bot.commands, self.bot.tree.get_commands(), self.bot.tree.get_commands(guild=inte_ctx.guild)]
        while lists:
            for cmd_group in lists.pop():
                if isinstance(cmd_group, discord.app_commands.Group):
                    lists.append(cmd_group.walk_commands())

                elif isinstance(
                        cmd_group,
                        (commands.Command, discord.app_commands.Command, discord.app_commands.ContextMenu)
                ):

                    module = self.__get_command_module(cmd_group)

                    if self.__has_perm(inte_ctx, cmd_group.callback.__name__, module):
                        if module not in command_list.keys():
                            command_list.update({module: [cmd_group]})

                        else:
                            command_list[module].append(cmd_group)

        return command_list

    @staticmethod
    def __has_perm(inte_ctx: Union[discord.Interaction, commands.Context], command_name: str, module: str):
        if module == "__main__":
            perm_fp = f"CoreConfig/{'test_' if is_test_version() else ''}permissions.json"

        else:
            perm_fp = f"Cogs/{module}/Config/{'test_' if is_test_version() else ''}permissions.json"

        with open(perm_fp, 'r') as f:
            perms = json.loads(f.read())

        if command_name in perms.keys():
            if isinstance(inte_ctx, discord.Interaction):
                return user_have_perm(inte_ctx.user, inte_ctx.guild, perms[command_name])

            elif isinstance(inte_ctx, commands.Context):
                return user_have_perm(inte_ctx.author, inte_ctx.guild, perms[command_name])

        else:
            return True

    def __generate_paginator(self, inte_ctx: Union[discord.Interaction, commands.Context]) -> Paginator:
        paginator = Paginator(self.db)

        for module, i in self.__get_commands(inte_ctx).items():
            if module == "__main__":
                module = "Main"

            e = discord.Embed(title="Help", description=f"Showing module: {module}\n\nBot made by picasso2005")
            for cmd in i:
                if isinstance(cmd, commands.Command):
                    prefix = get_config('core.bot_admin_prefix')

                    value = f"Usage: `{prefix}{cmd.name} {cmd.signature}`"

                    if cmd.brief:
                        value += f"\nBrief description: {cmd.brief}"

                    if cmd.description:
                        value += f"\nFull description: {cmd.description}"

                    if cmd.aliases:
                        value += "\nAliases:" + " ".join([f"`{prefix}{name}`" for name in cmd.aliases])

                    e.add_field(
                        name=f"{prefix}{cmd.name}",
                        value=value,
                        inline=False
                    )

                elif isinstance(cmd, discord.app_commands.Command):
                    value = f"Usage: `/{cmd.qualified_name} " + " ".join([f"[{j.name}]" for j in cmd.parameters]) + "`"

                    if cmd.description != chr(8230):
                        value += f"\nDescription: {cmd.description}"

                    if cmd.nsfw:
                        value += f"\nCan only be used in NSFW channel"

                    if cmd.allowed_contexts:
                        builder = (
                            ("guild", cmd.allowed_contexts.guild),
                            ("DM", cmd.allowed_contexts.dm_channel or cmd.allowed_contexts.private_channel)
                        )

                        value += "\nCan only be used in " + " ".join([j for j, k in builder if k])

                    if cmd.parameters:
                        value += "\n\nParameters:"

                        for param in cmd.parameters:
                            value += f"\n`{param.display_name} <{'.'.join(str(param.type).split('.')[1:])}>`"

                            if param.description != chr(8230):
                                value += f": {param.description}"

                            if param.required:
                                value += " [REQUIRED]"

                            else:
                                value += " [OPTIONAL]"

                    e.add_field(
                        name=f"/{cmd.qualified_name}",
                        value=value,
                        inline=False
                    )

                elif isinstance(cmd, discord.app_commands.ContextMenu):
                    if cmd.type == AppCommandType.user:
                        command_type = "`apps` tab when right clicking an user"

                    elif cmd.type == AppCommandType.message:
                        command_type = "`apps` tab when right clicking a message"

                    else:
                        command_type = "UNKNOWN"

                    value = f"Usage: `{cmd.name}` in {command_type}"

                    if cmd.nsfw:
                        value += f"\nCan only be used in NSFW channel"

                    if cmd.allowed_contexts:
                        builder = (
                            ("guild", cmd.allowed_contexts.guild),
                            ("DM", cmd.allowed_contexts.dm_channel or cmd.allowed_contexts.private_channel)
                        )

                        value += "\nCan only be used in " + " ".join([j for j, k in builder if k])

                    e.add_field(
                        name=f"{cmd.name}",
                        value=value,
                        inline=False
                    )

            paginator.add_page(e, module)

        return paginator

    @staticmethod
    def __get_command_module(command: Union[commands.Command, discord.app_commands.commands.Command]) -> str:
        if isinstance(command, commands.Command):
            return command.module

        elif isinstance(command, (discord.app_commands.commands.Command, discord.app_commands.ContextMenu)):
            if command.module == "__main__":
                return "__main__"

            else:
                return command.module.split(".")[1]
