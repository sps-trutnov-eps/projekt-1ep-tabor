import requests
import time
import sys
import asyncio
import aiohttp
import random

SERVER_HTTP_URL = "https://projekt-1ep-tabor.onrender.com/"
SERVER_WS_URL = "wss://projekt-1ep-tabor.onrender.com/ws"

MAX_RETRIES = 30  # Počet pokusů (cca 10 minut při 20s intervalech)
RETRY_INTERVAL = 20  # Interval v sekundách mezi pokusy

def clear_line():
    """Vyčistí aktuální řádek v konzoli."""
    sys.stdout.write("\r" + " " * 70)
    sys.stdout.write("\r")
    sys.stdout.flush()

async def check_server_ws():
    """Zkontroluje dostupnost WebSocket serveru."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(SERVER_WS_URL, timeout=5) as ws:
                # Pošleme inicializační zprávu
                x, y = random.randint(50, 750), random.randint(50, 550)
                await ws.send_json({"x": x, "y": y})
                
                # Zkusíme získat odpověď
                try:
                    msg = await asyncio.wait_for(ws.receive(), 5)
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        return True
                except asyncio.TimeoutError:
                    pass
        
        return False
    except Exception:
        return False

def check_server_http():
    """Zkontroluje dostupnost HTTP serveru."""
    try:
        response = requests.get(SERVER_HTTP_URL, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

async def main():
    print("Probouzím herní server...")
    print("Server může být v režimu spánku a jeho probuzení může trvat až 10 minut.")
    
    for attempt in range(1, MAX_RETRIES + 1):
        clear_line()
        message = f"Pokus {attempt}/{MAX_RETRIES}: Probouzím server..."
        sys.stdout.write(message)
        sys.stdout.flush()
        
        # Nejprve zkusíme HTTP endpoint (probudí server rychleji)
        if check_server_http():
            # Pak zkusíme WebSocket endpoint
            if await check_server_ws():
                clear_line()
                print(f"Server je online! Můžeš spustit hru (main.py).")
                return True
        
        if attempt < MAX_RETRIES:
            animation = "|/-\\"
            for i in range(RETRY_INTERVAL):
                time.sleep(1)
                anim_char = animation[i % len(animation)]
                clear_line()
                sys.stdout.write(f"Pokus {attempt}/{MAX_RETRIES}: Čekám na probuzení serveru... {anim_char} ({RETRY_INTERVAL-i} s)")
                sys.stdout.flush()
    
    clear_line()
    print("Nepodařilo se probudit server po mnoha pokusech.")
    print("Možné příčiny:")
    print("1. Server může být ve větší údržbě")
    print("2. Server může být přetížený")
    print("3. Můžeš mít problém s připojením k internetu")
    print("\nZkus to znovu později, nebo kontaktuj správce serveru.")
    return False

if __name__ == "__main__":
    try:
        print("Ctrl+C pro přerušení...")
        asyncio.run(main())
    except KeyboardInterrupt:
        clear_line()
        print("Probouzení serveru bylo přerušeno uživatelem.")