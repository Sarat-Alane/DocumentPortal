# /root/backend/python-services/src/services/pipeline.py
# This file contains the abstract pipeline flow, calling the processing functions in sequence for PDF Processing

import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

def process_pdf():
    print("Pipeline has been accessed")
    DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")
    print(DOWNLOAD_DIR)