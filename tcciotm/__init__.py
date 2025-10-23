"""
Módulo de integração para utilitários de comunicação, mídia, geolocalização e STT (Speech-to-Text).

Este módulo centraliza as importações de diferentes submódulos do pacote,
fornecendo um ponto único de acesso para funções relacionadas a envio de mensagens,
tratamento de mídia, localização geográfica e captura de áudio.

Estrutura de funcionalidades:

- telegram_utils: envio de mensagens, fotos e localização via Telegram.
- geo: obtenção e envio de informações de IP e localização geográfica.
- media: captura e envio de imagens, incluindo imagens térmicas.
- stt: gravação e envio de áudio para reconhecimento de fala (Speech-to-Text).
- media_pi: leitura e envio de frames térmicos diretamente de sensores (ex: MLX90640 em Raspberry Pi).

Notas:
    - O módulo `media_pi` é opcional e só será importado corretamente se o ambiente
      possuir suporte às bibliotecas e hardware necessários (como sensores térmicos).
    - Caso contrário, as funções `read_mlx_to_f32` e `send_thermal_from_mlx` são definidas como None.

Exemplo:
    >>> from pacote import send_message, record_with_arecord
    >>> send_message("Teste de envio via Telegram")
    >>> record_with_arecord(3, "/tmp/audio.wav")

"""

from .telegram_utils import send_message, send_photo, send_location
from .geo import get_public_ip, ip_geo_lookup, send_current_location
from .media import send_photo_path, send_numpy_frame, thermal_to_u8, send_thermal_u8, send_phone_rgb
from .stt import record_with_arecord, send_stt_from_wav

try:
    from .media_pi import read_mlx_to_f32, send_thermal_from_mlx
except Exception:
    read_mlx_to_f32 = None
    send_thermal_from_mlx = None
