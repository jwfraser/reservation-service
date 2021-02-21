import time
import uuid
import boto3
import logging
import botocore
import json
import os

import dateutil.parser

from botocore.exceptions import EndpointConnectionError
from decouple import config

from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from db import connect_db
from models import Reservation


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

LOCALSTACK_ENDPOINT_URL = config("LOCALSTACK_ENDPOINT_URL")

sqs = boto3.resource("sqs", endpoint_url=LOCALSTACK_ENDPOINT_URL)
sqs_client = boto3.client("sqs", endpoint_url=LOCALSTACK_ENDPOINT_URL)

def check_available(session, start_time, end_time, resource_id):

    logger.info(f"REQUESTED START: {start_time} | END: {end_time}")

    query = session.query(Reservation).filter(
            and_(Reservation.start_time <= start_time, Reservation.end_time > start_time)
    ).filter(Reservation.resource_id == resource_id)

    start_conflict = query.first()

    query = session.query(Reservation).filter(
            and_(Reservation.start_time <= end_time, Reservation.end_time > end_time)
    ).filter(Reservation.resource_id == resource_id)

    end_conflict = query.first()

    if start_conflict is None and end_conflict is None:
        logger.info(f"NO CONFLICT found!")
        logger.info(f"RETURNING AVAILABLE DATE: {start_time}")
        return (start_time, end_time)
    else:
        delta = dateutil.parser.parse(end_time) - dateutil.parser.parse(start_time)
        logger.info(f"TIME NOT AVAILABLE: {start_time}")
        if start_conflict is not None:
            logger.info(f"DELTA {delta} CONFLICT found!: {start_conflict}")
            end_time = start_conflict.end_time
        if end_conflict is not None:
            logger.info(f"DELTA {delta} CONFLICT found!: {end_conflict}")
            end_time = end_conflict.end_time
        new_end = (end_time + delta)
        return check_available(session, end_time, new_end, resource_id)

def message_handler(reservation_queue, notification_queue, session):
    logger.info("Handling Reservation Messages")
    for message in reservation_queue.receive_messages(MaxNumberOfMessages=10,WaitTimeSeconds=10):
        data = json.loads(message.body)
        reservation = Reservation(**data)

        available_start, available_end = check_available(session, reservation.start_time, reservation.end_time, reservation.resource_id)

        logger.info(f"FOUND AVAILABLE: {available_start}")

        if available_start == reservation.start_time:
            try:
                session.add(reservation)
                session.commit()
            except Exception as e:
                session.rollback()
                raise e

            body = {
                "status": "success",
                "email": reservation.employee_email,
                "name": reservation.employee_name,
                "start_time": reservation.start_time.isoformat(),
                "end_time": reservation.end_time.isoformat()
            }

        else:
            logger.info(f"START TYPE: {type(available_start)} | END TYPE: {type(available_end)}")
            body = {
                "status": "failed",
                "email": reservation.employee_email,
                "name": reservation.employee_name,
                "start_time": available_start.isoformat(),
                "end_time": available_end.isoformat()
            }
            
        response = sqs_client.send_message(
            QueueUrl=notification_queue.url,
            MessageBody=json.dumps(body),
            MessageDeduplicationId=str(uuid.uuid4()),
            MessageGroupId="notifications",
            MessageAttributes={
                "contentType": {
                    "StringValue": "application/json", "DataType": "String"}
            }
        )
        response_code = response["ResponseMetadata"]["HTTPStatusCode"]
        
        if response_code == 200:
            logger.info(f"Notifications response: {response}")
            logger.info(f"Reservation created: {data['employee_email']}")
            message.delete()
        else:
            raise ConnectionError(f"Notification not sent.  HTTPStatusCode: {response_code}")




while True:
    logger.info(f"Connecting to db")
    try:
        engine = connect_db()

        Session = sessionmaker()
        Session.configure(bind=engine)
        session = Session()

        Reservation.__table__.create(bind=engine, checkfirst=True)
        logger.info(f"Connected to db")
        break
    except SQLAlchemyError as sae:
        logger.error("Reconnecting to DB")
        time.sleep(3)

while True:
    logger.info(f"Getting Queues")
    reservation_queue = None
    notification_queue = None
    try:
        reservation_queue = sqs.get_queue_by_name(QueueName='reservation-queue')
        notification_queue = sqs.get_queue_by_name(QueueName='notification-queue')
        break
    except botocore.errorfactory.ClientError as error:
        if error.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            logger.error(f"Queue does not exist.")
            time.sleep(5)
        else:
            logger.info(f"error: {error}")
            logger.info(f"error code: {error.response['Error']['Code']}")
            time.sleep(5)
    except EndpointConnectionError as ece:
        logger.info("SQS Not Available")
        time.sleep(5)

if reservation_queue is not None and notification_queue is not None:
    while True:
        message_handler(reservation_queue, notification_queue, session)

