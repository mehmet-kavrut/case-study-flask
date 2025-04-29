import os
import time
import logging
from dotenv import load_dotenv
from google.cloud import storage


load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



def cleanup_old_files(folder, days=20):
    now = time.time()
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.stat(file_path).st_mtime < now - days * 86400:
            os.remove(file_path)
            logging.info(f"Deleted old file: {file_path}")


def upload_to_gcs(local_file_path, gcs_file_name):
    """Uploads a file to Google Cloud Storage"""
    try:
        client = storage.Client.from_service_account_json(os.getenv('GCS_CREDENTIALS_PATH'))
        bucket = client.bucket(os.getenv('GCS_BUCKET_NAME'))
        blob = bucket.blob(gcs_file_name)
        blob.upload_from_filename(local_file_path)
        logging.info(f"File {local_file_path} uploaded to GCS as {gcs_file_name}")
    except Exception as e:
        logging.error(f"Error uploading file to GCS: {e}")
        raise
