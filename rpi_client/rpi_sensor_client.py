#!/usr/bin/env python3
# ASCII only
# ----------------------------------------------------------
# Sistema embarcado em Raspberry Pi para capturar áudio e imagens térmicas,
# enviando dados a um servidor remoto via HTTP e sockets.
# Possui dois botões físicos: um para gravação de áudio/STT e outro para captura térmica.
# ----------------------------------------------------------

import os, time, json, socket, struct, requests, numpy as np, cv2
import RPi.GPIO as GPIO

# ===== CONFIG =====
# Pinos GPIO dos botões físicos
BTN_STT_LOC   = 17   # Botão 1: aciona gravação de áudio + localização
BTN_MEDIA_LOC = 27   # Botão 2: aciona captura térmica + localização

DEBOUNCE = 0.35      # Tempo mínimo entre cliques (em segundos) para evitar ruído

# Dispositivo de áudio e URLs de comunicação com o PC/notebook
AUDIO_DEVICE = "hw:2,0"  # Endereço ALSA do microfone (ver com 'arecord -l')
STT_URL  = os.getenv("TCCIOTM_STT_URL", "http://<notebook>:5000/stt")    # Endpoint de reconhecimento de fala
HUB_URL  = os.getenv("TCCIOTM_HUB_URL", "http://<notebook>:5050/event")  # Endpoint do hub central de eventos
THERMAL_PC_HOST = os.getenv("THERMAL_PC_HOST", "<notebook>")  # Host do receptor térmico
THERMAL_PC_PORT = int(os.getenv("THERMAL_PC_PORT", "9998"))   # Porta do receptor térmico
# ==================

# ----------------------------------------------------------
# Obtém o IP público do Raspberry Pi (para envio ao servidor)
# ----------------------------------------------------------
def public_ip(timeout=6):
    try:
        return requests.get("https://api.ipify.org?format=json", timeout=timeout).json().get("ip")
    except Exception:
        return None

# ----------------------------------------------------------
# Grava áudio usando 'arecord' e salva em WAV
# ----------------------------------------------------------
def record_with_arecord(seconds, out_wav="/home/rpi3/stt.wav", rate=16000, channels=1, device=None):
    import subprocess
    cmd = ["arecord","-q","-d",str(seconds),"-r",str(rate),"-c",str(channels),"-f","S16_LE",out_wav]
    if device:
        cmd = ["arecord","-q","-D",device,"-d",str(seconds),"-r",str(rate),"-c",str(channels),"-f","S16_LE",out_wav]
    subprocess.check_call(cmd)
    return out_wav

# ----------------------------------------------------------
# Envia um evento (JSON) ao servidor HUB com o tipo e IP
# ----------------------------------------------------------
def post_event(event_type, ip):
    try:
        r = requests.post(HUB_URL, json={"type": event_type, "ip": ip}, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print("Falha ao postar evento:", e)

# === MLX -> envia 1 frame JPEG ao PC (receiver) ===
# ----------------------------------------------------------
# Lê um frame do sensor térmico MLX90640 e retorna como matriz float32
# ----------------------------------------------------------
def read_mlx_to_f32():
    import board, busio, adafruit_mlx90640
    i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)  # Comunicação I2C
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_8_HZ
    frame = [0]*768  # Sensor tem 24x32 pixels (768 pontos)
    for _ in range(5):  # Tenta até 5 vezes obter frame válido
        try:
            mlx.getFrame(frame)
            arr = np.array(frame, dtype=np.float32).reshape(24,32)
            up = cv2.resize(arr, (160,120), interpolation=cv2.INTER_CUBIC)  # Redimensiona imagem
            return up
        except Exception:
            time.sleep(0.02)
    raise RuntimeError("MLX getFrame failed repeatedly")

# ----------------------------------------------------------
# Normaliza imagem térmica (float32) para 8 bits (0–255)
# ----------------------------------------------------------
def thermal_to_u8(img_f32):
    lo = np.percentile(img_f32, 5.0); hi = np.percentile(img_f32, 95.0)
    if hi - lo < 0.5: lo, hi = lo - 0.25, hi + 0.25
    return np.clip((img_f32 - lo) * (255.0 / max(1e-6, hi - lo)), 0, 255).astype(np.uint8)

# ----------------------------------------------------------
# Envia frame térmico (JPEG) via socket TCP ao PC receptor
# ----------------------------------------------------------
def send_thermal_to_pc(host, port):
    g = thermal_to_u8(read_mlx_to_f32())
    ok, enc = cv2.imencode(".jpg", g, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok: raise RuntimeError("JPEG encode failed (thermal)")
    data = enc.tobytes()
    pkt = struct.pack("!I", len(data)) + data  # Cabeçalho: tamanho do frame (4 bytes)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.sendall(pkt)
    s.close()

# ----------------------------------------------------------
# Manipula o botão de gravação de áudio e envio ao STT
# ----------------------------------------------------------
def handle_btn_stt(ip):
    # grava audio e manda ao STT (PC)
    wav = record_with_arecord(5, out_wav="/home/rpi3/stt.wav", device=AUDIO_DEVICE)
    with open(wav, "rb") as f:
        r = requests.post(STT_URL, files={"audio":("speech.wav", f, "audio/wav")}, timeout=60)
        r.raise_for_status()
    # avisa o hub para enviar localizacao (geo do RPi usando ip informado)
    post_event("STT_LOC", ip)

# ----------------------------------------------------------
# Manipula o botão de captura térmica e envio ao servidor
# ----------------------------------------------------------
def handle_btn_media(ip):
    # envia 1 frame termal ao PC (que manda ao Telegram)
    try:
        send_thermal_to_pc(THERMAL_PC_HOST, THERMAL_PC_PORT)
    except Exception as e:
        print("Falha termal:", e)
    # avisa o hub para capturar RGB do celular no PC + enviar geo do RPi
    post_event("MEDIA_LOC", ip)

# ----------------------------------------------------------
# Função principal: inicializa GPIO e monitora botões
# ----------------------------------------------------------
def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BTN_STT_LOC, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BTN_MEDIA_LOC, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print("Sensor RPi pronto. 17=STT+loc | 27=fotos+loc (via notebook).")

    my_ip = public_ip()
    last17 = last27 = 0.0
    try:
        while True:
            now = time.time()
            # Botão 17 -> grava áudio + envia localização
            if GPIO.input(BTN_STT_LOC) == 0 and (now-last17)>DEBOUNCE:
                handle_btn_stt(my_ip)
                last17 = now
            # Botão 27 -> captura térmica + envia localização
            if GPIO.input(BTN_MEDIA_LOC) == 0 and (now-last27)>DEBOUNCE:
                handle_btn_media(my_ip)
                last27 = now
            time.sleep(0.03)
    finally:
        GPIO.cleanup()  # Garante liberação dos pinos GPIO ao encerrar

# ----------------------------------------------------------
# Execução direta do script
# ----------------------------------------------------------
if __name__ == "__main__":
    main()
