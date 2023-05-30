"""Set correct start end end time in the `tap-config.json`"""

import argparse
import json
import os
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser(description="Set up tap time filters")
parser.add_argument("--start-time", dest="start_time", type=str, default="")
parser.add_argument("--end-time", dest="end_time", type=str, default="")

args = parser.parse_args()


# Update the `tap_config.json` to have correct `start_time` and `end_time`.
# By default `start_time` is the start of the previous hour and `end_time`
# is the start of this hour.
# This way we ensure that hourly cron captures all required records.

now = datetime.now(tz=timezone.utc)

if args.end_time == "now":
    end_time = now
elif args.end_time:
    end_time = datetime.fromisoformat(args.end_time)
else:
    end_time = now.replace(
        minute=0, second=0, microsecond=0
    )  # Start of the current hour

if args.start_time:
    start_time = datetime.fromisoformat(args.start_time)
else:
    start_time = end_time - timedelta(seconds=3600)  # Hour before the end time


with open(f"{BASE_DIR}/tap-config.json", "r") as f:
    config = json.loads(f.read())

config["start_time"] = start_time.isoformat()
config["end_time"] = end_time.isoformat()

with open(f"{BASE_DIR}/tap-config.json", "w") as f:
    f.write(json.dumps(config, indent=4))
