# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

from collections.abc import Awaitable, Callable
from typing import Any, Tuple

import discord


class ConfirmSelector(discord.ui.Select):
    def __init__(
            self,
            author: discord.Member,
            callback: Callable[[discord.Interaction, ...], Awaitable[...]],
            *args: Tuple[Any, ...]
    ):
        self.author = author
        self.callback: Callable[[discord.Interaction, ...], Awaitable[...]] = callback
        self.args = args

        placeholder = "Please confirm your action"

        super().__init__(
            placeholder=placeholder,
            options=[
                discord.SelectOption(label="Yes", value="y", description="Confirm your action"),
                discord.SelectOption(label="No", value="n", description="Cancel your action")
            ]
        )

    async def callback(self, inte: discord.Interaction) -> None:
        if inte.user.id != self.author.id:
            await inte.response.send_message("Only the author can answer this", ephemeral=True)
            return

        if int(inte.data['values'][0]) == "y":
            await self.callback(inte, *self.args)

        else:
            await self.inte.send_message("Action cancelled", ephemeral=True)
