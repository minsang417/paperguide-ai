import os
from dotenv import load_dotenv

load_dotenv()

SENDER_APP_PASSWORD = os.getenv(
    "SENDER_APP_PASSWORD"
)

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)

FEEDBACK_SECRET_KEY = os.getenv(
    "FEEDBACK_SECRET_KEY"
)

FEEDBACK_SERVER_URL = os.getenv(
    "FEEDBACK_SERVER_URL"
)

EXTRACTOR_MODE = "rule"   # "rule" or "ai"
USE_REAL_AI = True
SHOW_MOCK_COMPARISON = True
ENABLE_FEEDBACK = False
MAX_PAPERS_TO_PROCESS = 100
ENABLE_AI_IMPORTANCE = False
ENABLE_AI_NORMALIZATION = False
ENABLE_INSIGHT_GENERATION = True  # 추천된 것만
ENABLE_EMAIL_SENDING = True

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = "paperguide.ai@gmail.com"
SENDER_NAME = "PaperGuide AI"