# SPDX-License-Identifier: MIT
# Copyright (C) 2024 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import json
import os
from typing import Any

from Core.IsTestVersion import is_test_version


def get_config(config_key: str) -> Any:
    """
    :param config_key: The name of the config you want to get, use . as separators to get sub config
    :return: The data
    """

    module = config_key.split(".")[0]
    config_key = config_key.split(".")[1:]

    if module == "core":
        if not is_test_version():
            with open(f"CoreConfig{os.sep}config.json", "r") as f:
                config = json.load(f)

        else:
            with open(f"CoreConfig{os.sep}test_config.json", "r") as f:
                config = json.load(f)

    else:
        if not is_test_version():
            with open(f"Cogs{os.sep}{module}{os.sep}Config{os.sep}config.json", "r") as f:
                config = json.load(f)

        else:
            with open(f"Cogs{os.sep}{module}{os.sep}Config{os.sep}test_config.json", "r") as f:
                config = json.load(f)

    while config_key:
        config = config[config_key[0]]
        config_key.pop(0)

    return config
