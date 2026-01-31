from pathlib import Path
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Logging setup
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")

# OpenRouter LLM
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not set in environment")

LLM_MODEL_PRIMARY = os.getenv("LLM_MODEL_PRIMARY", "deepseek/deepseek-chat")
LLM_MODEL_FALLBACK = os.getenv("LLM_MODEL_FALLBACK", "anthropic/claude-3.5-sonnet")

# Google Calendar
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

# ntfy.sh
NTFY_URL = os.getenv("NTFY_URL", "https://ntfy.sh")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "productivity")

# Paths
BASE_DIR = Path(__file__).parent.parent
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR.parent / "data" / "productivity.db"))
VAULT_PATH = os.getenv("VAULT_PATH", str(BASE_DIR.parent / "obsidian-vault"))

# Timezone
TIMEZONE = os.getenv("TIMEZONE", "America/New_York")

# Bot Settings
SESSION_TIMEOUT_MINUTES = 30
MAX_CONVERSATION_MESSAGES = 5
