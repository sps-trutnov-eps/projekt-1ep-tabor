import os
import json
import asyncio
from aiohttp import web

# Globální proměnné
PORT = int(os.environ.get("PORT", 5555))
CLIENTS = {}  # Ukládá připojené hráče ve formátu {id: {...}}
WEBSOCKET_CONNECTIONS = set()  # Ukládá aktivní WebSocket připojení

# Generátor ID klientů
client_id_counter = 0

async def handle_websocket(request):
    """Zpracování WebSocket připojení přes aiohttp"""
    global client_id_counter
    client_id = str(client_id_counter)
    client_id_counter += 1
    
    # Vytvoření WebSocket připojení
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    try:
        # Registrace nového klienta
        CLIENTS[client_id] = {
            "x": 100,
            "y": 100,
            "angle": 0,
            "weapon": "Crossbow"
        }  # Startovní pozice a výchozí hodnoty
        
        WEBSOCKET_CONNECTIONS.add(ws)
        
        print(f"[NEW CONNECTION] WebSocket klient {client_id} připojen")
        
        # Nekonečná smyčka pro zpracování zpráv
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    
                    # Validace dat
                    if 'x' not in data or 'y' not in data:
                        print(f"[ERROR] Neplatná data od klienta {client_id}")
                        await ws.send_json({"error": "Neplatná data, chybí x nebo y"})
                        continue
                    
                    # Aktualizace dat hráče
                    CLIENTS[client_id]["x"] = data["x"]
                    CLIENTS[client_id]["y"] = data["y"]
                    if "angle" in data:
                        CLIENTS[client_id]["angle"] = data["angle"]
                    if "weapon" in data:
                        CLIENTS[client_id]["weapon"] = data["weapon"]
                    
                    print(f"[UPDATE] Klient {client_id} pozice: ({data['x']}, {data['y']}), angle: {CLIENTS[client_id].get('angle', 0)}, weapon: {CLIENTS[client_id].get('weapon', 'Crossbow')}")
                    
                    # Projektily (původní logika zachována)
                    if "projectile" in data:
                        for other_ws in WEBSOCKET_CONNECTIONS:
                            if other_ws.closed:
                                continue
                            try:
                                await other_ws.send_json({
                                    "projectile_broadcast": {
                                        "owner": client_id,
                                        **data["projectile"]
                                    }
                                })
                            except:
                                pass
                    
                    # Posílá zpět všechny hráče (včetně úhlu a zbraně)
                    await ws.send_json(CLIENTS)
                    
                except json.JSONDecodeError:
                    print(f"[ERROR] Neplatný JSON od klienta {client_id}")
                    await ws.send_json({"error": "Neplatný JSON"})
                except Exception as e:
                    print(f"[ERROR] Chyba při zpracování dat pro klienta {client_id}: {e}")
            
            elif msg.type == web.WSMsgType.ERROR:
                print(f"[ERROR] WebSocket connection closed with exception: {ws.exception()}")
                
        print(f"[DISCONNECTED] WebSocket klient {client_id} odpojen")
        
    finally:
        # Odstranění klienta při odpojení
        WEBSOCKET_CONNECTIONS.discard(ws)
        if client_id in CLIENTS:
            del CLIENTS[client_id]
        print(f"[CLEANUP] Klient {client_id} odstraněn")
        
    return ws

# HTTP endpointy pro základní informace
async def handle_root(request):
    """Základní endpoint pro kontrolu, že server běží"""
    html = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Game Server</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #333; }
                .info { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
                .status { margin-top: 20px; }
                .clients { margin-top: 20px; }
            </style>
        </head>
        <body>
            <h1>Game Server je aktivní</h1>
            <div class="info">
                <p>Server běží a je připraven přijímat WebSocket připojení.</p>
                <p>Pro připojení použij WebSocket URL: <code>wss://"""+ request.host + """</code></p>
            </div>
            <div class="status">
                <h2>Stav serveru</h2>
                <p>Počet připojených klientů: <strong>""" + str(len(CLIENTS)) + """</strong></p>
            </div>
            <div class="clients">
                <h2>Aktivní hráči</h2>
                <pre>""" + json.dumps(CLIENTS, indent=2) + """</pre>
            </div>
        </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def handle_status(request):
    """Endpoint pro zobrazení stavu serveru"""
    status = {
        "clients_count": len(CLIENTS),
        "clients": CLIENTS
    }
    return web.json_response(status)

# Nastavení HTTP a WebSocket serveru
async def init_app():
    app = web.Application()
    app.router.add_get('/', handle_root)
    app.router.add_get('/status', handle_status)
    app.router.add_get('/ws', handle_websocket)  # WebSocket endpoint
    
    return app

if __name__ == "__main__":
    # Spuštění aplikace
    try:
        print(f"[SERVER] Spouštím server na portu {PORT}")
        web.run_app(init_app(), port=PORT)
    except KeyboardInterrupt:
        print("[SERVER] Server zastaven uživatelem")
