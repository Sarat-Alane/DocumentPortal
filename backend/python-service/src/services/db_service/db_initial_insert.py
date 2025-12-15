# This module handles the initial database insertion of filename to ensure one file = one database entry

import psycopg2
from datetime import datetime

def insert_initial_record(conn, cursor, filename):
    """
    Insert initial record with just filename to ensure one file = one database entry
    Returns True if successful, False otherwise
    """
    try:
        # Check if filename already exists
        cursor.execute(
            "SELECT filename FROM customersnew WHERE filename = %s",
            (filename,)
        )
        existing = cursor.fetchone()
        
        if existing:
            print(f"⚠️ Record with filename '{filename}' already exists in database. Skipping insertion.")
            return False
        
        # Insert new record with only filename
        cursor.execute(
            """
            INSERT INTO customersnew (filename)
            VALUES (%s)
            """,
            (filename,)
        )
        conn.commit()
        print(f"✅ Initial record inserted for filename: {filename}")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error during initial insert: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Unexpected error during initial insert: {e}")
        conn.rollback()
        return False
