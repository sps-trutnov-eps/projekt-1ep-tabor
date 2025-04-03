import socket
import threading
import json

HOST = "0.0.0.0"  # Poslouchá na všech IP
PORT = 5555
MAX_PLAYERS = 15

clients = {}  # Ukládá připojené hráče ve formátu {addr: (x, y)}

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} připojen")
    clients[addr] = (100, 100)  # Startovní pozice

    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            
            data = json.loads(data)
            clients[addr] = (data["x"], data["y"])

            # Posílá zpět všechny pozice hráčů
            conn.send(json.dumps(clients).encode())

    except ConnectionResetError:
        print(f"[DISCONNECTED] {addr} odpojen")
    finally:
        del clients[addr]
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(MAX_PLAYERS)
    print(f"[SERVER] Běží na {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()
