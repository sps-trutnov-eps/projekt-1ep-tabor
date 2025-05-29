import pygame
import asyncio
import aiohttp
import json
import random
import time
import sys
import os
import math

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
VERY_DARK_GREEN = (0, 30, 0) # New very dark green for the outline
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19) # Brown color for branches (no longer used for drawing, but kept in constants)

# Keř specific colors - Updated
BUSH_GREEN = (40, 100, 40) # Unified color for all bush squares

# BUSH_SHADES is no longer used for stable square assignment, but can still be used for particles if desired
BUSH_PARTICLE_SHADES = [BUSH_GREEN, (30, 85, 30)] # Combining new shades with a middle one

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

# Inicializace hráče
player_x = MAP_WIDTH // 2 * TILE_SIZE + TILE_SIZE // 2  # Pro mapu
player_y = MAP_HEIGHT // 2 * TILE_SIZE + TILE_SIZE // 2  # Pro mapu
x = player_x # Initial sync for network
y = player_y # Initial sync for network
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
if not os.path.exists("gun"):
    os.makedirs("gun")

# Načtení textury hráče z gun folderu
player_texture = None
try:
    player_texture = pygame.image.load(os.path.join("gun", "player.png")).convert_alpha()
    player_texture = pygame.transform.scale(player_texture, (player_size, player_size))
    print(f"Textura hráče úspěšně načtena z gun/player.png (velikost: {player_size}x{player_size})")
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
        weapon_path = os.path.join("gun", weapon_info["image"])
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

# Keř variables (now a list of bushes)
bush_positions = []
bush_collision_radii = [] # Each bush can have its own radius, though here it's uniform
NUM_BUSHES = 4 # Define the number of bushes

for _ in range(NUM_BUSHES):
    random_bush_x = random.randint(BOUNDARY_WIDTH * TILE_SIZE, (MAP_WIDTH - BOUNDARY_WIDTH) * TILE_SIZE)
    random_bush_y = random.randint(BOUNDARY_WIDTH * TILE_SIZE, (MAP_HEIGHT - BOUNDARY_WIDTH) * TILE_SIZE)
    bush_positions.append([random_bush_x, random_bush_y])
    bush_collision_radii.append(player_radius * 1.25) # Uniform radius for all bushes

player_hidden = False # True if player is hidden in ANY bush
hide_pressed = False
player_prev_pos = [player_x, player_y]
current_hiding_bush_index = -1 # Stores the index of the bush the player is currently hiding in

# Global variable to store bush square segment data with stable colors
bush_squares_data = []

# Function to initialize bush squares with stable random colors
def init_bush_squares():
    global bush_squares_data
    bush_squares_data = [] # Reset it to ensure stability on re-init if ever called again
    bush_collision_radius_effective = player_radius * 1.25 # Use a fixed effective radius for bush shape generation

    # Define base square offsets and sizes (relative to center of the bush)
    # These definitions are adjusted to create a more organic, bushy shape.
    # More varied offsets and sizes, with some overlaps to avoid gaps and make it look dense.
    square_definitions = [
        # Central dense parts
        (0, 0, bush_collision_radius_effective * 1.3),
        (bush_collision_radius_effective * 0.4, bush_collision_radius_effective * 0.1, bush_collision_radius_effective * 1.0),
        (-bush_collision_radius_effective * 0.4, bush_collision_radius_effective * 0.1, bush_collision_radius_effective * 1.0),
        (0, bush_collision_radius_effective * 0.5, bush_collision_radius_effective * 0.9),
        (0, -bush_collision_radius_effective * 0.5, bush_collision_radius_effective * 0.9),

        # More irregular mid-range parts
        (bush_collision_radius_effective * 0.7, bush_collision_radius_effective * 0.3, bush_collision_radius_effective * 0.8),
        (-bush_collision_radius_effective * 0.7, bush_collision_radius_effective * 0.3, bush_collision_radius_effective * 0.8),
        (bush_collision_radius_effective * 0.3, bush_collision_radius_effective * 0.7, bush_collision_radius_effective * 0.8),
        (-bush_collision_radius_effective * 0.3, bush_collision_radius_effective * 0.7, bush_collision_radius_effective * 0.8),
        (bush_collision_radius_effective * 0.7, -bush_collision_radius_effective * 0.3, bush_collision_radius_effective * 0.8),
        (-bush_collision_radius_effective * 0.7, -bush_collision_radius_effective * 0.3, bush_collision_radius_effective * 0.8),
        (bush_collision_radius_effective * 0.3, -bush_collision_radius_effective * 0.7, bush_collision_radius_effective * 0.8),
        (-bush_collision_radius_effective * 0.3, -bush_collision_radius_effective * 0.7, bush_collision_radius_effective * 0.8),

        # Outer, more sparse and varied pieces
        (bush_collision_radius_effective * 1.0, 0, bush_collision_radius_effective * 0.6),
        (-bush_collision_radius_effective * 1.0, 0, bush_collision_radius_effective * 0.6),
        (0, bush_collision_radius_effective * 1.0, bush_collision_radius_effective * 0.6),
        (0, -bush_collision_radius_effective * 1.0, bush_collision_radius_effective * 0.6),
        
        (bush_collision_radius_effective * 0.8, bush_collision_radius_effective * 0.8, bush_collision_radius_effective * 0.7),
        (-bush_collision_radius_effective * 0.8, bush_collision_radius_effective * 0.8, bush_collision_radius_effective * 0.7),
        (bush_collision_radius_effective * 0.8, -bush_collision_radius_effective * 0.8, bush_collision_radius_effective * 0.7),
        (-bush_collision_radius_effective * 0.8, -bush_collision_radius_effective * 0.8, bush_collision_radius_effective * 0.7),

        # Even more small, irregular pieces to fill gaps and add density
        (bush_collision_radius_effective * 0.6, bush_collision_radius_effective * 0.9, bush_collision_radius_effective * 0.5),
        (-bush_collision_radius_effective * 0.6, bush_collision_radius_effective * 0.9, bush_collision_radius_effective * 0.5),
        (bush_collision_radius_effective * 0.9, bush_collision_radius_effective * 0.6, bush_collision_radius_effective * 0.5),
        (-bush_collision_radius_effective * 0.9, bush_collision_radius_effective * 0.6, bush_collision_radius_effective * 0.5),

        (bush_collision_radius_effective * 0.5, -bush_collision_radius_effective * 0.9, bush_collision_radius_effective * 0.5),
        (-bush_collision_radius_effective * 0.5, -bush_collision_radius_effective * 0.9, bush_collision_radius_effective * 0.5),
        (bush_collision_radius_effective * 0.9, -bush_collision_radius_effective * 0.5, bush_collision_radius_effective * 0.5),
        (-bush_collision_radius_effective * 0.9, -bush_collision_radius_effective * 0.5, bush_collision_radius_effective * 0.5),

        # Additional scattered smaller pieces for more irregularity
        (bush_collision_radius_effective * 0.2, bush_collision_radius_effective * 1.1, bush_collision_radius_effective * 0.4),
        (-bush_collision_radius_effective * 0.2, bush_collision_radius_effective * 1.1, bush_collision_radius_effective * 0.4),
        (bush_collision_radius_effective * 1.1, bush_collision_radius_effective * 0.2, bush_collision_radius_effective * 0.4),
        (-bush_collision_radius_effective * 1.1, bush_collision_radius_effective * 0.2, bush_collision_radius_effective * 0.4),
        (bush_collision_radius_effective * 0.9, -bush_collision_radius_effective * 0.1, bush_collision_radius_effective * 0.5),
        (-bush_collision_radius_effective * 0.9, -bush_collision_radius_effective * 0.1, bush_collision_radius_effective * 0.5),
        (bush_collision_radius_effective * 0.1, -bush_collision_radius_effective * 0.9, bush_collision_radius_effective * 0.5),
        (-bush_collision_radius_effective * 0.1, -bush_collision_radius_effective * 0.9, bush_collision_radius_effective * 0.5),
    ]

    for offset_x, offset_y, size in square_definitions:
        bush_color = BUSH_GREEN # All squares are now the same color
        bush_squares_data.append({'offset_x': offset_x, 'offset_y': offset_y, 'size': size, 'color': bush_color})

# Initialize bush squares once
init_bush_squares()

# Arrow to bush variables
show_bush_arrow = False # New variable to control arrow visibility

# Particle class (from keř.py)
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.radius = player_radius / 4
        self.color = color
        self.alpha = 255
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(-2, 0)
        self.gravity = 0.1
        self.lifetime = random.randint(30, 60)
    
    def update(self):
        self.vy += self.gravity
        self.x  += self.vx
        self.y  += self.vy
        self.lifetime -= 1
        self.alpha = int((self.lifetime / 60) * 255)
        if self.lifetime <= 0:
            self.alpha = 0
        self.radius = max(1, self.radius * 0.98)
    
    def draw(self, surface, camera_x, camera_y): # Added camera_x, camera_y
        if self.alpha > 0:
            screen_x = int(self.x - camera_x + SCREEN_WIDTH // 2)
            screen_y = int(self.y - camera_y + SCREEN_HEIGHT // 2)
            particle_surface = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, (*self.color, self.alpha), 
                             (self.radius, self.radius), self.radius)
            surface.blit(particle_surface, (screen_x - self.radius, screen_y - self.radius))
            
    def is_dead(self):
        return self.lifetime <= 0

particles = [] # list na aktivní particly

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
    player_hitbox = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2) # Adjusted hitbox size for circles
    for img in images:
        # Optimization: only check collision for nearby images
        if abs((img['x'] * TILE_SIZE + img['width'] / 2) - x) < TILE_SIZE * 3 and \
           abs((img['y'] * TILE_SIZE + img['height'] / 2) - y) < TILE_SIZE * 3:
            if img['hitbox'].colliderect(player_hitbox):
                return True
    return False

# Funkce pro pohyb hráče v herním světě
def move_player(dx, dy):
    global player_x, player_y, x, y, player_prev_pos, player_hidden
    if player_hidden: # Cannot move if hidden
        return False

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
    
    player_prev_pos = [player_x, player_y] # Save previous position before updating
    player_x = new_x
    player_y = new_y
    # Aktualizace pozice pro síťovou komunikaci (relativní k rozměrům okna)
    # These are not truly relative to window anymore, but map coords for network
    x = player_x
    y = player_y
    return True

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

# Vykreslení keře (reskinned to a rounded, jagged shape using squares)
def draw_boxy_bush(pos, collision_radius, player_pos, player_hidden, camera_x, camera_y):
    # Determine the bounding box of the entire bush from its squares
    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')

    # Calculate overall bounding box for the temporary surface for outline
    # The `pos` (bush_pos) is the center of the bush.
    # The `offset_x` and `offset_y` for each square are relative to `pos`.
    for sq_data in bush_squares_data:
        abs_x = pos[0] + sq_data['offset_x']
        abs_y = pos[1] + sq_data['offset_y']
        size = sq_data['size']
        min_x = min(min_x, abs_x - size / 2)
        max_x = max(max_x, abs_x + size / 2)
        min_y = min(min_y, abs_y - size / 2)
        max_y = max(max_y, abs_y + size / 2)

    # Add a small buffer for the outline
    outline_buffer = 5
    min_x -= outline_buffer
    max_x += outline_buffer
    min_y -= outline_buffer
    max_y += outline_buffer

    # Convert world coordinates to screen coordinates for the temporary surface
    screen_min_x = int(min_x - camera_x + SCREEN_WIDTH // 2)
    screen_min_y = int(min_y - camera_y + SCREEN_HEIGHT // 2)

    # Calculate dimensions of the temporary surface
    temp_surface_width = int(max_x - min_x)
    temp_surface_height = int(max_y - min_y)

    # Create a temporary surface with alpha for drawing the bush and its outline
    temp_surface = pygame.Surface((temp_surface_width, temp_surface_height), pygame.SRCALPHA)
    
    # Draw the outline first
    # Draw slightly larger squares in VERY_DARK_GREEN for the outline effect
    for sq_data in bush_squares_data:
        # Adjust position relative to the temporary surface's top-left corner
        draw_x = int((pos[0] + sq_data['offset_x'] - sq_data['size'] / 2) - min_x)
        draw_y = int((pos[1] + sq_data['offset_y'] - sq_data['size'] / 2) - min_y)
        draw_size = int(sq_data['size'] + 2 * outline_buffer) # Make outline slightly larger
        pygame.draw.rect(temp_surface, VERY_DARK_GREEN, (draw_x, draw_y, draw_size, draw_size), border_radius=int(draw_size * 0.3))

    # Then draw the main bush squares
    for sq_data in bush_squares_data:
        # Adjust position relative to the temporary surface's top-left corner
        draw_x = int((pos[0] + sq_data['offset_x'] - sq_data['size'] / 2) - min_x)
        draw_y = int((pos[1] + sq_data['offset_y'] - sq_data['size'] / 2) - min_y)
        draw_size = int(sq_data['size'])
        pygame.draw.rect(temp_surface, sq_data['color'], (draw_x, draw_y, draw_size, draw_size), border_radius=int(draw_size * 0.3))

    # Blit the temporary surface onto the main screen
    screen.blit(temp_surface, (screen_min_x, screen_min_y))

# Draw arrow to bush
def draw_bush_arrow(surface, player_x, player_y, bush_x, bush_y, camera_x, camera_y):
    # Calculate screen coordinates for player and bush
    player_screen_x = SCREEN_WIDTH // 2
    player_screen_y = SCREEN_HEIGHT // 2
    bush_screen_x = int(bush_x - camera_x + SCREEN_WIDTH // 2)
    bush_screen_y = int(bush_y - camera_y + SCREEN_HEIGHT // 2)

    # Calculate distance and angle
    distance = math.sqrt((bush_x - player_x)**2 + (bush_y - player_y)**2)
    angle = math.atan2(bush_screen_y - player_screen_y, bush_screen_x - player_screen_x)

    # Define arrow properties
    arrow_length = 50
    arrow_thickness = 3
    arrow_color = YELLOW
    
    # Position the arrow near the edge of the screen, pointing towards the bush
    # Adjust position to be visible but not covering the player
    
    # Define a radius for the arrow to appear around the player
    arrow_circle_radius = min(SCREEN_WIDTH, SCREEN_HEIGHT) / 2 - 20 # Keep it inside the screen boundary

    arrow_start_x = player_screen_x + arrow_circle_radius * math.cos(angle)
    arrow_start_y = player_screen_y + arrow_circle_radius * math.sin(angle)
    
    arrow_end_x = player_screen_x + (arrow_circle_radius + arrow_length) * math.cos(angle)
    arrow_end_y = player_screen_y + (arrow_circle_radius + arrow_length) * math.sin(angle)

    # Draw the arrow line
    pygame.draw.line(surface, arrow_color, (arrow_start_x, arrow_start_y), (arrow_end_x, arrow_end_y), arrow_thickness)

    # Draw the arrowhead (triangle)
    # Calculate points for the arrowhead
    arrowhead_size = 15
    point1_x = arrow_end_x
    point1_y = arrow_end_y
    point2_x = arrow_end_x - arrowhead_size * math.cos(angle - math.pi / 6)
    point2_y = arrow_end_y - arrowhead_size * math.sin(angle - math.pi / 6)
    point3_x = arrow_end_x - arrowhead_size * math.cos(angle + math.pi / 6)
    point3_y = arrow_end_y - arrowhead_size * math.sin(angle + math.pi / 6)

    pygame.draw.polygon(surface, arrow_color, [(point1_x, point1_y), (point2_x, point2_y), (point3_x, point3_y)])

# Funkce pro vykreslení hráče
def draw_player(surface, player_data, camera_x, camera_y, is_self=False):
    p_x = player_data['x']
    p_y = player_data['y']
    p_color = player_data['color']
    p_angle = player_data.get('angle', 0) # Get angle, default to 0 if not present
    p_hidden = player_data.get('hidden', False) # Get hidden status, default to False

    # Interpolace pro plynulý pohyb ostatních hráčů
    if not is_self and player_data['id'] in players_interpolated:
        interpolated_x = players_interpolated[player_data['id']]['x']
        interpolated_y = players_interpolated[player_data['id']]['y']
        
        target_x = p_x
        target_y = p_y

        interpolated_x += (target_x - interpolated_x) * other_players_interpolation_factor
        interpolated_y += (target_y - interpolated_y) * other_players_interpolation_factor
        
        p_x = interpolated_x
        p_y = interpolated_y
        players_interpolated[player_data['id']]['x'] = interpolated_x
        players_interpolated[player_data['id']]['y'] = interpolated_y
    else:
        # Initialize interpolated position for new players or for self
        players_interpolated[player_data['id']] = {'x': p_x, 'y': p_y}

    # World coordinates to screen coordinates
    screen_x = int(p_x - camera_x + SCREEN_WIDTH // 2)
    screen_y = int(p_y - camera_y + SCREEN_HEIGHT // 2)

    # Rotate player texture
    rotated_player_texture = pygame.transform.rotate(player_texture, -p_angle) # Negative angle for correct rotation
    new_rect = rotated_player_texture.get_rect(center=(screen_x, screen_y))

    # Apply transparency if hidden and not self
    if p_hidden: # Only make other players hidden, self remains visible to self
        alpha = 0 # 100 out of 255 for partial transparency
        rotated_player_texture.set_alpha(alpha)
    else:
        rotated_player_texture.set_alpha(255) # Full opacity

    surface.blit(rotated_player_texture, new_rect)

    # Draw weapon
    current_weapon_texture = weapon_textures.get(player_data['current_weapon'])
    if current_weapon_texture:
        # Calculate weapon position relative to player
        weapon_info = WEAPONS[player_data['current_weapon']]
        offset_x = weapon_info["offset_x"]
        offset_y = weapon_info["offset_y"]
        
        # Calculate weapon rotation
        weapon_angle_rad = math.radians(p_angle)
        
        # Apply rotation to offset
        rotated_offset_x = offset_x * math.cos(weapon_angle_rad) - offset_y * math.sin(weapon_angle_rad)
        rotated_offset_y = offset_x * math.sin(weapon_angle_rad) + offset_y * math.cos(weapon_angle_rad)

        weapon_screen_x = screen_x + rotated_offset_x
        weapon_screen_y = screen_y + rotated_offset_y

        # Rotate weapon texture
        rotated_weapon_texture = pygame.transform.rotate(current_weapon_texture, -p_angle)
        if p_hidden:
            rotated_weapon_texture.set_alpha(alpha) # Use the same alpha value as the player
        else:
            rotated_weapon_texture.set_alpha(255)
        weapon_rect = rotated_weapon_texture.get_rect(center=(weapon_screen_x, weapon_screen_y))
        surface.blit(rotated_weapon_texture, weapon_rect)


    # Draw player ID above head
    player_id_text = font.render(f"ID: {player_data['id']}", True, WHITE)
    id_rect = player_id_text.get_rect(center=(screen_x, screen_y - player_radius - 10))
    surface.blit(player_id_text, id_rect)

    # Draw player team color behind player ID
    if player_data['team'] == 2:
        team_color_text = font.render(f"Team A", True, RED)
    elif player_data['team'] == 3:
        team_color_text = font.render(f"Team B", True, BLUE)
    else:
        team_color_text = font.render(f"No Team", True, WHITE)
    team_rect = team_color_text.get_rect(center=(screen_x, screen_y - player_radius - 30))
    surface.blit(team_color_text, team_rect)

# Funkce pro vykreslení promptu
def draw_prompt(text, pos, player_world_x, player_world_y, camera_x, camera_y):
    # Convert world coordinates to screen coordinates
    screen_x = int(pos[0] - camera_x + SCREEN_WIDTH // 2)
    screen_y = int(pos[1] - camera_y + SCREEN_HEIGHT // 2)

    prompt_text = font.render(text, True, YELLOW)
    prompt_rect = prompt_text.get_rect(center=(screen_x, screen_y))

    # --- ADDED: Draw semi-transparent background for the prompt ---
    background_color = BLACK # Or any dark color you prefer
    padding = 5 # Padding around the text
    background_rect = pygame.Rect(prompt_rect.left - padding, prompt_rect.top - padding,
                                  prompt_rect.width + 2 * padding, prompt_rect.height + 2 * padding)
    
    # Create a surface for the background with alpha
    background_surface = pygame.Surface(background_rect.size, pygame.SRCALPHA)
    background_surface.fill((*background_color, 180)) # 180 out of 255 for transparency

    screen.blit(background_surface, background_rect.topleft)
    # --- END ADDED SECTION ---

    screen.blit(prompt_text, prompt_rect)

# Funkce pro vykreslení UI
def draw_ui(surface, font):
    # Current Weapon Display
    weapon_text = font.render(f"Weapon: {current_weapon}", True, WHITE)
    surface.blit(weapon_text, (10, 10))

    # Cooldown Display
    cooldown_time = weapon_cooldowns[current_weapon]
    if cooldown_time > 0:
        cooldown_display = f"Cooldown: {cooldown_time / 60:.1f}s" # Convert frames to seconds
        cooldown_color = RED
    else:
        cooldown_display = "Ready"
        cooldown_color = GREEN
    cooldown_text = font.render(cooldown_display, True, cooldown_color)
    surface.blit(cooldown_text, (10, 30))

    # Response Time Display
    if response_time is not None:
        response_text = font.render(f"Ping: {int(response_time*1000)}ms", True, WHITE)
        surface.blit(response_text, (SCREEN_WIDTH - response_text.get_width() - 10, 10))
    
    # Connection Status
    status_text = font.render(f"Status: {status}", True, WHITE)
    surface.blit(status_text, (SCREEN_WIDTH - status_text.get_width() - 10, 30))

# Main game loop
async def main():
    global player_x, player_y, player_angle, my_id, connected, status, response_time, current_weapon_index, current_weapon, hide_pressed, player_hidden, show_bush_arrow, last_update_time, current_hiding_bush_index, particles

    uri = SERVER_URL
    
    session = aiohttp.ClientSession()

    async with session.ws_connect(uri) as ws:
        connected = True
        status = "Připojeno"
        print("Připojeno k serveru.")

        # První odeslání dat o hráči po připojení
        await ws.send_json({
            'type': 'player_update',
            'x': player_x,
            'y': player_y,
            'color': my_color,
            'angle': player_angle,
            'team': player_team,
            'current_weapon': current_weapon,
            'hidden': player_hidden, # Send initial hidden status
            # Important: If server is authoritative for bush positions, they should be received here.
            # For now, client-side bushes are random.
        })

        async def send_player_data():
            global player_x, player_y, player_angle, my_id, connected, status, response_time, current_weapon_index, current_weapon, hide_pressed, player_hidden, show_bush_arrow, last_update_time, current_hiding_bush_index, particles

            if connected:
                current_time = time.time()
                if is_moving or (current_time - last_update_time > UPDATE_INTERVAL):
                    try:
                        data = {
                            'type': 'player_update',
                            'x': player_x,
                            'y': player_y,
                            'color': my_color,
                            'angle': player_angle,
                            'team': player_team,
                            'current_weapon': current_weapon,
                            'hidden': player_hidden,
                            'current_hiding_bush_index': current_hiding_bush_index
                        }
                        await ws.send_json(data)
                        last_update_time = current_time
                    except Exception as e:
                        print(f"Chyba při odesílání dat: {e}")
                        connected = False

        async def receive_messages():
            global player_x, player_y, player_angle, my_id, connected, status, response_time, current_weapon_index, current_weapon, hide_pressed, player_hidden, show_bush_arrow, last_update_time, current_hiding_bush_index, particles
            try:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        message = json.loads(msg.data)
                        if message['type'] == 'init' and my_id is None:
                            my_id = message['id']
                            print(f"Moje ID: {my_id}")
                            # If server sends initial bush positions, uncomment and process here
                            # if 'bush_positions' in message:
                            #     bush_positions = message['bush_positions']
                            #     # If radii are also server-sided
                            #     # bush_collision_radii = message.get('bush_collision_radii', [player_radius * 1.25] * len(bush_positions))

                        elif message['type'] == 'players_data':
                            new_players = {}
                            for player_id, p_data in message['players'].items():
                                if player_id != my_id:
                                    # Store previous position for interpolation
                                    if player_id not in players_prev:
                                        players_prev[player_id] = {'x': p_data['x'], 'y': p_data['y']}
                                    else:
                                        players_prev[player_id]['x'] = players.get(player_id, {}).get('x', p_data['x'])
                                        players_prev[player_id]['y'] = players.get(player_id, {}).get('y', p_data['y'])
                                    new_players[player_id] = p_data
                                else:
                                    # For the client's own player, ensure its own hidden state is synchronized from server
                                    # The server is authoritative for the hidden state.
                                    player_hidden = p_data.get('hidden', False)
                                    current_hiding_bush_index = p_data.get('current_hiding_bush_index', -1)
                            players = new_players
                            # Calculate response time
                            if 'timestamp' in message:
                                response_time = time.time() - message['timestamp']
                        elif message['type'] == 'player_disconnected':
                            if message['id'] in players:
                                del players[message['id']]
                                if message['id'] in players_interpolated:
                                    del players_interpolated[message['id']]
                                if message['id'] in players_prev:
                                    del players_prev[message['id']]
                                print(f"Hráč {message['id']} odpojen.")
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"Chyba ve websocketu: {ws.exception()}")
                        connected = False
                        break
            except Exception as e:
                print(f"Chyba při přijímání zpráv: {e}")
                connected = False

        # Spuštění úloh na pozadí
        producer_task = asyncio.create_task(send_player_data())
        consumer_task = asyncio.create_task(receive_messages())

        # Game loop
        try:
            while True:
                player_near_any_bush = False
                for i, bush_pos in enumerate(bush_positions):
                    dist_to_bush = math.sqrt((player_x - bush_pos[0])**2 + (player_y - bush_pos[1])**2)
                    if dist_to_bush < bush_collision_radii[i] + player_radius:
                        player_near_any_bush = True
                        break # Found a bush, no need to check others

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        print("Hra ukončena uživatelem.")
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_q:
                            current_weapon_index = (current_weapon_index - 1) % len(weapon_names)
                            current_weapon = weapon_names[current_weapon_index]
                        elif event.key == pygame.K_e:
                            # Bush interaction
                            if not hide_pressed: # Only toggle if key is pressed and was not pressed before
                                if player_near_any_bush and not player_hidden: # Try to hide
                                    # Find which bush the player is entering
                                    for i, bush_pos in enumerate(bush_positions):
                                        dist_to_bush = math.sqrt((player_x - bush_pos[0])**2 + (player_y - bush_pos[1])**2)
                                        if dist_to_bush < bush_collision_radii[i] + player_radius:
                                            current_hiding_bush_index = i
                                            break
                                    player_hidden = True
                                    
                                elif player_hidden: # Try to unhide (only if currently hidden)
                                    player_hidden = False
                                    current_hiding_bush_index = -1 # No longer hiding in any bush

                                hide_pressed = True # Mark as pressed
                                
                                # Instantly send update to server about hidden status change
                                await ws.send_json({
                                    'type': 'player_update',
                                    'x': player_x,
                                    'y': player_y,
                                    'color': my_color,
                                    'angle': player_angle,
                                    'team': player_team,
                                    'current_weapon': current_weapon,
                                    'hidden': player_hidden,
                                    'current_hiding_bush_index': current_hiding_bush_index
                                })
                                # Generate particles on hide/unhide from the relevant bush
                                particle_spawn_pos = bush_positions[current_hiding_bush_index] if current_hiding_bush_index != -1 else [player_x, player_y]
                                for _ in range(20):
                                    particles.append(Particle(particle_spawn_pos[0], particle_spawn_pos[1], random.choice(BUSH_PARTICLE_SHADES)))
                        # Weapon firing (example, not fully implemented for server-side)
                        elif event.key == pygame.K_SPACE:
                            if weapon_cooldowns[current_weapon] <= 0:
                                # Logic to fire weapon and reset cooldown
                                weapon_cooldowns[current_weapon] = WEAPONS[current_weapon]["cooldown"]
                                # print(f"{current_weapon} Fired!") # For debugging
                    elif event.type == pygame.KEYUP:
                        if event.key == pygame.K_e:
                            hide_pressed = False # Reset hide_pressed when E is released

                # Update weapon cooldowns
                for name in weapon_cooldowns:
                    if weapon_cooldowns[name] > 0:
                        weapon_cooldowns[name] -= 1

                # Pohyb hráče
                keys = pygame.key.get_pressed()
                dx, dy = 0, 0
                if keys[pygame.K_a]:
                    dx -= PLAYER_SPEED
                if keys[pygame.K_d]:
                    dx += PLAYER_SPEED
                if keys[pygame.K_w]:
                    dy -= PLAYER_SPEED
                if keys[pygame.K_s]:
                    dy += PLAYER_SPEED

                if dx != 0 or dy != 0:
                    is_moving = True
                    move_player(dx, dy)
                    # Update player angle based on movement direction
                    if dx == 0 and dy < 0: # Up
                        player_angle = 90
                    elif dx == 0 and dy > 0: # Down
                        player_angle = 270
                    elif dx < 0 and dy == 0: # Left
                        player_angle = 180
                    elif dx > 0 and dy == 0: # Right
                        player_angle = 0
                    elif dx > 0 and dy < 0: # Up-Right
                        player_angle = 45
                    elif dx < 0 and dy < 0: # Up-Left
                        player_angle = 135
                    elif dx > 0 and dy > 0: # Down-Right
                        player_angle = 315
                    elif dx < 0 and dy > 0: # Down-Left
                        player_angle = 225
                else:
                    is_moving = False

                # Vypocet kamery
                camera_x = player_x
                camera_y = player_y

                screen.fill(DARK_GREEN)

                # Vykreslení hranic a mapy
                for y_tile in range(MAP_HEIGHT):
                    for x_tile in range(MAP_WIDTH):
                        tile_color = vypocitej_tmavost_hranice(x_tile, y_tile)
                        pygame.draw.rect(screen, tile_color, (x_tile * TILE_SIZE - camera_x + SCREEN_WIDTH // 2,
                                                            y_tile * TILE_SIZE - camera_y + SCREEN_HEIGHT // 2,
                                                            TILE_SIZE, TILE_SIZE))

                # Vykreslení obrázků
                for img in images:
                    img_screen_x = int(img['x'] * TILE_SIZE - camera_x + SCREEN_WIDTH // 2)
                    img_screen_y = int(img['y'] * TILE_SIZE - camera_y + SCREEN_HEIGHT // 2)
                    screen.blit(img['image'], (img_screen_x, img_screen_y))
                
                # Update and draw particles
                for i, p in enumerate(particles):
                    p.update()
                    p.draw(screen, camera_x, camera_y)
                particles = [p for p in particles if not p.is_dead()]

                # Draw all bushes
                for i, bush_pos_single in enumerate(bush_positions):
                    draw_boxy_bush(bush_pos_single, bush_collision_radii[i], [player_x, player_y], player_hidden, camera_x, camera_y)

                # Vykreslení ostatních hráčů
                for p_id, p_data in players.items():
                    draw_player(screen, p_data, camera_x, camera_y, is_self=False)

                # Vykreslení našeho hráče (always draw on top, always visible to self)
                draw_player(screen, {'id': my_id, 'x': player_x, 'y': player_y, 'color': my_color, 'angle': player_angle, 'team': player_team, 'current_weapon': current_weapon, 'hidden': player_hidden}, camera_x, camera_y, is_self=True)

                # Show hide prompt
                # Find the closest bush to display the prompt or arrow
                closest_bush_index = -1
                min_dist_to_bush = float('inf')
                for i, bush_pos_single in enumerate(bush_positions):
                    dist = math.sqrt((player_x - bush_pos_single[0])**2 + (player_y - bush_pos_single[1])**2)
                    if dist < min_dist_to_bush:
                        min_dist_to_bush = dist
                        closest_bush_index = i

                if closest_bush_index != -1:
                    current_bush_pos = bush_positions[closest_bush_index]
                    current_bush_radius = bush_collision_radii[closest_bush_index]
                    
                    if min_dist_to_bush < current_bush_radius + player_radius and not player_hidden:
                        draw_prompt("Press E to hide", [player_x, player_y - 50], player_x, player_y, camera_x, camera_y)
                    elif player_hidden and closest_bush_index == current_hiding_bush_index: # Only show 'exit' prompt if hiding in this specific bush
                        draw_prompt("Press E to exit", [current_bush_pos[0], current_bush_pos[1] - 80], player_x, player_y, camera_x, camera_y)
                    
                    # Show arrow to bush if not hidden and not near closest bush, and within a certain range
                    if not player_hidden and min_dist_to_bush > current_bush_radius + player_radius and min_dist_to_bush < 500: # Example range
                        show_bush_arrow = True 
                        draw_bush_arrow(screen, player_x, player_y, current_bush_pos[0], current_bush_pos[1], camera_x, camera_y)
                    else:
                        show_bush_arrow = False
                else: # No bushes found or too far
                    show_bush_arrow = False


                # Vykreslení UI
                draw_ui(screen, font)
                
                # FPS počítadlo
                fps = clock.get_fps()
                fps_text = font.render(f"FPS: {fps:.1f}", True, YELLOW)
                screen.blit(fps_text, (600, 10))

                pygame.display.flip()
                clock.tick(60)
                
                await asyncio.sleep(0) # Yield control to asyncio event loop

        except aiohttp.ClientError as e:
            connected = False
            status = f"Chyba: {str(e)}"
            print(f"Chyba připojení: {e}")
        except Exception as e:
            connected = False
            status = f"Chyba: {str(e)}"
            print(f"Neočekávaná chyba: {e}")

    # Clean up
    await session.close()
    print("Spojení se serverem uzavřeno.")

if __name__ == "__main__":
    asyncio.run(main())