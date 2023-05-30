#!/usr/bin/env python3

import json
import os
import sys
import typing as t
from datetime import datetime

import backoff
import requests
import singer
from singer import Schema, utils

STREAM_NAME = "decisions"
ENDPOINT_URL = "/history/api/v1/decisions"
ORDER = "asc"
LIMIT = 1000
REQUIRED_CONFIG_KEYS = [
    "api_key",
    "base_url",
    "start_time",
    "end_time",
    "include_node_results",
    "include_external_resources",
]

LOGGER = singer.get_logger()

Config = t.Dict[str, t.Any]
State = t.Dict[str, t.Any]


def get_abs_path(path) -> str:
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def load_schema() -> Schema:
    """Load schemas from schemas folder"""
    schema_path = get_abs_path("schemas/schema.json")
    with open(schema_path) as file:
        return Schema.from_dict(json.load(file), selected=True)


def _backoff_handler(details):
    LOGGER.error(
        "Backing off {wait:0.1f} seconds after {tries} tries".format(**details)
    )


@backoff.on_exception(
    backoff.expo, requests.RequestException, max_tries=3, on_backoff=_backoff_handler
)
def _make_request(
    url: str, api_key: str, params: t.Dict[str, t.Any]
) -> t.Dict[str, t.Any]:
    LOGGER.info(f"Requesting {url} with query params {str(params)}")
    response = requests.get(url, params=params, headers={"X-Api-Key": api_key})
    response.raise_for_status()
    return response.json()


def fetch_records(
    base_url: str,
    api_key: str,
    start_time: datetime,
    end_time: datetime,
    include_external_resources: bool = False,
    include_node_results: bool = False,
) -> t.Generator[t.Dict[str, t.Any], None, None]:
    """Fetch a batch of records from Taktile Decision History API

    Args:
        base_url (str): Workspace base URL
        api_key (str): API Key
        start_time (datetime): Filter decision history records to only return those that
            were recorded after the `start_time`.
        end_time (datetime): Filter decision history records to only return those that
            were recorded before the `end_time`.
        include_external_resources (bool, optional): Indicate if additional data for external
            resources that were fetched should be included in the response. Defaults to False.
        include_node_results (bool, optional): Indicate if additional data for Nodes execution
            should be included in the response. Defaults to False.

    Returns:
        t.Generator[t.Dict[str, t.Any], None, None]: Returns a generator with decisions history records

    """

    params: t.Dict[str, t.Any] = {
        "limit": LIMIT,
        "include_external_resources": include_external_resources,
        "include_node_results": include_node_results,
        "order": ORDER,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
    }

    url = base_url + ENDPOINT_URL

    has_next = True
    next_cursor = None
    # Fetch all records from `start_time` to `end_time`
    while has_next:
        if next_cursor:
            params["after"] = next_cursor

        response_data = _make_request(url, api_key, params)
        LOGGER.info("Decisions batch fetched")

        yield from response_data["decisions"]

        has_next = response_data["pagination"]["has_next"]
        next_cursor = response_data["pagination"]["next_cursor"]


def sync(config: Config, state: State) -> None:
    """Sync data from tap source"""

    LOGGER.info("Syncing stream: " + STREAM_NAME)

    schema = load_schema()

    # Ensure times are in the correct format
    start_time = datetime.fromisoformat(config["start_time"])
    end_time = datetime.fromisoformat(config["end_time"])

    singer.write_schema(
        stream_name=STREAM_NAME,
        schema=schema.to_dict(),
        key_properties=["id"],
    )
    number_of_records = 0

    for row in fetch_records(
        config["base_url"],
        config["api_key"],
        start_time,
        end_time,
        include_external_resources=config["include_external_resources"],
        include_node_results=config["include_node_results"],
    ):
        singer.write_record(STREAM_NAME, row)
        number_of_records += 1

    LOGGER.info(f"Loaded {number_of_records} records from the tap")


@utils.handle_top_exception(LOGGER)
def main():
    # Parse command line arguments
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)

    if args.discover:
        LOGGER.error("There is just a single stream, no discovery is needed")
        sys.exit(1)

    sync(args.config, args.state)


if __name__ == "__main__":
    main()
