# This module identifies document types from OCR text using LLM

import re

class DocumentClassifier:
    def __init__(self, processor):
        """
        Initialize with reference to PDF_Processor for LLM calls
        """
        self.processor = processor
        
        # Document type keywords
        self.vehicle_keywords = [
            "sales tax invoice", "delivery acknowledgement note", 
            "customer discount declaration note", "customer exchange declaration note",
            "registration certificate", "rc", "vehicle", "chassis", "engine",
            "registration no", "regn no"
        ]
        
        self.government_keywords = [
            "government of india", "aadhaar", "unique identification",
            "permanent account", "income tax", "pan card", "driving licence",
            "driving license", "transport authority", "uidai"
        ]
        
        self.business_keywords = [
            "gst reg", "legal name", "trade name", "business",
            "gstin", "gst registration", "business registration", "tax registration"
        ]
    
    def identify_document_type(self, page_file, cleaned_ocr_text):
        """
        Identify what type of document this is using LLM
        Returns: dict with document_type, confidence, indicators, and sub_type
        """
        prompt = f"""
You are an AI system that identifies document types from OCR text.

Identify the document type from the following categories:
1. "government_identity" - Government Identity Documents (Aadhaar Card, PAN Card, Driving License)
2. "vehicle_document" - Vehicle Documents (Registration Certificate, Delivery Acknowledgement Note, Sales Tax Invoice, Customer Discount Declaration Note, Customer Exchange Declaration Note)
3. "business_document" - Business Documents with GSTIN (only if contains "GST Reg" or "Government of India" AND "Legal Name", "Trade Name", or "Business")
4. "unknown" - If document type cannot be determined

For government_identity documents, also identify the sub_type:
- "aadhaar" if it's an Aadhaar card
- "pan" if it's a PAN card
- "driving_license" if it's a Driving License

For vehicle_document documents, also identify the sub_type:
- "sales_tax_invoice" for Sales Tax Invoice
- "delivery_acknowledgement_note" for Delivery Acknowledgement Note (DAN)
- "customer_discount_declaration_note" for Customer Discount Declaration Note (CDDN)
- "customer_exchange_declaration_note" for Customer Exchange Declaration Note
- "registration_certificate" for RC

Look for these indicators:
- Government Identity: "Government of India", "Aadhaar", "PAN", "Driving License", "Income Tax Department", "UIDAI", "Permanent Account"
- Vehicle Document: "Registration Certificate", "Delivery Acknowledgement Note", "Sales Tax Invoice", "Customer Discount Declaration Note", "RC", "Vehicle", "Chassis", "Engine", "Registration No", "Regn No"
- Business Document: Must contain "GST Reg" or "Government of India" AND at least one of: "Legal Name", "Trade Name", "Business"

Return ONLY a JSON object:
{{
  "document_type": "government_identity|vehicle_document|business_document|unknown",
  "sub_type": "aadhaar|pan|driving_license|sales_tax_invoice|delivery_acknowledgement_note|customer_discount_declaration_note|registration_certificate|business_gst|unknown",
  "confidence": "high|medium|low",
  "indicators": ["list of text phrases that led to this classification"]
}}

OCR text from {page_file}:
{cleaned_ocr_text}
"""
        result = self.processor._make_llm_call(prompt, page_file)
        
        # Validate and return result
        if not result or 'document_type' not in result:
            # Fallback to keyword-based classification
            return self._fallback_classification(cleaned_ocr_text, page_file)
        
        return result
    
    def _fallback_classification(self, text, page_file):
        """
        Fallback keyword-based classification if LLM fails
        """
        text_lower = text.lower()
        
        # Check for government identity documents
        gov_matches = sum(1 for kw in self.government_keywords if kw in text_lower)
        vehicle_matches = sum(1 for kw in self.vehicle_keywords if kw in text_lower)
        business_matches = sum(1 for kw in self.business_keywords if kw in text_lower)
        
        if gov_matches >= 2:
            # Determine sub_type
            sub_type = self._identify_government_subtype(text)
            return {
                "document_type": "government_identity",
                "sub_type": sub_type,
                "confidence": "medium",
                "indicators": [kw for kw in self.government_keywords if kw in text_lower]
            }
        elif vehicle_matches >= 2:
            sub_type = self._identify_vehicle_subtype(text)
            return {
                "document_type": "vehicle_document",
                "sub_type": sub_type,
                "confidence": "medium",
                "indicators": [kw for kw in self.vehicle_keywords if kw in text_lower]
            }
        elif business_matches >= 2:
            return {
                "document_type": "business_document",
                "sub_type": "business_gst",
                "confidence": "medium",
                "indicators": [kw for kw in self.business_keywords if kw in text_lower]
            }
        else:
            return {
                "document_type": "unknown",
                "sub_type": "unknown",
                "confidence": "low",
                "indicators": []
            }
    
    def _identify_government_subtype(self, text):
        """Identify specific government document sub-type"""
        text_upper = text.upper()
        
        if any(keyword in text_upper for keyword in [
            'PERMANENT ACCOUNT', 'INCOME TAX', 'PAN CARD', "FATHER'S NAME"
        ]) or re.search(r'[A-Z]{5}[0-9]{4}[A-Z]', text):
            return 'pan'
        elif any(keyword in text_upper for keyword in [
            'AADHAAR', 'UNIQUE IDENTIFICATION', 'GOVERNMENT OF INDIA', 'UIDAI'
        ]) or re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\b', text):
            return 'aadhaar'
        elif any(keyword in text_upper for keyword in [
            'DRIVING LICENCE', 'DRIVING LICENSE', 'TRANSPORT AUTHORITY', 'LICENSE TO DRIVE'
        ]) or re.search(r'[A-Z]{2}[0-9]{2}[0-9]{11}', text):
            return 'driving_license'
        else:
            return 'unknown'
    
    def _identify_vehicle_subtype(self, text):
        """Identify specific vehicle document sub-type"""
        text_upper = text.upper()
        
        if 'SALES TAX INVOICE' in text_upper or 'TAX INVOICE' in text_upper:
            return 'sales_tax_invoice'
        elif 'DELIVERY ACKNOWLEDGEMENT' in text_upper or 'DELIVERY ACKNOWLEDGMENT' in text_upper:
            return 'delivery_acknowledgement_note'
        elif 'CUSTOMER DISCOUNT DECLARATION' in text_upper or 'DISCOUNT DECLARATION' in text_upper:
            return 'customer_discount_declaration_note'
        elif 'CUSTOMER EXCHANGE DECLARATION' in text_upper or 'EXCHANGE DECLARATION' in text_upper:
            return 'customer_exchange_declaration_note'
        elif any(kw in text_upper for kw in ['REGISTRATION CERTIFICATE', 'CERTIFICATE OF REGISTRATION', 'REGN', 'RC']):
            return 'registration_certificate'
        else:
            return 'unknown'
