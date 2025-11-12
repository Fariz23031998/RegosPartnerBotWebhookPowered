import os
from dotenv import load_dotenv

from translations.translator_service import TranslatorService

load_dotenv()

APP_NAME = os.getenv('APP_NAME')
TEST_INTEGRATION_TOKEN = os.getenv('TEST_INTEGRATION_TOKEN')
TEST_FIRM_ID = os.getenv("TEST_FIRM_ID")

translator_service = TranslatorService()
