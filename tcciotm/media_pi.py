# ASCII only
import numpy as np, board, busio, adafruit_mlx90640
from .media import thermal_to_u8, send_thermal_u8

def read_mlx_to_f32():
    i2c = busio.I2C(board.SCL, board.SDA)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    frame = np.zeros((24*32,), dtype=np.float32)
    mlx.getFrame(frame)
    return frame.reshape((24,32))

def send_thermal_from_mlx(chat_id=None):
    f32 = read_mlx_to_f32()
    u8 = thermal_to_u8(f32)
    send_thermal_u8(u8, caption="MLX90640 (RPi)", chat_id=chat_id)