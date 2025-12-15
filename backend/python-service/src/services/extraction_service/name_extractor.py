# This module extracts and validates customer names from documents

import re

class NameExtractor:
    def __init__(self, processor):
        """
        Initialize with reference to PDF_Processor for LLM calls and patterns
        """
        self.processor = processor
        
        # Titles to remove
        self.titles = [
            'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'shri', 'smt', 
            'sri', 'srimati', 'kumari', 'master', 'mx'
        ]
        
        # Relative indicators to exclude
        self.relative_indicators = ['w/o', 'd/o', 's/o', 'c/o', 'wife of', 'daughter of', 'son of', 'care of']
    
    def extract_names_from_vehicle_documents(self, page_data_list):
        """
        Extract customer names from vehicle documents (Sales Tax Invoice, DAN, CDDN)
        Returns: list of normalized names
        """
        vehicle_names = []
        
        for page_data in page_data_list:
            if page_data.get('document_type') != 'vehicle_document':
                continue
            
            page_file = page_data.get('page_file')
            cleaned_text = page_data.get('cleaned_ocr_text', '')
            
            prompt = f"""
You are an AI system that extracts customer names from vehicle purchase documents.

Extract the CUSTOMER NAME (buyer name) from this vehicle document. This is the person who purchased the vehicle.

Rules:
1. Look for fields like: "Customer Name", "Buyer Name", "Sold To", "Customer", "Bill To"
2. Extract ONLY the customer's name, NOT company names, NOT dealer names
3. Remove titles: Mr., Mrs., Dr., Miss, Prof., Shri, Smt.
4. Do NOT include relative names with W/O, D/O, S/O indicators
5. Return the full name as it appears

Return ONLY a JSON object:
{{
  "customer_name": "extracted customer name or null if not found",
  "confidence": "high|medium|low"
}}

OCR text from {page_file}:
{cleaned_text}
"""
            result = self.processor._make_llm_call(prompt, page_file)
            
            if result and result.get('customer_name'):
                raw_name = result['customer_name']
                normalized_name = self.normalize_name_for_comparison(raw_name)
                if normalized_name:
                    vehicle_names.append({
                        'raw_name': raw_name,
                        'normalized_name': normalized_name,
                        'source': page_data.get('sub_type', 'vehicle_document'),
                        'confidence': result.get('confidence', 'medium')
                    })
                    print(f"✅ Extracted name from vehicle doc: {raw_name} -> {normalized_name}")
        
        return vehicle_names
    
    def extract_names_from_identity_documents(self, page_data_list):
        """
        Extract customer names from identity documents (Aadhaar, PAN, DL)
        Returns: list of normalized names with document type
        """
        identity_names = []
        
        for page_data in page_data_list:
            if page_data.get('document_type') != 'government_identity':
                continue
            
            page_file = page_data.get('page_file')
            cleaned_text = page_data.get('cleaned_ocr_text', '')
            sub_type = page_data.get('sub_type', 'unknown')
            
            if sub_type == 'pan':
                name = self._extract_name_from_pan(cleaned_text, page_file)
            elif sub_type == 'aadhaar':
                name = self._extract_name_from_aadhaar(cleaned_text, page_file)
            elif sub_type == 'driving_license':
                name = self._extract_name_from_dl(cleaned_text, page_file)
            else:
                name = None
            
            if name:
                normalized_name = self.normalize_name_for_comparison(name)
                if normalized_name:
                    identity_names.append({
                        'raw_name': name,
                        'normalized_name': normalized_name,
                        'source': sub_type,
                        'document_type': 'government_identity'
                    })
                    print(f"✅ Extracted name from {sub_type}: {name} -> {normalized_name}")
        
        return identity_names
    
    def _extract_name_from_pan(self, text, page_file):
        """Extract name from PAN card - first line is customer name"""
        prompt = f"""
Extract the customer name from this PAN card.

Rules:
1. The FIRST line with a person's name is the CUSTOMER name
2. The SECOND line is usually the father's name - DO NOT extract this
3. Remove titles: Mr., Mrs., Dr., Miss, Prof., Shri, Smt.
4. Return only the customer's name

Return ONLY a JSON object:
{{
  "customer_name": "extracted customer name or null if not found"
}}

OCR text:
{text}
"""
        result = self.processor._make_llm_call(prompt, page_file)
        return result.get('customer_name') if result else None
    
    def _extract_name_from_aadhaar(self, text, page_file):
        """Extract name from Aadhaar card - customer name usually prominent"""
        prompt = f"""
Extract the customer name from this Aadhaar card.

Rules:
1. The customer name usually appears prominently near the top
2. Father's/husband's name appears separately with indicators or below the main name
3. Look for the LARGER or MORE PROMINENT name
4. Remove titles: Mr., Mrs., Dr., Miss, Prof., Shri, Smt.
5. Do NOT include names with S/O, D/O, W/O, C/O indicators

Return ONLY a JSON object:
{{
  "customer_name": "extracted customer name or null if not found"
}}

OCR text:
{text}
"""
        result = self.processor._make_llm_call(prompt, page_file)
        return result.get('customer_name') if result else None
    
    def _extract_name_from_dl(self, text, page_file):
        """Extract name from Driving License"""
        prompt = f"""
Extract the customer name from this Driving License.

Rules:
1. Look for fields like "Name", "Holder Name", "License Holder"
2. Father's/guardian's name appears separately
3. Remove titles: Mr., Mrs., Dr., Miss, Prof., Shri, Smt.
4. Do NOT include names with S/O, D/O, W/O indicators

Return ONLY a JSON object:
{{
  "customer_name": "extracted customer name or null if not found"
}}

OCR text:
{text}
"""
        result = self.processor._make_llm_call(prompt, page_file)
        return result.get('customer_name') if result else None
    
    def normalize_name_for_comparison(self, name):
        """
        Normalize name for comparison
        - Remove titles
        - Convert to lowercase
        - Remove extra spaces
        - Remove relative indicators
        """
        if not name:
            return ""
        
        # Convert to lowercase
        name = name.lower().strip()
        
        # Remove titles
        for title in self.titles:
            # Remove title with dot
            name = re.sub(rf'\b{title}\.\s*', '', name, flags=re.IGNORECASE)
            # Remove title without dot
            name = re.sub(rf'\b{title}\s+', '', name, flags=re.IGNORECASE)
        
        # Remove relative indicators
        for indicator in self.relative_indicators:
            name = re.sub(rf'\b{indicator}\b.*', '', name, flags=re.IGNORECASE)
        
        # Remove multiple spaces
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def match_customer_name(self, vehicle_names, identity_names):
        """
        Match customer name between vehicle documents and identity documents
        Returns: The best matched customer name
        """
        if not vehicle_names:
            print("⚠️ No names found in vehicle documents")
            return None
        
        if not identity_names:
            print("⚠️ No names found in identity documents")
            # Return the first vehicle name as fallback
            return vehicle_names[0]['raw_name']
        
        best_match = None
        best_score = 0
        
        print("\n🔍 Matching names between vehicle and identity documents...")
        
        for v_name in vehicle_names:
            for i_name in identity_names:
                score = self.enhanced_name_similarity(
                    v_name['normalized_name'], 
                    i_name['normalized_name']
                )
                
                print(f"  Comparing: '{v_name['raw_name']}' <-> '{i_name['raw_name']}' = {score:.2f}")
                
                if score > best_score:
                    best_score = score
                    best_match = i_name['raw_name']  # Use identity document name as it's more official
        
        if best_score >= 0.6:  # Threshold for match
            print(f"✅ Best match found: {best_match} (score: {best_score:.2f})")
            return best_match
        else:
            print(f"⚠️ No good match found (best score: {best_score:.2f}). Using vehicle document name.")
            return vehicle_names[0]['raw_name']
    
    def enhanced_name_similarity(self, name1, name2):
        """
        Calculate enhanced similarity score between two names
        Uses Jaccard similarity, overlap similarity, and fuzzy matching
        """
        if not name1 or not name2:
            return 0.0
        
        # Exact match
        if name1 == name2:
            return 1.0
        
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        jaccard = intersection / union if union > 0 else 0
        
        # Overlap similarity (intersection over minimum)
        overlap = intersection / min(len(words1), len(words2)) if min(len(words1), len(words2)) > 0 else 0
        
        # Compound name matching
        is_compound_match, compound_score = self.check_compound_name_match(name1, name2)
        
        # Fuzzy string similarity using Levenshtein distance
        fuzzy_score = self.string_similarity(name1, name2)
        
        # Weighted combination
        if is_compound_match and compound_score >= 0.8:
            similarity = (compound_score * 0.6) + (overlap * 0.2) + (jaccard * 0.1) + (fuzzy_score * 0.1)
        else:
            similarity = (jaccard * 0.3) + (overlap * 0.4) + (fuzzy_score * 0.2) + (compound_score * 0.1)
        
        return min(similarity, 1.0)
    
    def check_compound_name_match(self, name1, name2):
        """
        Check if names are compound matches (e.g., 'ramkumar dubey' vs 'ram kumar dubey')
        """
        # Remove all spaces and compare
        no_space1 = name1.replace(' ', '')
        no_space2 = name2.replace(' ', '')
        
        if no_space1 == no_space2:
            return True, 1.0
        
        # Check if one is substring of other (after space removal)
        if no_space1 in no_space2 or no_space2 in no_space1:
            ratio = min(len(no_space1), len(no_space2)) / max(len(no_space1), len(no_space2))
            return True, ratio
        
        return False, 0.0
    
    def string_similarity(self, s1, s2):
        """
        Calculate string similarity using Levenshtein distance
        Returns normalized similarity score between 0 and 1
        """
        if s1 == s2:
            return 1.0
        
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # Create matrix
        matrix = [[0 for _ in range(len2 + 1)] for _ in range(len1 + 1)]
        
        # Initialize first column and row
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        # Fill matrix
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if s1[i-1] == s2[j-1]:
                    matrix[i][j] = matrix[i-1][j-1]
                else:
                    matrix[i][j] = 1 + min(
                        matrix[i-1][j],      # deletion
                        matrix[i][j-1],      # insertion
                        matrix[i-1][j-1]     # substitution
                    )
        
        # Levenshtein distance
        distance = matrix[len1][len2]
        
        # Normalize to similarity score
        max_len = max(len1, len2)
        similarity = 1 - (distance / max_len)
        
        return similarity
