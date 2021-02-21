import time
import uuid
import boto3
import logging
import botocore
import json
import os

from db import connect_db

from sqlalchemy import create_engine

from decouple import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

LOCALSTACK_ENDPOINT_URL = config("LOCALSTACK_ENDPOINT_URL")

sqs = boto3.resource("sqs", endpoint_url=LOCALSTACK_ENDPOINT_URL)


while (True):
    try:
        queue = sqs.get_queue_by_name(QueueName='reservation-queue')
    
        for message in queue.receive_messages():
            reservation = json.loads(message.body)
            print(f"Email: {reservation['employee_email']}")
            message.delete()

    # Check if available

    # If available, create record, send notification

    # If not, send notification about nearest available

    except botocore.errorfactory.ClientError as error:
        if error.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            logger.error(f"Queue does not exist.")
            time.sleep(5)
        else:
            logger.info(f"error: {error}")
            logger.info(f"error code: {error.response['Error']['Code']}")
    
    except Exception as e:
        print(f"ERROR: {e}")
