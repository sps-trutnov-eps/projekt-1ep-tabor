import pygame
import math
import sys
# Initialize pygame
pygame.init()
# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Vlajka a Panáček")
# Colors
RED = (220, 50, 50)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (30, 30, 120)
GRID_COLOR = (180, 180, 180)
PLAYER_COLOR = (0, 120, 0)
# Clock and frame rate
clock = pygame.time.Clock()
FPS = 60
# Flag position
flag_x = WIDTH // 3
flag_y = HEIGHT // 2
# Player state
player_x = WIDTH + 50
player_y = flag_y
player_speed = 3
has_flag = False
retreating = False
def draw_grid():
    for x in range(0, WIDTH, 20):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, 20):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y), 1)
def draw_flag(time, visible=True):
    if not visible:
        return
    flag_height = 30
    pole_radius = 10
    pygame.draw.circle(screen, DARK_BLUE, (flag_x, flag_y), pole_radius)
    wave = math.sin(time * 2)
    flag_points = [
        (flag_x, flag_y - 5),
        (flag_x + 40, flag_y - 15 - 5 * wave),
        (flag_x, flag_y - flag_height - 3 * wave)
    ]
    pygame.draw.polygon(screen, RED, flag_points)
    pygame.draw.polygon(screen, BLACK, flag_points, 2)
    pygame.draw.line(screen, BLACK, (flag_x, flag_y), (flag_x, flag_y - flag_height - 3 * wave), 3)
def draw_player(x, y, carrying_flag=False, time=0):
    if carrying_flag:
        wave = math.sin(time * 2)
        # Malá vlajka na zádech (vpravo nahoře od panáčka)
        flag_height = 20
        flag_offset_x = -10
        flag_offset_y = -25
        pole_top = (x + flag_offset_x, y + flag_offset_y)
        flag_tip = (pole_top[0] - 25, pole_top[1] + 10 + 3 * wave)
        pole_base = (x + flag_offset_x, y - 5)
        flag_points = [pole_base, flag_tip, pole_top]
        pygame.draw.polygon(screen, RED, flag_points)
        pygame.draw.polygon(screen, BLACK, flag_points, 1)
        pygame.draw.line(screen, BLACK, pole_base, pole_top, 2)
# Main loop
running = True
time = 0
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill(WHITE)
    draw_grid()
    time += 0.05
    # Pohyb panáčka
    if not has_flag:
        if player_x > flag_x + 20:
            player_x -= player_speed
        else:
            has_flag = True
            retreating = True
    elif retreating:
        if player_x < WIDTH + 50:
            player_x += player_speed
    # Kreslení
    draw_flag(time, visible=not has_flag)
    if not (has_flag and not retreating):
        draw_player(player_x, player_y, carrying_flag=has_flag, time=time)
    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()
sys.exit()