import time
import uuid
import boto3
import logging
import botocore
import json
import os

from sqlalchemy.orm import sessionmaker
from decouple import config
from sqlalchemy.exc import SQLAlchemyError

from db import connect_db
from models import Reservation


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

LOCALSTACK_ENDPOINT_URL = config("LOCALSTACK_ENDPOINT_URL")

sqs = boto3.resource("sqs", endpoint_url=LOCALSTACK_ENDPOINT_URL)
sqs_client = boto3.client("sqs", endpoint_url=LOCALSTACK_ENDPOINT_URL)

def message_handler(reservation_queue, notification_queue):
    for message in reservation_queue.receive_messages():
        data = json.loads(message.body)
        reservation = Reservation(**data)
        session.add(reservation)
        session.commit()

        response = sqs_client.send_message(
            QueueUrl=notification_queue.url,
            MessageBody="reservation created!",
            MessageDeduplicationId=str(uuid.uuid4()),
            MessageGroupId="notifications",
            MessageAttributes={
                "contentType": {
                    "StringValue": "application/json", "DataType": "String"}
            }
        )
        # logger.info(f"Notifications response: {response}")
        logger.info(f"Reservation created: {data['employee_email']}")
        message.delete()

while True:
    try:
        engine = connect_db()

        Session = sessionmaker()
        Session.configure(bind=engine)
        session = Session()

        Reservation.__table__.create(bind=engine, checkfirst=True)
        break
    except SQLAlchemyError as sae:
        logger.error("Reconnecting to DB")
        time.sleep(3)

while True:
    time.sleep(2)

    reservation_queue = None
    notification_queue = None

    try:
        reservation_queue = sqs.get_queue_by_name(QueueName='reservation-queue')
        notification_queue = sqs.get_queue_by_name(QueueName='notification-queue')
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

    if reservation_queue is not None and notification_queue is not None:
        message_handler(reservation_queue, notification_queue)

