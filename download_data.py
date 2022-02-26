# Imports
import argparse

from util.logconf import logging

# import pdb


# Configs
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# Methods
def main(sys_argv=None):
    """
    Main script.
    """
    # print(sys.argv)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--start",
        default=660,
        help="Starting contest ID. Used with --to to create a range of step 1.",
        type=int,
    )
    parser.add_argument(
        "--end",
        default=790,
        help="Ending contest ID. Used with --from to create a range of step 1.",
        type=int,
    )
    parser.add_argument(
        "-l",
        "--list",
        nargs="+",
        help="Discrete list of contests (by contest ID) to retrieve. Will ignore --to and --from.",
        type=int,
    )
    parser.add_argument(
        "--override",
        default=False,
        help="Whether to override data of any contest already downloaded.",
        action="store_true",
    )

    cli_args = parser.parse_args(sys_argv)
    contest_ids = identify(cli_args)
    logging.info(list(contest_ids))


def identify(cli_args):
    """
    Create a list of contest IDs from given arguments.
    """
    if cli_args.list is not None:
        # Duplicate contest IDs are treated as one
        return set(cli_args.list)
    else:
        # Grab every contest from start to end, inclusively
        return range(cli_args.start, cli_args.end + 1)


# Execution
if __name__ == "__main__":
    main()
