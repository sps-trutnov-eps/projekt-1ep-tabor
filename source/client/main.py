import pygame
import asyncio
import aiohttp
import json
import random
import time
import sys
import os
import math
from items.medkit import *

# Pro server hostovaný na Render.com použij:
SERVER_URL = "wss://projekt-1ep-tabor.onrender.com/ws"
# Pro lokální server použij:
# SERVER_URL = "ws://localhost:5555/ws"

# Inicializace Pygame
pygame.init()
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600  # Fixní velikost okna pro hru
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Multiplayer CTF Game with Catastrophes")
font = pygame.font.SysFont(None, 24)
big_font = pygame.font.SysFont(None, 36) # Pro text katastrofy
clock = pygame.time.Clock()
flag_taken = False
flag_px = 600
flag_py = 3300
blue_flag_taken = False
blue_flag_px = 3300
blue_flag_py = 600

# Barvy
BLACK = (0, 0, 0)
DARK_GREEN = (0, 80, 0)
DARKER_GREEN = (0, 50, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

# --- Barvy týmů ---
BABY_BLUE = (137, 207, 240)
BABY_PINK = (255, 182, 193)
TEAM_COLORS = [BABY_BLUE, BABY_PINK]
TEAM_NAMES = ["Modrý tým", "Růžový tým"]

class PowerUp:
    def __init__(self, x, y, image_path, effect_type, duration = 20):
        self.x = x
        self.y = y
        try:    
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
        except:
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.image.fill((255, 255, 0))
        
        self.rect = self.image.get_rect(center=(x, y))
        self.effect_type = effect_type
        self.duration = duration
        self.active = True
    
    def draw(self, screen, camera_x, camera_y):
        if not self.active:
            return
        screen_x = int(self.x - camera_x + SCREEN_WIDTH // 2)
        screen_y = int(self.y - camera_y + SCREEN_WIDTH // 2)
        screen.blit(self.image, (screen_x - TILE_SIZE // 2, screen_y - TILE_SIZE // 2))
    
    
# Konstanty pro herní mapu
TILE_SIZE = 40
BOUNDARY_WIDTH = 5
MAP_WIDTH = 100
MAP_HEIGHT = 100
PLAYER_SIZE_MULTIPLIER = 2.5
BASE_SPEED = 4
PLAYER_SPEED = BASE_SPEED

# Weapons configuration
WEAPONS = {
    "Crossbow": {
        "image": "Crossbow_Gun.png",
        "scale": 0.355,
        "offset_x": 20,
        "offset_y": 10,
        "damage": 25,
        "cooldown": 30,
        "projectile_speed": 8,
        "projectile_lifetime": 80,
        "projectile_size": 4,
        "projectile_color": (255, 255, 0)  # Yellow
    },
    "Rocket Launcher": {
        "image": "RocketLauncher_Gun.png",
        "scale": 0.2,
        "offset_x": 25,
        "offset_y": 15,
        "damage": 50,
        "cooldown": 60,
        "projectile_speed": 6,
        "projectile_lifetime": 100,
        "projectile_size": 11,
        "projectile_color": (255, 100, 0)  # Orange
    },
    "Shotgun": {
        "image": "Shotgun_Gun.png",
        "scale": 0.4,
        "offset_x": 20,
        "offset_y": 10,
        "damage": 35,
        "cooldown": 45,
        "projectile_speed": 12,
        "projectile_lifetime": 40,
        "projectile_size": 6,
        "projectile_color": (255, 255, 255)  # White
    },
    "Sniper": {
        "image": "Sniper_Gun.png",
        "scale": 0.2,
        "offset_x": 30,
        "offset_y": 10,
        "damage": 75,
        "cooldown": 90,
        "projectile_speed": 15,
        "projectile_lifetime": 120,
        "projectile_size": 3,
        "projectile_color": (0, 255, 255)  # Cyan
    }
}


# Globální proměnné pro síťovou komunikaci
players = {}      # Data o hráčích ze serveru
players_interpolated = {}  # Data o hráčích pro vykreslení (interpolovaná)
players_prev = {}  # Předchozí pozice hráčů pro interpolaci
my_id = None      # ID našeho hráče přidělené serverem
holding_flag = False
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
medkit_amount = 5 # celkový počet medkitů na mapě
power_ups = []
sprint_active = False
sprint_timer = 0

# Inicializace hráče
x = random.randint(50, SCREEN_WIDTH-50)  # Inicializace pro klienta
y = random.randint(50, SCREEN_HEIGHT-50)  # Inicializace pro klienta
player_x = MAP_WIDTH // 2 * TILE_SIZE + TILE_SIZE // 2  # Pro mapu
player_y = MAP_HEIGHT // 2 * TILE_SIZE + TILE_SIZE // 2  # Pro mapu
player_team = 2  # 2 = tým A, 3 = tým B
player_size = int(TILE_SIZE * PLAYER_SIZE_MULTIPLIER)
player_radius = player_size // 2
player_angle = 0  # Úhel natočení hráče (ve stupních)
player_health = 100
max_player_health = 100
player_alive = True
players_health = {}

# Generuj náhodnou barvu pro rozlišení různých instancí na stejném počítači
r = random.randint(100, 255)
g = random.randint(100, 255)
b = random.randint(100, 255)
my_color = (r, g, b) # Tato my_color je globální

# --- Globální proměnné pro katastrofy ---
active_catastrophe = None
catastrophe_start_time = 0.0
catastrophe_duration = 10.0  # Délka katastrofy v sekundách
last_catastrophe_trigger_time = 0.0 # Pro automatické spouštění
catastrophe_interval = 120.0  # Interval pro automatické spuštění v sekundách (2 minuty)
# Lze nastavit na menší hodnotu pro častější testování, např. 20.0 pro 20 sekund
possible_catastrophes = ["Zemětřesení", "Tornádo"]
screen_shake_offset = (0, 0) # (dx, dy) pro třesení obrazovky
# --- Konec globálních proměnných pro katastrofy ---

# Vytvoření složky pro obrázky, pokud neexistuje
if not os.path.exists("images"):
    os.makedirs("images")

# Načtení textury hráče z gun folderu
player_texture = None
try:
    player_texture_path = os.path.join("images", "player.png")
    if os.path.exists(player_texture_path):
        player_texture = pygame.image.load(player_texture_path).convert_alpha()
        player_texture = pygame.transform.scale(player_texture, (player_size, player_size))
        print(f"Textura hráče úspěšně načtena z {player_texture_path} (velikost: {player_size}x{player_size})")
    else:
        print(f"Soubor textury hráče nenalezen: {player_texture_path}")
        raise FileNotFoundError # Vyvolá výjimku, aby se chytla níže a vytvořil se placeholder
except Exception as e:
    print(f"Chyba při načítání textury hráče ({e}), vytvářím placeholder.")
    player_surface = pygame.Surface((player_size, player_size), pygame.SRCALPHA)
    pygame.draw.circle(player_surface, RED, (player_size//2, player_size//2), player_size//2 - 2)
    pygame.draw.line(player_surface, WHITE, (player_size//2, 2), (player_size//2, player_size//4), 3) # Ukazovátko
    player_texture = player_surface
    print("Použita výchozí textura hráče (placeholder).")

CHARACTER_SKINS = {
    "Crossbow": "medic.png",
    "Rocket Launcher": "soldier.png",
    "Shotgun": "scout.png",
    "Sniper": "sniper.png"
}

SKIN_TEXTURES = {}
for weapon in weapon_names:
    img_name = CHARACTER_SKINS.get(weapon, "player.png")  # <--- USE CLASS IMAGE!
    path = os.path.join("images", img_name)
    try:
        SKIN_TEXTURES[weapon] = pygame.transform.scale(
            pygame.image.load(path).convert_alpha(), (player_size, player_size)
        )
        print(f'Loaded CHARACTER skin for {weapon} from {path}')
    except Exception as e:
        print(f'Could not load CHARACTER skin for {weapon} from {path}: {e}')
        SKIN_TEXTURES[weapon] = player_texture  # fallback to default player texture

CLASS_MAX_HP = {
    "Sniper": 100,
    "Crossbow": 125,           # Medic
    "Shotgun": 150,            # Scout
    "Rocket Launcher": 150     # Soldier
}

# Načítání zbraní
weapon_textures = {}
for name, weapon_info in WEAPONS.items():
    try:
        weapon_path = os.path.join("images", weapon_info["image"])
        if os.path.exists(weapon_path):
            original_texture = pygame.image.load(weapon_path).convert_alpha()
            scale = weapon_info["scale"]
            width = int(original_texture.get_width() * scale)
            height = int(original_texture.get_height() * scale)
            weapon_textures[name] = pygame.transform.scale(original_texture, (width, height))
            print(f"Zbraň '{name}' úspěšně načtena z {weapon_path}")
        else:
            print(f"Soubor obrázku pro zbraň '{name}' nenalezen: {weapon_path}")
            raise FileNotFoundError # Vyvolá výjimku pro placeholder
    except Exception as e:
        print(f"Chyba při načítání zbraně '{name}' ({e}), vytvářím placeholder.")
        placeholder_width = 40 * weapon_info.get("scale", 0.4) # Placeholder scale
        placeholder_height = 15 * weapon_info.get("scale", 0.4)
        placeholder = pygame.Surface((int(placeholder_width), int(placeholder_height)), pygame.SRCALPHA)
        pygame.draw.rect(placeholder, (200, 200, 200), (0, 0, int(placeholder_width), int(placeholder_height)))
        weapon_textures[name] = placeholder
        print(f"Použit placeholder pro zbraň '{name}'.")


# Projektily
projectiles = []
# Default values, individual weapons override these
# PROJECTILE_SPEED = 10
# PROJECTILE_LIFETIME = 60

def add_image(image_path, x_tile, y_tile, scale=1.0):
    """Přidá obrázek na mapu na dané dlaždicové souřadnice."""
    try:
        full_image_path = os.path.join("images", image_path)
        if not os.path.exists(full_image_path):
            print(f"Soubor obrázku pro přidání nenalezen: {full_image_path}")
            # Vytvoření jednoduchého placeholderu pro chybějící obrázek stromu
            placeholder_img = pygame.Surface((int(TILE_SIZE * scale), int(TILE_SIZE * 1.5 * scale)), pygame.SRCALPHA)
            placeholder_img.fill((0,0,0,0)) # Transparentní
            pygame.draw.rect(placeholder_img, (139,69,19), (0, int(TILE_SIZE*0.5*scale), int(TILE_SIZE*0.2*scale), int(TILE_SIZE*scale))) # Kmen
            pygame.draw.circle(placeholder_img, (34,139,34), (int(TILE_SIZE*0.1*scale), int(TILE_SIZE*0.5*scale)), int(TILE_SIZE*0.4*scale) ) # Koruna
            original_image = placeholder_img
            print(f"Použit placeholder pro {image_path}")
        else:
            original_image = pygame.image.load(full_image_path).convert_alpha()

        width = int(original_image.get_width() * scale)
        height = int(original_image.get_height() * scale)
        scaled_image = pygame.transform.scale(original_image, (width, height))
        
        # Hitbox je v mapových souřadnicích (pixely)
        hitbox = pygame.Rect(x_tile * TILE_SIZE, y_tile * TILE_SIZE, width, height)
        
        images.append({
            'x_tile': x_tile, # Dlaždicová pozice X
            'y_tile': y_tile, # Dlaždicová pozice Y
            'image': scaled_image,
            'width_px': width, # Šířka v pixelech
            'height_px': height, # Výška v pixelech
            'hitbox': hitbox # Hitbox v mapových souřadnicích
        })
        print(f"Obrázek {image_path} přidán na [{x_tile},{y_tile}] s hitboxem {hitbox}")
        return True
    except Exception as e:
        print(f"Chyba při přidávání obrázku '{image_path}': {e}")
        return False

def check_collision(current_player_x_map, current_player_y_map, player_rad):
    """Kontroluje kolizi hráče s objekty na mapě."""
    # Hitbox hráče je kruh, pro jednoduchost použijeme čtvercový Rect
    player_hit_rect = pygame.Rect(current_player_x_map - player_rad,
                                  current_player_y_map - player_rad,
                                  player_rad * 2, player_rad * 2)
    for img_obj in images:
        # img_obj['hitbox'] je již Rect v mapových souřadnicích
        if player_hit_rect.colliderect(img_obj['hitbox']):
            # print(f"Kolize hráče {player_hit_rect} s objektem {img_obj['hitbox']}")
            return True
    return False

def move_player(dx_map, dy_map):
    """Pohybuje hráčem o dx_map, dy_map v mapových souřadnicích."""
    global player_x, player_y, x, y # x, y jsou síťové pozice (0-SCREEN_WIDTH/HEIGHT)

    new_player_x_map = player_x + dx_map
    new_player_y_map = player_y + dy_map

    # Kontrola hranic mapy (v mapových souřadnicích)
    map_pixel_width = MAP_WIDTH * TILE_SIZE
    map_pixel_height = MAP_HEIGHT * TILE_SIZE
    boundary_pixels = BOUNDARY_WIDTH * TILE_SIZE

    if (new_player_x_map - player_radius < boundary_pixels or
        new_player_x_map + player_radius > map_pixel_width - boundary_pixels or
        new_player_y_map - player_radius < boundary_pixels or
        new_player_y_map + player_radius > map_pixel_height - boundary_pixels):
        # print("Kolize s hranicí mapy.")
        return False

    # Kontrola kolize s objekty
    if check_collision(new_player_x_map, new_player_y_map, player_radius):
        # print("Kolize s objektem.")
        return False

    player_x = new_player_x_map
    player_y = new_player_y_map

    # Aktualizace síťových souřadnic x, y (relativní k rozměrům okna)
    x = (player_x / map_pixel_width) * SCREEN_WIDTH
    y = (player_y / map_pixel_height) * SCREEN_HEIGHT
    return True


def vypocitej_tmavost_hranice(x_tile, y_tile):
    """Vypočítá barvu dlaždice na základě její vzdálenosti od okraje mapy."""
    vzdalenost_od_okraje_x = min(x_tile, MAP_WIDTH - 1 - x_tile)
    vzdalenost_od_okraje_y = min(y_tile, MAP_HEIGHT - 1 - y_tile)
    vzdalenost_od_okraje = min(vzdalenost_od_okraje_x, vzdalenost_od_okraje_y)
    
    hranice_prechodu = BOUNDARY_WIDTH + 5 # Kolik dlaždic trvá přechod
    
    if vzdalenost_od_okraje >= hranice_prechodu:
        return DARK_GREEN # Vnitřek mapy
    elif BOUNDARY_WIDTH <= vzdalenost_od_okraje < hranice_prechodu:
        # Plynulý přechod
        pomer = (vzdalenost_od_okraje - BOUNDARY_WIDTH) / (hranice_prechodu - BOUNDARY_WIDTH)
        # Interpolace zelené složky mezi DARKER_GREEN (0,50,0) a DARK_GREEN (0,80,0)
        g_hodnota = int(DARKER_GREEN[1] + pomer * (DARK_GREEN[1] - DARKER_GREEN[1]))
        return (0, g_hodnota, 0)
    else:
        return DARKER_GREEN # Vnější hranice

def draw_flag(screen, camera_x, camera_y, time_elapsed):
    if flag_taken:
        return
    
    # Výpočet pozice na obrazovce
    screen_x = int(flag_px - camera_x + SCREEN_WIDTH // 2)
    screen_y = int(flag_py - camera_y + SCREEN_HEIGHT // 2)
    
    # Zvětšené parametry vlajky
    scale = 2.0  # <- Zmenšit podle potřeby (1.5 = 150 %, 2.0 = 200 % atd.)
    flag_height = int(30 * scale)
    pole_radius = int(10 * scale)
    flag_length = int(40 * scale)
    wave_offset = 5 * math.sin(time_elapsed * 2) * scale
    
    # Výpočet bodů trojúhelníkové vlajky
    flag_points = [
        (screen_x, screen_y - 5),  # Bod u tyče
        (screen_x + flag_length, screen_y - 15 - wave_offset),
        (screen_x, screen_y - flag_height - 3 * math.sin(time_elapsed * 2) * scale)
    ]
    
    # Tyč (kruh + čára)
    pygame.draw.circle(screen, (220, 50, 50), (screen_x, screen_y), pole_radius)
    pygame.draw.line(screen, BLACK, (screen_x, screen_y), (screen_x, screen_y - flag_height - 10))
    
    # Vlajka
    pygame.draw.polygon(screen, (220, 50, 50), flag_points)
    pygame.draw.polygon(screen, BLACK, flag_points, 2)
    
def draw_blue_flag(screen, camera_x, camera_y, time_elapsed):
    if blue_flag_taken:
        return

    screen_x = int(blue_flag_px - camera_x + SCREEN_WIDTH // 2)
    screen_y = int(blue_flag_py - camera_y + SCREEN_HEIGHT // 2)

    scale = 2.0
    flag_height = int(30 * scale)
    pole_radius = int(10 * scale)
    flag_length = int(40 * scale)
    wave_offset = 5 * math.sin(time_elapsed * 2) * scale

    flag_points = [
        (screen_x, screen_y - 5),
        (screen_x + flag_length, screen_y - 15 - wave_offset),
        (screen_x, screen_y - flag_height - 3 * math.sin(time_elapsed * 2) * scale)
    ]

    pygame.draw.circle(screen, (50, 50, 220), (screen_x, screen_y), pole_radius)
    pygame.draw.line(screen, BLACK, (screen_x, screen_y), (screen_x, screen_y - flag_height - 10))
    pygame.draw.polygon(screen, (50, 50, 220), flag_points)
    pygame.draw.polygon(screen, BLACK, flag_points, 2)
    
def handle_blue_flag_action():
    global blue_flag_taken, player_x, player_y, blue_flag_px, blue_flag_py

    # Vypiš pro kontrolu:
    print(f"[DEBUG] Hráč: ({player_x:.1f}, {player_y:.1f}) | Vlajka: ({blue_flag_px:.1f}, {blue_flag_py:.1f})")

    if not blue_flag_taken:
        distance = math.hypot(player_x - blue_flag_px, player_y - blue_flag_py)
        print(f"[DEBUG] Vzdálenost: {distance:.1f}")
        if distance < 80:  # Zvětšil jsem na 80 pro jistotu
            blue_flag_taken = True
            print(" Sebral jsi modrou vlajku!")
    else:
        blue_flag_px = player_x
        blue_flag_py = player_y
        blue_flag_taken = False
        print(f" Položil jsi modrou vlajku na ({blue_flag_px:.1f}, {blue_flag_py:.1f})")

def draw_map(screen_surface, camera_center_x_map, camera_center_y_map):
    """Vykreslí mapu s ohledem na pozici kamery a screen shake."""
    global screen_shake_offset
    screen_surface.fill(DARKER_GREEN) # Pozadí
    
    # Výpočet viditelné oblasti dlaždic
    # Přidáme rezervu, aby se dlaždice načítaly i mimo přesný pohled kamery (kvůli shake)
    tiles_on_screen_x = (SCREEN_WIDTH // TILE_SIZE) + 4 
    tiles_on_screen_y = (SCREEN_HEIGHT // TILE_SIZE) + 4
    
    # Střed kamery v dlaždicových souřadnicích
    camera_tile_x = camera_center_x_map / TILE_SIZE
    camera_tile_y = camera_center_y_map / TILE_SIZE
    
    # Výpočet počátečních a koncových dlaždic pro vykreslení
    start_tile_x = max(0, int(camera_tile_x - tiles_on_screen_x / 2))
    end_tile_x = min(MAP_WIDTH, int(camera_tile_x + tiles_on_screen_x / 2) +1) # +1 pro range
    start_tile_y = max(0, int(camera_tile_y - tiles_on_screen_y / 2))
    end_tile_y = min(MAP_HEIGHT, int(camera_tile_y + tiles_on_screen_y / 2) +1) # +1 pro range

    # Vykreslení dlaždic
    for y_map_idx in range(start_tile_y, end_tile_y):
        for x_map_idx in range(start_tile_x, end_tile_x):
            # Pozice dlaždice na obrazovce = (pozice_dlazdice_mapa - pozice_kamera_mapa) + stred_obrazovky + shake
            screen_draw_x = (x_map_idx * TILE_SIZE - camera_center_x_map) + SCREEN_WIDTH // 2 + screen_shake_offset[0]
            screen_draw_y = (y_map_idx * TILE_SIZE - camera_center_y_map) + SCREEN_HEIGHT // 2 + screen_shake_offset[1]
            
            # Optimalizace: Kreslit jen pokud je dlaždice alespoň částečně viditelná
            if -TILE_SIZE < screen_draw_x < SCREEN_WIDTH + TILE_SIZE and \
               -TILE_SIZE < screen_draw_y < SCREEN_HEIGHT + TILE_SIZE:
                tile_color = vypocitej_tmavost_hranice(x_map_idx, y_map_idx)
                pygame.draw.rect(screen_surface, tile_color, (screen_draw_x, screen_draw_y, TILE_SIZE, TILE_SIZE))
   
    # Vykreslení vodicí mřížky
    GRID_SPACING = TILE_SIZE * 2
    GRID_COLOR = (60, 100, 60)
    # Svislé čáry
    grid_start_x = ((start_tile_x * TILE_SIZE) // GRID_SPACING) * GRID_SPACING
    grid_end_x = ((end_tile_x * TILE_SIZE) // GRID_SPACING + 1) * GRID_SPACING
    for gx in range(grid_start_x, grid_end_x, GRID_SPACING):
        screen_x = (gx - camera_center_x_map) + SCREEN_WIDTH // 2 + screen_shake_offset[0]
        pygame.draw.line(screen_surface, GRID_COLOR,
                         (screen_x, 0),
                         (screen_x, SCREEN_HEIGHT), 1)
    # Vodorovné čáry
    grid_start_y = ((start_tile_y * TILE_SIZE) // GRID_SPACING) * GRID_SPACING
    grid_end_y = ((end_tile_y * TILE_SIZE) // GRID_SPACING + 1) * GRID_SPACING
    for gy in range(grid_start_y, grid_end_y, GRID_SPACING):
        screen_y = (gy - camera_center_y_map) + SCREEN_HEIGHT // 2 + screen_shake_offset[1]
        pygame.draw.line(screen_surface, GRID_COLOR,
                         (0, screen_y),
                         (SCREEN_WIDTH, screen_y), 1)

    # Vykreslení obrazových objektů (stromy atd.)
    for img_data in images:
        # Pozice objektu na obrazovce
        img_screen_x = (img_data['x_tile'] * TILE_SIZE - camera_center_x_map) + SCREEN_WIDTH // 2 + screen_shake_offset[0]
        img_screen_y = (img_data['y_tile'] * TILE_SIZE - camera_center_y_map) + SCREEN_HEIGHT // 2 + screen_shake_offset[1]
        
        # Optimalizace: Kreslit jen pokud je objekt alespoň částečně viditelný
        if -img_data['width_px'] < img_screen_x < SCREEN_WIDTH + img_data['width_px'] and \
           -img_data['height_px'] < img_screen_y < SCREEN_HEIGHT + img_data['height_px']:
            screen_surface.blit(img_data['image'], (int(img_screen_x), int(img_screen_y)))


def draw_player(screen_surface, _camera_center_x_map, _camera_center_y_map):
    global player_texture, player_team, player_angle, player_size, screen_shake_offset
    global current_weapon, my_color

    player_draw_center_x = SCREEN_WIDTH // 2 + screen_shake_offset[0]
    player_draw_center_y = SCREEN_HEIGHT // 2 + screen_shake_offset[1]

    # --- Vykreslení tenké kružnice v barvě hráče ---
    pygame.draw.circle(
        screen_surface,
        my_color,
        (player_draw_center_x, player_draw_center_y),
        int(player_radius * 1.15),
        4  # Tloušťka kružnice
    )

    # Vykresli hráče vždy barevně správně (bez ohledu na tým)
    texture_to_render = SKIN_TEXTURES.get(current_weapon, player_texture)
    rotated_player_texture = pygame.transform.rotate(texture_to_render, -player_angle)
    player_rect = rotated_player_texture.get_rect(center=(player_draw_center_x, player_draw_center_y))
    screen_surface.blit(rotated_player_texture, player_rect.topleft)
    # ...rest of your weapon drawing code...
    if current_weapon in weapon_textures:
        weapon_data = WEAPONS[current_weapon]
        original_weapon_texture = weapon_textures[current_weapon]
        angle_rad = math.radians(player_angle - 90)
        forward_offset = weapon_data.get("offset_x", 20)
        side_offset = weapon_data.get("offset_y", 10)
        weapon_center_x = player_draw_center_x + forward_offset * math.cos(angle_rad) - side_offset * math.sin(angle_rad)
        weapon_center_y = player_draw_center_y + forward_offset * math.sin(angle_rad) + side_offset * math.cos(angle_rad)
        rotated_weapon_texture = pygame.transform.rotate(original_weapon_texture, -player_angle)
        weapon_rect = rotated_weapon_texture.get_rect(center=(int(weapon_center_x), int(weapon_center_y)))
        screen_surface.blit(rotated_weapon_texture, weapon_rect.topleft)
    else:
        pygame.draw.circle(screen_surface, (200, 200, 200), (player_draw_center_x, player_draw_center_y), player_radius)


def draw_other_players(screen_surface, camera_center_x_map, camera_center_y_map):
    """Vykreslí ostatní hráče s ohledem na kameru a screen shake."""
    global players_interpolated, my_id, player_radius, screen_shake_offset
    global player_texture, SKIN_TEXTURES, weapon_textures, WEAPONS
    map_pixel_width = MAP_WIDTH * TILE_SIZE
    map_pixel_height = MAP_HEIGHT * TILE_SIZE

    other_players_count = len([pid for pid in players_interpolated.keys() if pid != my_id])
    if other_players_count > 0:
        print(f"[DEBUG] Kreslím {other_players_count} ostatních hráčů (celkem {len(players_interpolated)}, můj ID: {my_id})")

    for player_id_server, p_data_server in players_interpolated.items():
        if player_id_server == my_id:
            continue
        if isinstance(p_data_server, (list, tuple)) and len(p_data_server) >= 2:
            other_player_net_x, other_player_net_y = p_data_server[0], p_data_server[1]
            other_player_angle = p_data_server[2] if len(p_data_server) > 2 else 0
            other_player_color_tuple = tuple(p_data_server[3]) if len(p_data_server) > 3 and isinstance(p_data_server[3], list) else GREEN
            other_player_weapon = p_data_server[4] if len(p_data_server) > 4 else "Crossbow"
            other_player_team = p_data_server[5] if len(p_data_server) > 5 else None

            other_player_map_x = (other_player_net_x / SCREEN_WIDTH) * map_pixel_width
            other_player_map_y = (other_player_net_y / SCREEN_HEIGHT) * map_pixel_height
            other_player_screen_x = int(other_player_map_x - camera_center_x_map + SCREEN_WIDTH // 2 + screen_shake_offset[0])
            other_player_screen_y = int(other_player_map_y - camera_center_y_map + SCREEN_HEIGHT // 2 + screen_shake_offset[1])

            # --- Vykreslení tenké kružnice podle barvy hráče ---
            pygame.draw.circle(
                screen_surface,
                other_player_color_tuple,
                (other_player_screen_x, other_player_screen_y),
                int(player_radius * 1.15),
                4  # Tloušťka kružnice
            )

            # --- Vykreslení hráče (skin/texture) ---
            texture_to_render = SKIN_TEXTURES.get(other_player_weapon, player_texture)
            if texture_to_render:
                rotated_texture = pygame.transform.rotate(texture_to_render, -other_player_angle)
                texture_rect = rotated_texture.get_rect(center=(other_player_screen_x, other_player_screen_y))
                screen_surface.blit(rotated_texture, texture_rect.topleft)
                
                # Vykreslení zbraně
                if other_player_weapon in weapon_textures:
                    weapon_data = WEAPONS[other_player_weapon]
                    original_weapon_texture = weapon_textures[other_player_weapon]
                    angle_rad = math.radians(other_player_angle - 90)
                    forward_offset = weapon_data.get("offset_x", 20)
                    side_offset = weapon_data.get("offset_y", 10)
                    
                    weapon_center_x = other_player_screen_x + forward_offset * math.cos(angle_rad) - side_offset * math.sin(angle_rad)
                    weapon_center_y = other_player_screen_y + forward_offset * math.sin(angle_rad) + side_offset * math.cos(angle_rad)
                    
                    rotated_weapon_texture = pygame.transform.rotate(original_weapon_texture, -other_player_angle)
                    weapon_rect = rotated_weapon_texture.get_rect(center=(int(weapon_center_x), int(weapon_center_y)))
                    
                    screen_surface.blit(rotated_weapon_texture, weapon_rect.topleft)
            else:
                # Záložní vykreslení jako barevný kruh
                pygame.draw.circle(screen_surface, other_player_color_tuple, 
                                   (other_player_screen_x, other_player_screen_y), 
                                   player_radius)
                
                # Ukazatel směru
                pointer_len = player_radius * 1.5
                end_x = other_player_screen_x + pointer_len * math.cos(math.radians(other_player_angle - 90))
                end_y = other_player_screen_y + pointer_len * math.sin(math.radians(other_player_angle - 90))
                pygame.draw.line(screen_surface, WHITE, (other_player_screen_x, other_player_screen_y), (int(end_x), int(end_y)), 2)


def draw_ui(screen_surface, ui_font):
    """Vykreslí uživatelské rozhraní (informace o zbrani, stavu sítě, katastrofě atd.)."""
    global current_weapon, weapon_cooldowns, WEAPONS, connected, status, players, my_id, my_color
    global response_time, is_moving, player_x, player_y
    global active_catastrophe, catastrophe_start_time, catastrophe_duration, big_font # Pro katastrofy

    # Informace o zbrani vlevo dole
    # weapon_info_bg_rect = pygame.Rect(10, SCREEN_HEIGHT - 60, 300, 50)
    # pygame.draw.rect(screen_surface, (0, 0, 0, 100), weapon_info_bg_rect) # Průhledné pozadí

    weapon_text_render = ui_font.render(f"Weapon: {current_weapon}", True, WHITE)
    screen_surface.blit(weapon_text_render, (20, SCREEN_HEIGHT - 55))
    
    cooldown_val = weapon_cooldowns[current_weapon]
    cooldown_max_val = WEAPONS[current_weapon]["cooldown"]
    cooldown_text_render = ui_font.render(f"Cooldown: {cooldown_val}/{cooldown_max_val}", True, WHITE)
    screen_surface.blit(cooldown_text_render, (20, SCREEN_HEIGHT - 35))
    
    # Instrukce vpravo dole
    instructions_render = ui_font.render("Kolo: změna, LMB: střelba, K: katastrofa", True, WHITE)
    screen_surface.blit(instructions_render, (SCREEN_WIDTH - instructions_render.get_width() - 10 , SCREEN_HEIGHT - 30))

    # Informace o síti a hráči vlevo nahoře
    status_text_color = GREEN if connected else RED
    status_text_render = ui_font.render(status, True, status_text_color)
    players_count_text_render = ui_font.render(f"Hráči: {len(players)}", True, WHITE)
    my_id_text_render = ui_font.render(f"Moje ID: {my_id}", True, my_color) # Použijeme barvu hráče
    
    screen_surface.blit(status_text_render, (10, 10))
    screen_surface.blit(players_count_text_render, (10, 35))
    screen_surface.blit(my_id_text_render, (10, 60))
    
    if response_time is not None:
        response_text_render = ui_font.render(f"Odezva: {response_time:.1f} ms", True, YELLOW)
        screen_surface.blit(response_text_render, (10, 85))
    
    # Informace o pohybu a pozici vpravo nahoře
    move_status_text = "Pohyb" if is_moving else "Stojím"
    move_status_color = YELLOW if is_moving else WHITE
    move_text_render = ui_font.render(move_status_text, True, move_status_color)
    screen_surface.blit(move_text_render, (SCREEN_WIDTH - move_text_render.get_width() - 10, 35))
    
    # Zobrazujeme mapové souřadnice hráče
    pos_text_render = ui_font.render(f"Pozice: {int(player_x)}, {int(player_y)}", True, WHITE)
    screen_surface.blit(pos_text_render, (SCREEN_WIDTH - pos_text_render.get_width() - 10, 60))

    # Zobrazení aktivní katastrofy (uprostřed nahoře)
    if active_catastrophe:
        time_now = time.time()
        remaining_cat_time = catastrophe_duration - (time_now - catastrophe_start_time)
        if remaining_cat_time < 0: remaining_cat_time = 0
        
        cat_text_str = f"KATASTROFA: {active_catastrophe.upper()} ({int(remaining_cat_time)}s)"
        cat_text_surface = big_font.render(cat_text_str, True, RED) # Použijeme big_font
        text_rect = cat_text_surface.get_rect(center=(SCREEN_WIDTH // 2, 30)) # Vycentrovat text
        screen_surface.blit(cat_text_surface, text_rect)


def get_player_tile_position():
    """Vrátí dlaždicové souřadnice hráče."""
    global player_x, player_y, TILE_SIZE
    return int(player_x // TILE_SIZE), int(player_y // TILE_SIZE)

def calculate_angle_to_mouse(player_screen_center_x, player_screen_center_y):
    """Vypočítá úhel od středu hráče na obrazovce k pozici myši."""
    mouse_x_screen, mouse_y_screen = pygame.mouse.get_pos()
    delta_x = mouse_x_screen - player_screen_center_x
    delta_y = mouse_y_screen - player_screen_center_y
    # math.atan2 vrací úhel v radiánech, math.degrees převede na stupně
    # Přičtení 90 stupňů může být potřeba kvůli orientaci os v Pygame (Y osa dolů)
    # a tomu, jak Pygame.transform.rotate interpretuje úhly (proti směru hodinových ručiček).
    angle_degrees = math.degrees(math.atan2(delta_y, delta_x)) + 90 
    return angle_degrees

def is_near_flag():
    """Vrátí True, pokud je hráč dost blízko vlajce pro sebrání."""
    distance = math.hypot(player_x - flag_px, player_y - flag_py)
    return distance < 50  # vzdálenost v pixelech

def shoot(weapon_name_arg):
    """Zpracuje střelbu ze zbraně."""
    global weapon_cooldowns, WEAPONS, projectiles
    global player_x, player_y, player_angle # Mapové souřadnice hráče a jeho úhel

    if weapon_cooldowns[weapon_name_arg] > 0: # Zbraň se ještě nabíjí
        return False
    
    weapon_cooldowns[weapon_name_arg] = WEAPONS[weapon_name_arg]["cooldown"] # Nastaví cooldown
    weapon_props = WEAPONS[weapon_name_arg]
    
    # Výpočet směrového vektoru projektilu na základě úhlu hráče
    # Úhel hráče je již nastaven funkcí calculate_angle_to_mouse
    # Pro výpočty v math je potřeba převést na radiány a případně upravit (0 stupňů je vpravo)
    angle_rad_math = math.radians(player_angle - 90) # -90 pro shodu s math.cos/sin (0° = doprava)
    
    # Směrový vektor projektilu
    proj_dx_normalized = math.cos(angle_rad_math)
    proj_dy_normalized = math.sin(angle_rad_math)

    # Vytvoření projektilu
    new_projectile = {
        "x": player_x, # Startovní pozice projektilu (střed hráče na mapě)
        "y": player_y,
        "dx": proj_dx_normalized * weapon_props["projectile_speed"], # Směr X * rychlost
        "dy": proj_dy_normalized * weapon_props["projectile_speed"], # Směr Y * rychlost
        "lifetime": weapon_props["projectile_lifetime"],
        "color": weapon_props["projectile_color"],
        "radius": weapon_props["projectile_size"]
    }
    projectiles.append(new_projectile)
    # print(f"Střelba: {weapon_name_arg}, projektil: {new_projectile}")
    return True
    
# Nastavení itemů
medkits = []
generate_medkits(medkit_amount, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT, BOUNDARY_WIDTH, medkits=medkits)


def change_weapon(direction_change):
    global current_weapon_index, current_weapon, weapon_names
    global max_player_health, player_health

    current_weapon_index = (current_weapon_index + direction_change) % len(weapon_names)
    current_weapon = weapon_names[current_weapon_index]

    # Set max HP based on class
    max_player_health = CLASS_MAX_HP.get(current_weapon, 100)
    # Optionally, heal to full when switching class:
    player_health = max_player_health

    print(f"Zbraň změněna na {current_weapon} (Max HP: {max_player_health})")

def start_new_random_catastrophe():
    """Spustí novou náhodnou katastrofu, pokud žádná neběží."""
    global active_catastrophe, catastrophe_start_time, possible_catastrophes
    global last_catastrophe_trigger_time, catastrophe_duration
    
    current_time = time.time()
    if not active_catastrophe: # Spustit pouze pokud žádná katastrofa neběží
        active_catastrophe = random.choice(possible_catastrophes)
        catastrophe_start_time = current_time
        # Zkontrolujeme, zda je klávesa K stále stisknutá, pro přesnější logování
        # Poznámka: pygame.key.get_pressed() nemusí být spolehlivé zde, pokud událost již byla zpracována.
        # Lepší je předat parametr nebo se spolehnout na kontext. Pro jednoduchost necháme.
        triggered_by = "Manuálně" if pygame.key.get_pressed()[pygame.K_k] else "Automaticky"
        print(f"--- KATASTROFA SPUŠTĚNA ({triggered_by}): {active_catastrophe} na {catastrophe_duration}s ---")
        # Resetovat časovač pro automatické spuštění, aby hned nenásledovala další
        last_catastrophe_trigger_time = current_time
    else:
        print(f"Pokus o spuštění katastrofy, ale '{active_catastrophe}' již probíhá.")


async def game_loop():
    """Hlavní herní smyčka s WebSocket komunikací."""
    global players, players_interpolated, players_prev, connected, status
    global x, y, player_x, player_y, my_id, response_time, last_update_time, is_moving
    global player_angle, current_weapon, weapon_cooldowns, projectiles, font
    global my_color # <-- OPRAVA: Deklarace, že pracujeme s globální proměnnou my_color
    
    # Globální proměnné pro katastrofy, které se zde modifikují nebo čtou
    global active_catastrophe, catastrophe_start_time, catastrophe_duration
    global last_catastrophe_trigger_time, catastrophe_interval, screen_shake_offset
    global sprint_active, sprint_timer, PLAYER_SPEED
    global sprint_respawn_timer
    
    

    # Inicializace časovače pro automatické katastrofy, aby nezačala hned
    last_catastrophe_trigger_time = time.time()
    should_shoot_this_frame = False # Příznak pro odeslání informace o střele

    try:
        async with aiohttp.ClientSession() as session:
            print(f"Pokouším se připojit k serveru: {SERVER_URL}")
            async with session.ws_connect(SERVER_URL) as ws_connection:
                connected = True
                status = "Připojeno"
                print(f"Úspěšně připojeno k {SERVER_URL}")

                # Odeslání úvodní pozice a barvy hráče
                initial_data = {"x": x, "y": y, "angle": player_angle, "color": list(my_color)}
                await ws_connection.send_json(initial_data)
                last_update_time = time.time()

                game_is_running = True
                sprint_respawn_timer = time.time()
                while game_is_running:
                    current_time = time.time()
                    current_loop_time = time.time()
                    should_shoot_this_frame = False # Reset na začátku každého snímku
                    if current_time - sprint_respawn_timer >= 2:
                        sprint_respawn_timer = current_time
                        spawn_x = random.randint(BOUNDARY_WIDTH + 1, MAP_WIDTH - BOUNDARY_WIDTH - 2) * TILE_SIZE
                        spawn_y = random.randint(BOUNDARY_WIDTH + 1, MAP_HEIGHT - BOUNDARY_WIDTH - 2) * TILE_SIZE
                        sprint = PowerUp(spawn_x, spawn_y, "images/sprint.png", "sprint", duration=5)
                        power_ups.append(sprint)
                        print("Nový sprint power-up přidán!")
                    current_time = time.time()

                    # Zpracování událostí (vstupy od uživatele)
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            game_is_running = False
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                game_is_running = False
                            elif event.key == pygame.K_t: # Testovací klávesa pro přidání stromu
                                current_tile_x, current_tile_y = get_player_tile_position()
                                add_image("tree1.png", current_tile_x + random.randint(-3,3), current_tile_y + random.randint(-3,3), scale=random.uniform(1.5, 2.5))
                            elif event.key == pygame.K_k: # Manuální spuštění katastrofy
                                print("Klávesa K stisknuta - pokus o spuštění katastrofy.")
                                start_new_random_catastrophe()
                            elif event.key == pygame.K_l:
                                handle_blue_flag_action()
                        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                            running = False
                        elif event.type == pygame.KEYDOWN and event.key == pygame.K_t:
                            player_tile_x, player_tile_y = get_player_tile_position()
                            add_image("images/tree1.png", player_tile_x + 2, player_tile_y + 2, 2.0)
                        elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                            tile_x, tile_y = get_player_tile_position()
                            sprint = PowerUp(spawn_x, spawn_y, "images/sprint.png", "sprint", duration=5)
                            power_ups.append(sprint)
                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            if event.button == 1: # Levé tlačítko myši - střelba
                                if shoot(current_weapon):
                                    should_shoot_this_frame = True # Nastaví příznak pro odeslání projektilu
                            elif event.button == 4: # Kolečko myši nahoru
                                change_weapon(1) # Další zbraň
                            elif event.button == 5: # Kolečko myši dolů
                                change_weapon(-1) # Předchozí zbraň

                    keys = pygame.key.get_pressed()
                    dx, dy = 0, 0
                    if sprint_active:
                        sprint_timer -= 1
                        if sprint_timer <=0:
                            sprint_active = False
                            PLAYER_SPEED = BASE_SPEED
                    current_speed = PLAYER_SPEED
                    # Pohyb hráče
                    pressed_keys = pygame.key.get_pressed()
                    movement_dx_map = 0; movement_dy_map = 0 # Změna pozice na mapě
                    if pressed_keys[pygame.K_w] or pressed_keys[pygame.K_UP]: movement_dy_map -= PLAYER_SPEED
                    if pressed_keys[pygame.K_s] or pressed_keys[pygame.K_DOWN]: movement_dy_map += PLAYER_SPEED
                    if pressed_keys[pygame.K_a] or pressed_keys[pygame.K_LEFT]: movement_dx_map -= PLAYER_SPEED
                    if pressed_keys[pygame.K_d] or pressed_keys[pygame.K_RIGHT]: movement_dx_map += PLAYER_SPEED
                    
                    # Normalizace diagonálního pohybu
                    if movement_dx_map != 0 and movement_dy_map != 0:
                        movement_dx_map *= 0.7071 # ~1/sqrt(2)
                        movement_dy_map *= 0.7071
                    
                    is_moving = (movement_dx_map != 0 or movement_dy_map != 0)
                    if is_moving:
                        move_player(movement_dx_map, movement_dy_map)
                    
                            

                    # Natočení hráče vůči myši (hráč je pro tento výpočet vždy ve středu obrazovky)
                    player_angle = calculate_angle_to_mouse(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

                    # Aktualizace cooldownů zbraní
                    for w_name in weapon_cooldowns:
                        if weapon_cooldowns[w_name] > 0:
                            weapon_cooldowns[w_name] -= 1 # Sníží cooldown o 1 snímek
                    
                    # Aktualizace projektilů (pohyb a životnost)
                    # Iterujeme pozpátku, abychom mohli bezpečně odstraňovat prvky
                    for i in range(len(projectiles) - 1, -1, -1):
                        proj = projectiles[i]
                        proj["x"] += proj["dx"]
                        proj["y"] += proj["dy"]
                        proj["lifetime"] -= 1
                        if proj["lifetime"] <= 0:
                            projectiles.pop(i) # Odstranění projektilu, kterému vypršela životnost
                    
                    # --- Logika Katastrof ---
                    # Automatické spuštění katastrofy, pokud žádná neběží a uplynul interval
                    if not active_catastrophe and \
                       (current_loop_time - last_catastrophe_trigger_time > catastrophe_interval):
                        start_new_random_catastrophe()
                    
                    # Zpracování efektů aktivní katastrofy
                    if active_catastrophe:
                        if current_loop_time - catastrophe_start_time >= catastrophe_duration:
                            # Katastrofa skončila
                            print(f"--- Katastrofa {active_catastrophe} oficiálně skončila. ---")
                            active_catastrophe = None
                            screen_shake_offset = (0, 0) # Vypnout třesení
                        else:
                            # Katastrofa stále probíhá - aplikovat efekty
                            if active_catastrophe == "Zemětřesení":
                                # Silnější, náhodné třesení
                                screen_shake_offset = (random.uniform(-10, 10), random.uniform(-10, 10))
                            elif active_catastrophe == "Tornádo":
                                # Jemnější, krouživé třesení
                                swirl_speed = current_loop_time * 5 # Rychlost kroužení
                                swirl_magnitude = 6 # Síla kroužení
                                screen_shake_offset = (math.cos(swirl_speed) * swirl_magnitude, 
                                                       math.sin(swirl_speed) * swirl_magnitude)
                    else:
                        # Žádná katastrofa není aktivní, ujistit se, že je třesení vypnuté
                        if screen_shake_offset != (0,0) : screen_shake_offset = (0, 0)
                    # --- Konec Logiky Katastrof ---

                    # Aktualizace stavu pohybu
                    moved = (dx != 0 or dy != 0)
                    is_moving = moved
                    
                    if moved:
                        move_player(dx, dy)
                        update_powerups()
                    
                    def update_powerups():
                        global sprint_active, sprint_timer
                        
                        player_rect = pygame.Rect(player_x - player_radius, player_y - player_radius,
                                                  player_radius * 2, player_radius * 2)
                    
                        for power_up in power_ups:
                            player_rect = pygame.Rect(
                                int(player_x - player_radius),
                                int(player_y - player_radius),
                                int(player_radius * 2),
                                int(player_radius * 2)
                            )
                            
                            if power_up.active and power_up.rect.colliderect(player_rect):
                                if power_up.effect_type == "sprint":
                                    sprint_active = True
                                    sprint_timer = power_up.duration * 60
                                    PLAYER_SPEED = BASE_SPEED * 2
                                    print("Sprint aktivován!")
                                power_up.active = False
                                power_ups.remove(power_up)
                                
                    
                    
                    if sprint_active:
                        sprint_timer -= 1
                        if sprint_timer <= 0:
                            sprint_active = False
                            PLAYER_SPEED = BASE_SPEED
                            print("Sprint skončil")
                    
                    # Provedení pohybu
                    if moved:
                        move_player(dx, dy)
                        update_powerups()

                    # Výpočet úhlu mezi hráčem a kurzorem myši
                    player_screen_x = int(SCREEN_WIDTH // 2)
                    player_screen_y = int(SCREEN_HEIGHT // 2)
                    player_angle = calculate_angle_to_mouse(player_screen_x, player_screen_y)
                    
                    # Aktualizace cooldownů zbraní
                    for weapon in weapon_cooldowns:
                        if weapon_cooldowns[weapon] > 0:
                            weapon_cooldowns[weapon] -= 1
                    
                    if sprint_active:
                        PLAYER_SPEED = BASE_SPEED * 2
                        sprint_timer -= 1
                        if sprint_timer <= 0:
                            sprint_active = False
                            PLAYER_SPEED = BASE_SPEED

                    # Posílání dat serveru (při pohybu nebo po uplynutí intervalu)
                    if moved or current_time - last_update_time >= UPDATE_INTERVAL:
                        start_time = time.time()
                        await ws_connection.send_json({"x": x, "y": y})
                        last_update_time = current_time
                    
                    # Přijímání dat od serveru (non-blocking)
                    # Posílání dat na server (pozice, úhel, barva, případně projektil)                    if is_moving or should_shoot_this_frame or (current_loop_time - last_update_time >= UPDATE_INTERVAL):
                        time_before_send = time.time()
                        data_to_send = {"x": x, "y": y, "angle": player_angle, "color": list(my_color), "weapon": current_weapon}
                        
                        if should_shoot_this_frame and projectiles: # Pokud jsme tento snímek střelili a máme projektil
                            # Předpokládáme, že poslední přidaný projektil je ten náš
                            # V reálné hře by projektily měly ID vlastníka
                            our_last_projectile = projectiles[-1] 
                            data_to_send["projectile"] = {
                                "x": our_last_projectile["x"], "y": our_last_projectile["y"],
                                "dx": our_last_projectile["dx"], "dy": our_last_projectile["dy"],
                                "color": list(our_last_projectile["color"]), # JSON nepodporuje tuple
                                "lifetime": our_last_projectile["lifetime"], 
                                "radius": our_last_projectile["radius"]
                            }
                        
                        await ws_connection.send_json(data_to_send)
                        last_update_time = current_loop_time # Aktualizace času posledního odeslání
                        
                        # Měření odezvy pouze pokud jsme odeslali kvůli pohybu nebo střele (ne keep-alive)
                        if is_moving or should_shoot_this_frame:
                             response_time = (time.time() - time_before_send) * 1000

                    # Příjem dat ze serveru
                    try:
                        # Použijeme krátký timeout, abychom neblokovali smyčku
                        server_message = await asyncio.wait_for(ws_connection.receive(), timeout=0.005) 
                        
                        if server_message.type == aiohttp.WSMsgType.TEXT:
                            server_data = json.loads(server_message.data)
                            
                            # Zpracování broadcastu projektilu od jiného hráče
                            if "projectile_broadcast" in server_data:
                                proj_info = server_data["projectile_broadcast"]
                                # Ověříme, zda projektil nepatří nám (pokud server přidává 'owner_id')
                                if proj_info.get("owner_id") != my_id : # Předpokládáme, že server může posílat owner_id
                                    # Vytvoření nového projektilu na základě dat od serveru
                                    # Použijeme defaultní hodnoty, pokud některé klíče chybí
                                    default_weapon_props = WEAPONS["Crossbow"] # Jako fallback
                                    received_projectile = {
                                        "x": proj_info["x"], "y": proj_info["y"],
                                        "dx": proj_info["dx"], "dy": proj_info["dy"],
                                        "lifetime": proj_info.get("lifetime", default_weapon_props["projectile_lifetime"]),
                                        "color": tuple(proj_info["color"]), # Převedeme seznam barev zpět na tuple
                                        "radius": proj_info.get("radius", default_weapon_props["projectile_size"])
                                    }
                                    projectiles.append(received_projectile)
                                # else: print(f"Ignoruji vlastní projektil od serveru: {proj_info.get('owner_id')}")                            # Zpracování pozic hráčů (slovník {id: [x_net, y_net, angle, color_list, weapon]})
                            players_prev = players_interpolated.copy() if players_interpolated else {}
                            
                            # Server posílá objekt, převedeme na pole pro kompatibilitu
                            players = {}
                            for pid, pdata in server_data.items():
                                if isinstance(pdata, dict):
                                    # Převod z objektu na pole [x, y, angle, color, weapon]
                                    players[pid] = [
                                        pdata.get("x", 100),
                                        pdata.get("y", 100), 
                                        pdata.get("angle", 0),
                                        pdata.get("color", [100, 255, 100]),
                                        pdata.get("weapon", "Crossbow")
                                    ]
                                else:
                                    # Pokud už je to pole, zachováme
                                    players[pid] = pdata

                            # První přiřazení ID našeho hráče
                            if my_id is None:
                                for server_pid, server_pdata in players.items():
                                    if isinstance(server_pdata, list) and len(server_pdata) >= 2:
                                        # Heuristika pro nalezení sebe sama - porovnání s naší aktuální síťovou pozicí
                                        # a barvou, pokud ji server posílá zpět.
                                        # Tato heuristika může být nespolehlivá, lepší je, když server přiřadí ID explicitně.
                                        if abs(server_pdata[0] - x) < 1.0 and abs(server_pdata[1] - y) < 1.0:
                                            my_id = server_pid
                                            print(f"Moje ID bylo pravděpodobně identifikováno jako: {my_id}")
                                            # Pokud server posílá barvu, můžeme ji také zkontrolovat/převzít
                                            if len(server_pdata) >= 4 and isinstance(server_pdata[3], list):
                                                my_color = tuple(server_pdata[3]) # Zde přiřazujeme globální my_color
                                            break
                              # Ujistíme se, že naše vlastní data jsou v `players` aktuální
                            if my_id and my_id in players:
                                players[my_id] = [x, y, player_angle, list(my_color), current_weapon]
                            
                            # Pokud jsme právě dostali první data, nastavíme `players_prev`
                            if not players_prev:
                                players_prev = players.copy()
                                players_interpolated = players.copy() # Začneme s neinterpolovanými daty

                        elif server_message.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            connected = False
                            status = "Spojení ukončeno serverem"
                            print(f"WebSocket spojení uzavřeno nebo chyba: {ws_connection.exception()}")
                            game_is_running = False # Ukončíme hlavní smyčku
                            break 
                    except asyncio.TimeoutError:
                        pass # Žádná zpráva ze serveru v daném timeoutu, pokračujeme dál
                    except json.JSONDecodeError as e:
                        print(f"Chyba při dekódování JSON od serveru: {e} - Data: {server_message.data if 'server_message' in locals() else 'N/A'}")
                    except Exception as e:
                        print(f"Neočekávaná chyba při příjmu dat ze serveru: {e}")

                    status = "Připojeno" if connected else "Odpojeno"                    # Interpolace pozic ostatních hráčů pro plynulejší pohyb
                    current_interpolated_state = {}
                    for server_pid, server_pdata in players.items():
                        if isinstance(server_pdata, list) and len(server_pdata) >= 2: # [x_net, y_net, angle, color, weapon]
                            net_x_from_server, net_y_from_server = server_pdata[0], server_pdata[1]
                            angle_from_server = server_pdata[2] if len(server_pdata) > 2 else 0
                            color_list_from_server = server_pdata[3] if len(server_pdata) > 3 and isinstance(server_pdata[3], list) else list(GREEN)
                            weapon_from_server = server_pdata[4] if len(server_pdata) > 4 else "Crossbow"
                            
                            if server_pid == my_id:
                                # Naše pozice je vždy aktuální (x, y jsou naše síťové souřadnice)
                                current_interpolated_state[server_pid] = [x, y, player_angle, list(my_color), current_weapon]
                            elif server_pid in players_prev and \
                                 isinstance(players_prev[server_pid], list) and \
                                 len(players_prev[server_pid]) >= 2:
                                # Máme předchozí pozici, můžeme interpolovat
                                prev_net_x, prev_net_y = players_prev[server_pid][0], players_prev[server_pid][1]
                                prev_angle = players_prev[server_pid][2] if len(players_prev[server_pid]) > 2 else angle_from_server
                                # Jednoduchá lineární interpolace
                                interp_net_x = prev_net_x + (net_x_from_server - prev_net_x) * other_players_interpolation_factor
                                interp_net_y = prev_net_y + (net_y_from_server - prev_net_y) * other_players_interpolation_factor
                                # Interpolace úhlu může být složitější (shortest angle), pro jednoduchost lineární
                                interp_angle = prev_angle + (angle_from_server - prev_angle) * other_players_interpolation_factor

                                current_interpolated_state[server_pid] = [interp_net_x, interp_net_y, interp_angle, color_list_from_server, weapon_from_server]
                            else:
                                # Nový hráč nebo chybí předchozí data, použijeme aktuální data ze serveru
                                current_interpolated_state[server_pid] = [net_x_from_server, net_y_from_server, angle_from_server, color_list_from_server, weapon_from_server]
                    
                    # Nastavíme interpolované data
                    players_interpolated = current_interpolated_state
                    

                    # Vykreslení
                    draw_map(screen, player_x, player_y)
                    draw_player(screen, player_x, player_y)
                    draw_other_players(screen, player_x, player_y)
                    
                    for power_up in power_ups:
                        if power_up.active:
                            power_up.draw(screen, player_x, player_y)
                    
                    # Vykreslení UI
                    draw_ui(screen, font)
                    
                    # FPS počítadlo
                    fps = clock.get_fps()
                    fps_text = font.render(f"FPS: {fps:.1f}", True, YELLOW)
                    screen.blit(fps_text, (600, 10))

                    # --- Vykreslování ---
                    # Kamera je vždy zaměřena na našeho hráče (player_x, player_y jsou mapové souřadnice)
                    # Efekt třesení (screen_shake_offset) se aplikuje uvnitř jednotlivých vykreslovacích funkcí.
                    draw_map(screen, player_x, player_y)
                    draw_flag(screen, player_x, player_y, pygame.time.get_ticks() / 1000.0)
                    draw_blue_flag(screen, player_x, player_y, pygame.time.get_ticks() / 1000.0)
                    draw_other_players(screen, player_x, player_y) # Ostatní hráči se kreslí relativně ke kameře
                    draw_player(screen, player_x, player_y) # Náš hráč (kreslený ve středu obrazovky + shake)
                    
                    # Vykreslení projektilů (s ohledem na kameru a shake)
                    for p_data in projectiles:
                        # Převod mapových souřadnic projektilu na souřadnice obrazovky
                        proj_screen_x = int(p_data["x"] - player_x + SCREEN_WIDTH // 2 + screen_shake_offset[0])
                        proj_screen_y = int(p_data["y"] - player_y + SCREEN_HEIGHT // 2 + screen_shake_offset[1])
                        pygame.draw.circle(screen, p_data["color"], (proj_screen_x, proj_screen_y), p_data["radius"])

                    draw_ui(screen, font) # UI se nekreslí s třesením

                    # Zobrazení FPS
                    current_fps = clock.get_fps()
                    fps_text_surface = font.render(f"FPS: {current_fps:.1f}", True, YELLOW)
                    screen.blit(fps_text_surface, (SCREEN_WIDTH - fps_text_surface.get_width() - 10, 10))

                    pygame.display.flip() # Aktualizace celé obrazovky
                    clock.tick(60) # Omezení na 60 FPS
                    await asyncio.sleep(0) # Důležité pro plynulý běh asyncio a uvolnění pro jiné úlohy

    except aiohttp.ClientConnectorError as e: # Specifická chyba pro problémy s připojením
        connected = False
        status = f"Chyba připojení k serveru!"
        print(f"Chyba ClientConnectorError při připojování k {SERVER_URL}: {e}")
        # Zde by se mohla zobrazit chybová hláška uživateli v Pygame okně
    except ConnectionRefusedError as e: # Další častá chyba připojení
        connected = False
        status = f"Server odmítl připojení!"
        print(f"Chyba ConnectionRefusedError při připojování k {SERVER_URL}: {e}")
    except Exception as e:
        connected = False
        status = f"Neočekávaná chyba!"
        print(f"Neočekávaná chyba v game_loop: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc() # Vytiskne kompletní traceback chyby pro ladění
    finally:
        print("Ukončuji game_loop (buď normálně nebo kvůli chybě).")
        if connected: # Pokud jsme stále připojeni, můžeme se pokusit poslat zprávu o odpojení
            try:
                if 'ws_connection' in locals() and not ws_connection.closed: # Zkontrolujeme, zda ws_connection existuje a je otevřené
                    await ws_connection.close()
                    print("WebSocket spojení bylo uzavřeno.")
            except Exception as e_close:
                print(f"Chyba při zavírání WebSocket spojení: {e_close}")
        connected = False
        status = "Odpojeno"

def show_team_selection_screen():
    """Zobrazí úvodní obrazovku pro výběr týmu/barvy s live aktualizací počtů hráčů v týmech."""
    global screen, font
    import threading
    import queue
    import websockets
    import asyncio

    selected_team = None
    running = True
    clock = pygame.time.Clock()
    team_counts = [0, 0]  # Počet hráčů v týmech
    team_counts_queue = queue.Queue()
    ws_stop_event = threading.Event()

    # Pozice kruhů
    circle_radius = 70
    circle_y = SCREEN_HEIGHT // 2
    circle_xs = [SCREEN_WIDTH // 3, 2 * SCREEN_WIDTH // 3]

    # --- Websocket klient pro live počty hráčů ---
    def ws_team_count_updater():
        async def ws_loop():
            try:
                async with websockets.connect(SERVER_URL.replace('wss://', 'ws://').replace('https://', 'ws://').replace('http://', 'ws://')) as ws:
                    while not ws_stop_event.is_set():
                        await ws.send(json.dumps({"action": "get_team_counts"}))
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                            data = json.loads(msg)
                            if "team_counts" in data:
                                team_counts_queue.put(data["team_counts"])
                        except Exception:
                            pass
                        await asyncio.sleep(0.5)
            except Exception:
                pass
        asyncio.run(ws_loop())

    ws_thread = threading.Thread(target=ws_team_count_updater, daemon=True)
    ws_thread.start()

    while running:
        # Zpracuj nové počty hráčů
        try:
            while True:
                team_counts = team_counts_queue.get_nowait()
        except queue.Empty:
            pass

        screen.fill((30, 30, 30))
        title = font.render("Vyber si tým:", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))
        for i, color in enumerate(TEAM_COLORS):
            pygame.draw.circle(screen, color, (circle_xs[i], circle_y), circle_radius)
            mouse_pos = pygame.mouse.get_pos()
            if (mouse_pos[0] - circle_xs[i]) ** 2 + (mouse_pos[1] - circle_y) ** 2 < circle_radius ** 2:
                pygame.draw.circle(screen, WHITE, (circle_xs[i], circle_y), circle_radius + 6, 3)
            count_text = font.render(f"{team_counts[i]} hráčů", True, WHITE)
            screen.blit(count_text, (circle_xs[i] - count_text.get_width() // 2, circle_y + circle_radius + 10))
            name_text = font.render(TEAM_NAMES[i], True, color)
            screen.blit(name_text, (circle_xs[i] - name_text.get_width() // 2, circle_y - circle_radius - 30))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ws_stop_event.set()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i in range(2):
                    if (event.pos[0] - circle_xs[i]) ** 2 + (event.pos[1] - circle_y) ** 2 < circle_radius ** 2:
                        selected_team = i
                        running = False
        pygame.display.flip()
        clock.tick(60)
    ws_stop_event.set()
    return selected_team

# --- Před vstupem do hry zobraz výběr týmu ---
if __name__ == "__main__":
    # ...existing code...
    selected_team = show_team_selection_screen()
    if selected_team == 0:
        my_color = BABY_BLUE
        player_team = 2
    else:
        my_color = BABY_PINK
        player_team = 3
    # Spuštění hlavní asynchronní smyčky hry
    asyncio.run(game_loop())
