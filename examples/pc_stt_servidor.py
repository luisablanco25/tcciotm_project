# ASCII only
"""Servidor Flask para transcrição automática de áudio com Whisper.

Este módulo implementa uma API REST simples com dois endpoints:
- `/health`: Verificação de integridade do serviço.
- `/stt`: Recebe um arquivo de áudio, transcreve usando `faster_whisper` e envia o texto via `tcciotm.send_message`.

O modelo Whisper utilizado é definido pela variável de ambiente `TCCIOTM_STT_MODEL`.
"""

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
    """Endpoint de verificação de integridade do serviço.

    Returns:
        tuple: JSON com `{"status": "ok"}` e código HTTP 200.
    """
    return jsonify({"status": "ok"}), 200

@app.route("/stt", methods=["POST"])
def stt():
    """Endpoint principal para transcrição de áudio.

    Recebe um arquivo de áudio via POST (campo `audio`), salva temporariamente,
    processa com o modelo Whisper e retorna o texto transcrito.

    Além disso, envia a transcrição diretamente ao Telegram via `send_message`.

    Returns:
        tuple: JSON contendo o texto transcrito (`"text"`) e a duração estimada (`"duration"`).
        Em caso de erro, retorna JSON com `"error"` e o respectivo código HTTP.
    """
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
    """Ponto de entrada principal do servidor Flask.

    Executa o app na porta 5000, ouvindo em todas as interfaces (0.0.0.0),
    com modo `debug` desativado.
    """
    app.run(host="0.0.0.0", port=5000, debug=False)
