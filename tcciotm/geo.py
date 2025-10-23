"""
Módulo de geolocalização e comunicação via Telegram.

Fornece funções para:
- Obter o endereço IP público do dispositivo.
- Consultar informações geográficas (latitude, longitude, cidade, país etc.) com base no IP.
- Enviar a localização geográfica atual e mensagens complementares via Telegram.

Dependências:
    - requests: para chamadas HTTP às APIs externas.
    - telegram_utils: para envio de mensagens e localizações no Telegram.
    - config: para configuração de timeout e variáveis de ambiente.

Funções:
    get_public_ip():
        Obtém o IP público do dispositivo através da API ipify.org.
    
    ip_geo_lookup(ip=None):
        Realiza uma consulta de geolocalização via API gratuita ip-api.com.
        Retorna um dicionário com informações como latitude, longitude, cidade, país, etc.
    
    send_current_location(extra_text=None, chat_id=None):
        Envia opcionalmente uma mensagem e um pino de localização via Telegram,
        com base na localização inferida pelo IP público.

Exemplo:
    >>> from tcciotm.geo import send_current_location
    >>> send_current_location("Localização atual do dispositivo")
    
Notas:
    - Para uso em produção, recomenda-se substituir o provedor gratuito ip-api.com
      por uma API de geolocalização paga, com SLA e privacidade garantidos.
    - O envio de mensagens e localizações depende da configuração correta
      das variáveis de ambiente no módulo `config`.
"""

# ASCII only
import requests
from . import config
from .telegram_utils import send_message, send_location

def get_public_ip():
    """Obtém o IP público do dispositivo usando a API 'ipify.org'."""
    r = requests.get("https://api.ipify.org?format=json", timeout=config.TIMEOUT_S)
    r.raise_for_status()
    return r.json().get("ip")

def ip_geo_lookup(ip=None):
    """
    Retorna um dicionário com informações geográficas baseadas no IP público.

    Parâmetros:
        ip (str, opcional): Endereço IP a consultar. Se None, usa o IP público atual.

    Retorna:
        dict: Informações de geolocalização, incluindo:
              - ip: IP consultado
              - lat: latitude
              - lon: longitude
              - city: cidade
              - region: estado/região
              - country: país
              - isp: provedor de internet
              - tz: fuso horário
              - status: status da consulta

    Observação:
        Usa a API gratuita "ip-api.com". Para maior confiabilidade e privacidade,
        recomenda-se usar um serviço pago em produção.
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
    Envia uma mensagem opcional e a localização atual no Telegram.

    Parâmetros:
        extra_text (str, opcional): Texto adicional a ser enviado antes do pino de localização.
        chat_id (str, opcional): ID do chat para envio. Se None, usa o padrão configurado.

    Retorna:
        dict ou None: Resposta da API do Telegram ou None se a localização não estiver disponível.
    """
    info = ip_geo_lookup()
    if extra_text:
        send_message(extra_text, chat_id)
    lat, lon = info.get("lat"), info.get("lon")
    if lat is None or lon is None:
        return send_message("Geo por IP indisponivel.", chat_id)
    return send_location(lat, lon, chat_id)
