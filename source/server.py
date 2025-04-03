import socket
import threading
import json

HOST = "192.168.216.218"  # Poslouchá na všech IP (měl by to být správný hostitel)
PORT = 5555
MAX_PLAYERS = 15

clients = {}  # Ukládá připojené hráče ve formátu {addr: (x, y)}

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} připojen")
    addr_str = f"{addr[0]}:{addr[1]}"  # Převod tuple na string
    clients[addr_str] = (100, 100)  # Startovní pozice

    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            
            data = json.loads(data)
            clients[addr_str] = (data["x"], data["y"])

            # Posílá zpět všechny pozice hráčů
            conn.send(json.dumps(clients).encode())

    except ConnectionResetError:
        print(f"[DISCONNECTED] {addr} odpojen")
    except Exception as e:
        print(f"[ERROR] Chyba při zpracování dat pro {addr}: {e}")
    finally:
        del clients[addr_str]
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Pokud použijeme '0.0.0.0', server poslouchá na všech rozhraních
    server.bind((HOST, PORT))
    server.listen(MAX_PLAYERS)
    print(f"[SERVER] Běží na {HOST}:{PORT}")

    while True:
        try:
            conn, addr = server.accept()
            print(f"[SERVER] Připojení od {addr}")
            threading.Thread(target=handle_client, args=(conn, addr)).start()

        except Exception as e:
            print(f"[ERROR] Chyba při přijímání připojení: {e}")
            break

if __name__ == "__main__":
    start_server()
