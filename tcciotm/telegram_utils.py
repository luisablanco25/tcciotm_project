# ASCII only
import requests
from . import config

def _base():
    config.assert_tokens()
    return "https://api.telegram.org/bot{}/".format(config.TELEGRAM_BOT_TOKEN)

def send_message(text, chat_id=None):
    url = _base() + "sendMessage"
    cid = chat_id or config.DEFAULT_CHAT_ID
    r = requests.post(url, data={"chat_id": cid, "text": text}, timeout=config.TIMEOUT_S)
    r.raise_for_status()
    return r.json()

def send_location(lat, lon, chat_id=None):
    url = _base() + "sendLocation"
    cid = chat_id or config.DEFAULT_CHAT_ID
    r = requests.post(url, data={"chat_id": cid, "latitude": lat, "longitude": lon},
                      timeout=config.TIMEOUT_S)
    r.raise_for_status()
    return r.json()

def send_photo(path_or_bytes, caption=None, chat_id=None):
    url = _base() + "sendPhoto"
    cid = chat_id or config.DEFAULT_CHAT_ID
    data = {"chat_id": cid}
    if caption:
        data["caption"] = caption
    if isinstance(path_or_bytes, (bytes, bytearray)):
        files = {"photo": ("image.jpg", path_or_bytes, "image/jpeg")}
    else:
        files = {"photo": open(path_or_bytes, "rb")}
    r = requests.post(url, data=data, files=files, timeout=config.TIMEOUT_S)
    r.raise_for_status()
    return r.json()