# This module compiles all extracted data into a single JSON object

import json

class JSONGenerator:
    def __init__(self):
        pass
    
    def generate_json(self, filename, customer_data, vehicle_data, business_data):
        """
        Generate final JSON object matching database schema
        """
        final_json = {
            'filename': filename,
            'name': customer_data.get('name'),
            'dob': customer_data.get('dob'),
            'gender': customer_data.get('gender'),
            'address': customer_data.get('address'),
            'city': customer_data.get('city'),
            'state': customer_data.get('state'),
            'aadhaar_provided': customer_data.get('aadhaar_provided', False),
            'aadhaar_number': customer_data.get('aadhaar_number'),
            'pan_provided': customer_data.get('pan_provided', False),
            'pan_number': customer_data.get('pan_number'),
            'dl_provided': customer_data.get('dl_provided', False),
            'dl_number': customer_data.get('dl_number'),
            'rc_provided': customer_data.get('rc_provided', False),
            'vehicle_rc': customer_data.get('vehicle_rc'),
            'gstin_provided': business_data.get('gstin_provided', False),
            'gstin': business_data.get('gstin'),
            'gst_company': business_data.get('gst_company'),
            'tax_invoice': vehicle_data.get('tax_invoice'),
            'dan': vehicle_data.get('dan'),
            'cddn': vehicle_data.get('cddn')
        }
        
        print("\n" + "="*60)
        print("GENERATED JSON DATA:")
        print("="*60)
        print(json.dumps(final_json, indent=2, ensure_ascii=False))
        print("="*60 + "\n")
        
        return final_json
