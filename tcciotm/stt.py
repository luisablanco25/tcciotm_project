# ASCII only
import subprocess, requests
from . import config
from .telegram_utils import send_message

def record_with_arecord(seconds, out_wav="rec.wav", rate=16000, channels=1, device=None):
    """
    Grava áudio usando o utilitário ALSA 'arecord' no Raspberry Pi ou Linux.

    Observações:
        - Requer instalação do pacote alsa-utils: sudo apt-get install -y alsa-utils
        - Suporta gravação em WAV, taxa de amostragem, número de canais e dispositivo específico.

    Parâmetros:
        seconds (int): Duração da gravação em segundos.
        out_wav (str): Caminho do arquivo WAV de saída. Padrão: "rec.wav".
        rate (int): Taxa de amostragem em Hz. Padrão: 16000.
        channels (int): Número de canais (1=mono, 2=stereo). Padrão: 1.
        device (str, opcional): Nome do dispositivo de gravação ALSA. Se None, usa o padrão.

    Retorno:
        str: Caminho do arquivo WAV gerado.
    """
    # monta comando padrão do arecord
    cmd = ["arecord", "-q", "-d", str(seconds), "-r", str(rate), "-c", str(channels),
           "-f", "S16_LE", out_wav]
    # se um dispositivo específico for informado, ajusta o comando
    if device:
        cmd = ["arecord", "-q", "-D", device, "-d", str(seconds), "-r", str(rate),
               "-c", str(channels), "-f", "S16_LE", out_wav]
    subprocess.check_call(cmd)
    return out_wav

def send_stt_from_wav(wav_path, chat_id=None, stt_url=None):
    """
    Envia um arquivo WAV para um serviço de STT (Speech-to-Text) e envia o resultado via Telegram.

    Etapas:
    1. Define a URL do serviço STT a partir do argumento stt_url, da configuração config.STT_ENDPOINT_URL
       ou padrão local "http://127.0.0.1:5000/stt".
    2. Abre o arquivo WAV e envia via HTTP POST como multipart/form-data.
    3. Aguarda a resposta do serviço STT e levanta erro se falhar.
    4. Extrai o texto reconhecido do JSON retornado.
    5. Se houver texto, envia mensagem "STT: <texto>" via Telegram. 
       Caso contrário, envia aviso de STT vazio ou não reconhecido.
    
    Parâmetros:
        wav_path (str): Caminho do arquivo WAV a ser enviado.
        chat_id (opcional): ID do chat para envio da mensagem via Telegram.
        stt_url (opcional): URL do serviço STT. Se None, usa configuração ou padrão local.

    Retorno:
        str: Texto reconhecido pelo STT. Pode ser vazio se não houver reconhecimento.
    """
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
