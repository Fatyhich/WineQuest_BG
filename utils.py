import os
from PIL import Image
import uuid
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_valid_image(file_path):
    """Check if the file is a valid image."""
    try:
        img = Image.open(file_path)
        img.verify()
        return True
    except Exception as e:
        logger.error(f"Invalid image file: {e}")
        return False

def get_job_info(job_id, redis_client):
    """Get job information from Redis."""
    try:
        job_info = redis_client.get(f"job:{job_id}")
        return job_info
    except Exception as e:
        logger.error(f"Error retrieving job info: {e}")
        return None

def generate_unique_id():
    """Generate a unique identifier."""
    return str(uuid.uuid4())

def cleanup_old_files(directory, max_age_hours=24):
    """Clean up files older than max_age_hours."""
    try:
        current_time = time.time()
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            # Check if it's a file and not a directory
            if os.path.isfile(file_path):
                # Check if file is older than max_age_hours
                file_age = current_time - os.path.getctime(file_path)
                if file_age > (max_age_hours * 3600):
                    os.remove(file_path)
                    logger.info(f"Removed old file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up files: {e}") 