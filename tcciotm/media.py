# ASCII only
# tcciotm/media.py
import time, requests, numpy as np, cv2
from .telegram_utils import send_photo

def send_photo_path(path, caption=None, chat_id=None):
    return send_photo(path, caption, chat_id)

def send_numpy_frame(frame_bgr, caption=None, chat_id=None, jpeg_quality=85):
    ok, enc = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)])
    if not ok:
        raise RuntimeError("JPEG encode failed")
    return send_photo(enc.tobytes(), caption, chat_id)

# ---------- helpers para pegar frame do celular ----------
def _grab_frame_mjpeg(url, warmup=8, timeout_s=8):
    cap = cv2.VideoCapture(url)
    t0 = time.time()
    for _ in range(max(1, warmup)):
        ok, frame = cap.read()
        if ok:
            cap.release()
            return frame
        if time.time() - t0 > timeout_s:
            break
        time.sleep(0.05)
    cap.release()
    return None

def _grab_frame_snapshot(url, timeout_s=8):
    r = requests.get(url, timeout=timeout_s)
    r.raise_for_status()
    arr = np.frombuffer(r.content, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)  # BGR
    return img

def send_phone_rgb(base_url, caption="RGB do celular", chat_id=None):
    """
    base_url ex.: 'http://192.168.0.221:8080'
    Tenta primeiro /video (MJPEG); se falhar, usa /shot.jpg
    """
    base = base_url.rstrip("/")
    url_mjpeg = base + "/video"
    url_shot  = base + "/shot.jpg"

    frame = _grab_frame_mjpeg(url_mjpeg)
    if frame is None:
        try:
            frame = _grab_frame_snapshot(url_shot)
        except Exception:
            frame = None
    if frame is None:
        raise RuntimeError("Falha ao capturar RGB do celular")
    return send_numpy_frame(frame, caption=caption, chat_id=chat_id)

# ---------- termal: normalizacao P/B ----------
def thermal_to_u8(img_f32):
    lo = np.percentile(img_f32, 5.0)
    hi = np.percentile(img_f32, 95.0)
    if hi - lo < 0.5:
        lo, hi = lo - 0.25, hi + 0.25
    g = np.clip((img_f32 - lo) * (255.0 / max(1e-6, hi - lo)), 0, 255).astype(np.uint8)
    return g

def send_thermal_u8(thermal_u8, caption=None, chat_id=None, jpeg_quality=85):
    if thermal_u8.ndim != 2:
        raise ValueError("thermal_u8 must be 2D (grayscale).")
    ok, enc = cv2.imencode(".jpg", thermal_u8, [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)])
    if not ok:
        raise RuntimeError("JPEG encode failed (thermal)")
    return send_photo(enc.tobytes(), caption, chat_id)