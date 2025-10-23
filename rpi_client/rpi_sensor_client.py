#!/usr/bin/env python3
# ASCII only
"""Sistema embarcado para Raspberry Pi — Captura térmica e áudio com envio remoto.

Este script controla dois botões físicos conectados ao Raspberry Pi:
- BTN_STT_LOC: Grava áudio e envia para o servidor de transcrição (STT) e localização.
- BTN_MEDIA_LOC: Captura imagem térmica, envia ao PC e solicita envio de imagem RGB e localização.

O código integra sensores térmicos (MLX90640), gravação de áudio (arecord),
requisições HTTP e comunicação via sockets com o servidor remoto.

Requer:
    - `adafruit_mlx90640` (sensor térmico)
    - `RPi.GPIO` (controle dos botões)
    - `requests`, `numpy`, `opencv-python`
"""

import os, time, json, socket, struct, requests, numpy as np, cv2
import RPi.GPIO as GPIO

# ===== CONFIG =====
BTN_STT_LOC   = 17
BTN_MEDIA_LOC = 27
DEBOUNCE = 0.35

AUDIO_DEVICE = "hw:2,0"  # seu mic (arecord -l)
STT_URL  = os.getenv("TCCIOTM_STT_URL", "http://<notebook>:5000/stt")    # PC
HUB_URL  = os.getenv("TCCIOTM_HUB_URL", "http://<notebook>:5050/event")  # PC
THERMAL_PC_HOST = os.getenv("THERMAL_PC_HOST", "<notebook>")  # PC thermal receiver
THERMAL_PC_PORT = int(os.getenv("THERMAL_PC_PORT", "9998"))
# ==================

def public_ip(timeout=6):
    """Obtém o IP público do Raspberry Pi.

    Args:
        timeout (int): Tempo limite da requisição (em segundos).

    Returns:
        str | None: IP público obtido via `api.ipify.org` ou None se falhar.
    """
    try:
        return requests.get("https://api.ipify.org?format=json", timeout=timeout).json().get("ip")
    except Exception:
        return None

def record_with_arecord(seconds, out_wav="/home/rpi3/stt.wav", rate=16000, channels=1, device=None):
    """Grava áudio utilizando o utilitário `arecord`.

    Args:
        seconds (int): Duração da gravação em segundos.
        out_wav (str): Caminho de saída do arquivo WAV.
        rate (int): Taxa de amostragem em Hz.
        channels (int): Número de canais de áudio.
        device (str, optional): Dispositivo ALSA (ex.: 'hw:2,0').

    Returns:
        str: Caminho do arquivo WAV gravado.
    """
    import subprocess
    cmd = ["arecord","-q","-d",str(seconds),"-r",str(rate),"-c",str(channels),"-f","S16_LE",out_wav]
    if device:
        cmd = ["arecord","-q","-D",device,"-d",str(seconds),"-r",str(rate),"-c",str(channels),"-f","S16_LE",out_wav]
    subprocess.check_call(cmd)
    return out_wav

def post_event(event_type, ip):
    """Envia evento JSON ao hub central.

    Args:
        event_type (str): Tipo do evento (ex.: 'STT_LOC' ou 'MEDIA_LOC').
        ip (str): IP público do Raspberry Pi.
    """
    try:
        r = requests.post(HUB_URL, json={"type": event_type, "ip": ip}, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print("Falha ao postar evento:", e)

def read_mlx_to_f32():
    """Lê uma imagem térmica do sensor MLX90640 e retorna como matriz float32.

    Returns:
        numpy.ndarray: Matriz 24x32 (float32) redimensionada para (160x120).
    Raises:
        RuntimeError: Se a leitura do sensor falhar repetidamente.
    """
    import board, busio, adafruit_mlx90640
    i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_8_HZ
    frame = [0]*768
    for _ in range(5):
        try:
            mlx.getFrame(frame)
            arr = np.array(frame, dtype=np.float32).reshape(24,32)
            up = cv2.resize(arr, (160,120), interpolation=cv2.INTER_CUBIC)
            return up
        except Exception:
            time.sleep(0.02)
    raise RuntimeError("MLX getFrame failed repeatedly")

def thermal_to_u8(img_f32):
    """Normaliza uma imagem térmica float32 para escala de cinza 8 bits (0–255).

    Args:
        img_f32 (numpy.ndarray): Imagem térmica em float32.

    Returns:
        numpy.ndarray: Imagem térmica em escala de cinza (uint8).
    """
    lo = np.percentile(img_f32, 5.0); hi = np.percentile(img_f32, 95.0)
    if hi - lo < 0.5: lo, hi = lo - 0.25, hi + 0.25
    return np.clip((img_f32 - lo) * (255.0 / max(1e-6, hi - lo)), 0, 255).astype(np.uint8)

def send_thermal_to_pc(host, port):
    """Envia um frame térmico (JPEG) ao PC via socket TCP.

    Args:
        host (str): Endereço do servidor de destino.
        port (int): Porta TCP do servidor receptor.
    """
    g = thermal_to_u8(read_mlx_to_f32())
    ok, enc = cv2.imencode(".jpg", g, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok: raise RuntimeError("JPEG encode failed (thermal)")
    data = enc.tobytes()
    pkt = struct.pack("!I", len(data)) + data
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.sendall(pkt)
    s.close()

def handle_btn_stt(ip):
    """Trata o evento do botão STT_LOC: grava áudio e envia localização.

    Args:
        ip (str): IP público do Raspberry Pi.
    """
    wav = record_with_arecord(5, out_wav="/home/rpi3/stt.wav", device=AUDIO_DEVICE)
    with open(wav, "rb") as f:
        r = requests.post(STT_URL, files={"audio":("speech.wav", f, "audio/wav")}, timeout=60)
        r.raise_for_status()
    post_event("STT_LOC", ip)

def handle_btn_media(ip):
    """Trata o evento do botão MEDIA_LOC: envia imagem térmica e localização.

    Args:
        ip (str): IP público do Raspberry Pi.
    """
    try:
        send_thermal_to_pc(THERMAL_PC_HOST, THERMAL_PC_PORT)
    except Exception as e:
        print("Falha termal:", e)
    post_event("MEDIA_LOC", ip)

def main():
    """Função principal — Inicializa GPIOs e escuta eventos dos botões."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BTN_STT_LOC, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BTN_MEDIA_LOC, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print("Sensor RPi pronto. 17=STT+loc | 27=fotos+loc (via notebook).")

    my_ip = public_ip()
    last17 = last27 = 0.0
    try:
        while True:
            now = time.time()
            if GPIO.input(BTN_STT_LOC) == 0 and (now-last17)>DEBOUNCE:
                handle_btn_stt(my_ip)
                last17 = now
            if GPIO.input(BTN_MEDIA_LOC) == 0 and (now-last27)>DEBOUNCE:
                handle_btn_media(my_ip)
                last27 = now
            time.sleep(0.03)
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    """Ponto de entrada do script.

    Executa a função principal, configurando o sistema embarcado para captura e envio de dados.
    """
    main()
