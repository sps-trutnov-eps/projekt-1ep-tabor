import os
import json
import asyncio
from aiohttp import web

# Globální proměnné
PORT = int(os.environ.get("PORT", 5555))
CLIENTS = {}  # Ukládá připojené hráče ve formátu {id: {...}}
WEBSOCKET_CONNECTIONS = set()  # Ukládá aktivní WebSocket připojení
active_grenades = {}

# Generátor ID klientů
client_id_counter = 0

async def update_grenades():
    """Pravidelná aktualizace granátů na serveru"""
    current_time = time.time()
    updates = {}
    
    for grenade_id, grenade in list(active_grenades.items()):
        if grenade["state"] == "moving":
            # Aktualizace pozice
            grenade["x"] += grenade["velocity_x"]
            grenade["y"] += grenade["velocity_y"]
            
            # Kontrola vzdálenosti
            distance = math.sqrt((grenade["x"] - grenade["start_x"])**2 + 
                               (grenade["y"] - grenade["start_y"])**2)
            
            if distance >= 500:
                grenade["state"] = "stopped"
                grenade["stop_time"] = current_time
                
        elif grenade["state"] == "stopped":
            if current_time - grenade["stop_time"] >= 1.0:
                grenade["state"] = "exploded"
                grenade["explosion_time"] = current_time
                
        elif grenade["state"] == "exploded":
            if current_time - grenade["explosion_time"] >= 0.5:
                del active_grenades[grenade_id]
                continue
        
        updates[grenade_id] = {
            "x": grenade["x"],
            "y": grenade["y"],
            "state": grenade["state"]
        }
    
    # Poslání aktualizací všem klientům
    if updates:
        broadcast_message = {"grenade_updates": updates}
        for ws in list(WEBSOCKET_CONNECTIONS):
            if ws.closed:
                WEBSOCKET_CONNECTIONS.discard(ws)
                continue
            try:
                await ws.send_json(broadcast_message)
            except:
                WEBSOCKET_CONNECTIONS.discard(ws)

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
            "health": 100,
            "alive": True,
            "grenades": {
                "amount": 3,
                "last_used": 0
            }
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
                    if "health" in data:
                        CLIENTS[client_id]["health"] = data["health"]
                    if "alive" in data:
                        CLIENTS[client_id]["alive"] = data["alive"]
                    if "grenades" in data:
                        CLIENTS[client_id]["grenades"] = data["grenades"]
                    
                    print(f"[UPDATE] Klient {client_id} pozice: ({data['x']}, {data['y']}), angle: {CLIENTS[client_id].get('angle', 0)}, weapon: {CLIENTS[client_id].get('weapon', 'Crossbow')}")
                    
                    if "thrown_grenade" in data:
                        grenade_data = data["thrown_grenade"]
                        grenade_id = grenade_data["id"]
                        
                        # Uložení granátu na server
                        active_grenades[grenade_id] = {
                            "x": grenade_data["x"],
                            "y": grenade_data["y"],
                            "velocity_x": grenade_data["velocity_x"],
                            "velocity_y": grenade_data["velocity_y"],
                            "owner": grenade_data["owner"],
                            "state": "moving",
                            "start_time": time.time(),
                            "start_x": grenade_data["x"],
                            "start_y": grenade_data["y"]
                        }
                        
                        print(f"[GRENADE] Klient {client_id} hodil granát {grenade_id}")
                        
                        # Broadcast granátu všem ostatním klientům
                        broadcast_message = {
                            "grenade_broadcast": grenade_data
                        }
                        
                        for other_ws in WEBSOCKET_CONNECTIONS:
                            if other_ws == ws or other_ws.closed:  # Neposílej zpět odesílateli
                                continue
                            try:
                                await other_ws.send_json(broadcast_message)
                            except:
                                WEBSOCKET_CONNECTIONS.discard(other_ws)
                    
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
                .grenades { margin-top: 20px; }
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
                <p>Aktivní granáty: <strong>""" + str(len(active_grenades)) + """</strong></p>
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
        "active_grenades_count": len(active_grenades),
        "active_grenades": active_grenades
    }
    return web.json_response(status)

async def start_grenade_updater():
    """Spustí pravidelný update granátů na pozadí"""
    while True:
        await update_grenades()
        await asyncio.sleep(0.05)

# Nastavení HTTP a WebSocket serveru
async def init_app():
    app = web.Application()
    app.router.add_get('/', handle_root)
    app.router.add_get('/status', handle_status)
    app.router.add_get('/ws', handle_websocket)  # WebSocket endpoint
    
    asyncio.create_task(start_grenade_updater())
    
    return app

if __name__ == "__main__":
    # Spuštění aplikace
    try:
        print(f"[SERVER] Spouštím server na portu {PORT}")
        web.run_app(init_app(), port=PORT)
    except KeyboardInterrupt:
        print("[SERVER] Server zastaven uživatelem")
