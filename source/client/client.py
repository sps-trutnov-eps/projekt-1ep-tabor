import pygame
import asyncio
import aiohttp
import json
import random
import time

# Pro server hostovaný na Render.com použij:
SERVER_URL = "wss://projekt-1ep-tabor.onrender.com/ws"
# Pro lokální server použij:
# SERVER_URL = "ws://localhost:5555/ws"

WIDTH, HEIGHT = 800, 600

# Pygame inicializace
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Multiplayer Hra")
font = pygame.font.SysFont(None, 24)
clock = pygame.time.Clock()

# Barvy
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

# Globální proměnné
players = {}      # Data o hráčích ze serveru
players_interpolated = {}  # Data o hráčích pro vykreslení (interpolovaná)
players_prev = {}  # Předchozí pozice hráčů pro interpolaci
my_id = None      # ID našeho hráče přidělené serverem 
my_color = None   # Barva našeho hráče (náhodná)
connected = False
status = "Připojování..."
x, y = random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)  # Náhodná počáteční pozice
speed = 5
response_time = None  # Proměnná pro měření odezvy serveru
other_players_interpolation_factor = 0.2  # Faktor pro plynulou interpolaci ostatních hráčů
is_moving = False  # Sledování, zda se hráč právě hýbe (stisknuté klávesy)

# Pro synchronizaci i při neaktivitě hráče
last_update_time = 0
UPDATE_INTERVAL = 0.1  # Interval pro odeslání keep-alive zpráv v sekundách

# Generuj náhodnou barvu pro rozlišení různých instancí na stejném počítači
r = random.randint(100, 255)
g = random.randint(100, 255)
b = random.randint(100, 255)
my_color = (r, g, b)

# WebSocket komunikace a herní smyčka
async def game_loop():
    global players, players_interpolated, players_prev, connected, status
    global x, y, my_id, response_time, last_update_time, is_moving

    # Připojení k serveru
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(SERVER_URL) as ws:
                connected = True
                status = "Připojeno"
                print("Připojeno k serveru")

                # Počáteční odeslání pozice pro registraci
                await ws.send_json({"x": x, "y": y})
                last_update_time = time.time()

                # Hlavní herní smyčka
                running = True
                while running:
                    current_time = time.time()

                    # Zpracování událostí
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False

                    # Zpracování vstupů
                    keys = pygame.key.get_pressed()
                    moved = False

                    if keys[pygame.K_w] or keys[pygame.K_UP]:
                        y -= speed
                        moved = True
                    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                        y += speed
                        moved = True
                    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                        x -= speed
                        moved = True
                    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                        x += speed
                        moved = True

                    # Aktualizace stavu pohybu
                    is_moving = moved

                    # Omezení pohybu na herní plochu
                    x = max(0, min(WIDTH - 20, x))
                    y = max(0, min(HEIGHT - 20, y))

                    # Posílání dat serveru (při pohybu nebo po uplynutí intervalu)
                    if moved or current_time - last_update_time >= UPDATE_INTERVAL:
                        start_time = time.time()
                        await ws.send_json({"x": x, "y": y})
                        last_update_time = current_time
                    
                    # Přijímání dat od serveru (non-blocking)
                    try:
                        msg = await asyncio.wait_for(ws.receive(), 0.01)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            # Uložíme předchozí pozice hráčů pro interpolaci
                            players_prev = players_interpolated.copy() if players_interpolated else {}
                            
                            # Aktualizujeme data ze serveru
                            data = json.loads(msg.data)
                            players = data

                            # Měření odezvy serveru
                            if moved:
                                response_time = (time.time() - start_time) * 1000  # ms

                            # Zjištění našeho ID při prvním příjmu dat
                            if my_id is None:
                                for pid, pos in players.items():
                                    if isinstance(pos, list) or isinstance(pos, tuple):
                                        if abs(pos[0] - x) < 15 and abs(pos[1] - y) < 15:
                                            my_id = pid
                                            print(f"Moje ID: {my_id}")
                                            break
                                
                            # Aktualizace našeho hráče v datech (lokální přepsání)
                            if my_id:
                                players[my_id] = [x, y]
                                
                            # Inicializujeme interpolované pozice, pokud ještě nemáme předchozí data
                            if not players_prev:
                                players_prev = players.copy()
                                players_interpolated = players.copy()

                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            connected = False
                            status = "Spojení ukončeno"
                            break
                    except asyncio.TimeoutError:
                        # Timeout je očekávaný, pokračujeme ve hře
                        pass
                    
                    # Aktualizace stavu
                    if is_moving:
                        status = "Připojeno (pohyb)"
                    else:
                        status = "Připojeno (stabilní)"
                    
                    # Interpolace pozic ostatních hráčů
                    players_interpolated = {}
                    for player_id, pos in players.items():
                        if isinstance(pos, list) or isinstance(pos, tuple):
                            if player_id == my_id:
                                # Pro našeho hráče používáme přesně lokální pozici
                                players_interpolated[player_id] = [x, y]
                            elif player_id in players_prev and isinstance(players_prev[player_id], (list, tuple)):
                                # Pro ostatní hráče interpolace pro plynulý pohyb
                                prev_x, prev_y = players_prev[player_id]
                                new_x, new_y = pos
                                interpolated_x = prev_x + (new_x - prev_x) * other_players_interpolation_factor
                                interpolated_y = prev_y + (new_y - prev_y) * other_players_interpolation_factor
                                players_interpolated[player_id] = [interpolated_x, interpolated_y]
                            else:
                                # Pokud nemáme předchozí pozici, použijeme aktuální
                                players_interpolated[player_id] = pos

                    # Vykreslení
                    screen.fill(BLACK)

                    # Vykreslení hráčů s interpolovanými pozicemi
                    for player_id, pos in players_interpolated.items():
                        if isinstance(pos, list) or isinstance(pos, tuple):
                            if player_id == my_id:
                                # Náš hráč
                                pygame.draw.rect(screen, my_color, (x, y, 20, 20))
                                pygame.draw.rect(screen, WHITE, (x, y, 20, 20), 2)
                            else:
                                # Ostatní hráči
                                pygame.draw.rect(screen, GREEN, (pos[0], pos[1], 20, 20))

                    # Zobrazení stavu
                    status_color = GREEN if connected else RED
                    status_text = font.render(status, True, status_color)
                    players_text = font.render(f"Hráči: {len(players)}", True, WHITE)
                    my_id_text = font.render(f"Moje ID: {my_id}", True, my_color)

                    # Zobrazení odezvy serveru
                    if response_time is not None:
                        response_text = font.render(f"Odezva: {response_time:.2f} ms", True, YELLOW)
                        screen.blit(response_text, (10, 100))
                    
                    # FPS počítadlo
                    fps = clock.get_fps()
                    fps_text = font.render(f"FPS: {fps:.1f}", True, YELLOW)
                    screen.blit(fps_text, (10, 130))
                    
                    # Zobrazení pohybového stavu
                    move_text = font.render("Pohyb" if is_moving else "Stojím", True, YELLOW if is_moving else GREEN)
                    screen.blit(move_text, (10, 160))
                    
                    # Zobrazení pozice
                    pos_text = font.render(f"Pozice: {x:.1f}, {y:.1f}", True, WHITE)
                    screen.blit(pos_text, (10, 190))

                    screen.blit(status_text, (10, 10))
                    screen.blit(players_text, (10, 40))
                    screen.blit(my_id_text, (10, 70))

                    pygame.display.flip()
                    clock.tick(30)
                    
                    # Přidání malého zpoždění pro asyncio
                    await asyncio.sleep(0)

    except aiohttp.ClientError as e:
        connected = False
        status = f"Chyba: {str(e)}"
        print(f"Chyba připojení: {e}")
    except Exception as e:
        connected = False
        status = f"Chyba: {str(e)}"
        print(f"Neočekávaná chyba: {e}")

# Hlavní funkce
async def main():
    try:
        await game_loop()
    finally:
        pygame.quit()

# Spuštění hry
if __name__ == "__main__":
    asyncio.run(main())
