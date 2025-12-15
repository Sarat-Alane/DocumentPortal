# This module updates the database with extracted JSON data

import psycopg2
from psycopg2.extras import Json
import json

def update_customer_record(conn, cursor, json_data):
    """
    Update database record with extracted data
    Uses filename as primary key to update the record
    """
    try:
        filename = json_data.get('filename')
        
        if not filename:
            print("❌ No filename provided for database update")
            return False
        
        # Prepare JSONB fields
        tax_invoice_json = Json(json_data.get('tax_invoice')) if json_data.get('tax_invoice') else None
        dan_json = Json(json_data.get('dan')) if json_data.get('dan') else None
        cddn_json = Json(json_data.get('cddn')) if json_data.get('cddn') else None
        
        # Update query
        update_query = """
        UPDATE customersnew
        SET 
            name = %s,
            dob = %s,
            gender = %s,
            address = %s,
            city = %s,
            state = %s,
            aadhaar_provided = %s,
            aadhaar_number = %s,
            pan_provided = %s,
            pan_number = %s,
            dl_provided = %s,
            dl_number = %s,
            rc_provided = %s,
            vehicle_rc = %s,
            gstin_provided = %s,
            gstin = %s,
            gst_company = %s,
            tax_invoice = %s,
            dan = %s,
            cddn = %s
        WHERE filename = %s
        """
        
        cursor.execute(update_query, (
            json_data.get('name'),
            json_data.get('dob'),
            json_data.get('gender'),
            json_data.get('address'),
            json_data.get('city'),
            json_data.get('state'),
            json_data.get('aadhaar_provided', False),
            json_data.get('aadhaar_number'),
            json_data.get('pan_provided', False),
            json_data.get('pan_number'),
            json_data.get('dl_provided', False),
            json_data.get('dl_number'),
            json_data.get('rc_provided', False),
            json_data.get('vehicle_rc'),
            json_data.get('gstin_provided', False),
            json_data.get('gstin'),
            json_data.get('gst_company'),
            tax_invoice_json,
            dan_json,
            cddn_json,
            filename
        ))
        
        conn.commit()
        
        rows_affected = cursor.rowcount
        if rows_affected > 0:
            print(f"✅ Database updated successfully for filename: {filename}")
            print(f"   Rows affected: {rows_affected}")
            return True
        else:
            print(f"⚠️ No rows updated. Record with filename '{filename}' may not exist.")
            return False
        
    except psycopg2.Error as e:
        print(f"❌ Database error during update: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Unexpected error during update: {e}")
        conn.rollback()
        return False
