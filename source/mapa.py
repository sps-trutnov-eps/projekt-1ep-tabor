import pygame
import sys
import os
import math
 
# Inicializace Pygame
pygame.init()
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Capture The Flag - Les (Simplified)")
 
# Barvy
BLACK = (0, 0, 0)
DARK_GREEN = (0, 80, 0)
DARKER_GREEN = (0, 50, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
 
# Konstanty
TILE_SIZE = 40
BOUNDARY_WIDTH = 5
PLAYER_SPEED = 4
MAP_WIDTH = 100
MAP_HEIGHT = 100
PLAYER_SIZE_MULTIPLIER = 2.5  # Pevně nastavená velikost hráče na 2.5x

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
 
# Vytvoření složky pro obrázky, pokud neexistuje
if not os.path.exists("images"):
    os.makedirs("images")
 
# Načtení textury hráče z gun folderu
player_texture = None
player_size = int(TILE_SIZE * PLAYER_SIZE_MULTIPLIER)
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
 
# Inicializace herních proměnných
images = []  # Seznam všech obrazových objektů na mapě
current_weapon_index = 0
weapon_names = list(WEAPONS.keys())
current_weapon = weapon_names[current_weapon_index]
weapon_cooldowns = {name: 0 for name in WEAPONS}
 
# Inicializace hráče
player_x = MAP_WIDTH // 2 * TILE_SIZE + TILE_SIZE // 2
player_y = MAP_HEIGHT // 2 * TILE_SIZE + TILE_SIZE // 2
player_team = 2  # 2 = tým A, 3 = tým B
player_radius = player_size // 2
player_angle = 0  # Úhel natočení hráče (ve stupních)
 
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
 
# Funkce pro pohyb hráče
def move_player(dx, dy):
    global player_x, player_y
   
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
    screen.blit(instructions, (20, 60))
 
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

# Hlavní herní smyčka
def main():
    global player_x, player_y, player_angle, current_weapon, current_weapon_index, weapon_cooldowns
   
    running = True
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)
   
    while running:
        # Měření FPS
        fps = clock.get_fps()
       
        # Zpracování událostí
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_t:
                player_tile_x, player_tile_y = get_player_tile_position()
                add_image("images/tree1.png", player_tile_x + 2, player_tile_y + 2, 2.0)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Levé tlačítko myši pro střelbu
                if event.button == 1:
                    shoot(current_weapon)
                # Kolečko myši pro změnu zbraně
                elif event.button == 4:  # Scroll nahoru
                    change_weapon(1)
                elif event.button == 5:  # Scroll dolů
                    change_weapon(-1)
       
        # Pohyb hráče pomocí kláves
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
       
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= PLAYER_SPEED
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += PLAYER_SPEED
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= PLAYER_SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += PLAYER_SPEED
           
        # Diagonální pohyb normalizujeme
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
           
        # Provedení pohybu
        move_player(dx, dy)
        
        # Výpočet úhlu mezi hráčem a kurzorem myši
        player_screen_x = int(SCREEN_WIDTH // 2)
        player_screen_y = int(SCREEN_HEIGHT // 2)
        player_angle = calculate_angle_to_mouse(player_screen_x, player_screen_y)
        
        # Aktualizace cooldownů zbraní
        for weapon in weapon_cooldowns:
            if weapon_cooldowns[weapon] > 0:
                weapon_cooldowns[weapon] -= 1
       
        # Vykreslení
        draw_map(screen, player_x, player_y)
        draw_player(screen, player_x, player_y)
        
        # Vykreslení UI
        draw_ui(screen, font)
       
        # Zobrazení FPS
        fps_text = font.render(f"FPS: {int(fps)}", True, WHITE)
        screen.blit(fps_text, (10, 10))
       
        pygame.display.flip()
        clock.tick(60)
   
    pygame.quit()
    sys.exit()
 
# Spuštění hry
if __name__ == "__main__":
    main()