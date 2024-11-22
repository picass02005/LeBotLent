"""
    The following script is used to generate a new cog or permission files
"""
import json
import os
import time
from typing import Union, Callable


def safe_input(
        display_message: str,
        type_input: int = 1,
        check_input: Callable[[Union[bool, int, str]], bool] = lambda x: True
) -> Union[bool, int, str]:
    """
    :param display_message: Message to display to the user
    :param type_input: The type of input you want: 1 = str; 2 = integer; 3 = boolean
    :param check_input: A callback made to check if an input is valid
    :return: The checked answer
    """

    while True:
        ans_str = input(f"\n{display_message}\n>>> ")
        ans = None

        if type_input == 1:
            ans = ans_str

        elif type_input == 2:
            try:
                ans = int(ans_str)

            except ValueError:
                pass

        elif type_input == 3:
            if ans_str.lower() in ["y", "yes"]:
                ans = True

            elif ans_str.lower() in ["n", "no"]:
                ans = False

        if ans is not None:
            if check_input(ans):
                return ans

            else:
                print("Your input is incorrect.")


def run_action():
    # === Main page === #
    action = safe_input(
        display_message="Select an action to make by typing its number:\n"
                        "0 : close this program\n"
                        "1 : Generate a new Cog\n"
                        "2 : Generate permission files for a Cog\n"
                        "3 : Generate config files for a Cog",
        type_input=2,
        check_input=lambda x: x in [0, 1, 2, 3]
    )

    if action == 0:
        exit(0)

    elif action == 1:
        cog_name = safe_input(
            display_message="Give your new cog name in CamelCase.\n"
                            "If this cog already exist, your input will be invalidated",
            type_input=1,
            check_input=lambda x: not os.path.exists(f"Cogs/{x}") and x != ""
        )

        generate_cog(cog_name)

    elif action == 2:
        cog_name = safe_input(
            display_message="Give the name of the cog where you want to create permission files.\n"
                            "If this cog doesn't exist, your input will be invalidated",
            type_input=1,
            check_input=lambda x: os.path.isdir(f"Cogs/{x}") and x != ""
        )

        generate_permission_files(cog_name)

    elif action == 3:
        cog_name = safe_input(
            display_message="Give the name of the cog where you want to create config files\n"
                            "If this cog doesn't exist, your input will be invalidated",
            type_input=1,
            check_input=lambda x: os.path.isdir(f"Cogs/{x}") and x != ""
        )

        generate_config_files(cog_name)


def generate_cog(cog_name: str):
    os.mkdir(f"Cogs/{cog_name}")

    with open(f"Cogs/{cog_name}/main.py", "w") as f:
        f.write(
            f"import sqlite3\n\n"
            f"from discord import app_commands\n"
            f"from discord.ext import commands\n\n"
            f"from GlobalModules.HasPerm import has_perm\n\n\n"
            f"# === DO NOT CHANGE CLASS NAME OR __init__ PARAMETERS === #\n"
            f"class {cog_name}(commands.GroupCog):\n"
            f"    def __init__(self, bot: commands.AutoShardedBot, database: sqlite3.Connection):\n"
            f"        self.bot: bot = bot\n"
            f"        self.database = database\n\n\n"
            f"# === DO NOT REMOVE THE FOLLOWING OR CHANGE PARAMETERS === #\n\n"
            f"async def setup(bot: commands.AutoShardedBot, database: sqlite3.Connection):\n"
            f"    await bot.add_cog({cog_name}(bot, database))\n"
        )

    print(f"Cog {cog_name} created successfully")


def check_files_not_exist(cog_name: str, *args) -> bool:
    for i in args:
        if os.path.exists(f"Cogs/{cog_name}/Config/{i}"):
            print(f"{i} is already existing in this cog. Please remove it if you want to regenerate it.")
            return False

    return True


def generate_permission_files(cog_name: str):
    if not os.path.exists(f"Cogs/{cog_name}/Config"):
        os.mkdir(f"Cogs/{cog_name}/Config")

    if not check_files_not_exist(cog_name, "permissions.json", "test_permissions.json"):
        return

    for i in ("permissions.json", "test_permissions.json"):
        with open(f"Cogs/{cog_name}/Config/{i}", "w") as f:
            f.write(json.dumps(
                {
                    "command_name_here": {
                        "roles": [], "users": [], "permission_code": [], "guilds": [], "group": ["bots_admin"]
                    }
                },
                indent=4)
            )

    print(f"Permission files for {cog_name} created successfully")


def generate_config_files(cog_name: str):
    if not os.path.exists(f"Cogs/{cog_name}/Config"):
        os.mkdir(f"Cogs/{cog_name}/Config")

    if not check_files_not_exist(cog_name, "config.json", "test_config.json"):
        return

    for i in ("config.json", "test_config.json"):
        with open(f"Cogs/{cog_name}/Config/{i}", "w") as f:
            f.write("{}")

    print(f"Config files for {cog_name} created successfully")


if __name__ == "__main__":
    while True:
        run_action()
        time.sleep(3)
        print("")

else:
    print("This script can't be imported.")
    exit(-1)
