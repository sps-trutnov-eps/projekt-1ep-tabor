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

# Player health system
player_max_health = 100
player_health = player_max_health
player_damage_cooldown = 0
DAMAGE_COOLDOWN_MAX = 30
health_bar_width = 50
health_bar_height = 8

# Map boundaries
MIN_X, MAX_X = -3000, 3000
MIN_Y, MAX_Y = -3000, 3000

#npc
jeleni = []
max_jelenu = 5
jelen_velikost = 20
jelen_barva = (150, 75, 0)
JELEN_UHYB = 3  
UTOK_VZDALENOST = 150
ATTACK_DISTANCE = 90  
ATTACK_DAMAGE = 40    
ATTACK_COOLDOWN = 120  

# Function to render coordinates
def draw_coords():
    font = pygame.font.Font(None, 36)
    text = font.render(f"Souřadnice: {player_x}, {player_y}", True, (200, 0, 0))
    okno.blit(text, (10, 10))

# Function to draw health bar above player
def draw_health_bar():
    # Calculate bar position (above player)
    bar_x = ROZLISENI_OKNA_X // 2 - health_bar_width // 2
    bar_y = ROZLISENI_OKNA_Y // 2 - player_size // 2 - health_bar_height - 5
    
    # Draw red background (base health bar)
    pygame.draw.rect(okno, (255, 0, 0), (bar_x, bar_y, health_bar_width, health_bar_height))
    
    # Calculate health percentage and current width
    health_percentage = player_health / player_max_health
    current_health_width = int(health_bar_width * health_percentage)
    
    # Draw green health bar on top (overlapping the red one)
    pygame.draw.rect(okno, (0, 255, 0), (bar_x, bar_y, current_health_width, health_bar_height))
    
    # Draw border
    pygame.draw.rect(okno, (0, 0, 0), (bar_x, bar_y, health_bar_width, health_bar_height), 1)

# Function to respawn player
def respawn_player():
    global player_x, player_y, player_health
    player_x = 0
    player_y = 0
    player_health = player_max_health

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
        'speed': random.uniform(1.0, 2.5),  # Zvýšená maximální rychlost
        'is_fleeing': False,  # Příznak, zda jelen utíká
        'fleeing_timer': 0,  # Časovač útěku
        'flee_speed_multiplier': 1.8,  # Zvýšený násobitel rychlosti při útěku
        'movement_style': random.choice(['normal', 'zigzag', 'circular']),  # Styl pohybu
        'wiggle_factor': random.uniform(0.2, 0.8),  # Faktor klikatosti pohybu
        'direction_change_timer': 0,  # Časovač pro náhodnou změnu směru
        'grazing': False,  # Příznak, zda se jelen pase
        'grazing_timer': 0,  # Časovač pasení
        'state': 'idle',  # Stav jelena: idle, walking, grazing, fleeing
        'state_timer': random.randint(60, 180),  # Časovač pro změnu stavu
        'attack_cooldown': 0,  # Cooldown between attacks
        'is_attacking': False,  # Whether deer is currently attacking
        'attack_timer': 0  # Timer for attack animation
    })

def pohni_jeleny():
    global player_health, player_damage_cooldown
    
    for jelen in jeleni:
        # Aktualizace časovačů
        if jelen['fleeing_timer'] > 0:
            jelen['fleeing_timer'] -= 1
            if jelen['fleeing_timer'] <= 0:
                jelen['is_fleeing'] = False
                jelen['state'] = 'walking'
                jelen['state_timer'] = random.randint(180, 300)
                
        if jelen['direction_change_timer'] > 0:
            jelen['direction_change_timer'] -= 1
            
        if jelen['state_timer'] > 0:
            jelen['state_timer'] -= 1
            
        if jelen['grazing_timer'] > 0:
            jelen['grazing_timer'] -= 1
            if jelen['grazing_timer'] <= 0:
                jelen['grazing'] = False
                
        if jelen['attack_cooldown'] > 0:
            jelen['attack_cooldown'] -= 1
            
        if jelen['attack_timer'] > 0:
            jelen['attack_timer'] -= 1
            if jelen['attack_timer'] <= 0:
                jelen['is_attacking'] = False
                
        # Kontrola blízkosti hráče - aktivace útěku nebo útoku
        vzdalenost = math.hypot(jelen['x'] - player_x, jelen['y'] - player_y)
        
        # If deer is very close to player, it might attack instead of fleeing
        if vzdalenost < ATTACK_DISTANCE and jelen['attack_cooldown'] <= 0 and player_damage_cooldown <= 0:
            # Deer attacks the player
            jelen['is_attacking'] = True
            jelen['attack_timer'] = 30  # Half a second attack animation
            jelen['attack_cooldown'] = ATTACK_COOLDOWN
            
            # Player takes damage
            player_health -= ATTACK_DAMAGE
            player_damage_cooldown = DAMAGE_COOLDOWN_MAX
            
            # Flash the screen red to indicate damage
            pygame.draw.rect(okno, (255, 0, 0, 128), (0, 0, ROZLISENI_OKNA_X, ROZLISENI_OKNA_Y))
            
            # Check if player died
            if player_health <= 0:
                respawn_player()
            
            # After attack, deer runs away
            jelen['is_fleeing'] = True
            jelen['state'] = 'fleeing'
            jelen['fleeing_timer'] = random.randint(180, 300)  # Longer flee after attack
            
            # Calculate direction away from player
            utek_x = jelen['x'] - player_x
            utek_y = jelen['y'] - player_y
            utek_dist = math.hypot(utek_x, utek_y) or 1
            
            # Set new target away from player
            flee_distance = random.randint(400, 600)  # Greater flee distance after attack
            jelen['target_x'] = jelen['x'] + (utek_x / utek_dist) * flee_distance
            jelen['target_y'] = jelen['y'] + (utek_y / utek_dist) * flee_distance
            
            # Add random deviation to flee direction
            jelen['target_x'] += random.randint(-100, 100)
            jelen['target_y'] += random.randint(-100, 100)
            
            # Limit target to map boundaries
            jelen['target_x'] = max(MIN_X, min(MAX_X, jelen['target_x']))
            jelen['target_y'] = max(MIN_Y, min(MAX_Y, jelen['target_y']))
            
        elif vzdalenost < UTOK_VZDALENOST:
            if not jelen['is_fleeing']:  # Začni utíkat pouze pokud ještě neutíká
                jelen['is_fleeing'] = True
                jelen['state'] = 'fleeing'
                jelen['fleeing_timer'] = random.randint(120, 240)  # Delší útěk
                
                # Vypočítej směr útěku - pryč od hráče
                utek_x = jelen['x'] - player_x
                utek_y = jelen['y'] - player_y
                utek_dist = math.hypot(utek_x, utek_y) or 1
                
                # Nastav nový cíl jako směr útěku
                flee_distance = random.randint(300, 500)  # Větší vzdálenost útěku
                jelen['target_x'] = jelen['x'] + (utek_x / utek_dist) * flee_distance
                jelen['target_y'] = jelen['y'] + (utek_y / utek_dist) * flee_distance
                
                # Přidej náhodnou odchylku ve směru útěku
                jelen['target_x'] += random.randint(-100, 100)
                jelen['target_y'] += random.randint(-100, 100)
                
                # Omez cíl na hranice mapy
                jelen['target_x'] = max(MIN_X, min(MAX_X, jelen['target_x']))
                jelen['target_y'] = max(MIN_Y, min(MAX_Y, jelen['target_y']))
                
                jelen['wait_timer'] = 0  # Okamžitě začni utíkat
        
        # Správa stavů jelena
        if jelen['state_timer'] <= 0 and not jelen['is_fleeing']:
            # Náhodná změna stavu
            if jelen['state'] == 'idle':
                jelen['state'] = random.choice(['walking', 'grazing'])
                if jelen['state'] == 'walking':
                    # Nastav nový cíl pro pohyb
                    offset_x = random.randint(-200, 200)
                    offset_y = random.randint(-200, 200)
                    jelen['target_x'] = max(MIN_X, min(MAX_X, jelen['x'] + offset_x))
                    jelen['target_y'] = max(MIN_Y, min(MAX_Y, jelen['y'] + offset_y))
                    jelen['movement_style'] = random.choice(['normal', 'zigzag', 'circular'])
                    jelen['state_timer'] = random.randint(180, 300)
                else:  # grazing
                    jelen['grazing'] = True
                    jelen['grazing_timer'] = random.randint(300, 600)
                    jelen['state_timer'] = random.randint(300, 600)
            elif jelen['state'] == 'walking':
                jelen['state'] = random.choice(['idle', 'grazing'])
                jelen['state_timer'] = random.randint(120, 240)
                if jelen['state'] == 'grazing':
                    jelen['grazing'] = True
                    jelen['grazing_timer'] = random.randint(300, 600)
            elif jelen['state'] == 'grazing':
                jelen['state'] = random.choice(['idle', 'walking'])
                jelen['grazing'] = False
                if jelen['state'] == 'walking':
                    # Nastav nový cíl pro pohyb
                    offset_x = random.randint(-200, 200)
                    offset_y = random.randint(-200, 200)
                    jelen['target_x'] = max(MIN_X, min(MAX_X, jelen['x'] + offset_x))
                    jelen['target_y'] = max(MIN_Y, min(MAX_Y, jelen['y'] + offset_y))
                    jelen['movement_style'] = random.choice(['normal', 'zigzag', 'circular'])
                    jelen['state_timer'] = random.randint(180, 300)
                else:
                    jelen['state_timer'] = random.randint(120, 240)
        
        # Pokud jelen čeká nebo se pase, proveď pouze malé pohyby
        if jelen['state'] == 'idle' and not jelen['is_fleeing']:
            # Občas udělej malý pohyb i při stání
            if random.random() < 0.05:
                jelen['x'] += random.uniform(-0.5, 0.5)
                jelen['y'] += random.uniform(-0.5, 0.5)
            continue
        
        if jelen['grazing'] and not jelen['is_fleeing']:
            # Při pasení dělej malé náhodné pohyby
            if random.random() < 0.1:
                jelen['x'] += random.uniform(-1.0, 1.0)
                jelen['y'] += random.uniform(-1.0, 1.0)
            continue
            
        # Výpočet směru pohybu k cíli
        dx = jelen['target_x'] - jelen['x']
        dy = jelen['target_y'] - jelen['y']
        dist = math.hypot(dx, dy)
            
        # Pokud je jelen dost blízko cíli a neutíká, začni čekat a vyber nové místo
        if dist < 5 and not jelen['is_fleeing']:
            jelen['state'] = 'idle'
            jelen['state_timer'] = random.randint(120, 240)
            # Možná přejdi rovnou do pasení
            if random.random() < 0.3:
                jelen['state'] = 'grazing'
                jelen['grazing'] = True
                jelen['grazing_timer'] = random.randint(300, 600)
                jelen['state_timer'] = random.randint(300, 600)
        else:
            # Pohyb směrem k cíli
            if dist > 0:  # Prevence dělení nulou
                dx /= dist
                dy /= dist
                
                # Aplikuj různé styly pohybu
                if jelen['movement_style'] == 'zigzag' and not jelen['is_fleeing']:
                    # Klikatý pohyb - přidej náhodnou odchylku kolmo ke směru
                    perp_x = -dy * jelen['wiggle_factor'] * math.sin(pygame.time.get_ticks() / 200)
                    perp_y = dx * jelen['wiggle_factor'] * math.sin(pygame.time.get_ticks() / 200)
                    dx += perp_x
                    dy += perp_y
                elif jelen['movement_style'] == 'circular' and not jelen['is_fleeing']:
                    # Krouživý pohyb - přidej rotující odchylku
                    angle = pygame.time.get_ticks() / 500
                    perp_x = -dy * jelen['wiggle_factor'] * math.sin(angle)
                    perp_y = dx * jelen['wiggle_factor'] * math.sin(angle)
                    dx += perp_x
                    dy += perp_y
                
                # Náhodné malé odchylky pro přirozenější pohyb
                if random.random() < 0.1 and not jelen['is_fleeing']:
                    dx += random.uniform(-0.2, 0.2)
                    dy += random.uniform(-0.2, 0.2)
                
                # Náhodná větší změna směru občas
                if jelen['direction_change_timer'] <= 0 and random.random() < 0.01 and not jelen['is_fleeing']:
                    jelen['direction_change_timer'] = random.randint(30, 60)
                    dx += random.uniform(-0.5, 0.5)
                    dy += random.uniform(-0.5, 0.5)
                
                # Normalizuj směr po všech úpravách
                magnitude = math.hypot(dx, dy) or 1
                dx /= magnitude
                dy /= magnitude
                
                # Základní rychlost + bonus při útěku
                current_speed = jelen['speed']
                if jelen['is_fleeing']:
                    current_speed *= jelen['flee_speed_multiplier']
                elif jelen['state'] == 'walking':
                    # Občas zrychli nebo zpomal při normální chůzi
                    if random.random() < 0.05:
                        current_speed *= random.uniform(0.8, 1.2)
                    
                jelen['x'] += dx * current_speed
                jelen['y'] += dy * current_speed
                
                # Zajistí, že jelen zůstane v hranicích mapy
                jelen['x'] = max(MIN_X, min(MAX_X, jelen['x']))
                jelen['y'] = max(MIN_Y, min(MAX_Y, jelen['y']))

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

    # Update damage cooldown
    if player_damage_cooldown > 0:
        player_damage_cooldown -= 1

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
    player_color = (100, 10, 120)
    if player_damage_cooldown > 0:
        # Flash player when damaged
        if player_damage_cooldown % 10 < 5:  # Create blinking effect
            player_color = (255, 0, 0)
    
    pygame.draw.rect(okno, player_color, (ROZLISENI_OKNA_X // 2 - player_size // 2, ROZLISENI_OKNA_Y // 2 - player_size // 2, player_size, player_size))
    
    # Spawn jelenů
    if len(jeleni) < max_jelenu and random.random() < 0.01:
        spawn_jelen()

    # Pohyb jelenů
    pohni_jeleny()

    # Vykreslení jelenů
    for jelen in jeleni:
        screen_x = jelen['x'] - player_x + ROZLISENI_OKNA_X // 2
        screen_y = jelen['y'] - player_y + ROZLISENI_OKNA_Y // 2
        
        # Změna barvy jelena podle stavu
        barva = jelen_barva
        if jelen['is_attacking']:
            barva = (255, 50, 0)  # Bright red-orange when attacking
        elif jelen['is_fleeing']:
            barva = (200, 75, 0)  # Světlejší barva při útěku
        elif jelen['grazing']:
            barva = (120, 60, 0)  # Tmavší barva při pasení
        elif jelen['state'] == 'idle':
            barva = (140, 70, 0)  # Mírně odlišná barva při stání
        
        # Make deer slightly larger when attacking    
        velikost = jelen_velikost
        if jelen['is_attacking']:
            velikost = jelen_velikost * 1.2
            
        pygame.draw.circle(okno, barva, (int(screen_x), int(screen_y)), int(velikost))
    
    draw_coords()
    draw_health_bar()
    pygame.display.update()
    clock.tick(60)