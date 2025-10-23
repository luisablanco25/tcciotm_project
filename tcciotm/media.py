"""
Módulo de mídia para captura e envio de imagens via Telegram.

Fornece funções para:
- Envio de fotos a partir de arquivos ou matrizes NumPy.
- Captura de frames de dispositivos móveis via MJPEG ou snapshots.
- Normalização e envio de imagens térmicas (grayscale) convertidas para uint8.

Dependências:
    - cv2: OpenCV, para manipulação e codificação de imagens.
    - numpy: para operações numéricas e conversão de imagens.
    - requests: para captura de snapshots via HTTP.
    - telegram_utils: para envio de fotos ao Telegram.

Funções principais:
    send_photo_path(path, caption=None, chat_id=None):
        Envia uma imagem a partir de um arquivo.

    send_numpy_frame(frame_bgr, caption=None, chat_id=None, jpeg_quality=85):
        Envia uma imagem a partir de uma matriz NumPy BGR.

    send_phone_rgb(base_url, caption="RGB do celular", chat_id=None):
        Captura um frame RGB do celular (via MJPEG ou snapshot) e envia.

    thermal_to_u8(img_f32):
        Normaliza imagem térmica float32 para uint8 (0-255) para visualização.

    send_thermal_u8(thermal_u8, caption=None, chat_id=None, jpeg_quality=85):
        Envia imagem térmica em grayscale (uint8) ao Telegram.

Funções auxiliares (não exportadas):
    _grab_frame_mjpeg(url, warmup=8, timeout_s=8):
        Captura frame de fluxo MJPEG com tentativa de warmup.

    _grab_frame_snapshot(url, timeout_s=8):
        Captura frame único de snapshot HTTP (JPEG).

Exemplo:
    >>> from tcciotm.media import send_phone_rgb
    >>> send_phone_rgb("http://192.168.0.221:8080", caption="Camera do celular")
"""

# ASCII only
import time, requests, numpy as np, cv2
from .telegram_utils import send_photo

def send_photo_path(path, caption=None, chat_id=None):
    """Envia uma imagem ao Telegram a partir de um arquivo local."""
    return send_photo(path, caption, chat_id)

def send_numpy_frame(frame_bgr, caption=None, chat_id=None, jpeg_quality=85):
    """Envia uma imagem ao Telegram a partir de uma matriz NumPy (BGR)."""
    ok, enc = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)])
    if not ok:
        raise RuntimeError("JPEG encode failed")
    return send_photo(enc.tobytes(), caption, chat_id)

# ---------- helpers para pegar frame do celular ----------
def _grab_frame_mjpeg(url, warmup=8, timeout_s=8):
    """
    Captura um frame de um stream MJPEG.
    
    Tenta capturar 'warmup' frames antes de retornar o primeiro frame válido.
    Retorna None se falhar após timeout.
    """
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
    """Captura um frame único via HTTP GET (snapshot JPEG) e retorna como matriz BGR."""
    r = requests.get(url, timeout=timeout_s)
    r.raise_for_status()
    arr = np.frombuffer(r.content, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)  # BGR
    return img

def send_phone_rgb(base_url, caption="RGB do celular", chat_id=None):
    """
    Captura e envia um frame RGB do celular via Telegram.

    Parâmetros:
        base_url (str): URL base do servidor de câmera do celular (ex.: http://192.168.0.221:8080).
        caption (str, opcional): Legenda a ser enviada junto com a imagem.
        chat_id (str, opcional): ID do chat para envio. Se None, usa o padrão configurado.
    
    Estratégia:
        Tenta capturar via MJPEG (/video). Se falhar, tenta snapshot JPEG (/shot.jpg).
    
    Levanta:
        RuntimeError se não conseguir capturar nenhuma imagem.
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
    """
    Normaliza uma imagem térmica float32 para uint8 (0-255).

    Usa percentis 5 e 95 para ajustar contraste e evita divisão por zero.
    Retorna uma matriz 2D uint8 (grayscale).
    """
    lo = np.percentile(img_f32, 5.0)
    hi = np.percentile(img_f32, 95.0)
    if hi - lo < 0.5:
        lo, hi = lo - 0.25, hi + 0.25
    g = np.clip((img_f32 - lo) * (255.0 / max(1e-6, hi - lo)), 0, 255).astype(np.uint8)
    return g

def send_thermal_u8(thermal_u8, caption=None, chat_id=None, jpeg_quality=85):
    """
    Envia uma imagem térmica (grayscale uint8) ao Telegram.

    Parâmetros:
        thermal_u8 (np.ndarray): Imagem 2D (grayscale) uint8.
        caption (str, opcional): Legenda da imagem.
        chat_id (str, opcional): ID do chat para envio.
        jpeg_quality (int, opcional): Qualidade JPEG (0-100).
    
    Levanta:
        ValueError se a imagem não for 2D.
        RuntimeError se a codificação JPEG falhar.
    """
    if thermal_u8.ndim != 2:
        raise ValueError("thermal_u8 must be 2D (grayscale).")
    ok, enc = cv2.imencode(".jpg", thermal_u8, [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)])
    if not ok:
        raise RuntimeError("JPEG encode failed (thermal)")
    return send_photo(enc.tobytes(), caption, chat_id)
