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

REQUIRED_CONFIG_KEYS = [
    "api_key",
    "base_url",
    "start_time",
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
    start_time: datetime | None = None,
    include_external_resources: bool = False,
    include_node_results: bool = False,
) -> t.Generator[t.Dict[str, t.Any], None, None]:
    params: t.Dict[str, t.Any] = {
        "limit": 1000,
        "include_external_resources": include_external_resources,
        "include_node_results": include_node_results,
        "order": "asc",
    }
    if start_time:
        params["start_time"] = start_time.isoformat()

    url = base_url + ENDPOINT_URL

    has_next = True
    next_cursor = None
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

    singer.write_schema(
        stream_name=STREAM_NAME,
        schema=schema.to_dict(),
        key_properties=["id"],
        bookmark_properties=["end_time"],
    )

    max_bookmark = None
    bookmark_column = "end_time"

    start_time_config = config.get("start_time")
    start_time = (
        datetime.fromisoformat(start_time_config) if start_time_config else None
    )

    for row in fetch_records(
        config["base_url"],
        config["api_key"],
        start_time,
        include_external_resources=config["include_external_resources"],
        include_node_results=config["include_node_results"],
    ):
        singer.write_record(STREAM_NAME, row)

        max_bookmark = (
            max(max_bookmark, row[bookmark_column])
            if max_bookmark
            else row[bookmark_column]
        )

    singer.write_state({STREAM_NAME: max_bookmark})


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
