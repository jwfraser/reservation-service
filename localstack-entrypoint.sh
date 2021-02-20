#!/usr/bin/env bash

readonly LOCALSTACK_URL=http://localhost:4566

sleep 5;

set -x

aws configure set aws_access_key_id foo
aws configure set aws_secret_access_key bar
echo "[default]" > ~/.aws/config
echo "region = us-east-1" >> ~/.aws/config
echo "output = json" >> ~/.aws/config

aws --endpoint-url $LOCALSTACK_URL sqs create-queue --queue-name reservation-queue
aws --endpoint-url $LOCALSTACK_URL sqs create-queue --queue-name notification-queue

# echo 'Running AWS verify identity command. See: https://github.com/localstack/localstack/issues/339'
aws ses verify-email-identity --email-address reservations@example.com --region us-east-1 --endpoint-url=$LOCALSTACK_URL

set +x