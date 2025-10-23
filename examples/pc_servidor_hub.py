# ASCII only
"""Módulo Flask que atua como um hub de integração entre dispositivos IoT.

Recebe eventos via HTTP (endpoint /event) e executa ações de envio de mensagens,
imagens RGB e localização com base em chamadas aos serviços do módulo `tcciotm`.

O módulo pode ser executado diretamente, iniciando um servidor Flask local
escutando na porta 5050.
"""

from flask import Flask, request, jsonify
import os, threading
from tcciotm import send_message, send_phone_rgb, ip_geo_lookup, send_location

PHONE_BASE = os.getenv("PHONE_BASE", "http://192.168.0.221:8080")
app = Flask(__name__)

def process_event(etype, rpi_ip):
    """Processa um evento recebido do endpoint `/event`.

    De acordo com o tipo de evento (`etype`), o hub executa diferentes ações:
    - `"STT_LOC"`: Envia a localização geográfica (obtida via IP) para o sistema.
    - `"MEDIA_LOC"`: Captura uma imagem RGB do celular e também envia a localização.

    Args:
        etype (str): Tipo do evento (por exemplo, `"STT_LOC"` ou `"MEDIA_LOC"`).
        rpi_ip (str | None): Endereço IP do dispositivo de origem, usado para lookup geográfico.

    Efeitos colaterais:
        - Chama funções de envio (`send_message`, `send_phone_rgb`, `send_location`).
        - Executa `ip_geo_lookup` para obter latitude e longitude aproximadas.

    Exceções:
        - Registra mensagens de erro via `send_message` em caso de falha.
    """
    try:
        send_message(f"Hub: evento recebido: {etype} (ip={rpi_ip})")
        lat = lon = None
        if rpi_ip:
            info = ip_geo_lookup(ip=rpi_ip)
            lat, lon = info.get("lat"), info.get("lon")

        if etype == "STT_LOC":
            if lat is not None and lon is not None:
                send_location(lat, lon)
            else:
                send_message("Hub: Geo por IP indisponivel.")
        elif etype == "MEDIA_LOC":
            try:
                send_phone_rgb(PHONE_BASE, caption="RGB do celular")
            except Exception as e:
                send_message(f"Hub: falha RGB ({e})")
            if lat is not None and lon is not None:
                send_location(lat, lon)
            else:
                send_message("Hub: Geo por IP indisponivel.")
    except Exception as e:
        send_message(f"Hub: erro interno ({e})")

@app.route("/health", methods=["GET"])
def health():
    """Endpoint de verificação de saúde da aplicação.

    Returns:
        (tuple): Resposta JSON `{"status": "ok"}` com código HTTP 200.
    """
    return jsonify({"status": "ok"}), 200

@app.route("/event", methods=["POST"])
def event():
    """Endpoint principal para recebimento de eventos IoT.

    Espera um JSON no corpo da requisição com as chaves:
        - `"type"`: tipo do evento (obrigatório)
        - `"ip"`: IP do dispositivo emissor (opcional)

    O processamento é executado em uma thread separada.

    Returns:
        (tuple): JSON `{"ok": True}` com código 200, ou erro 400 se faltar `"type"`.
    """
    j = request.get_json(force=True, silent=True) or {}
    etype = j.get("type"); rpi_ip = j.get("ip")
    if not etype:
        return jsonify({"error": "missing type"}), 400
    threading.Thread(target=process_event, args=(etype, rpi_ip), daemon=True).start()
    return jsonify({"ok": True})

if __name__ == "__main__":
    """Ponto de entrada principal.

    Executa o servidor Flask escutando em todas as interfaces (0.0.0.0),
    na porta 5050, com `debug` desativado.
    """
    app.run(host="0.0.0.0", port=5050, debug=False)
