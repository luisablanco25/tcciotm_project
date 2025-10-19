# ASCII only
from flask import Flask, request, jsonify
import os, threading
from tcciotm import send_message, send_phone_rgb, ip_geo_lookup, send_location

PHONE_BASE = os.getenv("PHONE_BASE", "http://192.168.0.221:8080")
app = Flask(__name__)

def process_event(etype, rpi_ip):
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
    return jsonify({"status": "ok"}), 200

@app.route("/event", methods=["POST"])
def event():
    j = request.get_json(force=True, silent=True) or {}
    etype = j.get("type"); rpi_ip = j.get("ip")
    if not etype:
        return jsonify({"error": "missing type"}), 400
    threading.Thread(target=process_event, args=(etype, rpi_ip), daemon=True).start()
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)