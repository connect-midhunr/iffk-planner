import os
import json
import logging
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

LOG_DIR = os.getenv("LOGS", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "iffk_planner.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

class ProgrammeManager:

    def __init__(self):
        logging.info("ProgrammeManager initialization started")

        try:
            # Load env vars
            self.RESOURCES_DIR = os.getenv("RESOURCES_DIR", "resources")
            self.CATEGORY_CODES_FILE = os.getenv("CATEGORY_CODES_FILE", "category_codes") + ".json"
            self.COUNTRIES_FILE = os.getenv("COUNTRIES_FILE", "countries") + ".json"
            self.LANGUAGES_FILE = os.getenv("LANGUAGES_FILE", "languages") + ".json"
            self.SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_KEY_FILE", "service_account_key_iffk") + ".json"
            self.SERVICE_ACCOUNT_INFO = {
                "type": os.getenv("SERVICE_ACCOUNT_TYPE"),
                "project_id": os.getenv("SERVICE_ACCOUNT_PROJECT_ID"),
                "private_key_id": os.getenv("SERVICE_ACCOUNT_PRIVATE_KEY_ID"),
                "private_key": os.getenv("SERVICE_ACCOUNT_PRIVATE_KEY").replace("\\n", "\n"),
                "client_email": os.getenv("SERVICE_ACCOUNT_CLIENT_EMAIL"),
                "client_id": os.getenv("SERVICE_ACCOUNT_CLIENT_ID"),
                "auth_uri": os.getenv("SERVICE_ACCOUNT_AUTH_URI"),
                "token_uri": os.getenv("SERVICE_ACCOUNT_TOKEN_URI"),
                "auth_provider_x509_cert_url": os.getenv("SERVICE_ACCOUNT_AUTH_PROVIDER_CERT_URL"),
                "client_x509_cert_url": os.getenv("SERVICE_ACCOUNT_CLIENT_CERT_URL"),
                "universe_domain": os.getenv("SERVICE_ACCOUNT_UNIVERSE_DOMAIN"),
            }
            self.DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
            self.WORKBOOK_FILENAME = os.getenv("WORKBOOK_FILENAME", "IFFK 2025")
            self.FILMS_LIST_SHEET = os.getenv("FILMS_LIST_SHEET", "Films")
            self.TALKS_SHEET = os.getenv("TALKS_AND_CONVESATIONS_SHEET", "Talks & Conversations")
            self.PROGRAMME_SELECTION_SHEET = os.getenv("PROGRAMME_SELECTION_SHEET", "Programme Selection")

            # Load resources
            self.CATEGORY_CODES = self._load_json(self.CATEGORY_CODES_FILE)
            self.COUNTRIES = sorted(self._load_json(self.COUNTRIES_FILE))
            self.LANGUAGES = sorted(self._load_json(self.LANGUAGES_FILE))

            logging.info("ProgrammeManager initialized successfully")

        except Exception as e:
            logging.exception(f"Failed during ProgrammeManager initialization: {e}")
            raise

    def _load_json(self, filename):
        try:
            full_path = os.path.join(self.RESOURCES_DIR, filename)
            with open(full_path, "r", encoding="utf-8") as f:
                logging.info(f"Loaded JSON file: {filename}")
                return json.load(f)
        except Exception:
            logging.exception(f"Error loading JSON: {filename}")
            raise

    def get_sheets_client(self):
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_info(
                self.SERVICE_ACCOUNT_INFO,
                scopes=scopes
            )

            client = gspread.authorize(creds)
            logging.info("Google Sheets client created successfully")
            return client

        except Exception:
            logging.exception("Failed to create Google Sheets client")
            raise

    def get_sheet(self, sheet_name):
        try:
            client = self.get_sheets_client()
            spreadsheet = client.open(self.WORKBOOK_FILENAME)
            sheet = spreadsheet.worksheet(sheet_name)

            logging.info(f"Accessed sheet: {sheet_name}")
            return sheet

        except Exception:
            logging.exception(f"Failed to access sheet: {sheet_name}")
            raise

    def generate_sl_no(self, sheet, category):
        try:
            data = sheet.get_all_records()
            same_category_rows = [row for row in data if row.get("CATEGORY") == category]
            sl_no = len(same_category_rows) + 1

            logging.info(f"Generated SL. No {sl_no} for category '{category}'")
            return sl_no

        except Exception:
            logging.exception("Failed to generate serial number")
            raise

    def generate_programme_id(self, category, sl_no):
        try:
            code = self.CATEGORY_CODES.get(category, "X")
            programme_id = f"{code}{str(sl_no).zfill(3)}"

            logging.info(f"Generated Programme ID: {programme_id} for category '{category}'")
            return programme_id

        except Exception:
            logging.exception("Failed to generate programme ID")
            raise

    def add_programme_entry(self, data):
        try:
            category = data["category"]

            sheet_name = (
                self.TALKS_SHEET
                if category == "Talks & Conversations"
                else self.FILMS_LIST_SHEET
            )

            sheet = self.get_sheet(sheet_name)
            sl_no = self.generate_sl_no(sheet, category)
            programme_id = self.generate_programme_id(category, sl_no)

            if category == "Talks & Conversations":
                row = [
                    category,
                    sl_no,
                    programme_id,
                    data["topic"],
                    data["duration"],
                    data["image_url"],
                ]
            else:
                row = [
                    category,
                    sl_no,
                    programme_id,
                    data["international_title"],
                    data["original_title"],
                    data["year"],
                    data["runtime"],
                    data["language"],
                    data["country"],
                    data["director"],
                    data["synopsis"],
                    data["image_url"],
                    data["letterboxd_url"],
                ]

            sheet.append_row(row)
            logging.info(f"New entry added: {programme_id}")

            return programme_id

        except Exception as e:
            logging.exception(f"Failed to add entry to sheet: {e}")
            raise

    def replace_sheet_data(self, sheet_name, df):
        try:
            sheet = self.get_sheet(sheet_name)

            # -------------------------
            # 1. Clear all rows except header
            # -------------------------
            # A2:ZZ chosen so it covers many columns safely
            sheet.batch_clear(["A2:Z1000"])
            logging.info(f"Cleared old rows except header in sheet: {sheet_name}")

            # -------------------------
            # 2. Append DataFrame rows
            # -------------------------
            if df.empty:
                logging.warning(f"DataFrame is empty. Nothing to append to sheet: {sheet_name}")
                return

            rows = df.astype(str).fillna("").values.tolist()
            sheet.append_rows(rows, value_input_option="USER_ENTERED")

            logging.info(f"Successfully appended {len(rows)} rows to sheet: {sheet_name}")

        except Exception:
            logging.exception(f"Failed to replace data in sheet: {sheet_name}")
            raise

