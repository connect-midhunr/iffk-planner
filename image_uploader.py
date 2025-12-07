import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

LOG_DIR = os.getenv("LOGS", "logs")

# Ensure folder exists
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "iffk_planner.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

class ImageUploader:
    """
    Handles uploading images to imgbb using API.
    Supports both bytes (Streamlit uploads) and file paths.
    Returns permanent public URLs.
    """

    def __init__(self):
        try:
            self.api_key = os.getenv("IMGBB_API_KEY")
            if not self.api_key:
                logging.error("IMGBB_API_KEY is missing in .env")
                raise ValueError("IMGBB_API_KEY not found in .env")

            self.upload_url = "https://api.imgbb.com/1/upload"
            logging.info("ImageUploader initialized successfully")

        except Exception as e:
            logging.exception("Failed to initialize ImageUploader")
            raise

    def upload_bytes(self, file_bytes: bytes, file_name="image.jpg"):
        """
        Upload image file bytes to imgbb.
        Returns the image public URL.
        """

        logging.info(f"Uploading image bytes: {file_name}")

        try:
            payload = { "key": self.api_key }
            files = { "image": (file_name, file_bytes) }

            response = requests.post(self.upload_url, data=payload, files=files)

            return self._handle_response(response)

        except Exception as e:
            logging.exception(f"Error uploading image bytes ({file_name}): {e}")
            raise

    def upload_file_path(self, file_path: str):
        """
        Upload image from a file path.
        """
        logging.info(f"Uploading file from path: {file_path}")

        try:
            if not os.path.exists(file_path):
                logging.error(f"File does not exist: {file_path}")
                raise FileNotFoundError(f"File not found: {file_path}")

            with open(file_path, "rb") as f:
                file_bytes = f.read()

            return self.upload_bytes(file_bytes, file_name=os.path.basename(file_path))

        except Exception as e:
            logging.exception(f"Error uploading file ({file_path}): {e}")
            raise

    def _handle_response(self, response):
        """
        Validates API response and returns the image URL.
        """

        try:
            if response.status_code != 200:
                logging.error(f"imgbb upload failed: {response.text}")
                raise Exception(f"imgbb upload failed: {response.text}")

            data = response.json()

            if not data.get("success"):
                logging.error(f"imgbb API error: {data}")
                raise Exception(f"imgbb responded with error: {data}")

            url = data["data"]["url"]
            logging.info(f"Image uploaded successfully: {url}")
            return url

        except Exception as e:
            logging.exception(f"Failed to process imgbb API response: {e}")
            raise
