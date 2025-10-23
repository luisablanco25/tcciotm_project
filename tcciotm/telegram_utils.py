# ASCII only
import requests
from . import config

def _base():
    """
    Retorna a URL base da API do Telegram usando o token do bot configurado.

    Etapas:
    1. Verifica se os tokens necessários estão configurados chamando config.assert_tokens().
    2. Constrói a URL base para chamadas à API do Telegram no formato:
       "https://api.telegram.org/bot<TOKEN>/"

    Retorno:
        str: URL base da API do Telegram.
    """
    config.assert_tokens()
    return "https://api.telegram.org/bot{}/".format(config.TELEGRAM_BOT_TOKEN)

def send_message(text, chat_id=None):
    """
    Envia uma mensagem de texto para um chat do Telegram.

    Parâmetros:
        text (str): Texto da mensagem a ser enviada.
        chat_id (opcional): ID do chat para envio. Se None, usa config.DEFAULT_CHAT_ID.

    Retorno:
        dict: Resposta JSON da API do Telegram.
    """
    url = _base() + "sendMessage"
    cid = chat_id or config.DEFAULT_CHAT_ID
    r = requests.post(url, data={"chat_id": cid, "text": text}, timeout=config.TIMEOUT_S)
    r.raise_for_status()
    return r.json()

def send_location(lat, lon, chat_id=None):
    """
    Envia a localização geográfica para um chat do Telegram.

    Parâmetros:
        lat (float): Latitude da localização.
        lon (float): Longitude da localização.
        chat_id (opcional): ID do chat para envio. Se None, usa config.DEFAULT_CHAT_ID.

    Retorno:
        dict: Resposta JSON da API do Telegram.
    """
    url = _base() + "sendLocation"
    cid = chat_id or config.DEFAULT_CHAT_ID
    r = requests.post(url, data={"chat_id": cid, "latitude": lat, "longitude": lon},
                      timeout=config.TIMEOUT_S)
    r.raise_for_status()
    return r.json()

def send_photo(path_or_bytes, caption=None, chat_id=None):
    """
    Envia uma foto para um chat do Telegram.

    Parâmetros:
        path_or_bytes (str ou bytes): Caminho para o arquivo de imagem ou dados em bytes.
        caption (str, opcional): Legenda da imagem.
        chat_id (opcional): ID do chat para envio. Se None, usa config.DEFAULT_CHAT_ID.

    Retorno:
        dict: Resposta JSON da API do Telegram.
    """
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
