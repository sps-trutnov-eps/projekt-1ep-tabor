import pygame
import asyncio
import aiohttp
import json
import random
import time
import sys
import os
import math
from scooter import Scooter

# Pro server hostovaný na Render.com použij:
SERVER_URL = "wss://projekt-1ep-tabor.onrender.com/ws"
# Pro lokální server použij:
# SERVER_URL = "ws://localhost:5555/ws"

# Inicializace Pygame
pygame.init()
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600  # Fixní velikost okna pro hru
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Multiplayer CTF Game")
font = pygame.font.SysFont(None, 24)
clock = pygame.time.Clock()

# Barvy
BLACK = (0, 0, 0)
DARK_GREEN = (0, 80, 0)
DARKER_GREEN = (0, 50, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

# Konstanty pro herní mapu
TILE_SIZE = 40
BOUNDARY_WIDTH = 5
MAP_WIDTH = 100
MAP_HEIGHT = 100
PLAYER_SIZE_MULTIPLIER = 2.5
PLAYER_SPEED = 4

# Weapons configuration
WEAPONS = {
    "Crossbow": {
        "image": "Crossbow_Gun.png",
        "scale": 0.355,
        "offset_x": 20,
        "offset_y": 10,
        "damage": 25,
        "cooldown": 30
    },
    "Rocket Launcher": {
        "image": "RocketLauncher_Gun.png",
        "scale": 0.2,
        "offset_x": 25,
        "offset_y": 15,
        "damage": 50,
        "cooldown": 60
    },
    "Shotgun": {
        "image": "Shotgun_Gun.png",
        "scale": 0.4,
        "offset_x": 20,
        "offset_y": 10,
        "damage": 35,
        "cooldown": 45
    },
    "Sniper": {
        "image": "Sniper_Gun.png",
        "scale": 0.2,
        "offset_x": 30,
        "offset_y": 10,
        "damage": 75,
        "cooldown": 90
    }
}

# Globální proměnné pro síťovou komunikaci
players = {}      # Data o hráčích ze serveru
players_interpolated = {}  # Data o hráčích pro vykreslení (interpolovaná)
players_prev = {}  # Předchozí pozice hráčů pro interpolaci
my_id = None      # ID našeho hráče přidělené serverem 
connected = False
status = "Připojování..."
response_time = None  # Proměnná pro měření odezvy serveru
other_players_interpolation_factor = 0.2  # Faktor pro plynulou interpolaci ostatních hráčů
is_moving = False  # Sledování, zda se hráč právě hýbe (stisknuté klávesy)

# Pro synchronizaci i při neaktivitě hráče
last_update_time = 0
UPDATE_INTERVAL = 0.1  # Interval pro odeslání keep-alive zpráv v sekundách

# Globální proměnné pro herní svět
images = []  # Seznam všech obrazových objektů na mapě
current_weapon_index = 0
weapon_names = list(WEAPONS.keys())
current_weapon = weapon_names[current_weapon_index]
weapon_cooldowns = {name: 0 for name in WEAPONS}
scooter = None
was_e_pressed = False

# Inicializace hráče
x = random.randint(50, SCREEN_WIDTH-50)  # Inicializace pro klienta
y = random.randint(50, SCREEN_HEIGHT-50)  # Inicializace pro klienta
player_x = MAP_WIDTH // 2 * TILE_SIZE + TILE_SIZE // 2  # Pro mapu
player_y = MAP_HEIGHT // 2 * TILE_SIZE + TILE_SIZE // 2  # Pro mapu
player_team = 2  # 2 = tým A, 3 = tým B
player_size = int(TILE_SIZE * PLAYER_SIZE_MULTIPLIER)
player_radius = player_size // 2
player_angle = 0  # Úhel natočení hráče (ve stupních)

# Generuj náhodnou barvu pro rozlišení různých instancí na stejném počítači
r = random.randint(100, 255)
g = random.randint(100, 255)
b = random.randint(100, 255)
my_color = (r, g, b)

# Vytvoření složky pro obrázky, pokud neexistuje
if not os.path.exists("images"):
    os.makedirs("images")

# Načtení textury hráče z gun folderu
player_texture = None
try:
    player_texture = pygame.image.load(os.path.join("images", "player.png")).convert_alpha()
    player_texture = pygame.transform.scale(player_texture, (player_size, player_size))
    print(f"Textura hráče úspěšně načtena z images/player.png (velikost: {player_size}x{player_size})")
except Exception as e:
    print(f"Chyba při načítání textury hráče: {e}")
    # Vytvoření výchozí textury hráče, pokud se nepodaří načíst obrázek
    player_surface = pygame.Surface((player_size, player_size), pygame.SRCALPHA)
    pygame.draw.circle(player_surface, RED, (player_size//2, player_size//2), player_size//2 - 2)
    player_texture = player_surface
    print("Použita výchozí textura hráče")

# Načítání zbraní
weapon_textures = {}
for name, weapon_info in WEAPONS.items():
    try:
        weapon_path = os.path.join("images", weapon_info["image"])
        original_texture = pygame.image.load(weapon_path).convert_alpha()
        
        # Calculate scaled dimensions
        scale = weapon_info["scale"]
        width = int(original_texture.get_width() * scale)
        height = int(original_texture.get_height() * scale)
        
        # Scale the weapon texture
        weapon_textures[name] = pygame.transform.scale(original_texture, (width, height))
        print(f"Zbraň '{name}' úspěšně načtena")
    except Exception as e:
        print(f"Chyba při načítání zbraně '{name}': {e}")
        # Create placeholder texture
        placeholder = pygame.Surface((40, 15), pygame.SRCALPHA)
        pygame.draw.rect(placeholder, (200, 200, 200), (0, 0, 40, 15))
        weapon_textures[name] = placeholder
        
# Projektily    
projectiles = []
PROJECTILE_SPEED = 10
PROJECTILE_LIFETIME = 60  # ve snímcích

# Funkce pro přidání PNG obrázku na mapu
def add_image(image_path, x, y, scale=1.0):
    try:
        original_image = pygame.image.load(image_path).convert_alpha()
        width = int(original_image.get_width() * scale)
        height = int(original_image.get_height() * scale)
        image = pygame.transform.scale(original_image, (width, height))
        hitbox = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, width, height)
        images.append({
            'x': x,
            'y': y,
            'image': image,
            'width': width,
            'height': height,
            'hitbox': hitbox
        })
        return True
    except Exception as e:
        print(f"Chyba při přidávání obrázku: {e}")
        return False

# Funkce pro kontrolu kolize s obrazovými objekty
def check_collision(x, y, radius):
    player_hitbox = pygame.Rect(x - radius // 2, y - radius // 2, radius, radius)
   
    for img in images:
        if abs(img['x'] * TILE_SIZE - x) < TILE_SIZE * 2 and abs(img['y'] * TILE_SIZE - y) < TILE_SIZE * 2:
            if img['hitbox'].colliderect(player_hitbox):
                return True
    return False

# Funkce pro pohyb hráče v herním světě
def move_player(dx, dy):
    global player_x, player_y, x, y
    new_x = player_x + dx
    new_y = player_y + dy
    tile_x = int(new_x // TILE_SIZE)
    tile_y = int(new_y // TILE_SIZE)
    # Kontrola hranic mapy
    if (tile_x < BOUNDARY_WIDTH or tile_x >= MAP_WIDTH - BOUNDARY_WIDTH or
        tile_y < BOUNDARY_WIDTH or tile_y >= MAP_HEIGHT - BOUNDARY_WIDTH):
        return False
    # Kontrola kolize s objekty
    if check_collision(new_x, new_y, player_radius):
        return False
    player_x = new_x
    player_y = new_y
    # Aktualizace pozice pro síťovou komunikaci (relativní k rozměrům okna)
    x = (player_x / (MAP_WIDTH * TILE_SIZE)) * SCREEN_WIDTH
    y = (player_y / (MAP_HEIGHT * TILE_SIZE)) * SCREEN_HEIGHT
    return True

def move_player_or_scooter(dx, dy, is_scooter=False):
    global player_x, player_y, x, y, scooter
    
    if is_scooter and scooter:
        # Pohyb koloběžky
        new_x = scooter.x + dx
        new_y = scooter.y + dy
        
        # Kontrola hranic mapy
        tile_x = int(new_x // TILE_SIZE)
        tile_y = int(new_y // TILE_SIZE)
        
        if (tile_x < BOUNDARY_WIDTH or tile_x >= MAP_WIDTH - BOUNDARY_WIDTH or
            tile_y < BOUNDARY_WIDTH or tile_y >= MAP_HEIGHT - BOUNDARY_WIDTH):
            return False
        
        # Dočasně nastavíme pozici pro kontrolu kolize
        old_x, old_y = scooter.x, scooter.y
        scooter.x, scooter.y = new_x, new_y
        
        if scooter.check_collision_with_images():
            scooter.x, scooter.y = old_x, old_y  # Vrátíme zpět
            return False
        
        # Aktualizace pozice hráče, pokud je na koloběžce
        if scooter.is_player_on:
            player_x = scooter.x
            player_y = scooter.y
            
            # Aktualizace pozice pro síťovou komunikaci
            x = (player_x / (MAP_WIDTH * TILE_SIZE)) * SCREEN_WIDTH
            y = (player_y / (MAP_HEIGHT * TILE_SIZE)) * SCREEN_HEIGHT
        
        return True
    else:
        # Původní pohyb hráče
        return move_player(dx, dy)

# Funkce pro výpočet tmavosti hranice
def vypocitej_tmavost_hranice(x, y):
    vzdalenost_od_okraje_x = min(x, MAP_WIDTH - 1 - x)
    vzdalenost_od_okraje_y = min(y, MAP_HEIGHT - 1 - y)
    vzdalenost_od_okraje = min(vzdalenost_od_okraje_x, vzdalenost_od_okraje_y)
   
    hranice_prechodu = BOUNDARY_WIDTH + 5
   
    if vzdalenost_od_okraje >= hranice_prechodu:
        return DARK_GREEN
    elif BOUNDARY_WIDTH <= vzdalenost_od_okraje < hranice_prechodu:
        pomer = (vzdalenost_od_okraje - BOUNDARY_WIDTH) / (hranice_prechodu - BOUNDARY_WIDTH)
        g_hodnota = int(50 + pomer * (80 - 50))
        return (0, g_hodnota, 0)
    else:
        return DARKER_GREEN

# Funkce pro vykreslení mapy
def draw_map(screen, camera_x, camera_y):
    screen.fill(DARKER_GREEN)
   
    viditelnych_dlazdic_x = (SCREEN_WIDTH // TILE_SIZE) + 10
    viditelnych_dlazdic_y = (SCREEN_HEIGHT // TILE_SIZE) + 10
   
    kamera_tile_x = camera_x // TILE_SIZE
    kamera_tile_y = camera_y // TILE_SIZE
   
    start_x = max(0, int(kamera_tile_x - viditelnych_dlazdic_x))
    end_x = min(MAP_WIDTH, int(kamera_tile_x + viditelnych_dlazdic_x))
    start_y = max(0, int(kamera_tile_y - viditelnych_dlazdic_y))
    end_y = min(MAP_HEIGHT, int(kamera_tile_y + viditelnych_dlazdic_y))
   
    # Vykreslení dlaždic
    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            screen_x = (x * TILE_SIZE - camera_x) + SCREEN_WIDTH // 2
            screen_y = (y * TILE_SIZE - camera_y) + SCREEN_HEIGHT // 2
           
            if -TILE_SIZE <= screen_x <= SCREEN_WIDTH+TILE_SIZE and -TILE_SIZE <= screen_y <= SCREEN_HEIGHT+TILE_SIZE:
                barva = vypocitej_tmavost_hranice(x, y)
                pygame.draw.rect(screen, barva, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
   
    # Vykreslení obrazových objektů
    for img in images:
        rel_x = img['x'] - kamera_tile_x
        rel_y = img['y'] - kamera_tile_y
       
        if abs(rel_x) <= viditelnych_dlazdic_x and abs(rel_y) <= viditelnych_dlazdic_y:
            screen_x = (img['x'] * TILE_SIZE - camera_x) + SCREEN_WIDTH // 2
            screen_y = (img['y'] * TILE_SIZE - camera_y) + SCREEN_HEIGHT // 2
            screen.blit(img['image'], (int(screen_x), int(screen_y)))

# Funkce pro vykreslení hráče a zbraně
def draw_player(screen, offset_x, offset_y):
    screen_x = int(player_x - offset_x + SCREEN_WIDTH // 2)
    screen_y = int(player_y - offset_y + SCREEN_HEIGHT // 2)
   
    if player_texture:
        # Vytvoření kopie textury pro rotaci
        texture_to_draw = player_texture
        
        # Pro tým B případně obarvíme texturu do modra (místo výchozí červené)
        if player_team == 3:
            texture_to_draw = player_texture.copy()
            texture_to_draw.fill(BLUE, special_flags=pygame.BLEND_RGBA_MULT)
        
        # Rotace textury hráče podle směru k myši
        rotated_texture = pygame.transform.rotate(texture_to_draw, -player_angle)
        
        # Úprava pozice po rotaci (aby byl střed rotace ve středu hráče)
        rot_rect = rotated_texture.get_rect(center=(screen_x, screen_y))
        
        # Vykreslení rotované textury
        screen.blit(rotated_texture, rot_rect.topleft)
        
        # Vykreslení aktuální zbraně
        if current_weapon in weapon_textures:
            # Get weapon information
            weapon_info = WEAPONS[current_weapon]
            weapon_texture = weapon_textures[current_weapon]
            
            # Calculate weapon position relative to player
            angle_rad = math.radians(player_angle - 90)  # Convert to radians and adjust for rotation
            offset_distance = weapon_info["offset_x"]
            
            # Calculate offset position (perpendicular to player angle)
            weapon_offset_x = math.cos(angle_rad) * offset_distance
            weapon_offset_y = math.sin(angle_rad) * offset_distance
            
            # Position for the weapon
            weapon_x = screen_x + weapon_offset_x
            weapon_y = screen_y + weapon_offset_y
            
            # Rotate weapon texture to match player angle
            rotated_weapon = pygame.transform.rotate(weapon_texture, -player_angle)
            weapon_rect = rotated_weapon.get_rect(center=(weapon_x, weapon_y))
            
            # Draw weapon
            screen.blit(rotated_weapon, weapon_rect.topleft)
    else:
        # Záloha - kruh pro případ, že by textura nebyla k dispozici
        color = RED if player_team == 2 else BLUE
        pygame.draw.circle(screen, color, (screen_x, screen_y), player_radius)

# Funkce pro vykreslení ostatních hráčů z multiplayer
def draw_other_players(screen, camera_x, camera_y):
    for player_id, pos in players_interpolated.items():
        if isinstance(pos, list) or isinstance(pos, tuple):
            if player_id != my_id:  # Kreslíme jen ostatní hráče
                # Konverze souřadnic z relativních (0-800, 0-600) na mapové
                map_x = (pos[0] / SCREEN_WIDTH) * (MAP_WIDTH * TILE_SIZE)
                map_y = (pos[1] / SCREEN_HEIGHT) * (MAP_HEIGHT * TILE_SIZE)
                
                # Přepočet na obrazovku s kamerou
                screen_x = int(map_x - camera_x + SCREEN_WIDTH // 2)
                screen_y = int(map_y - camera_y + SCREEN_HEIGHT // 2)
                
                # Vykreslení ostatních hráčů
                pygame.draw.rect(screen, GREEN, (screen_x - player_radius//2, screen_y - player_radius//2, player_radius, player_radius))

# Funkce pro vykreslení UI
def draw_ui(screen, font):
    # Vykreslení zbraně v levém dolním rohu
    weapon_info_bg = pygame.Rect(10, SCREEN_HEIGHT - 60, 300, 50)
    pygame.draw.rect(screen, (0, 0, 0, 128), weapon_info_bg)
    
    # Zobrazení jména zbraně
    weapon_text = font.render(f"Weapon: {current_weapon}", True, WHITE)
    screen.blit(weapon_text, (20, SCREEN_HEIGHT - 50))
    
    # Vykreslení cooldownu zbraně
    cooldown = weapon_cooldowns[current_weapon]
    cooldown_max = WEAPONS[current_weapon]["cooldown"]
    cooldown_text = font.render(f"Cooldown: {cooldown}/{cooldown_max}", True, WHITE)
    screen.blit(cooldown_text, (20, SCREEN_HEIGHT - 30))
    
    # Instrukce pro přepínání zbraní
    instructions = font.render("Mouse Wheel to change weapons, LMB to shoot", True, WHITE)
    screen.blit(instructions, (400, 550))    
    # Network status
    status_color = GREEN if connected else RED
    status_text = font.render(status, True, status_color)
    players_text = font.render(f"Hráči: {len(players)}", True, WHITE)
    my_id_text = font.render(f"Moje ID: {my_id}", True, my_color)
    
    # Zobrazení odezvy serveru
    if response_time is not None:
        response_text = font.render(f"Odezva: {response_time:.2f} ms", True, YELLOW)
        screen.blit(response_text, (10, 100))
    
    # Zobrazení pohybového stavu
    move_text = font.render("Pohyb" if is_moving else "Stojím", True, YELLOW if is_moving else GREEN)
    screen.blit(move_text, (600, 40))
    
    # Zobrazení pozice
    pos_text = font.render(f"Pozice: {player_x:.1f}, {player_y:.1f}", True, WHITE)
    screen.blit(pos_text, (600, 70))

    screen.blit(status_text, (10, 10))
    screen.blit(players_text, (10, 40))
    screen.blit(my_id_text, (10, 70))

# Funkce pro získání aktuální pozice hráče v dlaždicích
def get_player_tile_position():
    return int(player_x // TILE_SIZE), int(player_y // TILE_SIZE)

# Funkce pro výpočet úhlu mezi hráčem a kurzorem myši
def calculate_angle_to_mouse(player_screen_x, player_screen_y):
    mouse_x, mouse_y = pygame.mouse.get_pos()
    dx = mouse_x - player_screen_x
    dy = mouse_y - player_screen_y
    angle = math.degrees(math.atan2(dy, dx)) + 90
    return angle

# Funkce pro střelbu ze zbraně
def shoot(weapon_name):
    global weapon_cooldowns
    
    # Kontrola cooldownu
    if weapon_cooldowns[weapon_name] > 0:
        return False
    
    # Nastavení cooldownu zbraně
    weapon_cooldowns[weapon_name] = WEAPONS[weapon_name]["cooldown"]
    
    # Vytvoření projektilu
    angle_rad = math.radians(player_angle - 90)
    dx = math.cos(angle_rad)
    dy = math.sin(angle_rad)

    projectile = {
        "x": player_x,
        "y": player_y,
        "dx": dx * PROJECTILE_SPEED,
        "dy": dy * PROJECTILE_SPEED,
        "lifetime": PROJECTILE_LIFETIME,
        "color": YELLOW,
        "radius": 5
    }
    projectiles.append(projectile)
    
    # Zde by mohla být implementace střelby s efekty, projektily, atd.
    print(f"Střelba ze zbraně: {weapon_name}, poškození: {WEAPONS[weapon_name]['damage']}")
    
    return True

# Funkce pro změnu zbraně
def change_weapon(direction):
    global current_weapon_index, current_weapon
    
    current_weapon_index = (current_weapon_index + direction) % len(weapon_names)
    current_weapon = weapon_names[current_weapon_index]
    print(f"Zbraň změněna na: {current_weapon}")

# WebSocket komunikace a herní smyčka
async def game_loop():
    global players, players_interpolated, players_prev, connected, status
    global x, y, player_x, player_y, my_id, response_time, last_update_time, is_moving
    global player_angle, current_weapon, weapon_cooldowns, projectiles
    
    scooter = Scooter(
    MAP_WIDTH // 2 * TILE_SIZE + 100,  # Pozice vedle středu mapy
    MAP_HEIGHT // 2 * TILE_SIZE + 100
)

    shoot_this_frame = False  # Příznak pro odeslání projektilu

    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(SERVER_URL) as ws:
                connected = True
                status = "Připojeno"
                print("Připojeno k serveru")

                await ws.send_json({"x": x, "y": y})
                last_update_time = time.time()

                running = True
                while running:
                    current_time = time.time()
                    shoot_this_frame = False

                    for event in pygame.event.get():
                        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                            running = False
                        elif event.type == pygame.KEYDOWN and event.key == pygame.K_t:
                            player_tile_x, player_tile_y = get_player_tile_position()
                            add_image("images/tree1.png", player_tile_x + 2, player_tile_y + 2, 2.0)
                        elif event.type == pygame.KEYUP:
                            if event.key == pygame.K_e:
                                was_e_pressed = False
                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            if event.button == 1:
                                if shoot(current_weapon):
                                    shoot_this_frame = True
                            elif event.button == 4:
                                change_weapon(1)
                            elif event.button == 5:
                                change_weapon(-1)

                    keys = pygame.key.get_pressed()
                    dx, dy = 0, 0
                    
                    current_e_pressed = keys[pygame.K_e]
                    if current_e_pressed and not was_e_pressed:
                        if scooter:
                            # Výpočet vzdálenosti mezi hráčem a koloběžkou
                            distance = math.sqrt((player_x - scooter.x)**2 + (player_y - scooter.y)**2)
                            
                            if not scooter.is_player_on and distance < 60:
                                # Nasednout na koloběžku
                                scooter.is_player_on = True
                                scooter.x = player_x
                                scooter.y = player_y
                                scooter.direction = player_angle
                                print("Nasedli jste na koloběžku!")
                            elif scooter.is_player_on:
                                # Sesednout z koloběžky
                                scooter.is_player_on = False
                                # Posun hráče mírně od koloběžky
                                offset_x = math.cos(math.radians(player_angle)) * 40
                                offset_y = math.sin(math.radians(player_angle)) * 40
                                player_x += offset_x
                                player_y += offset_y
                                
                                # Aktualizace pozice pro síť
                                x = (player_x / (MAP_WIDTH * TILE_SIZE)) * SCREEN_WIDTH
                                y = (player_y / (MAP_HEIGHT * TILE_SIZE)) * SCREEN_HEIGHT
                                print("Sesedli jste z koloběžky!")
                    was_e_pressed = current_e_pressed
                    

                    if scooter and scooter.is_player_on:
                        # Pohyb na koloběžce - jiné ovládání
                        if keys[pygame.K_w] or keys[pygame.K_UP]:
                            # Dopředu podle směru koloběžky
                            dx = math.cos(math.radians(scooter.direction)) * scooter.speed
                            dy = math.sin(math.radians(scooter.direction)) * scooter.speed
                        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                            # Dozadu podle směru koloběžky
                            dx = -math.cos(math.radians(scooter.direction)) * (scooter.speed * 0.5)
                            dy = -math.sin(math.radians(scooter.direction)) * (scooter.speed * 0.5)
                        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                            # Zatáčení vlevo
                            scooter.direction = (scooter.direction - 4) % 360
                        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                            # Zatáčení vpravo
                            scooter.direction = (scooter.direction + 4) % 360
                        
                        # Aktualizace úhlu hráče podle koloběžky
                        player_angle = scooter.direction
                        
                        # Provedení pohybu koloběžky
                        if dx != 0 or dy != 0:
                            moved = move_player_or_scooter(dx, dy, is_scooter=True)
                            is_moving = moved
                        else:
                            is_moving = False
                    else:
                        # Normální pohyb hráče
                        if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= PLAYER_SPEED
                        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += PLAYER_SPEED
                        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= PLAYER_SPEED
                        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += PLAYER_SPEED

                        # Diagonální pohyb normalizujeme
                        if dx != 0 and dy != 0:
                            dx *= 0.7071
                            dy *= 0.7071

                        # Aktualizace stavu pohybu
                        moved = (dx != 0 or dy != 0)

                        # Provedení pohybu
                        if moved:
                            move_player_or_scooter(dx, dy, is_scooter=False)

                    player_angle = calculate_angle_to_mouse(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

                    for weapon in weapon_cooldowns:
                        if weapon_cooldowns[weapon] > 0:
                            weapon_cooldowns[weapon] -= 1

                    # Aktualizace projektilů
                    for p in list(projectiles):
                        p["x"] += p["dx"]
                        p["y"] += p["dy"]
                        p["lifetime"] -= 1
                        if p["lifetime"] <= 0:
                            projectiles.remove(p)

                    # Posílání pozice a případně projektilu
                    if is_moving or shoot_this_frame or current_time - last_update_time >= UPDATE_INTERVAL:
                        start_time = time.time()
                        message = {"x": x, "y": y}

                        if shoot_this_frame and len(projectiles) > 0:
                            last = projectiles[-1]
                            message["projectile"] = {
                                "x": last["x"],
                                "y": last["y"],
                                "dx": last["dx"],
                                "dy": last["dy"],
                                "color": list(last["color"])
                            }

                        await ws.send_json(message)
                        last_update_time = current_time
                        shoot_this_frame = False

                    # Příjem dat ze serveru
                    try:
                        msg = await asyncio.wait_for(ws.receive(), 0.01)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)

                            # Zpracování broadcastu projektilu od jiných hráčů
                            if "projectile_broadcast" in data:
                                p = data["projectile_broadcast"]
                                projectile = {
                                    "x": p["x"],
                                    "y": p["y"],
                                    "dx": p["dx"],
                                    "dy": p["dy"],
                                    "lifetime": PROJECTILE_LIFETIME,
                                    "color": tuple(p["color"]),
                                    "radius": 6
                                }
                                projectiles.append(projectile)
                                continue

                            # Zpracování pozic hráčů
                            players_prev = players_interpolated.copy() if players_interpolated else {}
                            players = data

                            if is_moving:
                                response_time = (time.time() - start_time) * 1000

                            if my_id is None:
                                for pid, pos in players.items():
                                    if isinstance(pos, list) and abs(pos[0] - x) < 15 and abs(pos[1] - y) < 15:
                                        my_id = pid
                                        print(f"Moje ID: {my_id}")
                                        break

                            if my_id:
                                players[my_id] = [x, y]

                            if not players_prev:
                                players_prev = players.copy()
                                players_interpolated = players.copy()

                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            connected = False
                            status = "Spojení ukončeno"
                            break
                    except asyncio.TimeoutError:
                        pass

                    status = "Připojeno (pohyb)" if is_moving else "Připojeno (stabilní)"

                    # Interpolace
                    players_interpolated = {}
                    for player_id, pos in players.items():
                        if isinstance(pos, list):
                            if player_id == my_id:
                                players_interpolated[player_id] = [x, y]
                            elif player_id in players_prev:
                                prev_x, prev_y = players_prev[player_id]
                                new_x, new_y = pos
                                interp_x = prev_x + (new_x - prev_x) * other_players_interpolation_factor
                                interp_y = prev_y + (new_y - prev_y) * other_players_interpolation_factor
                                players_interpolated[player_id] = [interp_x, interp_y]
                            else:
                                players_interpolated[player_id] = pos

                    draw_map(screen, player_x, player_y)
                    
                    if scooter:
                        scooter.draw(screen, player_x, player_y)
                        
                    draw_player(screen, player_x, player_y)
                    draw_other_players(screen, player_x, player_y)

                    # Projektily
                    for p in projectiles:
                        screen_x = int(p["x"] - player_x + SCREEN_WIDTH // 2)
                        screen_y = int(p["y"] - player_y + SCREEN_HEIGHT // 2)
                        pygame.draw.circle(screen, p["color"], (screen_x, screen_y), p["radius"])

                    draw_ui(screen, font)
                    
                    # FPS počítadlo
                    fps = clock.get_fps()
                    fps_text = font.render(f"FPS: {fps:.1f}", True, YELLOW)
                    screen.blit(fps_text, (600, 10))

                    pygame.display.flip()
                    clock.tick(60)
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