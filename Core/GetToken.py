from GlobalModules.GetConfig import get_config


def get_token() -> str:
    """
    :return: The bot token to use
    """

    with open(get_config("core.token"), "r") as f:
        return f.read()
