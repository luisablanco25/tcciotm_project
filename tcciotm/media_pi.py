# ASCII only
import numpy as np, board, busio, adafruit_mlx90640
from .media import thermal_to_u8, send_thermal_u8

def read_mlx_to_f32():
    """
    Lê os dados do sensor térmico MLX90640 e retorna uma matriz de
    ponto flutuante 32-bit (float32) representando a temperatura.

    Etapas:
    1. Inicializa o barramento I2C usando os pinos padrão do Raspberry Pi (SCL, SDA).
    2. Cria uma instância do sensor MLX90640.
    3. Inicializa um array de zeros de tamanho 24*32 para armazenar o frame.
    4. Preenche o array com os valores de temperatura lidos do sensor.
    5. Redimensiona o array 1D para 2D (24 linhas x 32 colunas) e retorna.

    Retorno:
        np.ndarray: Matriz 2D (24x32) de temperaturas em float32.
    """
    i2c = busio.I2C(board.SCL, board.SDA)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    frame = np.zeros((24*32,), dtype=np.float32)
    mlx.getFrame(frame)
    return frame.reshape((24,32))

def send_thermal_from_mlx(chat_id=None):
    """
    Lê a matriz térmica do MLX90640, converte para 8 bits (u8) e envia.

    Etapas:
    1. Chama read_mlx_to_f32() para obter os dados do sensor em float32.
    2. Converte a matriz float32 para 8-bit usando thermal_to_u8().
    3. Envia a matriz 8-bit usando send_thermal_u8(), incluindo
       legenda e chat_id opcional.

    Parâmetros:
        chat_id (opcional): ID do chat para envio da imagem térmica. 
                            Se None, envia para destinatário padrão.
    """
    f32 = read_mlx_to_f32()
    u8 = thermal_to_u8(f32)
    send_thermal_u8(u8, caption="MLX90640 (RPi)", chat_id=chat_id)
