# TCCIOTM Project
Toolkit IoT-M para integração entre **Raspberry Pi** (sensores) e **Notebook/PC** (processamento).

Este pacote fornece módulos prontos para:
- Envio de mensagens e mídias via Telegram.
- Captura de áudio, transcrição (STT) e envio automático.
- Captura de imagem térmica MLX90640 e envio.
- Captura RGB via IP (celular).
- Consulta de geolocalização e envio de posição.
- Servidores Flask integrados (STT, Hub, Termal).


## 🔄 Diagrama Geral de Fluxo

      ┌──────────────────────────┐
      │     Raspberry Pi (RPi)   │
      │──────────────────────────│
      │ 🔘 GPIO 17 → STT + Loc   │
      │ 🔘 GPIO 27 → Fotos + Loc │
      │ 📡 Envia áudio (arecord) │
      │ 🌡️ Lê câmera térmica MLX │
      │ 📱 Captura RGB do celular│
      └────────────┬─────────────┘
                   │
                   │ HTTP (POST)
                   ▼
 ┌────────────────────────────────────────────┐
 │               Notebook / PC               │
 │────────────────────────────────────────────│
 │ 🧠 pc_stt_servidor.py (porta 5000)         │
 │    → recebe áudio e transcreve (Whisper)   │
 │    → envia texto ao Telegram               │
 │                                            │
 │ ⚙️ pc_servidor_hub.py (porta 5050)         │
 │    → recebe eventos (STT_LOC / MEDIA_LOC)  │
 │    → coordena envio de fotos + localização │
 │                                            │
 │ 🌡️ pc_receber_termal.py (porta 9998)       │
 │    → recebe stream térmico do RPi          │
 │    → envia imagem ao Telegram              │
 └──────────────────┬─────────────────────────┘
                    │
                    │ via Bot API (HTTP)
                    ▼
            ┌────────────────────┐
            │      Telegram      │
            │────────────────────│
            │ 💬 Mensagens e logs│
            │ 📸 RGB + térmica   │
            │ 🗺️ Localização     │
            │ 🎙️ Texto STT       │
            └────────────────────┘

---

## 📁 Estrutura

tcciotm_project/
│
├── pyproject.toml # metadados do pacote
├── README.md # este arquivo
│
├── tcciotm/ # biblioteca principal
│ ├── init.py
│ ├── config.py
│ ├── telegram_utils.py
│ ├── geo.py
│ ├── media.py
│ ├── media_pi.py
│ ├── stt.py
│
└── examples/ # scripts prontos para execução
├── pc_stt_servidor.py # servidor de reconhecimento de fala (Whisper)
├── pc_servidor_hub.py # orquestrador (STT+loc / fotos+loc)
└── pc_receber_termal.py# receptor térmico (socket 9998)


---

## ⚙️ Instalação
###
### No Notebook / PC
Requisitos:
- Python ≥ 3.9  
- pip  
- ffmpeg (opcional para STT)

```bash
cd tcciotm_project
pip install -e .

### No Notebook / PC

Ative o ambiente:
source ~/Desktop/xxx/bin/activate
cd ~/tcciotm_project
pip install -e .
pip install adafruit-blinka adafruit-circuitpython-mlx90640 opencv-python-headless numpy

Ative o I2C:
sudo raspi-config
# Interface Options → I2C → Enable
sudo reboot



### VARIÁVEIS DE AMBIENTE
Defina em ambos (PC e RPi):
export TCCIOTM_TG_TOKEN="SEU_TOKEN_DO_BOT"
export TCCIOTM_CHAT_ID="SEU_CHAT_ID"

Somente no notebook:
export TCCIOTM_STT_URL="http://XXX.XXX.XXX.XX:5000/stt"



Execução (Fluxo Completo)
1️⃣ Notebook

Abra 3 terminais e execute:

# Terminal 1 - Servidor de transcrição (STT)
python examples/pc_stt_servidor.py

# Terminal 2 - Servidor de hub/orquestrador
python examples/pc_servidor_hub.py

# Terminal 3 - Receptor térmico
python examples/pc_receber_termal.py

2️⃣ Raspberry Pi

Ative o ambiente e execute seu script de controle:

python rpi_dual_buttons.py


Funções dos botões:

GPIO 17 → grava áudio, envia STT + localização

GPIO 27 → envia fotos (RGB + térmica) + localização

🌍 Fluxo de Comunicação
[RPi]
│
├── GPIO 17 → grava áudio (.wav)
│      │
│      ├── envia POST → http://<notebook>:5000/stt
│      └── envia evento → http://<notebook>:5050/event (type="STT_LOC")
│
└── GPIO 27 → envia fotos (termal + RGB)
       │
       └── envia evento → http://<notebook>:5050/event (type="MEDIA_LOC")

[Notebook]
│
├── Porta 5000 → recebe áudio, transcreve (Whisper) e envia texto ao Telegram
├── Porta 5050 → recebe eventos e coordena envios (RGB, localização)
└── Porta 9998 → recebe stream térmico e envia imagem ao Telegram


📦 Dependências Principais
Ambiente	Dependências
Notebook	requests, opencv-python, numpy, faster-whisper, flask
RPi	adafruit-blinka, adafruit-circuitpython-mlx90640, opencv-python-headless, numpy, requests
🛠️ Notas

A biblioteca foi criada como pacote editável (pip install -e .) para facilitar desenvolvimento conjunto entre PC e RPi.

As funções são modulares, permitindo testar individualmente (ex: send_message, send_stt_from_wav, send_phone_rgb).

media_pi.py é automaticamente ignorado no PC; só funciona no RPi.

📜 Licença

Uso livre para fins acadêmicos e pesquisa (TCC IoT-M).
Autor: Iury Costa


---

## ✅ Próximos passos
1️⃣ Salve esse conteúdo como `README.md` na pasta do projeto.  
2️⃣ No terminal (VS Code):

```powershell
git add README.md
git commit -m "docs: adiciona README com estrutura e instruções completas"
git push