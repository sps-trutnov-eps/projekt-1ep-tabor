import pygame
import sys
import math
import random


pygame.init()


WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("keř")

WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
GREEN = (45, 160, 45)  # středně zelená
LIGHT_GREEN = (75, 200, 75)
YELLOW_GREEN = (150, 220, 50)
BLUE = (100, 150, 255)


# kulička hráče
player_pos = [WIDTH // 2, HEIGHT // 2]  # spawn uprostřed
player_radius = 20
player_speed = 5
player_alpha = 255
player_prev_pos = player_pos.copy()
player_hidden = False  # nový stav - jestli je hráč schovaný
hide_pressed = False  # pro tracking E klávesy

# keř
bush_pos = [WIDTH // 2, HEIGHT // 2 - 100]  # pozice keře
bush_block_size = player_radius * 1.5  # velikost jednotlivý blocků

# font pro text
font = pygame.font.Font(None, 36)

# particle class
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.radius = player_radius / 4
        self.color = color
        self.alpha = 255
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(-2, 0)  # počáteční pohyb nahoru
        self.gravity = 0.1
        self.lifetime = random.randint(30, 60)
    
    def update(self):
        self.vy += self.gravity # aplikování gravitace
        # pohyb particlů
        self.x  += self.vx
        self.y  += self.vy
        self.lifetime -= 1
        self.alpha = int((self.lifetime / 60) * 255)
        if self.lifetime <= 0:
            self.alpha = 0
        self.radius = max(1, self.radius * 0.98)
    
    def draw(self, surface):
        if self.alpha > 0:
            particle_surface = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, (*self.color, self.alpha), 
                             (self.radius, self.radius), self.radius)
            surface.blit(particle_surface, (self.x - self.radius, self.y - self.radius))
            
    def is_dead(self):
        return self.lifetime <= 0

# list na aktivní particly
particles = []

# funkce pro počítání vzdálenost mezi body
def distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

# vykreslení keře
def draw_boxy_bush(pos, block_size, player_pos, player_hidden):
    # tvar pluska z 9 čtverců
    bush_blocks = [
        (pos[0] - block_size/2, pos[1] - block_size/2, block_size, block_size),
        (pos[0] - block_size/2, pos[1] - block_size*1.5, block_size, block_size),
        (pos[0] - block_size/2, pos[1] + block_size/2, block_size, block_size),
        (pos[0] - block_size*1.5, pos[1] - block_size/2, block_size, block_size),
        (pos[0] + block_size/2, pos[1] - block_size/2, block_size, block_size),
        (pos[0] + block_size/2, pos[1] + block_size/1.9, block_size, block_size), # pravý dolní block
        (pos[0] + block_size/2, pos[1] - block_size*1.5, block_size, block_size), # pravý horní block
        (pos[0] - block_size/0.67, pos[1] - block_size*1.5, block_size, block_size), # levý horní block
        (pos[0] - block_size/0.67, pos[1] + block_size/2, block_size, block_size) # levý dolní block
    ]
    
    player_near_bush = False
    bush_center = bush_pos
    
    # zkontrolovat jestli je hráč blízko keře
    if distance(player_pos, bush_center) < bush_block_size * 2:
        player_near_bush = True
    
    # vykreslení blocků
    for block in bush_blocks:
        # jestli je hráč schovaný, keř je plně neprůhledný
        if player_hidden:
            alpha = 255
        else:
            alpha = 255  # normální alpha když není schovaný
        
        # vytvoření povrchu pro bloky
        block_surface = pygame.Surface((block[2], block[3]), pygame.SRCALPHA)
        
        # vykreslit blok
        pygame.draw.rect(block_surface, (*GREEN, alpha), (0, 0, block[2], block[3]))
        pygame.draw.rect(block_surface, (*GREEN, min(alpha + 30, 255)), (0, 0, block[2], block[3]), 2)  # trochu darker outlina
        
        # vykreslit blok na obrazovku
        screen.blit(block_surface, (block[0], block[1]))
    
    return player_near_bush, bush_blocks

# funkce na zjištění jestli je bod ve čtverci
def point_in_rect(point, rect):
    return (rect[0] <= point[0] <= rect[0] + rect[2] and
            rect[1] <= point[1] <= rect[1] + rect[3])

# funkce na detekování kolize s okraji a vytvořit particly
def check_bush_collision(old_pos, new_pos, bush_blocks):
    was_inside = any(point_in_rect(old_pos, block) for block in bush_blocks)
    is_inside = any(point_in_rect(new_pos, block) for block in bush_blocks)
    
    # jestli se hráč dotkl okraje vytvořit particly
    if was_inside != is_inside:
        # vytvořit particly na místě dotyku (přibližně)
        collision_x = (old_pos[0] + new_pos[0]) / 2
        collision_y = (old_pos[1] + new_pos[1]) / 2
        
        # vytvořit skupinku patrticlů
        for _ in range(15): # <--- kolik particlů
            color = random.choice([LIGHT_GREEN, YELLOW_GREEN, GREEN])
            particles.append(Particle(collision_x, collision_y, color))

# funkce pro vykreslení promptu
def draw_prompt(text, pos):
    # vytvoření pozadí pro text
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.center = pos
    
    # pozadí
    background_rect = text_rect.inflate(20, 10)
    background_surface = pygame.Surface((background_rect.width, background_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(background_surface, (*BLACK, 180), (0, 0, background_rect.width, background_rect.height))
    pygame.draw.rect(background_surface, BLUE, (0, 0, background_rect.width, background_rect.height), 2)
    
    # vykreslení na obrazovku
    screen.blit(background_surface, background_rect.topleft)
    screen.blit(text_surface, text_rect)

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # handling E klávesy pro schovávání/vycházení
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                if not hide_pressed:  # prevence držení klávesy
                    hide_pressed = True
            
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_e:
                hide_pressed = False
                
    # uložit předchozí pozici pro detekování kolize přes okraje
    player_prev_pos = player_pos.copy()
    
    keys = pygame.key.get_pressed()
    
    # pohyb jen když není schovaný
    if not player_hidden:
        if keys[pygame.K_w] or keys[pygame.K_UP]:  
            player_pos[1] -= player_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  
            player_pos[1] += player_speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: 
            player_pos[0] -= player_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: 
            player_pos[0] += player_speed
        
        # aby hráč neopustil obrazovku
        player_pos[0] = max(player_radius, min(WIDTH - player_radius, player_pos[0]))
        player_pos[1] = max(player_radius, min(HEIGHT - player_radius, player_pos[1]))
    
    screen.fill(BLACK)
    
    player_near_bush, bush_blocks = draw_boxy_bush(bush_pos, bush_block_size, player_pos, player_hidden)
    
    # zkontrolovat kolizi s okraji a vytvořit particly když potřeba (jen když není schovaný)
    if player_pos != player_prev_pos and not player_hidden:
        check_bush_collision(player_prev_pos, player_pos, bush_blocks)
    
    # handling schovávání/vycházení
    if hide_pressed:
        if player_near_bush and not player_hidden:
            # schovat hráče
            player_hidden = True
            # vytvořit particly při schovávání
            for _ in range(20):
                color = random.choice([LIGHT_GREEN, YELLOW_GREEN, GREEN])
                particles.append(Particle(player_pos[0], player_pos[1], color))
        elif player_hidden:
            # vyjít z keře
            player_hidden = False
            # vytvořit particly při vycházení
            for _ in range(20):
                color = random.choice([LIGHT_GREEN, YELLOW_GREEN, GREEN])
                particles.append(Particle(player_pos[0], player_pos[1], color))
        hide_pressed = False  # reset po použití
    
    # update a vykreslení všech particlů
    for particle in particles[:]:
        particle.update()
        if particle.is_dead():
            particles.remove(particle)
        else:
            particle.draw(screen)
    
    # vykreslení hráče (jen když není schovaný)
    if not player_hidden:
        if player_near_bush:
            player_alpha = 200  # trochu průhledný když je blízko
        else:
            player_alpha = 255
        
        # vykreslení hráče    
        player_surface = pygame.Surface((player_radius*2, player_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(player_surface, (*RED, player_alpha), (player_radius, player_radius), player_radius)
        screen.blit(player_surface, (player_pos[0] - player_radius, player_pos[1] - player_radius))
    
    # vykreslení promptu
    if player_near_bush and not player_hidden:
        draw_prompt("Press E to hide", (player_pos[0], player_pos[1] - 50))
    elif player_hidden:
        draw_prompt("Press E to exit", (bush_pos[0], bush_pos[1] - 80))
    
    pygame.display.flip()
    
    clock.tick(60)


pygame.quit()
sys.exit()