import time
import uuid
import boto3
from decouple import config

LOCALSTACK_ENDPOINT_URL = config("LOCALSTACK_ENDPOINT_URL")
NOTIFICATION_QUEUE_URL = config("NOTIFICATION_QUEUE_URL")

sqs = boto3.client("sqs", endpoint_url=LOCALSTACK_ENDPOINT_URL)

# Receive messages from SQS Queue, email

while (True):
    try:
        messages = sqs.receive_message(QueueUrl=NOTIFICATION_QUEUE_URL,
                                       AttributeNames=['All'], MaxNumberOfMessages=10, WaitTimeSeconds=2, VisibilityTimeout=30)

        messages = messages.get("Messages", [])

        print("Messages", messages)
    except:
        print("SQS receive message failure")
        time.sleep(5)
