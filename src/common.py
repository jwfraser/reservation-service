import logging
import boto3

from decouple import config


logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger()

ENDPOINT_URL = config("ENDPOINT_URL")

sqs_resource = boto3.resource("sqs", endpoint_url=ENDPOINT_URL)
ses_client = boto3.client("ses", endpoint_url=ENDPOINT_URL)
sqs_client = boto3.client("sqs", endpoint_url=ENDPOINT_URL)