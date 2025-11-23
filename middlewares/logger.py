import boto3
import json
from datetime import datetime
import os

AWS_REGION = "us-east-1"
LOG_GROUP = "FastAPI-App-Logs"
LOG_STREAM = "RateLimitEvents"

logs_client = boto3.client(
    "logs",
    region_name=AWS_REGION
)

sequence_token = None

def send_log(message: dict):
    global sequence_token

    timestamp = int(datetime.utcnow().timestamp() * 1000)

    log_event = {
        "timestamp": timestamp,
        "message": json.dumps(message)
    }

    try:
        if sequence_token:
            response = logs_client.put_log_events(
                logGroupName=LOG_GROUP,
                logStreamName=LOG_STREAM,
                logEvents=[log_event],
                sequenceToken=sequence_token
            )
        else:
            try:
                logs_client.create_log_stream(
                    logGroupName=LOG_GROUP,
                    logStreamName=LOG_STREAM
                )
            except logs_client.exceptions.ResourceAlreadyExistsException:
                pass

            response = logs_client.put_log_events(
                logGroupName=LOG_GROUP,
                logStreamName=LOG_STREAM,
                logEvents=[log_event]
            )

        sequence_token = response["nextSequenceToken"]

    except logs_client.exceptions.InvalidSequenceTokenException as e:
        sequence_token = e.response["expectedSequenceToken"]
        send_log(message)
