import socket
import threading
import json
import os

# Render.com přiřazuje port pomocí proměnné prostředí PORT
# a používá 0.0.0.0 pro poslech na všech rozhraních
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 5555))
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
        # Bezpečné odstranění klienta, pokud existuje
        if addr_str in clients:
            del clients[addr_str]
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Povolí opětovné použití adresy
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind na HOST a PORT
    server.bind((HOST, PORT))
    server.listen(MAX_PLAYERS)
    print(f"[SERVER] Běží na {HOST}:{PORT}")

    try:
        while True:
            try:
                conn, addr = server.accept()
                print(f"[SERVER] Připojení od {addr}")
                thread = threading.Thread(target=handle_client, args=(conn, addr))
                thread.daemon = True  # Zajistí, že vlákno se ukončí, když se ukončí hlavní program
                thread.start()

            except Exception as e:
                print(f"[ERROR] Chyba při přijímání připojení: {e}")
    except KeyboardInterrupt:
        print("[SERVER] Server zastaven uživatelem")
    finally:
        server.close()
        print("[SERVER] Server vypnut")

if __name__ == "__main__":
    start_server()
    