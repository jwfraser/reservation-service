import time
import uuid
import os
import uvicorn
import botocore

from botocore.exceptions import EndpointConnectionError

from fastapi import FastAPI

from common import logger, sqs_client, sqs_resource
from schemas import Reservation


app = FastAPI()

port = os.getenv("PORT", "8080")

while True:
    logger.info(f"Checking for reservation-queue")
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

    # Validate start_time & end_time
    try:
        if reservation.start_time >= reservation.end_time:
            return {"Error": "start_date should be before end_date"}
    except TypeError as e:
        logger.error(e)
        return {"Error": e.args}

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

    response_code = response["ResponseMetadata"]["HTTPStatusCode"]

    if response_code == 200:
        return {"Status": "Success"}
    else:
        return {"Error": f"Failed - response_code: {response_code}"}

    

if __name__ == "__main__":
    uvicorn.run("service:app", host="0.0.0.0", port=int(port), reload=True)
