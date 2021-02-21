import time
import uuid
import boto3
import os
import uvicorn
import botocore
import logging

from schemas import Reservation
from botocore.exceptions import EndpointConnectionError

from decouple import config
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

LOCALSTACK_ENDPOINT_URL = config("LOCALSTACK_ENDPOINT_URL")

app = FastAPI()

sqs_client = boto3.client("sqs", endpoint_url=LOCALSTACK_ENDPOINT_URL)
sqs_resource = boto3.resource("sqs", endpoint_url=LOCALSTACK_ENDPOINT_URL)
port = os.getenv("PORT", "8080")

while True:
    try:
        queue = sqs_resource.get_queue_by_name(QueueName='reservation-queue')
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

@app.post("/")
async def create_reservation(reservation: Reservation):

    if reservation.start_time >= reservation.end_time:
        logger.error("WRONG DATE")
        return {"Status": "start_date should be before end_date"}

    try:
        response = sqs_client.send_message(
            QueueUrl=queue.url,
            MessageBody=reservation.json(),
            MessageDeduplicationId=str(uuid.uuid4()),
            MessageGroupId="reservations",
            MessageAttributes={
                "contentType": {
                    "StringValue": "application/json", "DataType": "String"}
            }
        )
        return {"Status": "posted"}
    except:
        return {"Status": "SQS send message failure"}

if __name__ == "__main__":
    uvicorn.run("service:app", host="0.0.0.0", port=int(port), reload=True)
