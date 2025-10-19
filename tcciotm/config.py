# ASCII only
import os
TELEGRAM_BOT_TOKEN = os.getenv("TCCIOTM_TG_TOKEN", "")
DEFAULT_CHAT_ID    = os.getenv("TCCIOTM_CHAT_ID", "")
STT_ENDPOINT_URL   = os.getenv("TCCIOTM_STT_URL", "")  # manter isto também no PC
TIMEOUT_S          = int(os.getenv("TCCIOTM_TIMEOUT", "15"))
def assert_tokens():
    if not TELEGRAM_BOT_TOKEN or not DEFAULT_CHAT_ID:
        raise RuntimeError("Set TCCIOTM_TG_TOKEN and TCCIOTM_CHAT_ID env vars.")