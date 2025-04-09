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
            print(f"[DATA] Přijata data od {addr}: '{data}'")  # Diagnostika
            
            if not data:
                print(f"[WARNING] Prázdná data od {addr}")
                break
            
            try:
                # Zpracování příchozích dat
                data_dict = json.loads(data)
                
                # Validace dat - ujistíme se, že obsahují 'x' a 'y'
                if 'x' not in data_dict or 'y' not in data_dict:
                    print(f"[ERROR] Chybějící x nebo y v datech od {addr}")
                    continue
                
                # Aktualizace pozice klienta
                clients[addr_str] = (data_dict["x"], data_dict["y"])
                
                # Příprava dat pro odeslání
                response_data = json.dumps(clients)
                print(f"[RESPONSE] Odesílám odpověď: '{response_data}'")  # Diagnostika
                
                # Odeslání odpovědi
                conn.send(response_data.encode())
            
            except json.JSONDecodeError as e:
                print(f"[ERROR] Neplatný JSON od {addr}: {e}")
                # Pošleme zpět chybovou zprávu
                error_msg = json.dumps({"error": "Neplatný JSON"})
                conn.send(error_msg.encode())
            except Exception as e:
                print(f"[ERROR] Chyba při zpracování dat pro {addr}: {e}")

    except ConnectionResetError:
        print(f"[DISCONNECTED] {addr} odpojen")
    except Exception as e:
        print(f"[ERROR] Obecná chyba pro {addr}: {e}")
    finally:
        # Bezpečné odstranění klienta, pokud existuje
        if addr_str in clients:
            del clients[addr_str]
        conn.close()
        print(f"[CLEANUP] Spojení s {addr} uzavřeno a klient odstraněn")

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
