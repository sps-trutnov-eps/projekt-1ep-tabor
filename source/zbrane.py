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
 
# Konstanty
TILE_SIZE = 40
BOUNDARY_WIDTH = 5
PLAYER_SPEED = 4
MAP_WIDTH = 100
MAP_HEIGHT = 100
PLAYER_SIZE_MULTIPLIER = 2.5  # Pevně nastavená velikost hráče na 3x
 
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
 
# Inicializace herních proměnných
images = []  # Seznam všech obrazových objektů na mapě
 
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
 
# Funkce pro vykreslení hráče
def draw_player(screen, offset_x, offset_y):
    screen_x = int(player_x - offset_x + SCREEN_WIDTH // 2)
    screen_y = int(player_y - offset_y + SCREEN_HEIGHT // 2)
   
    if player_texture:
        # Vykreslení textury hráče (pro oba týmy)
        texture_x = screen_x - player_size // 2
        texture_y = screen_y - player_size // 2
        
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
    else:
        # Záloha - kruh pro případ, že by textura nebyla k dispozici
        color = RED if player_team == 2 else BLUE
        pygame.draw.circle(screen, color, (screen_x, screen_y), player_radius)
 
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

# Hlavní herní smyčka
def main():
    global player_x, player_y, player_angle
   
    running = True
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
   
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
       
        # Vykreslení
        draw_map(screen, player_x, player_y)
        draw_player(screen, player_x, player_y)
       
        # Zobrazení pouze FPS
        fps_text = font.render(f"FPS: {int(fps)}", True, (255, 255, 255))
        screen.blit(fps_text, (10, 10))
       
        pygame.display.flip()
        clock.tick(60)
   
    pygame.quit()
    sys.exit()
 
# Spuštění hry
if __name__ == "__main__":
    main()