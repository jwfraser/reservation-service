import time
import uuid
import boto3
import os
import uvicorn

from decouple import config
from fastapi import FastAPI

LOCALSTACK_ENDPOINT_URL = config("LOCALSTACK_ENDPOINT_URL")
RESERVATION_QUEUE_URL = config("RESERVATION_QUEUE_URL")

app = FastAPI()

sqs = boto3.client("sqs", endpoint_url=LOCALSTACK_ENDPOINT_URL)
port = os.getenv("PORT", "8080")

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/items/")
async def send_posted():
    # return {"Status": "posted"}
    try:
        response = sqs.send_message(
            QueueUrl=RESERVATION_QUEUE_URL,
            MessageBody="body",
            MessageDeduplicationId=str(uuid.uuid4()),
            MessageGroupId="messages",
            MessageAttributes={
                "contentType": {
                    "StringValue": "application/json", "DataType": "String"}
            }
        )
        return {"Status": "posted"}
    except:
        return {"Status": "SQS send message failure"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(port))

# Validate parameters

# Send event to reservation

# while (True):
#     time.sleep(3)
#     try:
#         response = sqs.send_message(
#             QueueUrl=RESERVATION_QUEUE_URL,
#             MessageBody="body",
#             MessageDeduplicationId=str(uuid.uuid4()),
#             MessageGroupId="messages",
#             MessageAttributes={
#                 "contentType": {
#                     "StringValue": "application/json", "DataType": "String"}
#             }
#         )
#         print("posted")
#     except:
#         print("SQS send message failure")
#         time.sleep(3)
