from geotrellis_summary_update.slack import slack_webhook
from geotrellis_summary_update.dataset import get_dataset_status
import logging
import os

if "ENV" in os.environ:
    ENV = os.environ["ENV"]
else:
    ENV = "dev"


def handler(event, context):
    name = event["name"]
    analyses = event["analyses"]

    # check status of dataset requests
    dataset_statuses = dict()
    for analysis in analyses:
        for dataset_id in analysis["dataset_ids"].values():
            dataset_statuses[dataset_id] = get_dataset_status(dataset_id, ENV)

    pending_statuses = list(
        filter(lambda status: status == "pending", dataset_statuses.values())
    )
    if pending_statuses:
        event.update({"status": "PENDING"})
        return event

    error_statuses = list(
        filter(lambda id_status: id_status[1] == "failed", dataset_statuses.items())
    )
    if error_statuses:
        error_ids = ", ".join([dataset_id for dataset_id, status in error_statuses])
        error_message = (
            "Failed to run {} summary dataset update. "
            "The following datasets returned 'failed' status "
            "when trying to update in API: {}".format(name, error_ids)
        )

        logging.info(error_message)
        slack_webhook("ERROR", error_message, ENV)
        return {"status": "FAILED"}

    # send slack info message
    slack_webhook(
        "INFO", "Successfully ran {} summary dataset update".format(name), ENV
    )
    return {
        "status": "SUCCESS",
        "name": name,
        "feature_src": event["feature_src"],
        "analyses": analyses,
    }


if __name__ == "__main__":
    print(
        handler(
            {
                "env": "dev",
                "name": "new_area_test",
                "feature_src": "s3://gfw-pipelines-dev/geotrellis/features/*.tsv",
                "analyses": {
                    "gladalerts": {
                        "daily_alerts": "56aaab8b-35de-466b-96aa-616377ed3df7",
                        # "weekly_alerts": "Glad Alerts - Weekly - Geostore - User Areas",
                        # "summary": "Glad Alerts - Summary - Geostore - User Areas",
                    }
                },
            },
            None,
        )
    )
