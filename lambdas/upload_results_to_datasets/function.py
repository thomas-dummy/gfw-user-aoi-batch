from botocore.exceptions import ClientError
from geotrellis_summary_update.slack import slack_webhook
from geotrellis_summary_update.dataset import upload_dataset
import boto3
import os


def handler(event, context):
    env = event["env"]
    job_flow_id = event["job_flow_id"]
    analyses = event["analyses"]
    result_bucket = event["result_bucket"]
    result_dir = event["result_dir"]
    feature_type = event["feature_type"]
    name = event["name"]
    upload_type = event["upload_type"]

    # checks status of job
    emr_client = boto3.client("emr")
    cluster_description = emr_client.describe_cluster(ClusterId=job_flow_id)
    status = cluster_description["Cluster"]["Status"]

    error_message = "Failed to update {} summary datasets. Cluster with ID={} failed to complete analysis.".format(name, job_flow_id)

    if status["State"] == "TERMINATED":
        # only update AOIs atomically, so they don't get into a partially updated state if the
        # next nightly batch happens before we can fix partially updated AOIs
        if status["StateChangeReason"]["Code"] != "ALL_STEPS_COMPLETED":
            slack_webhook("ERROR", error_message, env)
            return {"status": "FAILED"}

        s3_client = boto3.client("s3")
        analysis_result_urls = dict()

        analysis_names = analyses.keys()
        analysis_result_map = get_analysis_result_map(result_bucket, result_dir, analysis_names, s3_client)

        for analysis_name in analysis_names:
            analysis_path = analysis_result_map[analysis_name]
            sub_analyses = analyses[analysis_name].keys() # get_analysis_result_dirs(analysis_name, analysis_path, feature_type)
            analysis_result_urls[analysis_name] = dict()

            for sub_analysis in sub_analyses:
                try:
                    sub_analysis_result_dir = get_sub_analysis_result_dir(analysis_path, sub_analysis, feature_type)

                    # this will throw exception if success file isn't present
                    success_file = s3_client.head_object(
                        Bucket=result_bucket,
                        Key="{}/_SUCCESS".format(sub_analysis_result_dir)
                    )

                    object_list = s3_client.list_objects(Bucket=result_bucket, Prefix=sub_analysis_result_dir)
                    keys = [object["Key"] for object in object_list['Contents']]
                    csv_keys = filter(lambda key: key.endswith(".csv"), keys)

                    analysis_result_urls[analysis_name][sub_analysis] = [
                        "https://{}.s3.amazonaws.com/{}".format(result_bucket, key)
                        for key in csv_keys
                    ]
                except ClientError:
                    # send slack message
                    slack_webhook("ERROR", error_message, env)
                    return {"status": "FAILED"}

        # concat to each datastore
        for analysis in analyses.keys():
            for sub_analysis in analyses[analysis].keys():
                upload_dataset(
                    analyses[analysis][sub_analysis],
                    analysis_result_urls[analysis][sub_analysis],
                    upload_type,
                    env
                )

        return {
            "status": "SUCCESS",
            "name": name,
            "env": env,
            "analyses": analyses,
            "feature_src": event["feature_src"],
        }

    else:
        return {"status": "PENDING"}


def get_sub_analysis_result_dir(analysis_result_path, sub_analysis_name, feature_type):
    return "{}/{}/{}".format(analysis_result_path, feature_type, sub_analysis_name)


def get_analysis_result_map(result_bucket, result_directory, analysis_names, s3_client):
    """
    Analysis result directories are named as <analysis>_<date>_<time>
    This creates a map of each analysis to its directory name so we know where to find
    the results for each analysis.
    """
    # adding '/' to result directory and listing with delimiter '/' will make boto list all the subdirectory
    # prefixes instead of all the actual objects
    response = s3_client.list_objects(Bucket=result_bucket, Prefix=result_directory + '/', Delimiter='/')

    # get prefixes from response and remove trailining '/' for consistency
    analysis_result_paths = [prefix['Prefix'][:-1] for prefix in response['CommonPrefixes']]

    analysis_result_map = dict()
    for path in analysis_result_paths:
        for analysis in analysis_names:
            if analysis in os.path.basename(path):
                analysis_result_map[analysis] = path

    return analysis_result_map


if __name__ == "__main__":
    print(handler({
        "env": "staging",
        "name": "new_area_test",
        "feature_src": "s3://gfw-pipelines-dev/geotrellis/features/*.tsv",
        "feature_type": "geostore",
        "job_flow_id": "j-396AK95T1I3DD",
        "result_bucket": "gfw-pipelines-dev",
        "result_dir": "geotrellis/results/v20191119/new_area_test",
        "analyses": {
            "gladalerts": {
                "daily_alerts": "72af8802-df3c-42ab-a369-5e7f2b34ae2f",
                #"weekly_alerts": "Glad Alerts - Weekly - Geostore - User Areas",
                #"summary": "Glad Alerts - Summary - Geostore - User Areas",
            }
        }
    }, None))