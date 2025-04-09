import asyncio
import json
import random
import aiohttp
import time

# Pro server hostovaný na Render.com použij:
SERVER_URL = "wss://projekt-1ep-tabor.onrender.com/ws"
# Pro lokální server použij:
# SERVER_URL = "ws://localhost:5555/ws"

async def connect_and_play():
    """Připojení k serveru a simulace pohybu hráče"""
    try:
        print(f"Připojuji se k {SERVER_URL}...")
        
        # Používáme aiohttp.ClientSession pro WebSocket připojení
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(SERVER_URL) as ws:
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
                    await ws.send_json(position)
                    
                    # Přijetí odpovědi
                    msg = await ws.receive()
                    
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        print(f"Přijata surová data: '{msg.data}'")
                        
                        try:
                            players_data = json.loads(msg.data)
                            if "error" in players_data:
                                print(f"Server vrátil chybu: {players_data['error']}")
                            else:
                                print(f"Přijata data od serveru ({len(players_data)} hráčů):")
                                for player_id, pos in players_data.items():
                                    print(f"  - Hráč {player_id}: pozice {pos}")
                        except json.JSONDecodeError as e:
                            print(f"Nepodařilo se zpracovat odpověď jako JSON: {e}")
                    else:
                        print(f"Neočekávaný typ zprávy: {msg.type}")
                    
                    # Pauza mezi kroky
                    await asyncio.sleep(1)
                
                print("\nTest dokončen, odpojuji se...")
                
    except aiohttp.ClientError as e:
        print(f"Chyba připojení: {e}")
    except Exception as e:
        print(f"Neočekávaná chyba: {e}")

if __name__ == "__main__":
    print("=== WEBSOCKET HERNÍ KLIENT - TEST ===")
    asyncio.run(connect_and_play())
