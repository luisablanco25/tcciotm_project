# ASCII only
import requests
from . import config
from .telegram_utils import send_message, send_location

def get_public_ip():
    r = requests.get("https://api.ipify.org?format=json", timeout=config.TIMEOUT_S)
    r.raise_for_status()
    return r.json().get("ip")

def ip_geo_lookup(ip=None):
    """
    Retorna um dict com lat/lon/city/region/country baseado no IP publico.
    Usa ip-api (gratuito). Para SLA/privacidade, use um provedor pago depois.
    """
    ip = ip or get_public_ip()
    r = requests.get(f"http://ip-api.com/json/{ip}", timeout=config.TIMEOUT_S)
    r.raise_for_status()
    j = r.json()
    return {
        "ip": ip,
        "lat": j.get("lat"),
        "lon": j.get("lon"),
        "city": j.get("city"),
        "region": j.get("regionName"),
        "country": j.get("country"),
        "isp": j.get("isp"),
        "tz": j.get("timezone"),
        "status": j.get("status"),
    }

def send_current_location(extra_text=None, chat_id=None):
    """
    Envia mensagem opcional + pino de localizacao no Telegram.
    """
    info = ip_geo_lookup()
    if extra_text:
        send_message(extra_text, chat_id)
    lat, lon = info.get("lat"), info.get("lon")
    if lat is None or lon is None:
        return send_message("Geo por IP indisponivel.", chat_id)
    return send_location(lat, lon, chat_id)