# SPDX-License-Identifier: MIT
# Copyright (C) 2024 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import gc
import json
import sqlite3
import time
from typing import Union, List

import discord
from discord import Embed, ui, ButtonStyle
from discord.ext import commands

from GlobalModules.GetConfig import get_config
from GlobalModules.Logger import Logger


class Paginator:
    def __init__(self, database: sqlite3.Connection):
        self.database = database
        self.pages = []
        self.logger = Logger(self.database)

    def __update_page_properties(self, author: discord.Member):
        pages = []

        for i, j in enumerate(self.pages):
            pages.append(j)
            pages[-1].update(
                {
                    'footer': {
                        'text': f'{author.name} - Page {i + 1}/{len(self.pages)}',
                        'icon_url': f'{author.avatar.url}'
                    }
                }
            )

            if "color" not in pages[-1].keys():
                pages[-1].update({"color": get_config("core.base_embed_color")})

    def add_page(self, page: Embed, page_name: Union[str, None] = None):
        page_dict = dict(page.to_dict())

        if page_name is not None:
            page_dict.update({'PaginatorPageName': page_name.capitalize()})

        else:
            page_dict.update({'PaginatorPageName': None})

        self.pages.append(page_dict)

    @staticmethod
    def __make_view(current_page: int, pages: List[dict]) -> ui.View:
        max_page = len(pages)

        c_id = get_config('core.paginator_view_base_id')

        kwargs1 = {'style': ButtonStyle.grey, 'custom_id': f"{c_id}_B1", 'emoji': chr(9198)}
        kwargs2 = {'style': ButtonStyle.green, 'custom_id': f"{c_id}_B2", 'emoji': chr(9194)}
        kwargs3 = {'style': ButtonStyle.red, 'custom_id': f"{c_id}_B3", 'emoji': chr(9209), 'label': "Stop"}
        kwargs4 = {'style': ButtonStyle.green, 'custom_id': f"{c_id}_B4", 'emoji': chr(9193)}
        kwargs5 = {'style': ButtonStyle.grey, 'custom_id': f"{c_id}_B5", 'emoji': chr(9197)}

        # Buttons 1-2

        if current_page == 0:
            kwargs1.update({'disabled': True})
            kwargs2.update({'disabled': True, 'label': "1"})

        else:
            kwargs1.update({'disabled': False})
            kwargs2.update({'disabled': False, 'label': str(current_page)})

        if current_page <= 4:
            kwargs1.update({'label': "1"})

        else:
            kwargs1.update({'label': str(current_page - 3)})

        # Buttons 4-5

        if current_page + 1 == max_page:
            kwargs4.update({'disabled': True, 'label': str(max_page)})
            kwargs5.update({'disabled': True, 'label': str(max_page)})

        else:
            kwargs4.update({'disabled': False, 'label': str(current_page + 2)})
            kwargs5.update({'disabled': False})

        if max_page - current_page < 5:
            kwargs5.update({'label': str(max_page)})

        else:
            kwargs5.update({'label': str(current_page + 5)})

        view = ui.View()

        for kwargs in [kwargs1, kwargs2, kwargs3, kwargs4, kwargs5]:
            view.add_item(ui.Button(**kwargs))

        if max_page < 25:
            range_values = (0, max_page)

        else:
            if current_page <= 14:
                range_values = (0, 25)

            elif current_page >= max_page - 15:
                range_values = (max_page - 25, max_page)

            else:
                range_values = (current_page - 6, current_page + 7)

        options = []
        for i in range(*range_values):
            if pages[i]["PaginatorPageName"] is None:
                label = f"Page {i + 1}"

            else:
                label = pages[i]["PaginatorPageName"]

            kwargs = {'label': label, 'value': str(i), 'description': f"Show {label.lower()}"}
            if i == current_page:
                kwargs.update({'default': True})

            else:
                kwargs.update({'default': False})

            options.append(discord.SelectOption(**kwargs))

        view.add_item(discord.ui.Select(
            custom_id=f"{c_id}_S1",
            options=options,
            placeholder=f"Page {current_page + 1}"
        ))

        return view

    async def send_paginator(self,
                             interaction_ctx: Union[discord.Interaction, commands.Context],
                             ephemeral: bool = True,
                             **kwargs):

        if isinstance(interaction_ctx, discord.Interaction):
            send_callback = eval("interaction_ctx.response.send_message")
            author = interaction_ctx.user

        elif isinstance(interaction_ctx, commands.Context):
            send_callback = interaction_ctx.send
            author = interaction_ctx.author

        else:
            raise TypeError(
                f"Type of interaction_ctx is neither a context or an interaction ({type(interaction_ctx) = })"
            )

        self.__update_page_properties(author)

        if len(self.pages) == 1:
            await send_callback(embed=discord.Embed.from_dict(self.pages[0]), ephemeral=ephemeral, **kwargs)

        else:
            msg = await send_callback(
                embed=discord.Embed.from_dict(self.pages[0]),
                ephemeral=ephemeral,
                view=self.__make_view(0, self.pages),
                **kwargs
            )

            if isinstance(interaction_ctx, discord.Interaction):
                msg = await interaction_ctx.original_response()

            self.database.execute(
                "INSERT INTO PAGINATOR (MESSAGE_ID, CHANNEL_ID, GUILD_ID, USER_ID, DELETE_TS, PAGES, CURRENT_PAGE) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    msg.id,
                    msg.channel.id,
                    msg.guild.id,
                    author.id,
                    int(time.time() + get_config("core.paginator_delete_after")),
                    json.dumps(self.pages),
                    0
                )
            )

            self.logger.add_log(
                "PAGINATOR",
                f"Paginator sent in {msg.guild.id} => message id: {msg.id}"
            )

        print(f"Garbage collector send_paginator: {gc.collect()}")

    async def process_interaction(self, inter: discord.Interaction):
        if "custom_id" not in inter.data.keys():
            return

        custom_id = inter.data['custom_id']

        if not get_config('core.paginator_view_base_id') in inter.data["custom_id"]:
            return

        values = self.database.execute(
            "SELECT USER_ID, PAGES, CURRENT_PAGE FROM PAGINATOR WHERE MESSAGE_ID = ?",
            (inter.message.id,)
        ).fetchone()

        if values is None:
            return

        user_id, pages_str, current_page = values
        pages = json.loads(pages_str)

        if user_id != inter.user.id:
            return

        c_id = get_config('core.paginator_view_base_id')
        if custom_id == f"{c_id}_B1":
            await self.__change_page(pages, current_page - 4, inter)

        elif custom_id == f"{c_id}_B2":
            await self.__change_page(pages, current_page - 1, inter)

        elif custom_id == f"{c_id}_B3":
            await self.remove_paginator(inter)

        elif custom_id == f"{c_id}_B4":
            await self.__change_page(pages, current_page + 1, inter)

        elif custom_id == f"{c_id}_B5":
            await self.__change_page(pages, current_page + 4, inter)

        elif custom_id == f"{c_id}_S1":
            if inter.data['values'][0] == str(current_page):
                await inter.response.defer()

            else:
                try:
                    new_page = int(inter.data['values'][0])

                except ValueError:
                    return

                await self.__change_page(pages, new_page, inter)
                self.database.execute(
                    "SELECT USER_ID, PAGES, CURRENT_PAGE FROM PAGINATOR WHERE MESSAGE_ID = ?",
                    (inter.message.id,)
                )

        print(f"Garbage collector paginator.process_interaction: {gc.collect()}")

    async def __change_page(self, pages: List[dict], new_page: int, interaction: discord.Interaction):
        if new_page < 0:
            new_page = 0

        elif new_page >= len(pages):
            new_page = len(pages) - 1

        view = self.__make_view(new_page, pages)
        await interaction.response.edit_message(embed=discord.Embed.from_dict(pages[new_page]), view=view)

        self.database.execute(
            "UPDATE PAGINATOR SET CURRENT_PAGE = ? WHERE MESSAGE_ID = ?",
            (new_page, interaction.message.id)
        )

        self.database.commit()

    async def remove_paginator(
            self,
            msg_interaction: Union[discord.Message, discord.PartialMessage, discord.Interaction]
    ):

        if isinstance(msg_interaction, (discord.Message, discord.PartialMessage)):
            msg_id = msg_interaction.id
            edit = msg_interaction.edit

        elif isinstance(msg_interaction, discord.Interaction):
            msg_id = msg_interaction.message.id
            edit = msg_interaction.response.edit_message

        else:
            return

        if edit is not None:
            try:
                await edit(view=None)

            except (discord.HTTPException, discord.Forbidden, TypeError, ValueError):
                pass

        self.database.execute("DELETE FROM PAGINATOR WHERE MESSAGE_ID = ?;", (msg_id,))
        self.database.commit()

        print(f"Garbage collector paginator.remove_paginator: {gc.collect()}")
