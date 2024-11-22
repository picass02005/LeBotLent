import asyncio
import gc
import json
import sqlite3
import time
from functools import wraps

import discord
from discord import Interaction, InteractionResponse
from discord.ext.commands.cog import Cog
from discord.ext.commands.context import Context
from discord.permissions import Permissions

from Core.IsTestVersion import is_test_version
from Core.UserOnCooldown import user_on_cooldown
from GlobalModules.Logger import Logger


def has_perm(db: sqlite3.Connection = None):
    """
    :param db: The database object
    :return: Wrapped function
    """

    def inner(func: asyncio.coroutines):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            ctx_interaction = None

            user = None
            guild = None
            cog_name = None
            database = db

            for i in args:
                if isinstance(i, Context):
                    ctx_interaction = i

                    user = ctx_interaction.author
                    guild = ctx_interaction.guild

                elif isinstance(i, Interaction):
                    ctx_interaction = i

                    user = ctx_interaction.user
                    guild = ctx_interaction.guild

                elif isinstance(i, Cog):
                    cog_name = f"{str(i).split(' ')[0][1:]}".split(".")
                    cog_object = i
                    database = cog_object.database

            if ctx_interaction is None:
                raise ValueError("The wrapper has_perm could not retrieve the context or interaction")

            logger = Logger(database)

            if cog_name is None:
                if is_test_version():
                    with open("CoreConfig/test_permissions.json", "r") as f:
                        perms = json.loads(f.read())[func.__name__]

                else:
                    with open("CoreConfig/permissions.json", "r") as f:
                        perms = json.loads(f.read())[func.__name__]

            else:
                if is_test_version():
                    with open(f"Cogs/{cog_name[1]}/Config/test_permissions.json", "r") as f:
                        perms = json.loads(f.read())[func.__name__]

                else:
                    with open(f"Cogs/{cog_name[1]}/Config/permissions.json", "r") as f:
                        perms = json.loads(f.read())[func.__name__]

            if is_bot_admin(user.id):
                have_perm = True
                send_output = True

            else:
                have_perm = user_have_perm(user, guild, perms)
                send_output = send_error_output(user_id=user.id, database=database)

                database.execute(
                    "INSERT INTO LAST_USED_COMMANDS (TIMESTAMP, USER_ID) VALUES (?, ?)",
                    (int(time.time()), user.id)
                )

                database.commit()

            args_ = list(args) + list(kwargs)
            args_.remove(ctx_interaction)
            for i in args_:
                if isinstance(i, Cog):
                    args_.remove(i)

            for i, j in enumerate(args_):
                if type(j) == tuple:
                    args_[i] = "".join(j)

            if have_perm:
                ret = await func(*args, **kwargs)
                logger.add_log(
                    "Command",
                    f"{user} (ID: {user.id}) invoked {func.__name__} command with args {args_}"
                )

            else:
                ret = None
                logger.add_log(
                    "Command",
                    f"{user} (ID: {user.id}) tried to invoke {func.__name__} command with args {args_} but "
                    f"have not the permission"
                )

                if send_output:
                    if isinstance(ctx_interaction, Context):
                        await ctx_interaction.send(
                            "You haven't the permission to perform this command.",
                            reference=ctx_interaction.message.to_reference(fail_if_not_exists=False)
                        )

                    elif isinstance(ctx_interaction, Interaction):
                        resp: InteractionResponse = ctx_interaction.response
                        await resp.send_message(
                            content="You haven't the permission to perform this command.",
                            ephemeral=True
                        )

            print(f"Garbage collector: {gc.collect()}")
            return ret

        return wrapper

    print(f"Garbage collector HasPerm: {gc.collect()}")

    return inner


def user_have_perm(user: discord.Member, guild: discord.Guild, perms: dict) -> bool:
    if is_test_version():
        with open("CoreConfig/test_roles_id.json") as f:
            config_roles = json.loads(f.read())
    else:
        with open("CoreConfig/roles_id.json") as f:
            config_roles = json.loads(f.read())

    allowed_roles = []
    for i in perms["roles"]:
        allowed_roles.append(config_roles[i])

    for i in user.roles:
        if i.id in allowed_roles:
            return True

    if user.id in perms["users"]:
        return True

    for i in perms["permission_code"]:
        if user.guild_permissions.is_superset(Permissions(i)):
            return True

    if guild.id in perms["guilds"]:
        return True

    for i in perms["group"]:
        if is_test_version():
            with open(f"CoreConfig/Groups/test_{i}.json") as f:
                group = json.loads(f.read())

        else:
            with open(f"CoreConfig/Groups/{i}.json") as f:
                group = json.loads(f.read())

        for j in group:
            if user.id == j["id"]:
                return True

    return False


def is_bot_admin(user_id: int) -> bool:
    if is_test_version():
        with open("CoreConfig/Groups/test_bots_admin.json") as f:
            group = json.loads(f.read())

    else:
        with open("CoreConfig/Groups/bots_admin.json") as f:
            group = json.loads(f.read())

    for j in group:
        if user_id == j["id"]:
            return True

    return False


def send_error_output(user_id: int, database: sqlite3.Connection) -> bool:
    if user_on_cooldown(user_id=user_id, database=database):
        return False

    else:
        return True
