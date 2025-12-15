# This module extracts business context (GSTIN and company name) from business documents

import re

class BusinessContextExtractor:
    def __init__(self, processor):
        """
        Initialize with reference to PDF_Processor for patterns and LLM calls
        """
        self.processor = processor
    
    def extract_business_context(self, page_data_list):
        """
        Extract GSTIN and company name from business documents
        Returns: dict with gstin_provided, gstin, gst_company
        """
        business_data = {
            'gstin_provided': False,
            'gstin': None,
            'gst_company': None
        }
        
        # Check if any page has business context
        has_business_doc = any(
            page.get('document_type') == 'business_document' 
            for page in page_data_list
        )
        
        if not has_business_doc:
            return business_data
        
        for page_data in page_data_list:
            if page_data.get('document_type') != 'business_document':
                continue
            
            cleaned_text = page_data.get('cleaned_ocr_text', '')
            
            # Check if it has valid business context
            if not self._has_valid_business_context(cleaned_text):
                continue
            
            extracted = self._extract_business_details(page_data)
            
            if extracted and extracted.get('gstin'):
                business_data['gstin_provided'] = True
                business_data['gstin'] = extracted['gstin']
                business_data['gst_company'] = extracted.get('company_name')
                print(f"✅ Business details extracted: GSTIN={extracted['gstin']}, Company={extracted.get('company_name')}")
                break  # Found valid business data, stop searching
        
        return business_data
    
    def _has_valid_business_context(self, text):
        """
        Check if document has valid business context
        Must have "GST Reg" or "Government of India" AND business-related terms
        """
        text_lower = text.lower()
        
        has_gst_indicator = any(keyword in text_lower for keyword in [
            'gst reg', 'gst registration', 'government of india', 'gstin'
        ])
        
        has_business_term = any(keyword in text_lower for keyword in [
            'legal name', 'trade name', 'business', 'company'
        ])
        
        return has_gst_indicator and has_business_term
    
    def _extract_business_details(self, page_data):
        """Extract GSTIN and company name from business document"""
        cleaned_text = page_data.get('cleaned_ocr_text', '')
        page_file = page_data.get('page_file')
        
        prompt = f"""
Extract business registration details from this document.

Extract the following:
1. GSTIN (GST Identification Number) - Format: 99AAAAA9999A9Z9 (2 digits, 5 letters, 4 digits, 1 letter, 1 digit, Z, 1 digit)
2. Legal Name of the Company / Trade Name

Rules:
- GSTIN is EXACTLY 15 characters: 2 digits, 5 uppercase letters, 4 digits, 1 letter, 1 digit, Z, 1 digit
- Look for labels: "GSTIN", "GST No", "GST Registration Number"
- Legal Name is usually labeled as "Legal Name", "Trade Name", "Business Name"

Return ONLY a JSON object:
{{
  "gstin": "15 character GSTIN or null",
  "company_name": "legal/trade name of company or null"
}}

OCR text:
{cleaned_text}
"""
        result = self.processor._make_llm_call(prompt, page_file)
        
        if not result or not result.get('gstin'):
            # Fallback to regex extraction
            result = self._extract_with_regex(cleaned_text)
        
        # Validate GSTIN
        if result and result.get('gstin'):
            gstin = self._clean_gstin(result['gstin'])
            if gstin and self._validate_gstin(gstin):
                result['gstin'] = gstin
            else:
                result['gstin'] = None
        
        return result if result and result.get('gstin') else None
    
    def _extract_with_regex(self, text):
        """Fallback regex extraction for GSTIN and company name"""
        result = {
            'gstin': None,
            'company_name': None
        }
        
        # GSTIN patterns
        gstin_patterns = [
            r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9][Z][0-9]\b',
            r'(?:GSTIN|GST\s?NO\.?|GST\s?REG\.?\s?NO\.?)[:\s]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9][Z][0-9])',
        ]
        
        for pattern in gstin_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                gstin = matches[0] if isinstance(matches[0], str) else matches[0]
                gstin_cleaned = self._clean_gstin(gstin)
                if gstin_cleaned and self._validate_gstin(gstin_cleaned):
                    result['gstin'] = gstin_cleaned
                    break
        
        # Company name patterns - look for Legal Name or Trade Name
        company_patterns = [
            r'(?:LEGAL\s?NAME|TRADE\s?NAME)[:\s]*([A-Z\s&.]+)',
            r'(?:BUSINESS\s?NAME|COMPANY\s?NAME)[:\s]*([A-Z\s&.]+)',
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                company = matches[0].strip()
                if len(company) > 3:  # Basic validation
                    result['company_name'] = company
                    break
        
        return result if result['gstin'] else None
    
    def _clean_gstin(self, gstin):
        """Clean GSTIN number"""
        if not gstin:
            return None
        # Remove spaces and convert to uppercase
        cleaned = re.sub(r'\s', '', str(gstin)).upper()
        return cleaned if len(cleaned) == 15 else None
    
    def _validate_gstin(self, gstin):
        """Validate GSTIN format"""
        if not gstin or len(gstin) != 15:
            return False
        return bool(self.processor.gstin_pattern.match(gstin))
