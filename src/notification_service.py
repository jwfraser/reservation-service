import time
import uuid
import boto3
import botocore
import json

from decouple import config
from botocore.exceptions import EndpointConnectionError

from common import logger


ENDPOINT_URL = config("ENDPOINT_URL")

sqs = boto3.resource("sqs", endpoint_url=ENDPOINT_URL)
ses = boto3.client("ses", endpoint_url=ENDPOINT_URL)

# Receive messages from SQS Queue, email

def send_email(to_address, subject, body):
    try:
        response = ses.send_email(
            Destination={
                "ToAddresses": [
                    to_address,
                ],
            },
            Message={
                "Body": {
                    "Text": {
                        "Charset": "UTF-8",
                        "Data": body,
                    }
                },
                "Subject": {
                    "Charset": "UTF-8",
                    "Data": subject,
                },
            },
            Source="reservations@example.com",
        )
        return response
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
    for message in queue.receive_messages(MaxNumberOfMessages=10,WaitTimeSeconds=10):
        logger.info(f"Message received: {message.body}")
        data = json.loads(message.body)
        if data["status"] == "success":
            body = f"Successfully booked appointment for {data['start_time']} to {data['end_time']}"
            subject = "Reservation successful"
        else:
            body = f"Failed to book appointment.  Next available slot: {data['start_time']} to {data['end_time']}"
            subject = "Reservation failed"

        email_response = send_email(data["email"], subject, body)

        response_code = email_response["ResponseMetadata"]["HTTPStatusCode"]

        if response_code == 200:
            logger.info(f"Email sent to: {data['email']}")
            message.delete()
        else:
            raise ConnectionError(f"Notification not sent.  HTTPStatusCode: {response_code}")