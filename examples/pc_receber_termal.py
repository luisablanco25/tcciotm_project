# ASCII only
# examples/pc_receber_termal.py
# Recebe 1 frame termico (JPEG) via socket (porta 9998) e roda YOLOv8 termal.
# Envia apenas a imagem ANOTADA + resumo textual.
import os, socket, struct
import numpy as np, cv2
from ultralytics import YOLO
from tcciotm import send_message
from tcciotm.media import send_numpy_frame

HOST = os.getenv("THERMAL_BIND_HOST", "0.0.0.0")
PORT = int(os.getenv("THERMAL_BIND_PORT", "9998"))

# === CONFIG YOLO TERMICO ===
YOLO_MODEL = os.getenv("TCCIOTM_YOLO_THERMAL_MODEL", "models/thermal/best.pt")
CONF_TH = float(os.getenv("TCCIOTM_YOLO_CONF", "0.35"))
USE_CLAHE = os.getenv("TCCIOTM_THERMAL_CLAHE", "1") == "1"
UPSCALE_W = int(os.getenv("TCCIOTM_THERMAL_UPSCALE_W", "640"))
UPSCALE_H = int(os.getenv("TCCIOTM_THERMAL_UPSCALE_H", "480"))

# Carrega modelo YOLO (custom termal)
_model = YOLO(YOLO_MODEL)

def _summarize(result0):
    """
    Gera um resumo textual das detecções do YOLOv8 térmico.

    Analisa as caixas detectadas e retorna uma string descrevendo os
    objetos encontrados, juntamente com suas quantidades.

    Args:
        result0 (ultralytics.engine.results.Results): Resultado de inferência do YOLO.

    Returns:
        str: Texto resumindo as detecções ou informando ausência de objetos.
    """
    names = result0.names
    counts = {}
    for b in result0.boxes:
        cls = int(b.cls[0].item())
        conf = float(b.conf[0].item())
        if conf < CONF_TH:
            continue
        label = names.get(cls, str(cls))
        counts[label] = counts.get(label, 0) + 1
    if not counts:
        return "YOLO térmico: nenhum objeto detectado."
    parts = [f"{k} x{v}" for k, v in counts.items()]
    return "YOLO térmico: " + ", ".join(parts)


def _enhance_gray(gray):
    """
    Aplica aprimoramento de contraste em imagem térmica em escala de cinza.

    Utiliza o método CLAHE (Contrast Limited Adaptive Histogram Equalization)
    quando habilitado via variável de ambiente.

    Args:
        gray (numpy.ndarray): Imagem térmica em tons de cinza (uint8).

    Returns:
        numpy.ndarray: Imagem aprimorada (ou original se CLAHE desativado).
    """
    if not USE_CLAHE:
        return gray
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    return clahe.apply(gray)


def _handle_jpeg(jpg_bytes):
    """
    Decodifica e processa um frame térmico JPEG recebido via socket.

    - Decodifica o JPEG em escala de cinza;
    - Aplica aprimoramento de contraste e redimensionamento;
    - Converte para BGR (3 canais) e roda inferência YOLOv8;
    - Envia a imagem anotada e um resumo textual.

    Args:
        jpg_bytes (bytes): Conteúdo binário do frame JPEG recebido.

    Raises:
        RuntimeError: Caso a decodificação do JPEG falhe.
    """
    arr = np.frombuffer(jpg_bytes, dtype=np.uint8)
    gray = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise RuntimeError("Falha ao decodificar frame termico (JPG).")

    # melhora contraste + upscaling
    proc = _enhance_gray(gray)
    if UPSCALE_W > 0 and UPSCALE_H > 0:
        proc = cv2.resize(proc, (UPSCALE_W, UPSCALE_H), interpolation=cv2.INTER_CUBIC)

    # YOLO espera 3 canais
    bgr = cv2.cvtColor(proc, cv2.COLOR_GRAY2BGR)

    # roda YOLO
    results = _model.predict(source=bgr, conf=CONF_TH, device="cpu", verbose=False)
    r0 = results[0]
    annotated = r0.plot()

    # envia apenas a imagem anotada + resumo
    try:
        send_numpy_frame(annotated, caption=f"YOLO térmica (conf>={CONF_TH})")
        send_message(_summarize(r0))
    except Exception as e:
        send_message(f"Receiver termal: falha ao enviar anotada ({e})")


def _recv_all(sock, n):
    """
    Lê exatamente `n` bytes de um socket TCP, bloqueando até receber tudo.

    Args:
        sock (socket.socket): Socket TCP ativo.
        n (int): Número de bytes esperados.

    Returns:
        bytes: Dados recebidos.

    Raises:
        ConnectionError: Caso a conexão seja encerrada antes do recebimento completo.
    """
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Conexao encerrada inesperadamente")
        buf.extend(chunk)
    return bytes(buf)


def serve():
    """
    Inicia o servidor TCP que recebe frames térmicos e executa YOLOv8.

    - Aguarda conexões na porta configurada (padrão 9998);
    - Recebe frames JPEG e processa cada um com `_handle_jpeg()`;
    - Envia mensagens de status via `tcciotm.send_message()`.

    O servidor roda continuamente até ser interrompido.
    """
    send_message(f"Receiver termal ativo na porta {PORT} (YOLOv8 térmico)")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)
    try:
        while True:
            conn, addr = s.accept()
            with conn:
                hdr = _recv_all(conn, 4)
                (length,) = struct.unpack("!I", hdr)
                data = _recv_all(conn, length)
                _handle_jpeg(data)
    finally:
        s.close()


if __name__ == "__main__":
    """
    Ponto de entrada principal do script.

    Quando executado diretamente, inicia o servidor térmico YOLOv8.
    """
    serve()
