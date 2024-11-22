import json
import time

import discord.ext.commands

from Core.IsTestVersion import is_test_version
from GlobalModules.GetConfig import get_config


class CommandPrefix:
    def __init__(self):
        self.__config = {'bot_admin': [], 'prefix': "", 'next_update': 0}
        self.__update_config()

    def __update_config(self):
        if is_test_version():
            filename_startswith = "test_"

        else:
            filename_startswith = ""

        with open(f"CoreConfig/Groups/{filename_startswith}bots_admin.json", "r") as f:
            self.__config['bot_admin'] = [i['id'] for i in json.loads(f.read())]

        self.__config['prefix'] = get_config("core.bot_admin_prefix")
        self.__config['next_update'] = int(time.time() + get_config("core.update_config_prefix_delay"))

    async def prefix_callback(self, _, message: discord.Message) -> str:
        if time.time() > self.__config['next_update']:
            self.__update_config()

        if message.author.id in self.__config['bot_admin']:
            return self.__config['prefix']

        return message.content.split(" ")[0] + "NO"

    def get_allowed_users(self):
        self.__update_config()
        return self.__config['bot_admin']

    def get_prefix(self):
        return self.__config['prefix']
