import asyncio
import json
import random
import time
import argparse
import sys
import aiohttp
import math
from datetime import datetime

def print_colored(text, color_code):
    """Vypíše barevný text do konzole"""
    print(f"\033[{color_code}m{text}\033[0m")

def print_info(text):
    """Vypíše informační zprávu modře"""
    print_colored(text, "94")

def print_success(text):
    """Vypíše úspěšnou zprávu zeleně"""
    print_colored(text, "92")

def print_warning(text):
    """Vypíše varovnou zprávu žlutě"""
    print_colored(text, "93")

def print_error(text):
    """Vypíše chybovou zprávu červeně"""
    print_colored(text, "91")

async def player_session(player_id, url, moves, move_delay, pattern="random"):
    """Funkce pro simulaci jednoho hráče v samostatném vlákně"""
    try:
        print_info(f"Hráč {player_id}: Připojuji se k {url}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(url) as ws:
                print_success(f"Hráč {player_id}: Připojen")
                
                # Počáteční pozice
                position = {"x": 100 + random.randint(-30, 30), 
                            "y": 100 + random.randint(-30, 30)}
                
                for i in range(moves):
                    if pattern == "random":
                        # Náhodný pohyb
                        position["x"] += random.randint(-10, 10)
                        position["y"] += random.randint(-10, 10)
                    elif pattern == "circle":
                        # Pohyb po kruhové dráze
                        angle = (i / moves) * 6.28  # 0 až 2π
                        position["x"] = 150 + int(50 * math.cos(angle))
                        position["y"] = 150 + int(50 * math.sin(angle))
                    elif pattern == "square":
                        # Pohyb po čtverci
                        segment = i % 4
                        progress = (i % (moves//4)) / (moves//4)
                        if segment == 0:  # Horní strana
                            position["x"] = 100 + int(100 * progress)
                            position["y"] = 100
                        elif segment == 1:  # Pravá strana
                            position["x"] = 200
                            position["y"] = 100 + int(100 * progress)
                        elif segment == 2:  # Dolní strana
                            position["x"] = 200 - int(100 * progress)
                            position["y"] = 200
                        else:  # Levá strana
                            position["x"] = 100
                            position["y"] = 200 - int(100 * progress)
                    
                    # Odeslání pozice na server
                    await ws.send_json(position)
                    
                    # Přijetí odpovědi
                    msg = await ws.receive()
                    
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            players_data = json.loads(msg.data)
                            if "error" in players_data:
                                print_warning(f"Hráč {player_id}: Server vrátil chybu: {players_data['error']}")
                            else:
                                print_info(f"Hráč {player_id}: Krok {i+1}, Pozice {position}, Vidí {len(players_data)} hráčů")
                        except json.JSONDecodeError:
                            print_warning(f"Hráč {player_id}: Nepodařilo se zpracovat odpověď")
                    else:
                        print_warning(f"Hráč {player_id}: Neočekávaný typ zprávy: {msg.type}")
                    
                    await asyncio.sleep(move_delay)
                
                print_success(f"Hráč {player_id}: Test dokončen")
    
    except aiohttp.ClientError as e:
        print_error(f"Hráč {player_id}: Chyba připojení - {e}")
    except Exception as e:
        print_error(f"Hráč {player_id}: Neočekávaná chyba - {e}")
    finally:
        print_info(f"Hráč {player_id}: Odpojil se")

async def run_stress_test(url, num_players=3, moves_per_player=20, move_delay=0.5, pattern="random"):
    """Spustí zátěžový test se zadaným počtem hráčů"""
    print_info(f"=== ZÁTĚŽOVÝ TEST - {num_players} HRÁČŮ ===")
    print_info(f"Server: {url}")
    print_info(f"Počet pohybů na hráče: {moves_per_player}")
    print_info(f"Zpoždění mezi pohyby: {move_delay}s")
    print_info(f"Vzor pohybu: {pattern}")
    print_info("Spouštím test...")
    
    # Vytvoříme tasky pro všechny hráče
    tasks = []
    for i in range(num_players):
        task = asyncio.create_task(
            player_session(i+1, url, moves_per_player, move_delay, pattern)
        )
        tasks.append(task)
        # Postupné připojování hráčů
        await asyncio.sleep(0.2)
    
    # Počkáme na dokončení všech tasků
    await asyncio.gather(*tasks)
    
    print_success("Test dokončen!")

async def latency_test(url, rounds=10):
    """Test latence serveru"""
    print_info(f"=== TEST LATENCE SERVERU ===")
    print_info(f"Server: {url}")
    
    latencies = []
    position = {"x": 100, "y": 100}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(url) as ws:
                print_success("Připojeno k serveru")
                
                for i in range(rounds):
                    start_time = time.time()
                    
                    # Odeslání pozice
                    await ws.send_json(position)
                    
                    # Čekání na odpověď
                    msg = await ws.receive()
                    
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        json.loads(msg.data)  # Jen ověříme, že odpověď je validní JSON
                        
                        end_time = time.time()
                        latency = (end_time - start_time) * 1000  # v milisekundách
                        latencies.append(latency)
                        
                        print_info(f"Kolo {i+1}: Latence {latency:.2f} ms")
                    else:
                        print_warning(f"Neočekávaný typ zprávy: {msg.type}")
                    
                    await asyncio.sleep(0.5)
                
                # Statistiky
                if latencies:
                    avg_latency = sum(latencies) / len(latencies)
                    min_latency = min(latencies)
                    max_latency = max(latencies)
                    
                    print_success("\nVýsledky testu latence:")
                    print_info(f"Průměrná latence: {avg_latency:.2f} ms")
                    print_info(f"Minimální latence: {min_latency:.2f} ms")
                    print_info(f"Maximální latence: {max_latency:.2f} ms")
                else:
                    print_warning("Nepodařilo se naměřit žádné hodnoty latence")
    
    except aiohttp.ClientError as e:
        print_error(f"Chyba připojení: {e}")
    except Exception as e:
        print_error(f"Neočekávaná chyba: {e}")

async def continuous_monitoring(url, interval=5, duration=60):
    """Dlouhodobé monitorování serveru"""
    print_info(f"=== DLOUHODOBÉ MONITOROVÁNÍ SERVERU ===")
    print_info(f"Server: {url}")
    print_info(f"Interval kontroly: {interval} sekund")
    print_info(f"Doba monitorování: {duration} sekund")
    
    start_time = time.time()
    end_time = start_time + duration
    check_count = 0
    success_count = 0
    
    position = {"x": 100, "y": 100}
    
    try:
        while time.time() < end_time:
            check_time = datetime.now().strftime("%H:%M:%S")
            check_count += 1
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(url, timeout=5) as ws:
                        await ws.send_json(position)
                        msg = await ws.receive(timeout=5)
                        
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            players = json.loads(msg.data)
                            success_count += 1
                            print_success(f"[{check_time}] Kontrola {check_count}: OK - {len(players)} hráčů online")
                        else:
                            print_warning(f"[{check_time}] Kontrola {check_count}: Neplatná odpověď - {msg.type}")
            
            except asyncio.TimeoutError:
                print_error(f"[{check_time}] Kontrola {check_count}: Timeout - server neodpovídá včas")
            except aiohttp.ClientError as e:
                print_error(f"[{check_time}] Kontrola {check_count}: Chyba připojení - {e}")
            except Exception as e:
                print_error(f"[{check_time}] Kontrola {check_count}: Chyba - {e}")
            
            # Čekání do dalšího intervalu
            await asyncio.sleep(interval)
        
        # Souhrn
        reliability = (success_count / check_count) * 100 if check_count > 0 else 0
        print_success("\nVýsledky monitorování:")
        print_info(f"Celkem kontrol: {check_count}")
        print_info(f"Úspěšných kontrol: {success_count}")
        print_info(f"Spolehlivost serveru: {reliability:.1f}%")
    
    except KeyboardInterrupt:
        print_warning("\nMonitorování přerušeno uživatelem")
        # Souhrn i při přerušení
        if check_count > 0:
            reliability = (success_count / check_count) * 100
            print_success("\nVýsledky monitorování:")
            print_info(f"Celkem kontrol: {check_count}")
            print_info(f"Úspěšných kontrol: {success_count}")
            print_info(f"Spolehlivost serveru: {reliability:.1f}%")

async def main():
    parser = argparse.ArgumentParser(description="WebSocket testovací nástroj pro herní server")
    parser.add_argument('--host', default="localhost", help="Adresa serveru")
    parser.add_argument('--port', type=int, default=5555, help="Port serveru")
    parser.add_argument('--test', choices=['basic', 'stress', 'latency', 'monitor', 'all'], 
                        default='basic', help="Typ testu")
    parser.add_argument('--players', type=int, default=3, help="Počet hráčů pro zátěžový test")
    parser.add_argument('--moves', type=int, default=20, help="Počet pohybů na hráče")
    parser.add_argument('--delay', type=float, default=0.5, help="Zpoždění mezi pohyby (sekundy)")
    parser.add_argument('--pattern', choices=['random', 'circle', 'square'], 
                        default='random', help="Vzor pohybu hráčů")
    parser.add_argument('--duration', type=int, default=60, 
                        help="Doba monitorování v sekundách")
    parser.add_argument('--interval', type=int, default=5, 
                        help="Interval kontrol při monitorování v sekundách")
    
    args = parser.parse_args()
    
    # Sestavení URL pro WebSocket
    # Pro lokální vývoj použijeme ws://, pro produkci wss://
    protocol = "ws"
    if args.host != "localhost" and args.host != "127.0.0.1":
        protocol = "wss"
    
    # Přidáme endpoint /ws na konec URL
    base_url = f"{protocol}://{args.host}"
    if args.port != 80 and args.port != 443 and (args.host == "localhost" or args.host == "127.0.0.1"):
        base_url += f":{args.port}"
    
    ws_url = f"{base_url}/ws"
    
    print_info(f"WebSocket URL: {ws_url}")
    
    if args.test == 'basic' or args.test == 'all':
        # Základní test s jedním hráčem
        await player_session(0, ws_url, args.moves, args.delay, args.pattern)
    
    if args.test == 'stress' or args.test == 'all':
        # Zátěžový test
        await run_stress_test(ws_url, args.players, args.moves, args.delay, args.pattern)
    
    if args.test == 'latency' or args.test == 'all':
        # Test latence
        await latency_test(ws_url)
    
    if args.test == 'monitor' or args.test == 'all':
        # Dlouhodobé monitorování
        await continuous_monitoring(ws_url, args.interval, args.duration)

if __name__ == "__main__":
    print_info("=== POKROČILÝ WEBSOCKET HERNÍ KLIENT - TEST ===")
    asyncio.run(main())
