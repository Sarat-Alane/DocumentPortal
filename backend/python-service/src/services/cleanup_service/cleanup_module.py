# /root/backend/python-service/src/services/db_service/cleanup_module.py

# This module contains functions to implement cleanup of the files and the folders when invoked (generally after the PDF and its images have been processed or the json file is converted to SQL entries)

import os
import shutil

def cleanup_files(files_to_delete, folders_to_delete):
    """Clean up temporary files and folders"""
    for file_path in files_to_delete:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
    
    for folder_path in folders_to_delete:
        try:
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                print(f"Deleted folder: {folder_path}")
        except Exception as e:
            print(f"Error deleting folder {folder_path}: {e}")