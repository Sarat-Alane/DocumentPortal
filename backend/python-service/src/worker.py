# /root/backend/python-service/src/worker.py
# This is the main worker.py file which co-ordinates with the S3, SQS and the pipeline.py module

import os, sys
sys.path.append(os.path.dirname(__file__))

import re
import json
import time
import shutil
import psycopg2
from datetime import datetime
from paddleocr import PaddleOCR
from pdf2image import convert_from_path
import requests
from requests.exceptions import ConnectionError, Timeout
import boto3
import json
import time
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from urllib.parse import unquote

# Load the pipeline file
# from services.pipeline import process_pdf
from services.pdfprocessor import PDF_Processor

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

sqs=boto3.client('sqs', region_name="eu-north-1")
s3=boto3.client('s3', region_name="eu-north-1")

QUEUE_URL=os.getenv("QUEUE_URL")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def run_worker():
    print("Worker is running")
    
    while True:
        try:
            resp = sqs.receive_message(

                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )
        except Exception as e:
            print(f"Error receiving messages from SQS: {e}")
            continue

        if 'Messages' in resp:
            for msg in resp['Messages']:
                try:
                    body = json.loads(msg['Body'])
                    print("DEBUG body:", body)

                    bucket = body['bucket']
                    key = unquote(body['key'])

                    # Extract jobId from S3 key: "incoming/<jobId>-filename.pdf"
                    job_id = os.path.basename(key).split("-")[0]

                    local_file = os.path.join(DOWNLOAD_DIR, os.path.basename(key))

                    # Download from S3
                    s3.download_file(bucket, key, local_file)
                    print(f"Downloaded {key} → {local_file}")

                    # Process PDF
                    processor = PDF_Processor()
                    processor.connect_to_db()

                    result = processor.process_pdf_to_database(local_file)
                    print(f"Processing complete → {result}")

                    processor.close_db_connection()


                    # Cleanup
                    if os.path.exists(local_file):
                        print("Deleting file")
                        os.remove(local_file)

                    # Delete SQS message
                    sqs.delete_message(
                        QueueUrl=QUEUE_URL,
                        ReceiptHandle=msg['ReceiptHandle']
                    )
                    print(f"Deleted message from SQS: {msg['MessageId']}")

                except Exception as e:
                    print(f"Error processing message: {e}")


if __name__ == "__main__":
    run_worker()