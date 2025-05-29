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

# Keř variables
# Generate random coordinates for the bush, avoiding map boundaries
random_bush_x = random.randint(BOUNDARY_WIDTH * TILE_SIZE, (MAP_WIDTH - BOUNDARY_WIDTH) * TILE_SIZE)
random_bush_y = random.randint(BOUNDARY_WIDTH * TILE_SIZE, (MAP_HEIGHT - BOUNDARY_WIDTH) * TILE_SIZE)
bush_pos = [random_bush_x, random_bush_y]
bush_collision_radius = player_radius * 1.25
player_hidden = False
hide_pressed = False
player_prev_pos = [player_x, player_y]

# Global variable to store bush square segment data with stable colors
bush_squares_data = []

# Function to initialize bush squares with stable random colors
def init_bush_squares():
    global bush_squares_data
    bush_squares_data = [] # Reset it to ensure stability on re-init if ever called again
    bush_collision_radius_effective = bush_collision_radius # Use the updated bush_collision_radius

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
    # The `pos` (bush_pos) is the center of the bush model
    for segment in bush_squares_data:
        # Calculate world coordinates of the square's top-left corner
        world_square_x = pos[0] + segment['offset_x'] - segment['size'] / 2
        world_square_y = pos[1] + segment['offset_y'] - segment['size'] / 2
        
        min_x = min(min_x, world_square_x)
        max_x = max(max_x, world_square_x + segment['size'])
        min_y = min(min_y, world_square_y)
        max_y = max(max_y, world_square_y + segment['size'])
    
    # Add a small buffer for the outline itself (increased for more structure)
    buffer = 8 
    surface_width = int(max_x - min_x) + 2 * buffer
    surface_height = int(max_y - min_y) + 2 * buffer
    
    # If the calculated surface is too small or invalid, use a default size
    if surface_width <= 0 or surface_height <= 0:
        surface_width = int(collision_radius * 2.5) # Fallback approximate size
        surface_height = int(collision_radius * 2.5)
        # Recalculate min_x, min_y to center the default surface on pos
        min_x = pos[0] - surface_width / 2
        min_y = pos[1] - surface_height / 2


    bush_surface_for_outline = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
    
    # Draw all the bush squares onto the temporary surface for mask generation
    # AND draw them directly to the screen for visual rendering
    for segment in bush_squares_data:
        world_x = pos[0] + segment['offset_x']
        world_y = pos[1] + segment['offset_y']

        screen_x = int(world_x - segment['size'] / 2 - camera_x + SCREEN_WIDTH // 2)
        screen_y = int(world_y - segment['size'] / 2 - camera_y + SCREEN_HEIGHT // 2)
        
        bush_color = segment['color'] # Stable color
        
        # Draw filled square without individual border to main screen
        bush_draw_surface = pygame.Surface((segment['size'], segment['size']), pygame.SRCALPHA)
        pygame.draw.rect(bush_draw_surface, (*bush_color, 255), (0, 0, segment['size'], segment['size']), 0)
        
        screen.blit(bush_draw_surface, (screen_x, screen_y))

        # Draw filled square to the temporary surface for outline generation
        draw_x_outline = int(segment['offset_x'] + pos[0] - segment['size'] / 2 - min_x + buffer)
        draw_y_outline = int(segment['offset_y'] + pos[1] - segment['size'] / 2 - min_y + buffer)
        pygame.draw.rect(bush_surface_for_outline, (*bush_color, 255), (draw_x_outline, draw_y_outline, segment['size'], segment['size']), 0)


    # Branches code removed here


    # Now, draw the outline from the temporary surface (which only has green squares)
    if bush_surface_for_outline.get_size() != (0, 0): # Ensure surface is valid
        bush_mask = pygame.mask.from_surface(bush_surface_for_outline, 50) # Adjust alpha threshold as needed
        outline_points = bush_mask.outline()

        if outline_points:
            # Translate outline points from temporary surface's local coordinates to screen coordinates
            translated_outline = []
            for p in outline_points:
                # Convert from local surface coords (relative to its top-left)
                # to world coords, then to screen coords
                world_p_x = (min_x - buffer) + p[0] # Add min_x and subtract buffer to get back to original world coord relative to top-left of the bounding box
                world_p_y = (min_y - buffer) + p[1]

                screen_p_x = int(world_p_x - camera_x + SCREEN_WIDTH // 2)
                screen_p_y = int(world_p_y - camera_y + SCREEN_HEIGHT // 2)
                translated_outline.append((screen_p_x, screen_p_y))
            
            # Draw the outline. Use a thick line for visibility
            pygame.draw.lines(screen, VERY_DARK_GREEN, True, translated_outline, 3) # Increased outline thickness


    player_near_bush = distance([player_pos[0], player_pos[1]], pos) < collision_radius + player_radius # Player radius added for better "near" detection

    return player_near_bush, pos, collision_radius # Return bush center and collision radius for collision detection

# funkce pro počítání vzdálenost mezi body (from keř.py)
def distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

# funkce na zjištění jestli je bod ve čtverci (from keř.py) - NO LONGER USED, KEPT FOR REFERENCE
def point_in_rect(point, rect):
    return (rect[0] <= point[0] <= rect[0] + rect[2] and
            rect[1] <= point[1] <= rect[1] + rect[3])

# funkce na detekování kolize s okraji a vytvořit particly
def check_bush_collision(old_pos, new_pos, bush_center, bush_radius):
    # Check if player was inside/outside and is now outside/inside the bush's collision circle
    was_inside = distance(old_pos, bush_center) < bush_radius
    is_inside = distance(new_pos, bush_center) < bush_radius
    
    # If the player crossed the boundary, generate particles
    if was_inside != is_inside:
        # Approximate collision point
        collision_x = (old_pos[0] + new_pos[0]) / 2
        collision_y = (old_pos[1] + new_pos[1]) / 2
        
        for _ in range(15): # Number of particles
            # Particles should use the general bush color scheme, not necessarily just one of the random shades for squares
            # Use BUSH_PARTICLE_SHADES for a more consistent particle color
            color = random.choice(BUSH_PARTICLE_SHADES) 
            particles.append(Particle(collision_x, collision_y, color))

# funkce pro vykreslení promptu (from keř.py, adapted for camera)
def draw_prompt(text, world_pos, camera_x, camera_y): # Added world_pos, camera_x, camera_y
    # Convert world position to screen position
    screen_x = int(world_pos[0] - camera_x + SCREEN_WIDTH // 2)
    screen_y = int(world_pos[1] - camera_y + SCREEN_HEIGHT // 2)

    # vytvoření pozadí pro text
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.center = (screen_x, screen_y)
    
    # pozadí
    background_rect = text_rect.inflate(20, 10)
    background_surface = pygame.Surface((background_rect.width, background_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(background_surface, (*BLACK, 180), (0, 0, background_rect.width, background_rect.height))
    pygame.draw.rect(background_surface, BLUE, (0, 0, background_rect.width, background_rect.height), 2)
    
    # vykreslení na obrazovku
    screen.blit(background_surface, background_rect.topleft)
    screen.blit(text_surface, text_rect)

# Funkce pro vykreslení mapy
def draw_map(screen, camera_x, camera_y):
    screen.fill(DARKER_GREEN)
   
    viditelnych_dlazdic_x = (SCREEN_WIDTH // TILE_SIZE) + 10
    viditelnych_dlazdic_y = (SCREEN_HEIGHT // TILE_SIZE) + 10
   
    kamera_tile_x = camera_x // TILE_SIZE
    kamera_tile_y = camera_y // TILE_SIZE
   
    start_x = max(0, int(kamera_tile_x - viditelnych_dlazdic_x // 2)) # Adjusted for visible tiles
    end_x = min(MAP_WIDTH, int(kamera_tile_x + viditelnych_dlazdic_x // 2 + 1)) # Adjusted for visible tiles
    start_y = max(0, int(kamera_tile_y - viditelnych_dlazdic_y // 2)) # Adjusted for visible tiles
    end_y = min(MAP_HEIGHT, int(kamera_tile_y + viditelnych_dlazdic_y // 2 + 1)) # Adjusted for visible tiles
   
    # Vykreslení dlaždic
    for y_tile in range(start_y, end_y): # Renamed y to y_tile to avoid conflict
        for x_tile in range(start_x, end_x): # Renamed x to x_tile to avoid conflict
            screen_x = (x_tile * TILE_SIZE - camera_x) + SCREEN_WIDTH // 2
            screen_y = (y_tile * TILE_SIZE - camera_y) + SCREEN_HEIGHT // 2
           
            if -TILE_SIZE <= screen_x <= SCREEN_WIDTH+TILE_SIZE and -TILE_SIZE <= screen_y <= SCREEN_HEIGHT+TILE_SIZE:
                barva = vypocitej_tmavost_hranice(x_tile, y_tile)
                pygame.draw.rect(screen, barva, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
   
    # Vykreslení obrazových objektů
    for img in images:
        # Calculate image's center in world coordinates
        img_world_center_x = img['x'] * TILE_SIZE + img['width'] / 2
        img_world_center_y = img['y'] * TILE_SIZE + img['height'] / 2

        # Convert image's world center to screen coordinates
        screen_x = int(img_world_center_x - camera_x + SCREEN_WIDTH // 2 - img['width'] / 2)
        screen_y = int(img_world_center_y - camera_y + SCREEN_HEIGHT // 2 - img['height'] / 2)
        
        # Only blit if it's potentially on screen
        if -img['width'] < screen_x < SCREEN_WIDTH and -img['height'] < screen_y < SCREEN_HEIGHT:
            screen.blit(img['image'], (screen_x, screen_y))

# Funkce pro vykreslení hráče a zbraně
def draw_player(screen, offset_x, offset_y):
    global player_hidden # No need for player_alpha here, it's calculated before draw
    
    if player_hidden: # Don't draw if hidden
        return

    screen_x = int(player_x - offset_x + SCREEN_WIDTH // 2)
    screen_y = int(player_y - offset_y + SCREEN_HEIGHT // 2)
   
    # Determine player alpha based on proximity to bush
    player_alpha = 255
    # Calculate distance to bush using world coordinates
    dist_to_bush = distance([player_x, player_y], bush_pos)
    # The condition for player alpha should also be based on the bush_collision_radius
    if dist_to_bush < bush_collision_radius: # If near bush, make slightly transparent
        player_alpha = 200
    
    if player_texture:
        texture_to_draw = player_texture.copy()
        
        if player_team == 3:
            texture_to_draw.fill(BLUE, special_flags=pygame.BLEND_RGBA_MULT)
        
        # Apply alpha to player texture
        texture_to_draw.set_alpha(player_alpha)

        rotated_texture = pygame.transform.rotate(texture_to_draw, -player_angle)
        rot_rect = rotated_texture.get_rect(center=(screen_x, screen_y))
        screen.blit(rotated_texture, rot_rect.topleft)
        
        if current_weapon in weapon_textures:
            weapon_info = WEAPONS[current_weapon]
            weapon_texture = weapon_textures[current_weapon]
            
            angle_rad = math.radians(player_angle - 90)
            offset_distance = weapon_info["offset_x"]
            
            weapon_offset_x = math.cos(angle_rad) * offset_distance
            weapon_offset_y = math.sin(angle_rad) * offset_distance
            
            weapon_x = screen_x + weapon_offset_x
            weapon_y = screen_y + weapon_offset_y
            
            rotated_weapon = pygame.transform.rotate(weapon_texture, -player_angle)
            weapon_rect = rotated_weapon.get_rect(center=(weapon_x, weapon_y))
            
            screen.blit(rotated_weapon, weapon_rect.topleft)
    else:
        # Fallback circle, also with alpha
        color = (*(RED if player_team == 2 else BLUE), player_alpha)
        player_surface = pygame.Surface((player_radius*2, player_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(player_surface, color, (player_radius, player_radius), player_radius)
        screen.blit(player_surface, (screen_x - player_radius, screen_y - player_radius))

# Funkce pro vykreslení ostatních hráčů z multiplayer
def draw_other_players(screen, camera_x, camera_y):
    for player_id, pos in players_interpolated.items():
        if isinstance(pos, dict) and pos.get('hidden', False): # Don't draw if hidden on server
            continue

        if isinstance(pos, list) or isinstance(pos, tuple):
            net_x, net_y = pos[0], pos[1]
        elif isinstance(pos, dict):
            net_x, net_y = pos['x'], pos['y']
        else:
            continue # Skip invalid player data

        if player_id != my_id:
            # Convert network coordinates (which are now map coordinates) to screen coordinates
            screen_x = int(net_x - camera_x + SCREEN_WIDTH // 2)
            screen_y = int(net_y - camera_y + SCREEN_HEIGHT // 2)
            
            # Vykreslení ostatních hráčů (simple green rect for now)
            pygame.draw.rect(screen, GREEN, (screen_x - player_radius//2, screen_y - player_radius//2, player_radius, player_radius))

# New function to draw the arrow pointing to the bush
def draw_bush_arrow(screen, player_x, player_y, bush_x, bush_y, camera_x, camera_y):
    # Convert player and bush world coordinates to screen coordinates
    player_screen_x = int(player_x - camera_x + SCREEN_WIDTH // 2)
    player_screen_y = int(player_y - camera_y + SCREEN_HEIGHT // 2)
    bush_screen_x = int(bush_x - camera_x + SCREEN_WIDTH // 2)
    bush_screen_y = int(bush_y - camera_y + SCREEN_HEIGHT // 2)

    # Calculate angle from player to bush
    dx = bush_screen_x - player_screen_x
    dy = bush_screen_y - player_screen_y
    angle_rad = math.atan2(dy, dx)

    # Calculate arrow position (e.g., 50 pixels from player's center)
    arrow_distance_from_player = 100 # How far from the player the arrow should be
    arrow_x = player_screen_x + arrow_distance_from_player * math.cos(angle_rad)
    arrow_y = player_screen_y + arrow_distance_from_player * math.sin(angle_rad)

    # Draw the arrow as a triangle
    arrow_size = 20
    
    # Define triangle points relative to arrow_x, arrow_y
    # Pointing towards the bush
    point1 = (arrow_x + arrow_size * math.cos(angle_rad + math.pi/2), 
              arrow_y + arrow_size * math.sin(angle_rad + math.pi/2))
    point2 = (arrow_x + arrow_size * math.cos(angle_rad - math.pi/2), 
              arrow_y + arrow_size * math.sin(angle_rad - math.pi/2))
    point3 = (arrow_x + arrow_size * 2 * math.cos(angle_rad), 
              arrow_y + arrow_size * 2 * math.sin(angle_rad))

    pygame.draw.polygon(screen, RED, [point1, point2, point3])
    
    # Optional: Draw a small circle at the base for better visibility
    pygame.draw.circle(screen, RED, (int(arrow_x), int(arrow_y)), arrow_size // 3)


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
    global player_angle, current_weapon, weapon_cooldowns
    global player_hidden, hide_pressed, player_prev_pos, particles, bush_pos, bush_collision_radius
    global show_bush_arrow # Declare global for the new variable

    # Připojení k serveru
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(SERVER_URL) as ws:
                connected = True
                status = "Připojeno"
                print("Připojeno k serveru")

                # Počáteční odeslání pozice pro registraci (using map coordinates now)
                await ws.send_json({"x": player_x, "y": player_y})
                last_update_time = time.time()

                # Hlavní herní smyčka
                running = True
                while running:
                    current_time = time.time()

                    # Zpracování událostí
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                            running = False
                        elif event.type == pygame.K_t:
                            player_tile_x, player_tile_y = get_player_tile_position()
                            add_image("images/tree1.png", player_tile_x + 2, player_tile_y + 2, 2.0)
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_e: # Handling E key for hide/unhide
                                if not hide_pressed:
                                    hide_pressed = True
                            # Check for Ctrl+A
                            if event.key == pygame.K_a and (pygame.key.get_mods() & pygame.KMOD_LCTRL or pygame.key.get_mods() & pygame.KMOD_RCTRL):
                                show_bush_arrow = not show_bush_arrow # Toggle visibility
                                print(f"Bush arrow visibility: {show_bush_arrow}")
                        elif event.type == pygame.KEYUP:
                            if event.key == pygame.K_e: # Handling E key for hide/unhide
                                hide_pressed = False
                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            if event.button == 1:
                                if not player_hidden: # Can only shoot if not hidden
                                    shoot(current_weapon)
                            elif event.button == 4:
                                change_weapon(1)
                            elif event.button == 5:
                                change_weapon(-1)

                    # Zpracování vstupů
                    keys = pygame.key.get_pressed()
                    dx, dy = 0, 0

                    if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= PLAYER_SPEED
                    if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += PLAYER_SPEED
                    if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= PLAYER_SPEED
                    if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += PLAYER_SPEED

                    if dx != 0 and dy != 0:
                        dx *= 0.7071
                        dy *= 0.7071

                    # Aktualizace stavu pohybu
                    # Only consider movement if player is not hidden
                    moved = (dx != 0 or dy != 0) and not player_hidden
                    is_moving = moved

                    # Provedení pohybu
                    if moved:
                        move_player(dx, dy)
                    
                    # Update previous player position for bush collision detection
                    # This was moved into move_player, but needs to be careful if move_player returns False
                    # so player_prev_pos needs to be updated outside this conditional too.
                    # For now, it's handled inside move_player.

                    # Výpočet úhlu mezi hráčem a kurzorem myši
                    player_screen_x = int(SCREEN_WIDTH // 2)
                    player_screen_y = int(SCREEN_HEIGHT // 2)
                    player_angle = calculate_angle_to_mouse(player_screen_x, player_screen_y)
                    
                    # Aktualizace cooldownů zbraní
                    for weapon in weapon_cooldowns:
                        if weapon_cooldowns[weapon] > 0:
                            weapon_cooldowns[weapon] -= 1

                    # Posílání dat serveru (při pohybu nebo po uplynutí intervalu)
                    # Send player_x, player_y which are world coordinates
                    if moved or current_time - last_update_time >= UPDATE_INTERVAL:
                        start_time = time.time()
                        await ws.send_json({"x": player_x, "y": player_y, "hidden": player_hidden}) # Send hidden state
                        last_update_time = current_time
                    
                    # Přijímání dat od serveru (non-blocking)
                    try:
                        msg = await asyncio.wait_for(ws.receive(), 0.01)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            players_prev = players_interpolated.copy() if players_interpolated else {}
                            
                            data = json.loads(msg.data)
                            players = data

                            if moved:
                                response_time = (time.time() - start_time) * 1000

                            if my_id is None:
                                # Find our ID based on the sent world coordinates
                                for pid, p_data in players.items():
                                    if isinstance(p_data, list) or isinstance(p_data, tuple): # Old format
                                        if abs(p_data[0] - player_x) < TILE_SIZE and abs(p_data[1] - player_y) < TILE_SIZE: # Adjusted tolerance
                                            my_id = pid
                                            print(f"Moje ID: {my_id}")
                                            break
                                    elif isinstance(p_data, dict): # New format with 'hidden'
                                        if abs(p_data['x'] - player_x) < TILE_SIZE and abs(p_data['y'] - player_y) < TILE_SIZE:
                                            my_id = pid
                                            print(f"Moje ID: {my_id}")
                                            break
                                
                            # Aktualizace našeho hráče v datech (lokální přepis)
                            if my_id:
                                players[my_id] = {"x": player_x, "y": player_y, "hidden": player_hidden} # Ensure our local state is correct in 'players'
                                
                            if not players_prev:
                                players_prev = players.copy()
                                players_interpolated = players.copy()

                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            connected = False
                            status = "Spojení ukončeno"
                            break
                    except asyncio.TimeoutError:
                        pass
                    
                    # Update status
                    if is_moving:
                        status = "Připojeno (pohyb)"
                    else:
                        status = "Připojeno (stabilní)"
                    
                    # Interpolace pozic ostatních hráčů
                    players_interpolated = {}
                    for player_id, p_data in players.items():
                        if isinstance(p_data, list) or isinstance(p_data, tuple): # Handle old format from server if necessary
                            new_x, new_y = p_data[0], p_data[1]
                            new_hidden = False # Default to not hidden if old format
                        elif isinstance(p_data, dict): # New format
                            new_x, new_y = p_data['x'], p_data['y']
                            new_hidden = p_data.get('hidden', False) # Default to False if 'hidden' not present
                        else:
                            continue # Skip invalid player data

                        if player_id == my_id:
                            # For our player, use exact local position and hidden state
                            players_interpolated[player_id] = {"x": player_x, "y": player_y, "hidden": player_hidden}
                        elif player_id in players_prev and isinstance(players_prev[player_id], (dict, list)):
                            # For other players, interpolate for smooth movement
                            prev_data = players_prev[player_id]
                            if isinstance(prev_data, list): # Old format
                                prev_x, prev_y = prev_data[0], prev_data[1]
                            else: # New format
                                prev_x, prev_y = prev_data['x'], prev_data['y']

                            interpolated_x = prev_x + (new_x - prev_x) * other_players_interpolation_factor
                            interpolated_y = prev_y + (new_y - prev_y) * other_players_interpolation_factor
                            players_interpolated[player_id] = {"x": interpolated_x, "y": interpolated_y, "hidden": new_hidden}
                        else:
                            # If no previous position, use current
                            players_interpolated[player_id] = {"x": new_x, "y": new_y, "hidden": new_hidden}


                    # Vykreslení
                    draw_map(screen, player_x, player_y)
                    
                    # Get bush collision data from draw_boxy_bush
                    player_near_bush, bush_col_center, bush_col_radius = draw_boxy_bush(bush_pos, bush_collision_radius, [player_x, player_y], player_hidden, player_x, player_y)

                    # Check bush collision for particles using the new collision data
                    if ([player_x, player_y] != player_prev_pos) and not player_hidden: # Only if player moved and is not hidden
                        check_bush_collision(player_prev_pos, [player_x, player_y], bush_col_center, bush_col_radius)

                    # Handle hide/unhide logic
                    if hide_pressed:
                        # Use the same 'player_near_bush' from draw_boxy_bush which now uses the more accurate collision circle
                        if player_near_bush and not player_hidden:
                            player_hidden = True
                            for _ in range(20):
                                color = random.choice(BUSH_PARTICLE_SHADES) # Use BUSH_PARTICLE_SHADES for particles
                                particles.append(Particle(player_x, player_y, color))
                        elif player_hidden:
                            player_hidden = False
                            for _ in range(20):
                                color = random.choice(BUSH_PARTICLE_SHADES) # Use BUSH_PARTICLE_SHADES for particles
                                particles.append(Particle(player_x, player_y, color))
                        hide_pressed = False
                    
                    # Update and draw particles
                    for particle in particles[:]:
                        particle.update()
                        if particle.is_dead():
                            particles.remove(particle)
                        else:
                            particle.draw(screen, player_x, player_y) # Pass camera coords

                    draw_player(screen, player_x, player_y) # This function now handles player_hidden status
                    draw_other_players(screen, player_x, player_y)
                    
                    # Draw prompts for bush interaction
                    # These also use 'player_near_bush' for consistency
                    if player_near_bush and not player_hidden:
                        draw_prompt("Press E to hide", [player_x, player_y - 50], player_x, player_y)
                    elif player_hidden:
                        draw_prompt("Press E to exit", [bush_pos[0], bush_pos[1] - 80], player_x, player_y)
                    
                    # Draw the bush arrow if visible
                    if show_bush_arrow:
                        draw_bush_arrow(screen, player_x, player_y, bush_pos[0], bush_pos[1], player_x, player_y)

                    # Vykreslení UI
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