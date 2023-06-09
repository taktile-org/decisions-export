# Export Decision History

This repository provides an example code for exporting the Taktile Decision History to the system of your choice using [Singer](https://www.singer.io/#what-it-is) Taps and Targets.

## Singer
Singer is a open-source specification that facilitates data transfer between various [Taps](https://www.singer.io/#taps) and [Targets](https://www.singer.io/#targets). Tap is an application that extracts the data from the source system and writes each exported record to stdout in the specified format. Target is an application that reads records from stdout and loads them into the target system. Singer describes the format of the records that are being transferred and how Tap and Target operate.
Learn more about Singer specification in their [documentation](https://github.com/singer-io/getting-started/tree/master)

## Taktile Tap
This repository provides a Tap that extracts Decision History Records from the Taktile API and exports them to the [Stitch Target](https://pypi.org/project/target-stitch/). You can easily adapt the logic to export the data to a different Target. You can use one of the [available targets](https://www.singer.io/#targets) or create your own.

## Setting up
To export the data, you need to set up credentials for both the Tap and the Target:

### Tap settings
Configure the Tap settings in the `tap-config.json` file. The settings include:

- `base_url` - The base URL of the Taktile Workspace from which you want to extract decisions. Follow [our guide](https://help.taktile.com/en/articles/40930-integrate-a-taktile-decision-flow-into-your-backend) to lear how to get base URL. The value should be similar to `https://<workspace-name>.<organization-name>.decide.taktile.com`.
- `api_key` - Taktile API Key. Follow [our guide](https://help.taktile.com/en/articles/28423-api-keys) to learn how to get an API Key.
- `start_time` - The start time is used to filter the records retrieved from the Taktile API. It specifies the timestamp after which the decisions should be included in the response. Only decisions that happened after the `start_time` will be exported. Must be formatted according to the [ISO 8610](https://www.iso.org/iso-8601-date-and-time-format.html). The default value is calculated dynamically as the start of the **previous** full hour.
- `end_time` - The end time is used for filtering the records retrieved from the Taktile API. It specifies the timestamp before which the decisions should be included in the response. Only decisions that happened before the `end_time` will be exported. Must be formatted according to the [ISO 8610](https://www.iso.org/iso-8601-date-and-time-format.html). The default value is calculated dynamically as the start of the **current** full hour.
- `include_node_results` - A boolean flag indicating whether intermediate execution results for each Decision Flow node should be included in the exported data. The default value is `false`
- `include_external_resources` - A boolean flag indicating whether detailed external resources data should be included in the exported data. The default value is `false`

Get the `base_url` and `api_key` from the Taktile platform and update the corresponding fields in the `tap-config.json` file. Also, decide whether you need to include node results and detailed external resources data. You don't need to update the `start_time` and `end_time` values at this point as they are configured just before executing the Tap.

### Target settings
Configure the Target settings in the `target-config.json` file. The settings include:

- `client_id` - Stitch client ID. Consult the [Stitch documentation](https://www.stitchdata.com/docs/developers/import-api/api) to find where to obtain this value.
- `token` - Stitch API token. Consult the [Stitch documentation](https://www.stitchdata.com/docs/developers/import-api/api) for instructions on getting this value.
- `big_batch_url` and `small_batch_url` - The Stitch API URLs to which the exported data will be uploaded. Refer to the [Stitch API docs]((https://www.stitchdata.com/docs/developers/import-api/api#base-urls)) to determine which URL to use.
- `batch_size_preferences` - An internal Stitch Target setting; leave it unchanged.
- `disable_collection` - A boolean flag indicating whether Stitch can collect anonymous usage statistics.

Get the `client_id` and `token` from Stitch and update the corresponding fields in the `target-config.json` file. Also, ensure that the `big_batch_url` and `small_batch_url` are set correctly based on the region where you are running Stitch. Otherwise, you will get an error during the export.

### Requirements
Both the Tap and Target require their own execution environment. You will notice two requirements files: `tap_requirements.txt` and `target_requirements.txt`. The `run.sh` script takes care of setting up the virtual environments, installing the necessary dependencies and executing the exporting logic in correct environments.

## Execution

To execute the sync manually, run the following command using bash:
```bash
./run.sh
```

This command will fetch all the decisions that occurred in the previous full hour and send them to Stitch. For example, if the command is executed at 15:05 on May 30, 2023, the decisions will be fetched for the period between 14:00 and 15:00 on May 30, 2023. This allows you to easily run an hourly job to synchronize all decisions from the last hour to your warehouse.

To automate the export process, schedule the script to run using cron. `10 * * * *` ([details](https://crontab.guru/#10_*_*_*_*)). We recommend running the script 10 minutes past the full hour to ensure that all internal archiving jobs are completed, and you get the complete history of decisions for the previous hour.

If needed, you can provide custom start and end times to the script by specifying the `TAP_START_TIME` and `TAP_END_TIME` environment variables during execution:
```bash
TAP_START_TIME=2023-05-22T15:00:00 TAP_END_TIME=2023-05-22T17:00:00 ./run.sh
```

Ensure that the values for `TAP_START_TIME` and `TAP_END_TIME` are formatted according to the ISO 8601 standard.
