# ASCII only
from flask import Flask, request, jsonify
from faster_whisper import WhisperModel
import tempfile, os, time

# NEW: usar a biblioteca para enviar ao Telegram
from tcciotm import send_message

MODEL_NAME = os.getenv("TCCIOTM_STT_MODEL", "small")

app = Flask(__name__)
model = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/stt", methods=["POST"])
def stt():
    try:
        if "audio" not in request.files:
            return jsonify({"error": "no file 'audio'"}), 400

        f = request.files["audio"]
        upload_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        tmp_path = os.path.join(upload_dir, "temp_audio.wav")
        f.save(tmp_path)

        t0 = time.time()
        segments, info = model.transcribe(tmp_path, language="pt", vad_filter=False)
        text = "".join(seg.text for seg in segments).strip()
        dur = getattr(info, "duration", 0.0)
        infer = time.time() - t0
        print(f"[STT] audio={dur:.2f}s | inferencia={infer:.1f}s | texto='{text[:60]}'")

        # NEW: enviar a transcrição para o Telegram diretamente no notebook
        if text:
            send_message("STT: " + text)
        else:
            send_message("STT vazio.")

        try:
            os.remove(tmp_path)
        except OSError:
            pass

        return jsonify({"text": text, "duration": dur})

    except Exception as e:
        print("[STT] erro:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)