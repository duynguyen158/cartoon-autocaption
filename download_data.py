# Imports
import argparse
import asyncio
import pdb
import re

import aiofiles
import aiohttp
from aiohttp import ClientSession

from util.logconf import logging

# Configs
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Methods
class DownloadDataScript:
    def __init__(self, sys_argv=None):
        """
        Initializer.
        """
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

        self.cli_args = parser.parse_args(sys_argv)
        self.contest_ids = self.identify()
        self.prefix = (
            "https://raw.githubusercontent.com/nextml/caption-contest-data2/gh-pages"
        )
        self.urls = {
            "contests": [self.urlize(contest_id) for contest_id in self.contest_ids],
            "winners": f"{self.prefix}/nyccwinners/nyc_winners.json",
        }

    def main(self):
        """
        Main script.
        """
        asyncio.run(self.download())

    def identify(self):
        """
        Create a list of contest IDs from given command line arguments.
        """
        cli_args = self.cli_args
        if cli_args.list is not None:
            # Duplicate contest IDs are treated as one
            return set(cli_args.list)
        else:
            # Grab every contest from start to end, inclusively
            return range(cli_args.start, cli_args.end + 1)

    def urlize(self, contest_id):
        """
        Grab data URLs given a contest ID.
        """
        prefix = self.prefix
        return {
            "cartoon": f"{prefix}/cartoons/{contest_id}.jpg",
            "captions": f"{prefix}/summaries/{contest_id}.csv",
        }

    async def download(self):
        """
        Downloading script.
        """
        async with ClientSession() as session:
            # All contest winners are in the same file, so download that file first
            winners = await self.download_winners(
                url=self.urls["winners"], session=session
            )
            # For each contest, download its cartoon and captions, then append its winners
            await self.download_contests(
                url=self.urls["contests"], winners=winners, session=session
            )

    async def download_winners(self, url, session):
        """
        Fetch and parse JSON of contest winning captions.
        """
        winners = {"unavail_id": []}

        try:
            response = await session.request("GET", url)
            # Raise an aiohttp.ClientResponseError if the response status is 400 or higher.
            response.raise_for_status()
            data = await response.json(content_type="text/plain")

        except (aiohttp.ClientError, aiohttp.http_exceptions.HttpProcessingError) as e:
            logger.error(
                "aiohttp exception for %s [%s]: %s",
                url,
                getattr(e, "status", None),
                getattr(e, "message", None),
                stack_info=True,
            )

        except Exception as e:
            logger.exception(
                "Non-aiohttp exception occured: %s", getattr(e, "__dict__", {})
            )

        else:
            # Append contest ID as a key-value pair
            for d in data:
                # Assuming d["data"] and d["data"]["cartoon"] are always available
                contest = d["data"]["cartoon"]
                # Fetch ID (e.g., 660) from contest title (e.g., Contest #660)
                contest_id = re.search(r"#\d+", contest["title"])
                if contest_id is not None:
                    contest_id = int(contest_id.group()[1:])
                    winners[contest_id] = d
                else:
                    logger.warning(
                        "Unable to find or parse contest ID from this JSON object: %s",
                        d,
                    )
                    winners["unavail_id"].append(d)

        return winners

    async def download_contests(self, url, winners, session):
        """
        Fetch and save cartoons, captions and winners of every specified contest.
        """
        pdb.set_trace()


# Execution
if __name__ == "__main__":
    DownloadDataScript().main()
