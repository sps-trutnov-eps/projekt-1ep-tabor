import pygame
import sys
import math


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


# kulička hráče
player_pos = [WIDTH // 2, HEIGHT // 2]  # spawn uprostřed
player_radius = 20
player_speed = 5
player_alpha = 255
player_prev_pos = player_pos.copy()

# keř
bush_pos = [WIDTH // 2, HEIGHT // 2 - 100]  # pozice keře
bush_block_size = player_radius * 1.5  # velikost jednotlivý blocků

# funkce pro počítání vzdálenost mezi body
def distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

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
        

# vykreslení keře
def draw_boxy_bush(pos, block_size, player_pos):
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
    
    player_touching = False
    player_inside = False
    
    # vykreslení blocků
    for block in bush_blocks:
        # vypočítání prostředek blocků
        block_center = (block[0] + block[2]/2, block[1] + block[3]/2)
        
        # vypočítání vzdálenosti od hráče do prostředku
        dist = distance(player_pos, block_center)
        
        # alpha = 0 - transparency max
        # alpha = 255 - transparency nulová
        
        # jestli je hráč v bloku nebo hodně blízko
        if (block[0] <= player_pos[0] <= block[0] + block[2] and 
            block[1] <= player_pos[1] <= block[1] + block[3]):
            alpha = 64  # hodně transparent když uvnitř
            player_inside = True 
        elif dist < player_radius + block_size:
            # postupně snižovat alphu když je hráč blíže
            alpha = max(64, int(255 * (dist - player_radius) / block_size))
            player_touching = True 
        else:
            alpha = 255  # plná alpha když je hráč pryč
        
        # vytvoření povrchu pro bloky
        block_surface = pygame.Surface((block[2], block[3]), pygame.SRCALPHA)
        
        # vykreslit blok s transparency která je adektvátní
        pygame.draw.rect(block_surface, (*GREEN, alpha), (0, 0, block[2], block[3]))
        pygame.draw.rect(block_surface, (*GREEN, min(alpha + 30, 255)), (0, 0, block[2], block[3]), 2)  # trochu darker outlina
        
        # vykreslit blok na obrazovku
        screen.blit(block_surface, (block[0], block[1]))
    
    return player_inside, player_touching

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    keys = pygame.key.get_pressed()
    
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
    
    player_inside, player_touching = draw_boxy_bush(bush_pos, bush_block_size, player_pos)
    
    if player_inside:
        player_alpha = 64
    elif player_touching:
        player_alpha = 128
    else:
        player_alpha = min(255, player_alpha + 10)
    
    # vykreslení hráče    
    player_surface = pygame.Surface((player_radius*2, player_radius*2), pygame.SRCALPHA)
    pygame.draw.circle(player_surface, (*RED, player_alpha), (player_radius, player_radius), player_radius)
    screen.blit(player_surface, (player_pos[0] - player_radius, player_pos[1] - player_radius))
    
    # vykreslení pluska
    draw_boxy_bush(bush_pos, bush_block_size, player_pos)
    
    pygame.display.flip()
    
    clock.tick(60)


pygame.quit()
sys.exit()