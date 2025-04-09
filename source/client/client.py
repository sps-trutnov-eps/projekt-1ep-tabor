import pygame
import asyncio
import aiohttp
import json
import random

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
BLUE = (0, 0, 255)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

# Globální proměnné
players = {}      # Data o hráčích
my_id = None      # ID našeho hráče přidělené serverem 
my_color = None   # Barva našeho hráče (náhodná)
connected = False
status = "Připojování..."
x, y = random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)  # Náhodná počáteční pozice
speed = 5

# Generuj náhodnou barvu pro rozlišení různých instancí na stejném počítači
r = random.randint(100, 255)
g = random.randint(100, 255)
b = random.randint(100, 255)
my_color = (r, g, b)

# WebSocket komunikace a herní smyčka
async def game_loop():
    global players, connected, status, x, y, my_id
    
    # Připojení k serveru
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(SERVER_URL) as ws:
                connected = True
                status = "Připojeno"
                print("Připojeno k serveru")
                
                # Počáteční odeslání pozice pro registraci
                await ws.send_json({"x": x, "y": y})
                
                # Hlavní herní smyčka
                running = True
                while running:
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
                    
                    # Omezení pohybu na herní plochu
                    x = max(0, min(WIDTH - 20, x))
                    y = max(0, min(HEIGHT - 20, y))
                    
                    # Posílání dat serveru, jen pokud se hráč pohnul
                    if moved:
                        await ws.send_json({"x": x, "y": y})
                    
                    # Přijímání dat od serveru (non-blocking)
                    try:
                        # Použití wait_for s timeoutem pro neblokující příjem
                        msg = await asyncio.wait_for(ws.receive(), 0.01)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            players = data
                            
                            # Zjištění našeho ID při prvním příjmu dat
                            if my_id is None:
                                # Najdeme své ID podle pozice
                                for pid, pos in players.items():
                                    if isinstance(pos, list) or isinstance(pos, tuple):
                                        if abs(pos[0] - x) < 5 and abs(pos[1] - y) < 5:
                                            my_id = pid
                                            print(f"Moje ID: {my_id}")
                                            break
                            
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            connected = False
                            status = "Spojení ukončeno"
                            break
                    except asyncio.TimeoutError:
                        # Timeout je očekávaný, pokračujeme ve hře
                        pass
                    
                    # Vykreslení
                    screen.fill(BLACK)
                    
                    # Vykreslení ostatních hráčů
                    for player_id, pos in players.items():
                        if isinstance(pos, list) or isinstance(pos, tuple):
                            # Barva podle toho, zda je to náš hráč nebo jiný
                            if player_id == my_id:
                                # Pokud je to náš hráč, použijeme svou barvu, která je pro tuto instanci unikátní
                                pygame.draw.rect(screen, my_color, (pos[0], pos[1], 20, 20))
                                # A ještě ohraničení, aby bylo jasné, který je náš
                                pygame.draw.rect(screen, WHITE, (pos[0], pos[1], 20, 20), 2)
                                
                                # Pro jistotu aktualizujeme svou pozici podle serveru
                                x, y = pos[0], pos[1]
                            else:
                                # Ostatní hráči jsou zelení
                                pygame.draw.rect(screen, GREEN, (pos[0], pos[1], 20, 20))
                    
                    # Zobrazení stavu
                    status_color = GREEN if connected else RED
                    status_text = font.render(status, True, status_color)
                    players_text = font.render(f"Hráči: {len(players)}", True, WHITE)
                    my_id_text = font.render(f"Moje ID: {my_id}", True, my_color)
                    
                    screen.blit(status_text, (10, 10))
                    screen.blit(players_text, (10, 40))
                    screen.blit(my_id_text, (10, 70))
                    
                    pygame.display.flip()
                    clock.tick(30)
                    await asyncio.sleep(0)  # Umožní asyncio zpracovat další úlohy
    
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
