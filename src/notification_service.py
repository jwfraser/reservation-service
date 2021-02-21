import time
import uuid
import boto3
import botocore
import logging

from decouple import config
from botocore.exceptions import EndpointConnectionError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

LOCALSTACK_ENDPOINT_URL = config("LOCALSTACK_ENDPOINT_URL")

sqs = boto3.resource("sqs", endpoint_url=LOCALSTACK_ENDPOINT_URL)
ses = boto3.client("ses", endpoint_url=LOCALSTACK_ENDPOINT_URL)

# Receive messages from SQS Queue, email

def send_email():
    try:
        response = ses.send_email(
            Destination={
                "ToAddresses": [
                    "jwfraser@gmail.com",
                ],
            },
            Message={
                "Body": {
                    "Text": {
                        "Charset": "UTF-8",
                        "Data": "Hello, world!",
                    }
                },
                "Subject": {
                    "Charset": "UTF-8",
                    "Data": "Amazing Email Tutorial",
                },
            },
            Source="reservations@example.com",
        )
    except Exception as e:
        logger.error(e)

while True:
    try:
        queue = sqs.get_queue_by_name(QueueName='notification-queue')
        break
    except botocore.errorfactory.ClientError as error:
        if error.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            logger.error(f"Queue does not exist.")
            time.sleep(5)
        else:
            logger.info(f"error: {error}")
            logger.info(f"error code: {error.response['Error']['Code']}")
    except EndpointConnectionError as ece:
        logger.info("SQS Not Available")
        time.sleep(5)

while True:
    time.sleep(2)
    try:
        for message in queue.receive_messages():
            logger.info(f"Message received: {message.body}")
            send_email()
            message.delete()
    except:
        logger.error("SQS receive message failure")
        time.sleep(5)
