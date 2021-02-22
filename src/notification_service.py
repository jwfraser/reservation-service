import time
import uuid
import botocore
import json

import dateutil.parser

from botocore.exceptions import EndpointConnectionError

from common import logger, sqs_resource, ses_client


# Receive messages from SQS Queue, email

def send_email(to_address, subject, body):
    '''
    Sends email over AWS SES.  Takes subject and body and sends it to to_address.

        Parameters
            to_address (str): Address to send to
            subject (str): Subject for email
            body (str): Body for email
        
        Returns
            response (dict): Response from SES
    '''
    try:
        response = ses_client.send_email(
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

# Checking for SQS notification-queue

while True:
    logger.info(f"Checking for notification-queue")
    try:
        queue = sqs_resource.get_queue_by_name(QueueName='notification-queue')
        break
    except botocore.errorfactory.ClientError as error:
        if error.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            logger.error(f"Queue does not exist.")
            time.sleep(5)
        else:
            logger.error(f"error: {error}")
            logger.error(f"error code: {error.response['Error']['Code']}")
    except EndpointConnectionError as ece:
        logger.error("SQS Not Available")
        time.sleep(5)

# Handle messages in notification queue.

while True:
    for message in queue.receive_messages(MaxNumberOfMessages=10,WaitTimeSeconds=10,VisibilityTimeout=5):
        data = json.loads(message.body)
        delta = dateutil.parser.parse(data['end_time']) - dateutil.parser.parse(data['start_time'])

        days, rem = divmod(delta.seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)

        locals_ = locals()
        magnitudes_str = ("{n} {magnitude}".format(n=int(locals_[magnitude]), magnitude=magnitude)
                for magnitude in ("days", "hours", "minutes", "seconds") if locals_[magnitude])
        eta_str = ", ".join(magnitudes_str)

        if data["status"] == "success":
            body = f"""
Hello {data['name']},
You have successfully reserved {data['workplace']} for {eta_str}
Starting at {data['start_time']} 
Ending at {data['end_time']}
            """
            subject = f"Reservation successful for {data['workplace']}"
        else:
            body = f"""
Hello {data['name']},
We have failed to reserve {data['workplace']} between {data['requested_start']} and {data['requested_end']}
Next available slot for {eta_str} for that workplace is from {data['start_time']} to {data['end_time']}
            """
            subject = f"Reservation failed for {data['workplace']}"

        email_response = send_email(data["email"], subject, body)

        response_code = email_response["ResponseMetadata"]["HTTPStatusCode"]

        if response_code == 200:
            logger.info(f"Email sent to: {data['email']}")
            message.delete()
        else:
            raise ConnectionError(f"Notification not sent.  HTTPStatusCode: {response_code}")