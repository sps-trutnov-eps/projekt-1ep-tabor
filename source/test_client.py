import asyncio
import json
import random
import websockets
import time

# URL tvého serveru na Render.com
SERVER_URL = "wss://projekt-1ep-tabor.onrender.com"  # Použij svou URL z Render.com
# Pro lokální testování použij:
# SERVER_URL = "ws://localhost:5555"

async def connect_and_play():
    """Připojení k serveru a simulace pohybu hráče"""
    try:
        print(f"Připojuji se k {SERVER_URL}...")
        
        async with websockets.connect(SERVER_URL) as websocket:
            print("Připojení úspěšné!")
            
            # Počáteční pozice
            position = {"x": 100, "y": 100}
            
            # Simulace pohybu hráče
            for i in range(10):  # 10 kroků
                # Náhodný pohyb
                position["x"] += random.randint(-10, 10)
                position["y"] += random.randint(-10, 10)
                
                print(f"\nKrok {i+1}:")
                print(f"Odesílám pozici: {position}")
                
                # Odeslání pozice
                await websocket.send(json.dumps(position))
                
                # Přijetí odpovědi
                response = await websocket.recv()
                print(f"Přijata surová data: '{response}'")
                
                try:
                    players_data = json.loads(response)
                    if "error" in players_data:
                        print(f"Server vrátil chybu: {players_data['error']}")
                    else:
                        print(f"Přijata data od serveru ({len(players_data)} hráčů):")
                        for player_id, pos in players_data.items():
                            print(f"  - Hráč {player_id}: pozice {pos}")
                except json.JSONDecodeError as e:
                    print(f"Nepodařilo se zpracovat odpověď jako JSON: {e}")
                
                # Pauza mezi kroky
                await asyncio.sleep(1)
            
            print("\nTest dokončen, odpojuji se...")
            
    except websockets.exceptions.ConnectionError as e:
        print(f"Chyba při připojení: {e}")
    except Exception as e:
        print(f"Neočekávaná chyba: {e}")

if __name__ == "__main__":
    print("=== WEBSOCKET HERNÍ KLIENT - TEST ===")
    asyncio.run(connect_and_play())
