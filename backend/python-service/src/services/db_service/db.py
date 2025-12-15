# /root/backend/python-service/src/services/db_services/db.py

# This module contains functions for extablishing and closing connection with the PostgreSQL database on AWS

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        cursor = conn.cursor()
        print("Database connection established")
        return conn, cursor
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise


