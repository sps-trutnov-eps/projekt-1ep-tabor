import socket
import json
import time
import random

# Adresa tvého serveru na Render.com - tuto URL změň na svoji
SERVER_HOST = "projekt-1ep-tabor.onrender.com"  # Změň na URL tvého Render serveru
SERVER_PORT = 5555

def test_connection():
    """Test základního připojení k serveru"""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        print(f"Pokouším se připojit k {SERVER_HOST}:{SERVER_PORT}...")
        client.connect((SERVER_HOST, SERVER_PORT))
        print("Připojení úspěšné!")
        return client
    except Exception as e:
        print(f"Chyba při připojení: {e}")
        return None

def simulate_player(client, moves=5):
    """Simuluje pohyb hráče a přijímá aktualizace od serveru"""
    if not client:
        return
    
    try:
        # Počáteční pozice
        position = {"x": 100, "y": 100}
        
        for i in range(moves):
            # Náhodný pohyb
            position["x"] += random.randint(-10, 10)
            position["y"] += random.randint(-10, 10)
            
            print(f"\nKrok {i+1}:")
            print(f"Odesílám pozici: {position}")
            
            # Odeslání pozice na server
            message = json.dumps(position)
            client.send(message.encode())
            
            # Přijetí odpovědi
            response = client.recv(4096).decode()
            
            try:
                players_data = json.loads(response)
                print(f"Přijata data od serveru ({len(players_data)} hráčů):")
                for addr, pos in players_data.items():
                    print(f"  - Hráč {addr}: pozice {pos}")
            except json.JSONDecodeError:
                print(f"Nepodařilo se zpracovat odpověď: {response}")
            
            time.sleep(1)  # Počkáme sekundu mezi pohyby
    
    except ConnectionResetError:
        print("Server ukončil spojení")
    except ConnectionAbortedError:
        print("Spojení bylo přerušeno")
    except Exception as e:
        print(f"Chyba: {e}")
    finally:
        client.close()
        print("Spojení ukončeno")

def run_test():
    print("=== TEST HERNÍHO SERVERU ===")
    client = test_connection()
    
    if client:
        print("\nServer běží! Začínám testovat pohyb hráče...")
        simulate_player(client, moves=10)
    else:
        print("\nTest selhal: Nepodařilo se připojit k serveru.")
        print("Zkontroluj, že:")
        print("1. SERVER_HOST obsahuje správnou URL adresu tvého Render serveru")
        print("2. Server na Render.com běží a není v režimu spánku")
        print("3. Firewall neblokuje odchozí připojení na port 5555")

if __name__ == "__main__":
    run_test()
    