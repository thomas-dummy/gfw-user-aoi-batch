import requests
import boto3
import json


def slack_webhook(level, message, env="production"):
    if env != "dev" and env != "staging":
        app = "GFW SYNC - USER AOI BATCH"

        if level.upper() == "WARNING":
            color = "#E2AC37"
        elif level.upper() == "ERROR" or level.upper() == "CRITICAL":
            color = "#FF0000"
        else:
            color = "#36A64F"

        attachment = {
            "attachments": [
                {
                    "fallback": "{} - {} - {}".format(app, level.upper(), message),
                    "color": color,
                    "title": app,
                    "fields": [
                        {"title": level.upper(), "value": message, "short": False}
                    ],
                }
            ]
        }

        url = get_slack_webhook("data-updates")
        return requests.post(url, json=attachment)


def get_slack_webhook(channel):
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId="slack/gfw-sync")
    return json.loads(response["SecretString"])[channel]