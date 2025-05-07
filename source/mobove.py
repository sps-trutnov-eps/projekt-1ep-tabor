import sys
import math
import pygame
import random
pygame.init()

# Window settings
ROZLISENI_OKNA_X = 800
ROZLISENI_OKNA_Y = 600
okno = pygame.display.set_mode((ROZLISENI_OKNA_X, ROZLISENI_OKNA_Y))
pygame.display.set_caption('Scrolling Map')

# Game settings
player_size = 30
player_x = 0  
player_y = 0
speed = 10

# Map boundaries
MIN_X, MAX_X = -3000, 3000
MIN_Y, MAX_Y = -3000, 3000

#npc
jeleni = []
max_jelenu = 5
jelen_velikost = 20
jelen_barva = (150, 75, 0)
JELEN_UHYB = 3  # Snížená hodnota pro plynulejší pohyb
UTOK_VZDALENOST = 150

# Function to render coordinates
def draw_coords():
    font = pygame.font.Font(None, 36)
    text = font.render(f"Souřadnice: {player_x}, {player_y}", True, (200, 0, 0))
    okno.blit(text, (10, 10))

# Funkce pro spawn jelena s více parametry
def spawn_jelen():
    x = random.randint(MIN_X, MAX_X)
    y = random.randint(MIN_Y, MAX_Y)
    jeleni.append({
        'x': x,
        'y': y,
        'target_x': x,
        'target_y': y,
        'wait_timer': random.randint(0, 300),
        'speed': random.uniform(1.0, 2.0),  # Rychlost každého jelena
        'is_fleeing': False,  # Příznak, zda jelen utíká
        'fleeing_timer': 0,  # Časovač útěku
        'flee_speed_multiplier': 1.5  # Násobitel rychlosti při útěku
    })

def pohni_jeleny():
    for jelen in jeleni:
        # Aktualizace časovače útěku
        if jelen['fleeing_timer'] > 0:
            jelen['fleeing_timer'] -= 1
            if jelen['fleeing_timer'] <= 0:
                jelen['is_fleeing'] = False

        # Kontrola blízkosti hráče - aktivace útěku
        vzdalenost = math.hypot(jelen['x'] - player_x, jelen['y'] - player_y)
        if vzdalenost < UTOK_VZDALENOST:
            if not jelen['is_fleeing']:  # Začni utíkat pouze pokud ještě neutíká
                jelen['is_fleeing'] = True
                jelen['fleeing_timer'] = random.randint(60, 120)
                
                # Vypočítej směr útěku - pryč od hráče
                utek_x = jelen['x'] - player_x
                utek_y = jelen['y'] - player_y
                utek_dist = math.hypot(utek_x, utek_y) or 1
                
                # Nastav nový cíl jako směr útěku
                flee_distance = random.randint(200, 300)  # Náhodná vzdálenost útěku
                jelen['target_x'] = jelen['x'] + (utek_x / utek_dist) * flee_distance
                jelen['target_y'] = jelen['y'] + (utek_y / utek_dist) * flee_distance
                
                # Omez cíl na hranice mapy
                jelen['target_x'] = max(MIN_X, min(MAX_X, jelen['target_x']))
                jelen['target_y'] = max(MIN_Y, min(MAX_Y, jelen['target_y']))
                
                jelen['wait_timer'] = 0  # Okamžitě začni utíkat
        
        # Pokud jelen čeká, zmenši timer
        if jelen['wait_timer'] > 0:
            jelen['wait_timer'] -= 1
            continue
            
        # Výpočet směru pohybu k cíli
        dx = jelen['target_x'] - jelen['x']
        dy = jelen['target_y'] - jelen['y']
        dist = math.hypot(dx, dy)
            
        # Pokud je jelen dost blízko cíli a neutíká, začni čekat a vyber nové místo
        if dist < 3 and not jelen['is_fleeing']:
            jelen['wait_timer'] = 300  # cca 5 sekund při 60 FPS
            offset_x = random.randint(-100, 100)
            offset_y = random.randint(-100, 100)
            jelen['target_x'] = max(MIN_X, min(MAX_X, jelen['x'] + offset_x))
            jelen['target_y'] = max(MIN_Y, min(MAX_Y, jelen['y'] + offset_y))
        else:
            # Pohyb směrem k cíli
            if dist > 0:  # Prevence dělení nulou
                dx /= dist
                dy /= dist
                
                # Základní rychlost + bonus při útěku
                current_speed = jelen['speed']
                if jelen['is_fleeing']:
                    current_speed *= jelen['flee_speed_multiplier']
                    
                jelen['x'] += dx * current_speed
                jelen['y'] += dy * current_speed

# Main loop
clock = pygame.time.Clock()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()

    # Get key inputs
    keys = pygame.key.get_pressed()
    if keys[pygame.K_a]:
        player_x = max(MIN_X, player_x - speed)
    if keys[pygame.K_d]:
        player_x = min(MAX_X, player_x + speed)
    if keys[pygame.K_w]:
        player_y = max(MIN_Y, player_y - speed)
    if keys[pygame.K_s]:
        player_y = min(MAX_Y, player_y + speed)
    
    # Clear screen
    okno.fill((40, 200, 250))

    # Draw grid (stationary, but moves relative to player)
    for x in range(MIN_X, MAX_X + 1, 50):
        pygame.draw.line(okno, (0, 0, 0), (x - player_x + ROZLISENI_OKNA_X // 2, 0), (x - player_x + ROZLISENI_OKNA_X // 2, ROZLISENI_OKNA_Y))
    for y in range(MIN_Y, MAX_Y + 1, 50):
        pygame.draw.line(okno, (0, 0, 0), (0, y - player_y + ROZLISENI_OKNA_Y // 2), (ROZLISENI_OKNA_X, y - player_y + ROZLISENI_OKNA_Y // 2))

    # Draw player (always in center)
    pygame.draw.rect(okno, (100, 10, 120), (ROZLISENI_OKNA_X // 2 - player_size // 2, ROZLISENI_OKNA_Y // 2 - player_size // 2, player_size, player_size))
    
    # Spawn jelenů
    if len(jeleni) < max_jelenu and random.random() < 0.01:
        spawn_jelen()

    # Pohyb jelenů
    pohni_jeleny()

    # Vykreslení jelenů
    for jelen in jeleni:
        screen_x = jelen['x'] - player_x + ROZLISENI_OKNA_X // 2
        screen_y = jelen['y'] - player_y + ROZLISENI_OKNA_Y // 2
        
        # Změna barvy jelena, když utíká
        barva = jelen_barva
        if jelen['is_fleeing']:
            barva = (200, 75, 0)  # Světlejší barva při útěku
            
        pygame.draw.circle(okno, barva, (int(screen_x), int(screen_y)), jelen_velikost)
    
    draw_coords()
    pygame.display.update()
    clock.tick(60)