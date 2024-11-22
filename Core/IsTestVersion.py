import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-t', dest='test_version', action="store_true", help='Indicate if you use test version')
args = parser.parse_args()


def is_test_version(print_message: bool = False) -> bool:
    """
    Indicates if the bot instance is prod or test
    :param print_message: Print a message indicating if the bot is test version or no
    :return: bool
    """

    global args

    if print_message:
        if args.test_version:
            tp = "TEST"

        else:
            tp = "PROD"

        print(
            f"################\n"
            f"# CHUCK NOBOT  #\n"
            f"# ------------ #\n"
            f"# {tp} VERSION #\n"
            f"################"
        )

    return args.test_version
