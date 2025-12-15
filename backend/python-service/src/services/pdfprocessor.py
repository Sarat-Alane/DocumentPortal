# Updated pdfprocessor.py with integrated modules

import os
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

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Import existing modules
from services.db_service import db
from services.poppler_service import popplermodule
from services.ocr_service import ocr_module
from services.cleanup_service import cleanup_module

# Import NEW extraction modules
from services.db_service import db_initial_insert
from services.extraction_service.document_classifier import DocumentClassifier
from services.extraction_service.name_extractor import NameExtractor
from services.extraction_service.customer_details_extractor import CustomerDetailsExtractor
from services.extraction_service.vehicle_details_extractor import VehicleDetailsExtractor
from services.extraction_service.business_context_extractor import BusinessContextExtractor
from services.extraction_service.json_generator import JSONGenerator
from services.db_service import db_update

class PDF_Processor:
    def __init__(self):
        # Initialize the PaddleOCR Model
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en')

        # Initialize Llama LLM Model
        self.lm_studio_url = "https://ventilable-pivotally-keely.ngrok-free.dev/v1/chat/completions"
        self.MODEL_NAME = "meta-llama-3-8b-instruct"
        self.sagemaker_endpoint = os.getenv("sagemaker_endpoint")
        self.sagemaker_client = boto3.client('sagemaker-runtime')

        # Regex patterns for customer ID documents
        self.aadhaar_extract_pattern = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
        self.aadhaar_validate_pattern = re.compile(r"^\d{12}$")
        self.pan_pattern = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
        self.dl_pattern = re.compile(r"\b[A-Z]{2}[0-9]{2}\s?[0-9]{11}\b")
        self.dob_pattern = re.compile(r"\b(?:0?[1-9]|[12][0-9]|3[01])[-/](?:0?[1-9]|1[0-2])[-/](?:19\d{2}|20\d{2})\b")

        # Regex patterns for vehicle details
        self.vin_pattern = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b")
        self.engine_pattern = re.compile(r"\b[A-Z0-9]{7,12}\b")
        self.rc_pattern = re.compile(r"\b[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}\b")

        # Regex pattern for GSTIN
        self.gstin_pattern = re.compile(r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9][Z][0-9]\b")
        
        # Registration certificate keywords for validation
        self.rc_keywords = [
            "registration", "regn", "certificate of registration", 
            "registration no", "regn no", "vehicle registration",
            "rc", "registration certificate"
        ]
        
        # Business document keywords for GSTIN validation
        self.business_keywords = [
            "gst reg", "government of india", "legal name", 
            "trade name", "business", "gstin", "gst registration",
            "business registration", "tax registration"
        ]
        
        # Database connection
        self.conn = None
        self.cursor = None
        
        # Initialize extraction modules
        self.document_classifier = DocumentClassifier(self)
        self.name_extractor = NameExtractor(self)
        self.customer_extractor = CustomerDetailsExtractor(self)
        self.vehicle_extractor = VehicleDetailsExtractor(self)
        self.business_extractor = BusinessContextExtractor(self)
        self.json_generator = JSONGenerator()

    def connect_to_db(self):
        self.conn, self.cursor = db.connect_to_db()

    def close_db_connection(self):
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            if self.conn:
                self.conn.close()
                self.conn = None
            print("Database connection closed successfully.")
        except Exception as e:
            print(f"⚠️ Error while closing database connection: {e}")

    def pdf_to_images(self, pdf_path, output_folder):
        image_paths = popplermodule.pdf_to_images_function(pdf_path, output_folder, poppler_path=r"C:\poppler-24.08.0\Library\bin", dpi=200, image_format='png')
        return image_paths
    
    def extract_text_from_image(self, image_path, output_file='extracted_text.txt'):
        result = ocr_module.extract_text_from_image(self.ocr, image_path, output_file=output_file)
        return result
    
    def cleanup_files(self, files_to_delete, folders_to_delete):
        cleanup_module.cleanup_files(files_to_delete, folders_to_delete)
    
    def extract_json(self, text):
        """Extract JSON from LLM response"""
        try:
            # Try direct JSON parse first
            return json.loads(text)
        except:
            pass
        
        # Try to find JSON between curly braces
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        return {}
    
    def _make_llm_call(self, prompt, pagefile, retries=3):
        """Make call to AWS SageMaker endpoint for Llama model with proper chat formatting."""
        
        print(f"\n{'='*60}")
        print(f"Making LLM call for: {pagefile}")
        print(f"{'='*60}")
        
        for attempt in range(retries):
            try:
                print(f"Attempt {attempt + 1}/{retries}")
                
                # Format prompt as a proper chat conversation for Llama
                formatted_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful AI assistant that extracts structured data from documents. You MUST respond with valid JSON only, no other text.<|eot_id|><|start_header_id|>user<|end_header_id|>

{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
                
                # Prepare the payload for SageMaker
                payload = {
                    "inputs": formatted_prompt,
                    "parameters": {
                        "max_new_tokens": 800,
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "do_sample": True,
                        "return_full_text": False,
                        "stop": ["<|eot_id|>", "<|end_of_text|>"]
                    }
                }
                
                print(f"Payload prepared (formatted prompt length: {len(formatted_prompt)} chars)")
                
                # Convert payload to JSON string
                payload_json = json.dumps(payload)
                
                print(f"Invoking SageMaker endpoint: {self.sagemaker_endpoint}")
                
                # Invoke the SageMaker endpoint
                response = self.sagemaker_client.invoke_endpoint(
                    EndpointName=self.sagemaker_endpoint,
                    ContentType='application/json',
                    Body=payload_json
                )
                
                print("SageMaker endpoint responded successfully")
                
                # Parse the response
                response_body = response['Body'].read().decode()
                print(f"Raw response (first 500 chars): {response_body[:500]}")
                
                result = json.loads(response_body)
                print(f"Response type: {type(result)}")
                
                # Extract the generated text
                reply = None
                
                if isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], dict) and "generated_text" in result[0]:
                        reply = result[0]["generated_text"]
                elif isinstance(result, dict):
                    if "generated_text" in result:
                        reply = result["generated_text"]
                    elif "predictions" in result:
                        reply = result["predictions"]
                    elif "output" in result:
                        reply = result["output"]
                    elif len(result) == 1:
                        reply = list(result.values())[0]
                elif isinstance(result, str):
                    reply = result
                
                if reply is None:
                    print(f"ERROR: Could not extract reply from response structure")
                    raise ValueError("Unable to extract text from SageMaker response")
                
                print(f"Reply extracted (length: {len(str(reply))} chars)")
                
                # Clean up the reply
                reply_str = str(reply).strip()
                reply_str = re.sub(r'<\|.*?\|>', '', reply_str)
                
                if formatted_prompt in reply_str:
                    reply_str = reply_str.replace(formatted_prompt, '').strip()
                
                # Extract JSON
                extracted_json = self.extract_json(reply_str)
                
                if extracted_json:
                    print(f"Successfully extracted JSON with keys: {extracted_json.keys()}")
                    print(f"{'='*60}\n")
                    return extracted_json
                else:
                    print("WARNING: No JSON could be extracted from reply")
                    return {}
                        
            except Exception as e:
                print(f"ERROR in attempt {attempt + 1}: {type(e).__name__}: {str(e)}")
                
                if attempt < retries - 1:
                    print(f"Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print(f"All retries exhausted. Skipping {pagefile}")
                    return {}
        
        return {}
    
    def process_pdf_to_database(self, pdf_path):
        """
        Complete pipeline: PDF -> Images -> OCR -> Extraction -> Database
        """
        print("\n" + "="*80)
        print(f"STARTING PDF PROCESSING PIPELINE FOR: {pdf_path}")
        print("="*80 + "\n")
        
        # Generate output paths
        pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
        output_folder = f"{pdf_basename}_images"
        output_file = f"{pdf_basename}_extracted.txt"
        
        try:
            # Step 1: Convert PDF to images
            print("\n[STEP 1] Converting PDF to images...")
            image_paths = self.pdf_to_images(pdf_path, output_folder)
            
            # Step 2: Extract text from images using OCR
            print("\n[STEP 2] Extracting text from images using OCR...")
            for image_path in image_paths:
                self.extract_text_from_image(image_path, output_file=output_file)
            
            # Step 3: Insert initial database record with filename
            print("\n[STEP 3] Inserting initial database record...")
            success = db_initial_insert.insert_initial_record(self.conn, self.cursor, pdf_basename)
            
            if not success:
                print("⚠️ Skipping processing as record already exists or insertion failed.")
                self.cleanup_files([output_file], [output_folder])
                return False
            
            # Step 4: Read and parse OCR text
            print("\n[STEP 4] Reading and parsing OCR text...")
            with open(output_file, "r", encoding="utf-8") as f:
                ocr_text = f.read()
            
            # Split text into pages
            page_blocks = re.split(r"={70,}\nText extracted from: (.*?)\n", ocr_text)
            
            # Initialize data containers
            page_data_list = []
            
            # Step 5: FIRST PASS - Identify document types
            print("\n[STEP 5] First Pass - Identifying document types...")
            for i in range(1, len(page_blocks), 2):
                page_file = page_blocks[i]
                page_text = page_blocks[i + 1]
                
                # Extract rec_texts from OCR (raw lines)
                match = re.search(r"'rec_texts': \[(.*?)\]", page_text, re.DOTALL)
                rec_texts = [t.strip(" '\"\\n") for t in match.group(1).split(",")] if match else []
                cleaned_ocr_text = "\n".join(rec_texts)
                
                page_key = page_file.split("/")[-1].replace(".png", "")
                
                print(f"\n  Processing page: {page_key}")
                
                # Identify document type
                doc_type_result = self.document_classifier.identify_document_type(page_file, cleaned_ocr_text)
                
                page_info = {
                    'page_key': page_key,
                    'page_file': page_file,
                    'cleaned_ocr_text': cleaned_ocr_text,
                    'document_type': doc_type_result.get('document_type', 'unknown'),
                    'sub_type': doc_type_result.get('sub_type', 'unknown'),
                    'confidence': doc_type_result.get('confidence', 'low'),
                    'indicators': doc_type_result.get('indicators', [])
                }
                
                page_data_list.append(page_info)
                
                print(f"    Document Type: {page_info['document_type']}")
                print(f"    Sub Type: {page_info['sub_type']}")
                print(f"    Confidence: {page_info['confidence']}")
            
            # Step 6: Extract customer names
            print("\n[STEP 6] Extracting customer names...")
            vehicle_names = self.name_extractor.extract_names_from_vehicle_documents(page_data_list)
            identity_names = self.name_extractor.extract_names_from_identity_documents(page_data_list)
            
            # Step 7: Match customer name
            print("\n[STEP 7] Matching customer name...")
            customer_name = self.name_extractor.match_customer_name(vehicle_names, identity_names)
            
            if not customer_name:
                print("⚠️ No customer name found. Using filename as fallback.")
                customer_name = pdf_basename
            
            print(f"✅ Final customer name: {customer_name}")
            
            # Step 8: Extract customer details
            print("\n[STEP 8] Extracting customer details from identity documents...")
            customer_data = self.customer_extractor.extract_customer_details(page_data_list, customer_name)
            
            # Step 9: Extract vehicle details
            print("\n[STEP 9] Extracting vehicle details from purchase documents...")
            vehicle_data = self.vehicle_extractor.extract_vehicle_details(page_data_list)
            
            # Step 10: Extract business context
            print("\n[STEP 10] Extracting business context...")
            business_data = self.business_extractor.extract_business_context(page_data_list)
            
            # Step 11: Generate final JSON
            print("\n[STEP 11] Generating final JSON...")
            final_json = self.json_generator.generate_json(
                pdf_basename, 
                customer_data, 
                vehicle_data, 
                business_data
            )
            
            # Step 12: Update database
            print("\n[STEP 12] Updating database...")
            db_success = db_update.update_customer_record(self.conn, self.cursor, final_json)
            
            # Step 13: Cleanup temporary files
            print("\n[STEP 13] Cleaning up temporary files...")
            self.cleanup_files([output_file], [output_folder])
            
            print("\n" + "="*80)
            print("✅ PDF PROCESSING PIPELINE COMPLETED SUCCESSFULLY")
            print("="*80 + "\n")
            
            return db_success
            
        except Exception as e:
            print(f"\n❌ ERROR in processing pipeline: {e}")
            import traceback
            print(traceback.format_exc())
            
            # Cleanup on error
            self.cleanup_files([output_file], [output_folder])
            return False

if __name__ == "__main__":
    processor = PDF_Processor()
    processor.connect_to_db()

    # Generate output paths
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "downloads", "LEONAL_RETAIL_LLP_1.pdf")
    
    # Run complete pipeline
    processor.process_pdf_to_database(pdf_path)

    processor.close_db_connection()
