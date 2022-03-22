# Imports
import argparse
import asyncio
import json
import pdb
import re
from shutil import rmtree

import aiohttp
from aiohttp import ClientSession
from aiopath import AsyncPath
from tqdm.asyncio import tqdm_asyncio

from util.asyncio import to_thread
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
            "https://raw.githubusercontent.com/nextml/caption-contest-data/gh-pages"
        )
        self.urls = {
            "contests": [self.urlize(contest_id) for contest_id in self.contest_ids],
            "winners": f"{self.prefix}/nyccwinners/nyc_winners.json",
        }
        # Will be assigned an aiohttp.ClientSession object in the download function
        self.session = None
        # Will be assigned a dict of winning captions for each contest
        self.winners = None

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
            "id": contest_id,
            "cartoon": f"{prefix}/cartoons/{contest_id}.jpg",
            "captions": f"{prefix}/summaries/{contest_id}.csv",
        }

    async def download(self):
        """
        Downloading script.
        """
        async with ClientSession() as session:
            # Pass session object as a class attribute so that we don't have to keep
            # calling it in the download and fetch functions below. Since self.session
            # refers to the same ClientSession object as session, it will be closed
            # when we exit this context manager
            self.session = session
            # All contest winners are in the same file, so download that file first
            self.winners = await self.fetch_winners(self.urls["winners"])
            # For each contest, download its cartoon and captions, then append its
            # winners and write into files
            tasks = [
                self.fetch_and_write_contest(contest_urls)
                for contest_urls in self.urls["contests"]
            ]
            await tqdm_asyncio.gather(*tasks)

    async def fetch_winners(self, url):
        """
        Fetch and parse JSON of contest winning captions.
        """
        response = await self.fetch(url)
        if response is None:
            logger.info(
                "An exception was encountered while retrieving contest winners. No data will be returned."
            )
            return None

        winners = {"unavail_id": []}
        data = await response.json(content_type="text/plain")

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

    async def fetch_and_write_contest(self, urls):
        """
        Fetch and write cartoon, captions and winners of a contest into files.
        """
        contest_id = urls["id"]

        path_contest = AsyncPath(f"./data/{contest_id}")
        override = self.cli_args.override
        path_contest_exists = await path_contest.exists()

        # Skip if --override is not set and path already exists
        if override is False and path_contest_exists is True:
            return

        # If path already exists and --override is set, delete directory
        if path_contest_exists is True:
            # Assuming path is always a directory
            await to_thread(rmtree, path_contest)

        # Send requests
        url_cartoon = urls["cartoon"]
        url_captions = urls["captions"]
        response_cartoon, response_captions = await asyncio.gather(
            self.fetch(url_cartoon), self.fetch(url_captions)
        )

        # Validation check
        if response_cartoon is None or response_captions is None:
            logger.info(
                "An exception was encountered while retrieving data for contest #%s. No data will be returned.",
                contest_id,
            )
            return

        # Grab content from responses as bytes
        content_cartoon, content_captions = await asyncio.gather(
            response_cartoon.read(), response_captions.read()
        )
        # Store contest winners as text
        content_winners = await to_thread(json.dumps, self.winners.get(contest_id, {}))

        # Re-create contest directory
        await path_contest.mkdir()

        # Write cartoon, caption and winner data to respective files
        path_cartoon = AsyncPath(f"{str(path_contest)}/cartoon.jpg")
        path_captions = AsyncPath(f"{str(path_contest)}/captions.csv")
        path_winners = AsyncPath(f"{str(path_contest)}/winners.json")

        await asyncio.gather(
            path_cartoon.write_bytes(content_cartoon),
            path_captions.write_bytes(content_captions),
            path_winners.write_text(content_winners),
        )

    async def fetch(self, url):
        """
        Helper that sends a request to a URL and returns a response or handles errors
        (from Brad Solomon, https://realpython.com/async-io-python/#a-full-program-asynchronous-requests)
        """
        try:
            response = await self.session.request("GET", url)
            # Raise an aiohttp.ClientResponseError if the response status is 400 or higher.
            response.raise_for_status()
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
            return response


# Execution
if __name__ == "__main__":
    DownloadDataScript().main()
