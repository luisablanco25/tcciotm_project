# ASCII only
import subprocess, requests
from . import config
from .telegram_utils import send_message

def record_with_arecord(seconds, out_wav="rec.wav", rate=16000, channels=1, device=None):
    # requer: sudo apt-get install -y alsa-utils (no RPi)
    cmd = ["arecord", "-q", "-d", str(seconds), "-r", str(rate), "-c", str(channels),
           "-f", "S16_LE", out_wav]
    if device:
        cmd = ["arecord", "-q", "-D", device, "-d", str(seconds), "-r", str(rate),
               "-c", str(channels), "-f", "S16_LE", out_wav]
    subprocess.check_call(cmd)
    return out_wav

def send_stt_from_wav(wav_path, chat_id=None, stt_url=None):
    url = stt_url or config.STT_ENDPOINT_URL or "http://127.0.0.1:5000/stt"
    with open(wav_path, "rb") as f:
        files = {"audio": ("speech.wav", f, "audio/wav")}
        r = requests.post(url, files=files, timeout=max(30, config.TIMEOUT_S))
    r.raise_for_status()
    text = r.json().get("text", "").strip()
    if text:
        send_message("STT: " + text, chat_id)
    else:
        send_message("STT vazio ou nao reconhecido.", chat_id)
    return text