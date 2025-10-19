# ASCII only
import socket, struct, numpy as np, cv2
from tcciotm import send_message, send_thermal_u8

HOST = "0.0.0.0"  # escuta em todas as interfaces
PORT = 9998

def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf

def main():
    send_message("PC pronto para receber termal (porta 9998).")
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(1)
    print("Listening on {}:{} ...".format(HOST, PORT))

    while True:
        conn, addr = srv.accept()
        print("Client connected:", addr)
        try:
            while True:
                # protocolo: [u32 tamanho][bytes jpeg]
                hdr = recv_exact(conn, 4)
                if not hdr:
                    break
                (size,) = struct.unpack("!I", hdr)  # big-endian
                jpg = recv_exact(conn, size)
                if not jpg:
                    break

                arr = np.frombuffer(jpg, dtype=np.uint8)
                gray = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)  # (H,W) uint8
                if gray is None:
                    print("Falha ao decodificar JPEG")
                    continue

                # envia pro Telegram
                send_thermal_u8(gray, caption="Thermal PB (do RPi)")
                print("Frame termal recebido e enviado.")
        finally:
            conn.close()
            print("Client disconnected.")

if __name__ == "__main__":
    main()