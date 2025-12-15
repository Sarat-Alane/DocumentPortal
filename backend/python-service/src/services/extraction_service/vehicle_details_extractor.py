# This module extracts vehicle details from vehicle purchase documents

import re
import json

class VehicleDetailsExtractor:
    def __init__(self, processor):
        """
        Initialize with reference to PDF_Processor for patterns and LLM calls
        """
        self.processor = processor
    
    def extract_vehicle_details(self, page_data_list):
        """
        Extract vehicle details from tax_invoice, dan, and cddn documents
        Returns: dict with tax_invoice, dan, cddn as JSONB
        """
        vehicle_data = {
            'tax_invoice': None,
            'dan': None,
            'cddn': None
        }
        
        for page_data in page_data_list:
            if page_data.get('document_type') != 'vehicle_document':
                continue
            
            sub_type = page_data.get('sub_type')
            
            if sub_type == 'sales_tax_invoice':
                vehicle_details = self._extract_from_vehicle_document(page_data, 'Sales Tax Invoice')
                if vehicle_details:
                    vehicle_data['tax_invoice'] = vehicle_details
                    print(f"✅ Vehicle details extracted from Sales Tax Invoice")
            
            elif sub_type == 'delivery_acknowledgement_note':
                vehicle_details = self._extract_from_vehicle_document(page_data, 'Delivery Acknowledgement Note')
                if vehicle_details:
                    vehicle_data['dan'] = vehicle_details
                    print(f"✅ Vehicle details extracted from DAN")
            
            elif sub_type == 'customer_discount_declaration_note':
                vehicle_details = self._extract_from_vehicle_document(page_data, 'Customer Discount Declaration Note')
                if vehicle_details:
                    vehicle_data['cddn'] = vehicle_details
                    print(f"✅ Vehicle details extracted from CDDN")
        
        return vehicle_data
    
    def _extract_from_vehicle_document(self, page_data, doc_name):
        """
        Extract VIN/Chassis number and Engine number from vehicle document
        """
        cleaned_text = page_data.get('cleaned_ocr_text', '')
        page_file = page_data.get('page_file')
        
        prompt = f"""
Extract vehicle details from this {doc_name}.

Extract the following:
1. VIN Number / Chassis Number (17 character alphanumeric code, format: [A-HJ-NPR-Z0-9]{{17}})
   - VIN and Chassis Number are the SAME thing
   - Look for labels: "VIN", "VIN No", "Chassis No", "Chassis Number"
2. Engine Number (7-12 character alphanumeric code)
   - Look for labels: "Engine No", "Engine Number", "ENG NO"

Rules:
- VIN/Chassis is typically 17 characters
- Engine number is typically 7-12 alphanumeric characters
- Both are alphanumeric (letters and numbers)

Return ONLY a JSON object:
{{
  "vin_number": "17 character VIN/Chassis number or null",
  "chassis_number": "same as vin_number (they are identical)",
  "engine_number": "engine number or null"
}}

OCR text from {doc_name}:
{cleaned_text}
"""
        result = self.processor._make_llm_call(prompt, page_file)
        
        if not result:
            # Fallback to regex extraction
            result = self._extract_with_regex(cleaned_text)
        
        # Ensure VIN and chassis are the same
        if result:
            vin = result.get('vin_number') or result.get('chassis_number')
            if vin:
                vin_cleaned = self._clean_vin(vin)
                if vin_cleaned and self._validate_vin(vin_cleaned):
                    result['vin_number'] = vin_cleaned
                    result['chassis_number'] = vin_cleaned
                else:
                    result['vin_number'] = None
                    result['chassis_number'] = None
            
            engine = result.get('engine_number')
            if engine:
                engine_cleaned = self._clean_engine(engine)
                if engine_cleaned and self._validate_engine(engine_cleaned):
                    result['engine_number'] = engine_cleaned
                else:
                    result['engine_number'] = None
        
        # Return only if we have at least one valid field
        if result and (result.get('vin_number') or result.get('engine_number')):
            return result
        
        return None
    
    def _extract_with_regex(self, text):
        """Fallback regex extraction for vehicle details"""
        result = {
            'vin_number': None,
            'chassis_number': None,
            'engine_number': None
        }
        
        # VIN/Chassis patterns
        chassis_patterns = [
            r'\b[A-HJ-NPR-Z0-9]{17}\b',
            r'(?:CHASSIS\s?NO\.?|CHASSIS\s?NUMBER)[:\s]*([A-HJ-NPR-Z0-9]{17})',
            r'(?:VIN\s?NO\.?|VIN)[:\s]*([A-HJ-NPR-Z0-9]{17})',
        ]
        
        for pattern in chassis_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                vin = matches[0] if isinstance(matches[0], str) else matches[0]
                vin_cleaned = self._clean_vin(vin)
                if vin_cleaned and self._validate_vin(vin_cleaned):
                    result['vin_number'] = vin_cleaned
                    result['chassis_number'] = vin_cleaned
                    break
        
        # Engine patterns
        engine_patterns = [
            r'(?:ENGINE\s?NO\.?|ENGINE\s?NUMBER)[:\s]*([A-Z0-9]{7,12})',
            r'(?:ENG\.?\s?NO\.?)[:\s]*([A-Z0-9]{7,12})',
            r'\b[A-Z0-9]{7,12}\b'  # Generic pattern - use cautiously
        ]
        
        for pattern in engine_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    engine = match if isinstance(match, str) else match
                    engine_cleaned = self._clean_engine(engine)
                    if engine_cleaned and self._validate_engine(engine_cleaned):
                        result['engine_number'] = engine_cleaned
                        break
                if result['engine_number']:
                    break
        
        return result if (result['vin_number'] or result['engine_number']) else None
    
    def _clean_vin(self, vin):
        """Clean VIN/Chassis number"""
        if not vin:
            return None
        # Remove spaces and convert to uppercase
        cleaned = re.sub(r'\s', '', str(vin)).upper()
        return cleaned if len(cleaned) == 17 else None
    
    def _validate_vin(self, vin):
        """Validate VIN format - 17 alphanumeric characters"""
        if not vin or len(vin) != 17:
            return False
        return bool(self.processor.vin_pattern.match(vin))
    
    def _clean_engine(self, engine):
        """Clean engine number"""
        if not engine:
            return None
        # Remove spaces and convert to uppercase
        cleaned = re.sub(r'\s', '', str(engine)).upper()
        return cleaned if 7 <= len(cleaned) <= 12 else None
    
    def _validate_engine(self, engine):
        """Validate engine number format - 7-12 alphanumeric characters"""
        if not engine:
            return False
        return bool(self.processor.engine_pattern.match(engine)) and 7 <= len(engine) <= 12
