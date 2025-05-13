# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import sqlite3

import discord

from GlobalModules.GetConfig import get_config
from GlobalModules.Logger import Logger


async def send_tutor_request_message(channel: discord.TextChannel) -> discord.Message:
    b = discord.ui.Button(
        style=discord.ButtonStyle.green,
        label="Demander un tutorat",
        custom_id=f"TUTORINSA.TUTOR_REQUEST.{channel.id}"
    )
    v = discord.ui.View()
    v.add_item(b)

    e = discord.Embed(
        title="Demander une séance de tutorat / Request a tutoring session",
        description="### Afin de demander une séance de tutorat, veuillez suivre cette démarche:\n"
                    "1. Sélectionnez votre rôle de classe (si pas encore fait)\n"
                    "2. Appuyez sur le bouton ci-dessous, une fenêtre s'ouvrira\n"
                    "3. Remplissez les informations demandées\n"
                    "4. Cliquez sur \"Envoyer\"\n\n"
                    "### In order to request a tutoring session, please follow thoses steps:\n"
                    "1. Select your class role (if not already done)\n"
                    "2. Click on the button below, a window will be opened\n"
                    "3. Fill every fields accordingly\n"
                    "4. Click on \"Submit\"",
        color=get_config("core.base_embed_color")
    )

    msg = await channel.send(embed=e, view=v)
    return msg


async def delete_tutor_request_message(db: sqlite3.Connection, guild: discord.Guild):
    msg_id, channel_id = db.execute(
        "SELECT REQ_MSG_ID,REQ_CHANNEL_ID FROM TUTOR_REQUEST WHERE GUILD_ID = ?;",
        (guild.id,)
    ).fetchone()

    try:
        channel = guild.get_channel(channel_id)
        await channel.get_partial_message(msg_id).delete()

    except Exception as err:
        Logger(db).add_log("TUTORINSA", f"COULDN'T DELETE TUTOR REQUEST MESSAGE: {type(err)}: {err}")


async def tutor_request_callback(db: sqlite3.Connection, inte: discord.Interaction):
    roles_id = [i[0] for i in db.execute(
        "SELECT ROLE_ID FROM TUTOR_ROLES WHERE GUILD_ID=?;",
        (inte.guild_id,)
    ).fetchall()]

    common_roles = list(filter(lambda x: x.id in roles_id, inte.user.roles))

    if len(common_roles) != 1:
        c = db.execute(
            "SELECT MESSAGE_ID,CHANNEL_ID FROM TUTOR_ROLES_SELECTOR WHERE GUILD_ID=?;",
            (inte.guild_id,)
        ).fetchone()

        if c is None:
            await inte.response.send_message(
                "Aucun message de sélection de classe n'est défini, merci de contacter les administrateurs du serveur."
                "\n\nNo role selection message defined, please contact guild admins.",
                ephemeral=True
            )
            return

        msg = inte.guild.get_channel(c[1]).get_partial_message(c[0])
        if len(common_roles) == 0:
            await inte.response.send_message(
                f"Pour pouvoir demander un tutorat, merci de sélectionner votre classe dans {msg.jump_url}\n\n"
                f"In order to ask for a tutoring session, please select your class in {msg.jump_url}",
                ephemeral=True
            )
            return

        else:
            await inte.response.send_message(
                f"Vous avez plusieurs roles de classes. Pour pouvoir demander un tutorat, merci de sélectionner "
                f"votre classe actuelle dans {msg.jump_url}\n\n"
                f"You have multiple class roles. In order to ask for a tutoring session, please select your current "
                f"class in {msg.jump_url}",
                ephemeral=True
            )
            return

    await inte.response.send_message("TODO MODAL", ephemeral=True)

# TODO: Listener on button + modal for requesting tutoring session
