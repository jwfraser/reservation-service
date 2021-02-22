import time
import uuid
import botocore
import json

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