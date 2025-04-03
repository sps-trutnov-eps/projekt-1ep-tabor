import pygame
import sys
import math


pygame.init()


WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("schovka")

WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
GREEN = (45, 160, 45)  # středně zelená

# kulička hráče
player_pos = [WIDTH // 2, HEIGHT // 2]  # spawn uprostřed
player_radius = 20
player_speed = 5

# keř
bush_pos = [WIDTH // 2, HEIGHT // 2 - 100]  # pozice keře
bush_block_size = player_radius * 1.5  # velikost jednotlivý blocků

# funkce pro počítání vzdálenost mezi body
def distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

# vykreslení keře
def draw_boxy_bush(pos, block_size, player_pos):
    # tvar pluska z 5 čtverců
    bush_blocks = [
        (pos[0] - block_size/2, pos[1] - block_size/2, block_size, block_size),
        (pos[0] - block_size/2, pos[1] - block_size*1.5, block_size, block_size),
        (pos[0] - block_size/2, pos[1] + block_size/2, block_size, block_size),
        (pos[0] - block_size*1.5, pos[1] - block_size/2, block_size, block_size),
        (pos[0] + block_size/2, pos[1] - block_size/2, block_size, block_size)
    ]
    
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
        elif dist < player_radius + block_size:
            # postupně snižovat alphu když je hráč blíže
            alpha = max(64, int(255 * (dist - player_radius) / block_size))
        else:
            alpha = 255  # plná alpha když je hráč pryč
        
        # vytvoření povrchu pro bloky
        block_surface = pygame.Surface((block[2], block[3]), pygame.SRCALPHA)
        
        # vykreslit blok s transparency která je adektvátní
        pygame.draw.rect(block_surface, (*GREEN, alpha), (0, 0, block[2], block[3]))
        pygame.draw.rect(block_surface, (*GREEN, min(alpha + 30, 255)), (0, 0, block[2], block[3]), 2)  # trochu darker outlina
        
        # vykreslit blok na obrazovku
        screen.blit(block_surface, (block[0], block[1]))

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
    
    # vykreslení pluska
    draw_boxy_bush(bush_pos, bush_block_size, player_pos)
    
    # vykreslení hráče
    pygame.draw.circle(screen, RED, player_pos, player_radius)
    
    pygame.display.flip()
    
    clock.tick(60)


pygame.quit()
sys.exit()