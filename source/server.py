import os
import json
import asyncio
import websockets
from aiohttp import web

# Globální proměnné
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 5555))
CLIENTS = {}  # Ukládá připojené hráče ve formátu {id: (x, y)}
WEBSOCKET_CLIENTS = {}  # Ukládá WebSocket připojení

# Generátor ID klientů
client_id_counter = 0

async def handle_websocket(websocket, path):
    """Zpracování WebSocket připojení"""
    global client_id_counter
    client_id = str(client_id_counter)
    client_id_counter += 1
    
    try:
        # Registrace nového klienta
        CLIENTS[client_id] = (100, 100)  # Startovní pozice
        WEBSOCKET_CLIENTS[client_id] = websocket
        
        print(f"[NEW CONNECTION] WebSocket klient {client_id} připojen")
        
        # Nekonečná smyčka pro zpracování zpráv
        async for message in websocket:
            try:
                data = json.loads(message)
                
                # Validace dat
                if 'x' not in data or 'y' not in data:
                    print(f"[ERROR] Neplatná data od klienta {client_id}")
                    await websocket.send(json.dumps({"error": "Neplatná data, chybí x nebo y"}))
                    continue
                
                # Aktualizace pozice
                CLIENTS[client_id] = (data["x"], data["y"])
                print(f"[UPDATE] Klient {client_id} pozice: ({data['x']}, {data['y']})")
                
                # Posílá zpět všechny pozice hráčů
                await websocket.send(json.dumps(CLIENTS))
                
                # Nepovinné: Rozešli aktualizaci všem připojeným klientům
                # await broadcast_positions()
                
            except json.JSONDecodeError:
                print(f"[ERROR] Neplatný JSON od klienta {client_id}")
                await websocket.send(json.dumps({"error": "Neplatný JSON"}))
            except Exception as e:
                print(f"[ERROR] Chyba při zpracování dat pro klienta {client_id}: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        print(f"[DISCONNECTED] WebSocket klient {client_id} odpojen")
    finally:
        # Odstranění klienta při odpojení
        if client_id in CLIENTS:
            del CLIENTS[client_id]
        if client_id in WEBSOCKET_CLIENTS:
            del WEBSOCKET_CLIENTS[client_id]
        print(f"[CLEANUP] Klient {client_id} odstraněn")

async def broadcast_positions():
    """Rozešle pozice všem připojeným klientům"""
    if WEBSOCKET_CLIENTS:
        positions_json = json.dumps(CLIENTS)
        await asyncio.gather(
            *[ws.send(positions_json) for ws in WEBSOCKET_CLIENTS.values()],
            return_exceptions=True
        )

# HTTP endpointy pro základní informace
async def handle_root(request):
    """Základní endpoint pro kontrolu, že server běží"""
    return web.Response(text="Game server is running. Connect via WebSocket.")

async def handle_status(request):
    """Endpoint pro zobrazení stavu serveru"""
    status = {
        "clients_count": len(CLIENTS),
        "clients": CLIENTS
    }
    return web.json_response(status)

# Nastavení HTTP a WebSocket serveru
async def start_server():
    # Vytvoření HTTP aplikace
    app = web.Application()
    app.router.add_get('/', handle_root)
    app.router.add_get('/status', handle_status)
    
    # Nastavení WebSocket serveru
    ws_server = websockets.serve(handle_websocket, HOST, 0)  # Port 0 pro automatické přiřazení
    
    # Spuštění HTTP serveru
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    
    print(f"[SERVER] HTTP server běží na http://{HOST}:{PORT}")
    print(f"[SERVER] WebSocket server připraven pro připojení")
    
    # Spuštění obou serverů
    await asyncio.gather(
        site.start(),
        ws_server
    )
    
    # Udržuj server spuštěný
    await asyncio.Future()  # Běží dokud se nevypne

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("[SERVER] Server zastaven uživatelem")
