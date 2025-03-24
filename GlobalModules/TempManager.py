# SPDX-License-Identifier: MIT
# Copyright (C) 2024 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import os.path
import random
import shutil
import string
import time

from GlobalModules.GetConfig import get_config


class TempManager:
    def __init__(self, after_id: str = None, time: int = None, id_length: int = None) -> None:
        """
        :param after_id: The file / directory name which comes after temp ID, specify file extension if needed
        :param time: The time in seconds we want the file / directory to last after last modification (must be >= 1)
        :param id_length: The length of the ID, recommended to be at least 16 (must be >= 1)
        """

        self.after_id = after_id

        if time is None:
            self.time = get_config("core.temp_dir.default_max_time")

        else:
            if time <= 0:
                raise ValueError("Time specified for TempManager is less than 1")

            else:
                self.time = time

        if id_length is None:
            self.id_length = get_config("core.temp_dir.default_id_length")

        else:
            if id_length <= 0:
                raise ValueError("ID length specified for TempManager is less than 1")

            else:
                self.id_length = id_length

        self.temp_dir = get_config("core.temp_dir.path")

        if not os.path.exists(self.temp_dir):
            os.mkdir(self.temp_dir)

    def __make_path_temp(self) -> str:
        """
        :return: Temp file path according to infos given in __init__
        """

        while True:
            id_ = f"{self.__create_random_string(length=self.id_length)}_{self.time:x}"  # {int:x} => to hex
            path = f"{self.temp_dir}{os.sep}{id_}{'_' + self.after_id if self.after_id else ''}"

            if not os.path.exists(path):
                return path

    def make_temp_dir(self) -> str:
        """
        :return: The temp dir path
        """

        path = self.__make_path_temp()
        os.mkdir(path)

        return path

    def make_temp_file(self) -> str:
        """
        :return: The temp file path
        """

        path = self.__make_path_temp()
        with open(path, "w"):
            pass

        return path

    @staticmethod
    def __create_random_string(length: int = 32, contain_digits: bool = False) -> str:
        """
        :param length: The length of the random screen
        :param contain_digits: If set to True, the random string will contain digits
        :return: The random string
        """

        chars = string.ascii_letters
        if contain_digits:
            chars += string.digits

        return "".join([random.choice(chars) for _ in range(length)])

    @staticmethod
    def purge_temp(purge_all: bool = False) -> None:
        """
        :param purge_all: Set to true if you want to clean temp dir
        :return: None
        """

        temp_dir = get_config("core.temp_dir.path")

        if not os.path.exists(temp_dir):
            os.mkdir(temp_dir)

        current_time = time.time()

        for i in os.listdir(temp_dir):
            path = f"{temp_dir}{os.sep}{i}"
            file_time = int(i.split("_")[1], 16)

            try:
                if purge_all:
                    if os.path.isfile(path):
                        os.remove(path)
                    else:
                        shutil.rmtree(path)

                elif os.stat(path).st_mtime < current_time - file_time:
                    print(f"TempManager: removed {path}")

                    if os.path.isfile(path):
                        os.remove(path)

                    else:
                        shutil.rmtree(path)

            except Exception:
                pass
