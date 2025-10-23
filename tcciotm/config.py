"""
Módulo de configuração e verificação de variáveis de ambiente para integração com o Telegram e o sistema STT.

Este módulo define e valida variáveis de ambiente necessárias para a execução do sistema de
comunicação entre dispositivos e serviços (como Telegram e reconhecimento de fala).

Constantes:
    TELEGRAM_BOT_TOKEN (str): Token do bot do Telegram, obtido via BotFather.
    DEFAULT_CHAT_ID (str): ID do chat padrão para envio de mensagens no Telegram.
    STT_ENDPOINT_URL (str): URL do endpoint do serviço de Speech-to-Text (STT) — deve ser o mesmo no PC.
    TIMEOUT_S (int): Tempo máximo (em segundos) para requisições HTTP antes de timeout.

Funções:
    assert_tokens():
        Verifica se as variáveis de ambiente obrigatórias estão configuradas.
        Lança um erro se o token do bot do Telegram ou o chat ID não estiverem definidos.

Exemplo:
    >>> assert_tokens()
    RuntimeError: Set TCCIOTM_TG_TOKEN and TCCIOTM_CHAT_ID env vars.

Notas:
    - Este módulo deve ser importado antes de qualquer tentativa de uso de funções
      que enviem mensagens via Telegram.
    - Todas as variáveis podem ser definidas no ambiente do sistema operacional ou em um arquivo `.env`.
"""

# ASCII only
import os

TELEGRAM_BOT_TOKEN = os.getenv("TCCIOTM_TG_TOKEN", "")
DEFAULT_CHAT_ID    = os.getenv("TCCIOTM_CHAT_ID", "")
STT_ENDPOINT_URL   = os.getenv("TCCIOTM_STT_URL", "")  # manter isto também no PC
TIMEOUT_S          = int(os.getenv("TCCIOTM_TIMEOUT", "15"))

def assert_tokens():
    """
    Verifica se as variáveis de ambiente necessárias para comunicação via Telegram estão configuradas.

    Raises:
        RuntimeError: Se o token do bot (`TCCIOTM_TG_TOKEN`) ou o chat ID (`TCCIOTM_CHAT_ID`)
        não estiverem definidos.
    """
    if not TELEGRAM_BOT_TOKEN or not DEFAULT_CHAT_ID:
        raise RuntimeError("Set TCCIOTM_TG_TOKEN and TCCIOTM_CHAT_ID env vars.")
