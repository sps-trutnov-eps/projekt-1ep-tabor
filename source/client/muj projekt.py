import pygame
import math
import sys

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flag Marker - Top View")

# Colors
RED = (220, 50, 50)         # Red for the flag
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (30, 30, 120)   # Dark blue for the pole
GRID_COLOR = (180, 180, 180)  # Light gray grid color

# Clock to control frame rate
clock = pygame.time.Clock()
FPS = 60

def draw_grid():
    # Draw vertical grid lines
    for x in range(0, WIDTH, 20):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT), 1)
    
    # Draw horizontal grid lines
    for y in range(0, HEIGHT, 20):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y), 1)

def draw_flag(time):
    # Position in the center of the screen
    flag_x = WIDTH // 3
    flag_y = HEIGHT // 2
    
    # Simple flag marker design
    flag_height = 30
    pole_radius = 10
    
    # Draw pole base (small dark circle)
    pygame.draw.circle(screen, DARK_BLUE, (flag_x, flag_y), pole_radius)
    
    # Draw flag using a simple triangle
    flag_points = [
        (flag_x, flag_y - 5),  # Bottom of pole where flag attaches
        (flag_x + 40, flag_y - 15 - 5 * math.sin(time * 2)),  # Top point of flag (with slight wave)
        (flag_x, flag_y - flag_height - 3 * math.sin(time * 2))  # Top of pole
    ]
    
    # Draw the flag as a solid triangle
    pygame.draw.polygon(screen, RED, flag_points)
    # Draw outline
    pygame.draw.polygon(screen, BLACK, flag_points, 2)
    
    # Draw the pole line
    pygame.draw.line(screen, BLACK, (flag_x, flag_y), (flag_x, flag_y - flag_height - 3 * math.sin(time * 2)), 3)

# Main game loop
running = True
time = 0
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Clear the screen with white background
    screen.fill(WHITE)
    
    # Draw grid
    draw_grid()
    
    # Update time
    time += 0.05
    
    # Draw the flag
    draw_flag(time)
    
    # Update the display
    pygame.display.flip()
    
    # Control frame rate
    clock.tick(FPS)

# Quit pygame
pygame.quit()
sys.exit()

# Main game loop
running = True
time = 0
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Clear the screen
    screen.fill(WHITE)
    
    # Update time
    time += 0.05
    
    # Draw the flag
    draw_flag(time)
    
    # Update the display
    pygame.display.flip()
    
    # Control frame rate
    clock.tick(FPS)

# Quit pygame
pygame.quit()
sys.exit()