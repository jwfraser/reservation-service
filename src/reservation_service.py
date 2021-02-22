import time
import uuid
import botocore
import json
import os

import dateutil.parser

from botocore.exceptions import EndpointConnectionError

from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from db import connect_db
from models import Reservation
from common import logger, sqs_resource, sqs_client


def datetime_format(dt):
    return dateutil.parser.parse(dt).strftime("%m/%d/%Y, %H:%M:%S")


def check_available(session, start_time, end_time, workplace):
    '''
    Takes in a database session, and searches reservations table for available time for specified workplace.
    If none are available, the next available time slot for the same duration is returned.

    Dates should be in ISO 8601

        Parameters:
            session (sqlalchemy.orm.session.Session): DB session
            start_time (str): Start of appointment
            end_time (str): End of appointment
            workplace (str): Name of workplace

        Returns
            (start_time (str), end_time(str)): Tuple containing nearest available start and end time.
    '''
    
    logger.debug(f"CHECKING AVAILABLE START: {start_time} | END: {end_time}")

    base_query = session.query(Reservation).filter(Reservation.workplace == workplace)

    start_query = base_query.filter(
            and_(Reservation.start_time <= start_time, Reservation.end_time > start_time)
    )

    start_conflict = start_query.first()

    end_query = base_query.filter(
            and_(Reservation.start_time < end_time, Reservation.end_time >= end_time)
    )

    end_conflict = end_query.first()

    if start_conflict is None and end_conflict is None:
        return (start_time, end_time)
    else:
        logger.debug(f"CONFLICT FOUND, TRYING AGAIN")
        delta = dateutil.parser.parse(end_time) - dateutil.parser.parse(start_time)
        if start_conflict is not None:
            new_start = start_conflict.end_time
        if end_conflict is not None:
            new_start = end_conflict.end_time
        new_end = new_start + delta
        return check_available(session, new_start.isoformat(), new_end.isoformat(), workplace)

def reservation_handler(reservation_queue, notification_queue, session):
    '''
    Checks reservation_queue new messages and checks for availablility.  If the workplace is available, it commits a new
    reservation record on session and a message is sent to the notification_queue.  Otherwise it sends a message to the notification_queue
    with the next available period.

        Parameters
            reservation_queue (boto3.resources.factory.sqs.Queue): SQS queue for reservation messages
            notification_queue (boto3.resources.factory.sqs.Queue): SQS queue for notification messages
            session (sqlalchemy.orm.session.Session): Database session
    '''
    
    for message in reservation_queue.receive_messages(MaxNumberOfMessages=10,WaitTimeSeconds=10,VisibilityTimeout=5):
        data = json.loads(message.body)
        reservation = Reservation(**data)

        available_start, available_end = check_available(session, reservation.start_time, reservation.end_time, reservation.workplace)

        start_time_str = datetime_format(reservation.start_time)
        end_time_str = datetime_format(reservation.end_time)

        available_start_str = datetime_format(available_start)
        available_end_str = datetime_format(available_end)

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
                "start_time": start_time_str,
                "end_time": end_time_str,
                "workplace": reservation.workplace
            }
        else:
            body = {
                "status": "failed",
                "email": reservation.employee_email,
                "name": reservation.employee_name,
                "requested_start": start_time_str,
                "requested_end": end_time_str,
                "start_time": available_start_str,
                "end_time": available_end_str,
                "workplace": reservation.workplace
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
            logger.debug(f"Reservation created: {data['employee_email']}")
            message.delete()
        else:
            logger.debug(f"Notification not sent.  HTTPStatusCode: {response_code}")

# Check for database connection and create required table

while True:
    logger.debug(f"Connecting to db")
    try:
        engine = connect_db()

        Session = sessionmaker()
        Session.configure(bind=engine)
        session = Session()

        Reservation.__table__.create(bind=engine, checkfirst=True)
        logger.debug(f"Connected to db")
        break
    except SQLAlchemyError as sae:
        logger.error(f"Reconnecting to DB: {sae}")
        time.sleep(3)

# Check for reservation-queue and notification-queue

while True:
    logger.info(f"Checking for reservation-queue and notification-queue")
    reservation_queue = None
    notification_queue = None
    try:
        reservation_queue = sqs_resource.get_queue_by_name(QueueName='reservation-queue')
        notification_queue = sqs_resource.get_queue_by_name(QueueName='notification-queue')
        break
    except botocore.errorfactory.ClientError as error:
        if error.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            logger.error(f"Queue does not exist.  Retrying in 5.")
            time.sleep(5)
        else:
            logger.info(f"Error: {error}")
            logger.info(f"Error Code: {error.response['Error']['Code']}")
            time.sleep(5)
    except EndpointConnectionError as ece:
        logger.info("SQS Not Available")
        time.sleep(5)

# If queues are found, start handling messages.

if reservation_queue is not None and notification_queue is not None:
    while True:
        reservation_handler(reservation_queue, notification_queue, session)

