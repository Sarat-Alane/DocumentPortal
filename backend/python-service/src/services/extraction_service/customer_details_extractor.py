# This module extracts customer personal details and identity numbers from government documents

import re
from datetime import datetime
from dateutil import parser as date_parser

class CustomerDetailsExtractor:
    def __init__(self, processor):
        """
        Initialize with reference to PDF_Processor for patterns and LLM calls
        """
        self.processor = processor
    
    def extract_customer_details(self, page_data_list, customer_name):
        """
        Extract customer details from identity documents
        Returns: dict with all customer details
        """
        customer_data = {
            'name': customer_name,
            'dob': None,
            'gender': None,
            'address': None,
            'city': None,
            'state': None,
            'aadhaar_provided': False,
            'aadhaar_number': None,
            'pan_provided': False,
            'pan_number': None,
            'dl_provided': False,
            'dl_number': None,
            'rc_provided': False,
            'vehicle_rc': None
        }
        
        for page_data in page_data_list:
            if page_data.get('document_type') != 'government_identity':
                continue
            
            sub_type = page_data.get('sub_type')
            
            if sub_type == 'aadhaar':
                aadhaar_data = self._extract_aadhaar_details(page_data)
                customer_data.update(aadhaar_data)
            elif sub_type == 'pan':
                pan_data = self._extract_pan_details(page_data)
                customer_data.update(pan_data)
            elif sub_type == 'driving_license':
                dl_data = self._extract_dl_details(page_data)
                customer_data.update(dl_data)
        
        # Also check for RC in vehicle documents
        for page_data in page_data_list:
            if page_data.get('sub_type') == 'registration_certificate':
                rc_data = self._extract_rc_details(page_data)
                customer_data.update(rc_data)
        
        return customer_data
    
    def _extract_aadhaar_details(self, page_data):
        """Extract details from Aadhaar card"""
        cleaned_text = page_data.get('cleaned_ocr_text', '')
        page_file = page_data.get('page_file')
        
        prompt = f"""
Extract the following information from this Aadhaar card:
1. Aadhaar Number (12 digits, may have spaces like XXXX XXXX XXXX)
2. Date of Birth (DOB)
3. Gender (Male/Female)
4. Full Address
5. City
6. State

Rules:
- Aadhaar number is EXACTLY 12 digits
- DOB can be in various formats: DD/MM/YYYY, DD-MM-YYYY, etc.
- Extract complete address
- Gender is usually Male, Female, or M, F

Return ONLY a JSON object:
{{
  "aadhaar_number": "12 digit number without spaces",
  "dob": "date of birth as found",
  "gender": "Male or Female",
  "address": "full address",
  "city": "city name",
  "state": "state name"
}}

OCR text:
{cleaned_text}
"""
        result = self.processor._make_llm_call(prompt, page_file)
        
        extracted_data = {}
        
        if result:
            # Process Aadhaar number - remove spaces and validate
            if result.get('aadhaar_number'):
                aadhaar = self._clean_aadhaar_number(result['aadhaar_number'])
                if aadhaar and self._validate_aadhaar(aadhaar):
                    extracted_data['aadhaar_provided'] = True
                    extracted_data['aadhaar_number'] = aadhaar
                    print(f"✅ Aadhaar extracted: {aadhaar}")
                else:
                    # Fallback to regex extraction
                    aadhaar = self._extract_aadhaar_with_regex(cleaned_text)
                    if aadhaar:
                        extracted_data['aadhaar_provided'] = True
                        extracted_data['aadhaar_number'] = aadhaar
                        print(f"✅ Aadhaar extracted (regex): {aadhaar}")
            
            # Process DOB
            if result.get('dob'):
                dob = self._parse_date(result['dob'])
                if dob:
                    extracted_data['dob'] = dob
                    print(f"✅ DOB extracted: {dob}")
            
            # Process Gender
            if result.get('gender'):
                gender = self._normalize_gender(result['gender'])
                if gender:
                    extracted_data['gender'] = gender
            
            # Process Address
            if result.get('address'):
                extracted_data['address'] = result['address'].strip()
            
            if result.get('city'):
                extracted_data['city'] = result['city'].strip()
            
            if result.get('state'):
                extracted_data['state'] = result['state'].strip()
        
        return extracted_data
    
    def _extract_pan_details(self, page_data):
        """Extract details from PAN card"""
        cleaned_text = page_data.get('cleaned_ocr_text', '')
        page_file = page_data.get('page_file')
        
        prompt = f"""
Extract the following information from this PAN card:
1. PAN Number (format: AAAAA9999A - 5 letters, 4 digits, 1 letter)
2. Date of Birth (DOB)
3. Full Name (already extracted separately)

Rules:
- PAN number is EXACTLY 10 characters: 5 uppercase letters, 4 digits, 1 uppercase letter
- DOB can be in various formats

Return ONLY a JSON object:
{{
  "pan_number": "10 character PAN number",
  "dob": "date of birth as found"
}}

OCR text:
{cleaned_text}
"""
        result = self.processor._make_llm_call(prompt, page_file)
        
        extracted_data = {}
        
        if result:
            # Process PAN number
            if result.get('pan_number'):
                pan = self._clean_pan_number(result['pan_number'])
                if pan and self._validate_pan(pan):
                    extracted_data['pan_provided'] = True
                    extracted_data['pan_number'] = pan
                    print(f"✅ PAN extracted: {pan}")
                else:
                    # Fallback to regex extraction
                    pan = self._extract_pan_with_regex(cleaned_text)
                    if pan:
                        extracted_data['pan_provided'] = True
                        extracted_data['pan_number'] = pan
                        print(f"✅ PAN extracted (regex): {pan}")
            
            # Process DOB
            if result.get('dob'):
                dob = self._parse_date(result['dob'])
                if dob:
                    extracted_data['dob'] = dob
                    print(f"✅ DOB extracted from PAN: {dob}")
        
        return extracted_data
    
    def _extract_dl_details(self, page_data):
        """Extract details from Driving License"""
        cleaned_text = page_data.get('cleaned_ocr_text', '')
        page_file = page_data.get('page_file')
        
        prompt = f"""
Extract the following information from this Driving License:
1. DL Number (format: AA99 99999999999 - 2 letters, 2 digits, 11 digits, may have spaces)
2. Date of Birth (DOB)
3. Address
4. City
5. State
6. Gender

Return ONLY a JSON object:
{{
  "dl_number": "DL number",
  "dob": "date of birth",
  "address": "full address",
  "city": "city name",
  "state": "state name",
  "gender": "Male or Female"
}}

OCR text:
{cleaned_text}
"""
        result = self.processor._make_llm_call(prompt, page_file)
        
        extracted_data = {}
        
        if result:
            # Process DL number
            if result.get('dl_number'):
                dl = self._clean_dl_number(result['dl_number'])
                if dl and self._validate_dl(dl):
                    extracted_data['dl_provided'] = True
                    extracted_data['dl_number'] = dl
                    print(f"✅ DL extracted: {dl}")
                else:
                    # Fallback to regex extraction
                    dl = self._extract_dl_with_regex(cleaned_text)
                    if dl:
                        extracted_data['dl_provided'] = True
                        extracted_data['dl_number'] = dl
                        print(f"✅ DL extracted (regex): {dl}")
            
            # Process DOB
            if result.get('dob'):
                dob = self._parse_date(result['dob'])
                if dob:
                    extracted_data['dob'] = dob
            
            # Process Gender
            if result.get('gender'):
                gender = self._normalize_gender(result['gender'])
                if gender:
                    extracted_data['gender'] = gender
            
            # Process Address
            if result.get('address'):
                extracted_data['address'] = result['address'].strip()
            
            if result.get('city'):
                extracted_data['city'] = result['city'].strip()
            
            if result.get('state'):
                extracted_data['state'] = result['state'].strip()
        
        return extracted_data
    
    def _extract_rc_details(self, page_data):
        """Extract RC number from Registration Certificate"""
        cleaned_text = page_data.get('cleaned_ocr_text', '')
        page_file = page_data.get('page_file')
        
        prompt = f"""
Extract the Vehicle Registration Number (RC Number) from this Registration Certificate.

Format: AA99AA9999 or AA99A9999 (2 letters, 2 digits, 1-2 letters, 4 digits)
May have spaces or hyphens like: AA 99 AA 9999 or AA-99-AA-9999

Return ONLY a JSON object:
{{
  "rc_number": "registration number"
}}

OCR text:
{cleaned_text}
"""
        result = self.processor._make_llm_call(prompt, page_file)
        
        extracted_data = {}
        
        if result and result.get('rc_number'):
            rc = self._clean_rc_number(result['rc_number'])
            if rc and self._validate_rc(rc):
                extracted_data['rc_provided'] = True
                extracted_data['vehicle_rc'] = rc
                print(f"✅ RC extracted: {rc}")
            else:
                # Fallback to regex extraction
                rc = self._extract_rc_with_regex(cleaned_text)
                if rc:
                    extracted_data['rc_provided'] = True
                    extracted_data['vehicle_rc'] = rc
                    print(f"✅ RC extracted (regex): {rc}")
        
        return extracted_data
    
    # Cleaning and validation methods
    
    def _clean_aadhaar_number(self, aadhaar):
        """Clean Aadhaar number - remove spaces and validate"""
        if not aadhaar:
            return None
        # Remove all non-digit characters
        cleaned = re.sub(r'\D', '', str(aadhaar))
        return cleaned if len(cleaned) == 12 else None
    
    def _validate_aadhaar(self, aadhaar):
        """Validate Aadhaar number - must be exactly 12 digits"""
        if not aadhaar:
            return False
        return bool(self.processor.aadhaar_validate_pattern.match(aadhaar))
    
    def _extract_aadhaar_with_regex(self, text):
        """Extract Aadhaar using regex as fallback"""
        matches = self.processor.aadhaar_extract_pattern.findall(text)
        for match in matches:
            cleaned = re.sub(r'\D', '', match)
            if self._validate_aadhaar(cleaned):
                return cleaned
        return None
    
    def _clean_pan_number(self, pan):
        """Clean PAN number - uppercase and remove spaces"""
        if not pan:
            return None
        cleaned = re.sub(r'\s', '', str(pan)).upper()
        return cleaned if len(cleaned) == 10 else None
    
    def _validate_pan(self, pan):
        """Validate PAN number format"""
        if not pan:
            return False
        return bool(self.processor.pan_pattern.match(pan))
    
    def _extract_pan_with_regex(self, text):
        """Extract PAN using regex as fallback"""
        matches = self.processor.pan_pattern.findall(text)
        return matches[0] if matches else None
    
    def _clean_dl_number(self, dl):
        """Clean DL number - uppercase"""
        if not dl:
            return None
        return str(dl).upper().strip()
    
    def _validate_dl(self, dl):
        """Validate DL number format"""
        if not dl:
            return False
        # Remove spaces for validation
        dl_no_space = re.sub(r'\s', '', dl)
        return bool(self.processor.dl_pattern.match(dl_no_space))
    
    def _extract_dl_with_regex(self, text):
        """Extract DL using regex as fallback"""
        matches = self.processor.dl_pattern.findall(text)
        return matches[0] if matches else None
    
    def _clean_rc_number(self, rc):
        """Clean RC number - uppercase and standardize format"""
        if not rc:
            return None
        # Remove spaces and hyphens, convert to uppercase
        cleaned = re.sub(r'[\s\-]', '', str(rc)).upper()
        return cleaned if len(cleaned) >= 9 and len(cleaned) <= 10 else None
    
    def _validate_rc(self, rc):
        """Validate RC number format"""
        if not rc:
            return False
        rc_no_space = re.sub(r'[\s\-]', '', rc)
        return bool(self.processor.rc_pattern.match(rc_no_space))
    
    def _extract_rc_with_regex(self, text):
        """Extract RC using multiple regex patterns as fallback"""
        rc_patterns = [
            r'\b[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}\b',
            r'\b[A-Z]{2}[0-9]{2}\s[A-Z]{1,2}\s[0-9]{4}\b',
            r'\b[A-Z]{2}-[0-9]{1,2}-[A-Z]{1,3}-[0-9]{4}\b',
            r'(?:REGN\.?\s?NO\.?|REG\.?\s?NO\.?|REGISTRATION\s?NO\.?)[:\s]*([A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4})',
        ]
        
        for pattern in rc_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                rc = matches[0] if isinstance(matches[0], str) else matches[0]
                cleaned = self._clean_rc_number(rc)
                if cleaned and self._validate_rc(cleaned):
                    return cleaned
        return None
    
    def _parse_date(self, date_str):
        """
        Parse date from various formats and return in YYYY-MM-DD format
        """
        if not date_str:
            return None
        
        try:
            # Try using dateutil parser which handles multiple formats
            parsed_date = date_parser.parse(date_str, dayfirst=True)
            return parsed_date.strftime('%Y-%m-%d')
        except:
            pass
        
        # Try common Indian date formats manually
        date_formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
            '%d/%m/%y', '%d-%m-%y', '%d.%m.%y',
            '%Y-%m-%d', '%Y/%m/%d',
            '%d %b %Y', '%d %B %Y',
            '%b %d %Y', '%B %d %Y'
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(str(date_str).strip(), fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except:
                continue
        
        print(f"⚠️ Could not parse date: {date_str}")
        return None
    
    def _normalize_gender(self, gender):
        """Normalize gender to Male/Female"""
        if not gender:
            return None
        
        gender_lower = str(gender).lower().strip()
        
        if gender_lower in ['male', 'm', 'man']:
            return 'Male'
        elif gender_lower in ['female', 'f', 'woman']:
            return 'Female'
        else:
            return gender.strip()
