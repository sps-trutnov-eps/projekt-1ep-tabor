import pygame
import sys
import math
import random

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
MAP_WIDTH, MAP_HEIGHT = 3000, 3000  # Large map, bigger than screen
FPS = 60
PLAYER_SPEED = 5
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (150, 150, 150)

# Weapon attributes - only the sniper
WEAPONS = {
    "Sniper_Gun": {
        "damage": 80,
        "range": 1500,
        "fire_rate": 1.5,  # seconds between shots
        "accuracy": 0.95,  # 0-1, higher is better
        "reload_time": 3.0,
        "projectile_speed": 25,
        "bullet_size": 4,
        "bullet_color": BLACK,
        "ammo": 10,
        "description": "High damage, long range, slow fire rate"
    }
}

# Create the game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("TaborBG Testing Area - Sniper Only")
clock = pygame.time.Clock()

# Load images (placeholder rectangle if image not found)
def load_image(name, size=(40, 40)):
    try:
        image = pygame.image.load(name)
        return pygame.transform.scale(image, size)
    except pygame.error:
        # Create a colored placeholder
        surf = pygame.Surface(size, pygame.SRCALPHA)
        if "player" in name.lower():
            pygame.draw.rect(surf, BLUE, surf.get_rect(), border_radius=10)
            pygame.draw.circle(surf, WHITE, (size[0]//2, size[0]//2), size[0]//4)
        elif "sniper" in name.lower():
            pygame.draw.rect(surf, RED, surf.get_rect(), border_radius=5)
            pygame.draw.line(surf, BLACK, (5, size[1]//2), (size[0]-5, size[1]//2), 4)
        return surf

# Load images
player_img = load_image("player.png", (30, 30))
weapon_images = {name: load_image(f"{name}.png") for name in WEAPONS.keys()}

# Game classes
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.speed = PLAYER_SPEED
        self.current_weapon = None
        self.last_shot_time = 0
        self.rect = pygame.Rect(x - self.width/2, y - self.height/2, self.width, self.height)
        self.angle = 0  # Angle player is facing

    def update(self, keys, camera):
        dx, dy = 0, 0
        if keys[pygame.K_w]:
            dy -= self.speed
        if keys[pygame.K_s]:
            dy += self.speed
        if keys[pygame.K_a]:
            dx -= self.speed
        if keys[pygame.K_d]:
            dx += self.speed

        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            magnitude = math.sqrt(dx**2 + dy**2)
            dx = dx / magnitude * self.speed
            dy = dy / magnitude * self.speed

        # Update position
        self.x += dx
        self.y += dy

        # Keep player within map bounds
        self.x = max(0, min(self.x, MAP_WIDTH))
        self.y = max(0, min(self.y, MAP_HEIGHT))
        
        # Update rect for collision detection
        self.rect = pygame.Rect(self.x - self.width/2, self.y - self.height/2, self.width, self.height)
        
        # Update player angle to face mouse
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # Convert screen coordinates to world coordinates
        world_mouse_x = mouse_x + camera.x
        world_mouse_y = mouse_y + camera.y
        self.angle = math.atan2(world_mouse_y - self.y, world_mouse_x - self.x)

    def draw(self, screen, camera):
        # Draw player at screen position
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y
        
        # Rotate player image to face mouse
        rotated_img = pygame.transform.rotate(player_img, -math.degrees(self.angle))
        rotated_rect = rotated_img.get_rect(center=(screen_x, screen_y))
        screen.blit(rotated_img, rotated_rect.topleft)
        
        # Draw current weapon info if applicable
        if self.current_weapon:
            weapon_info = WEAPONS[self.current_weapon]
            text = f"Weapon: {self.current_weapon.replace('_Gun', '')}"
            text_surf = font.render(text, True, WHITE)
            screen.blit(text_surf, (10, 50))
            
            # Draw ammo
            ammo_text = f"Ammo: {weapon_info['ammo']}"
            ammo_surf = font.render(ammo_text, True, WHITE)
            screen.blit(ammo_surf, (10, 80))

    def shoot(self, bullets, current_time):
        if not self.current_weapon:
            return
        
        weapon_info = WEAPONS[self.current_weapon]
        
        # Check if enough time has passed since last shot
        if current_time - self.last_shot_time >= weapon_info["fire_rate"] * 1000 and weapon_info["ammo"] > 0:
            self.last_shot_time = current_time
            weapon_info["ammo"] -= 1
            
            # Add slight accuracy variation
            accuracy_offset = 0
            if weapon_info["accuracy"] < 1.0:
                max_deviation = (1.0 - weapon_info["accuracy"]) * 0.2
                accuracy_offset = random.uniform(-max_deviation, max_deviation)
            
            bullets.append(Bullet(
                self.x, self.y, 
                self.angle + accuracy_offset,
                weapon_info["projectile_speed"],
                weapon_info["damage"],
                weapon_info["range"],
                weapon_info["bullet_size"],
                weapon_info["bullet_color"],
                self.current_weapon
            ))
            
            # Play gunshot sound
            # If you want to add sound: pygame.mixer.Sound("sniper_shot.wav").play()

class Weapon:
    def __init__(self, x, y, type_name):
        self.x = x
        self.y = y
        self.type = type_name
        self.width = 40
        self.height = 40
        self.rect = pygame.Rect(x - self.width/2, y - self.height/2, self.width, self.height)
        self.picked_up = False

    def draw(self, screen, camera):
        if self.picked_up:
            return
        
        # Draw weapon at screen position
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y
        
        # Only draw if on screen
        if -self.width <= screen_x <= SCREEN_WIDTH + self.width and \
           -self.height <= screen_y <= SCREEN_HEIGHT + self.height:
            screen.blit(weapon_images[self.type], (screen_x - self.width/2, screen_y - self.height/2))

    def check_collision(self, player):
        return not self.picked_up and self.rect.colliderect(player.rect)

class Bullet:
    def __init__(self, x, y, angle, speed, damage, max_range, size, color, weapon_type):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.angle = angle
        self.speed = speed
        self.damage = damage
        self.max_range = max_range
        self.size = size
        self.color = color
        self.weapon_type = weapon_type
        self.distance_traveled = 0
        self.active = True
        self.trail = []  # For sniper bullet trail effect

    def update(self):
        if not self.active:
            return
            
        # Save previous position for trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:  # Keep only the latest positions
            self.trail.pop(0)
            
        # Move bullet
        dx = math.cos(self.angle) * self.speed
        dy = math.sin(self.angle) * self.speed
        self.x += dx
        self.y += dy
        
        # Calculate distance traveled
        self.distance_traveled = math.hypot(self.x - self.start_x, self.y - self.start_y)
        
        # Check if bullet is out of range or out of map bounds
        if self.distance_traveled > self.max_range or \
           self.x < 0 or self.x > MAP_WIDTH or \
           self.y < 0 or self.y > MAP_HEIGHT:
            self.active = False

    def draw(self, screen, camera):
        if not self.active:
            return
            
        # Draw bullet at screen position
        screen_x = int(self.x - camera.x)
        screen_y = int(self.y - camera.y)
        
        # Only draw if on screen
        if 0 <= screen_x <= SCREEN_WIDTH and 0 <= screen_y <= SCREEN_HEIGHT:
            # Draw trail effect for sniper bullet
            if self.weapon_type == "Sniper_Gun":
                # Draw bullet trail
                if len(self.trail) > 1:
                    trail_points = [(int(x - camera.x), int(y - camera.y)) for x, y in self.trail]
                    for i in range(len(trail_points) - 1):
                        alpha = int(255 * (i + 1) / len(trail_points))
                        color = (0, 0, 0, alpha)
                        trail_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                        pygame.draw.line(trail_surf, color, trail_points[i], trail_points[i+1], 2)
                        screen.blit(trail_surf, (0, 0))
            
            # Draw the bullet itself
            pygame.draw.circle(screen, self.color, (screen_x, screen_y), self.size)

class Camera:
    def __init__(self, width, height):
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        
    def update(self, target_x, target_y):
        # Center camera on target (player)
        self.x = target_x - self.width // 2
        self.y = target_y - self.height // 2
        
        # Keep camera within map bounds
        self.x = max(0, min(self.x, MAP_WIDTH - self.width))
        self.y = max(0, min(self.y, MAP_HEIGHT - self.height))

# Font setup
font = pygame.font.SysFont(None, 24)

def draw_map(screen, camera):
    # Draw the background
    # We'll only draw the visible portion of the grid
    cell_size = 50  # Grid cell size
    
    # Calculate grid starting positions
    start_col = camera.x // cell_size
    start_row = camera.y // cell_size
    
    # Calculate number of cells to draw
    cols = (SCREEN_WIDTH // cell_size) + 2
    rows = (SCREEN_HEIGHT // cell_size) + 2
    
    # Draw grid
    for col in range(int(start_col), int(start_col + cols)):
        x = col * cell_size - camera.x
        pygame.draw.line(screen, (170, 170, 170), (x, 0), (x, SCREEN_HEIGHT))
    
    for row in range(int(start_row), int(start_row + rows)):
        y = row * cell_size - camera.y
        pygame.draw.line(screen, (170, 170, 170), (0, y), (SCREEN_WIDTH, y))
    
    # Draw map border
    border_rect = pygame.Rect(-camera.x, -camera.y, MAP_WIDTH, MAP_HEIGHT)
    pygame.draw.rect(screen, RED, border_rect, 3)

def draw_minimap(screen, player, weapons, bullets):
    # Draw minimap in top-right corner
    minimap_size = 150
    minimap_scale = minimap_size / MAP_WIDTH
    
    # Minimap background
    minimap_rect = pygame.Rect(SCREEN_WIDTH - minimap_size - 10, 10, minimap_size, minimap_size)
    pygame.draw.rect(screen, (50, 50, 50), minimap_rect)
    pygame.draw.rect(screen, WHITE, minimap_rect, 2)
    
    # Draw weapons on minimap
    for weapon in weapons:
        if not weapon.picked_up:
            weapon_x = SCREEN_WIDTH - minimap_size - 10 + int(weapon.x * minimap_scale)
            weapon_y = 10 + int(weapon.y * minimap_scale)
            pygame.draw.circle(screen, RED, (weapon_x, weapon_y), 2)
    
    # Draw player on minimap
    player_x = SCREEN_WIDTH - minimap_size - 10 + int(player.x * minimap_scale)
    player_y = 10 + int(player.y * minimap_scale)
    pygame.draw.circle(screen, BLUE, (player_x, player_y), 3)
    
    # Draw player view direction
    direction_length = 10
    end_x = player_x + math.cos(player.angle) * direction_length
    end_y = player_y + math.sin(player.angle) * direction_length
    pygame.draw.line(screen, WHITE, (player_x, player_y), (end_x, end_y), 2)

def display_weapon_info(screen, weapon_type=None):
    if weapon_type:
        # Remove "_Gun" suffix for display
        name = weapon_type.replace('_Gun', '')
        weapon_info = WEAPONS[weapon_type]
        
        # Create info text
        info_text = [
            f"{name}:",
            f"Damage: {weapon_info['damage']}",
            f"Range: {weapon_info['range']}",
            f"Fire Rate: {weapon_info['fire_rate']:.1f}s",
            f"Reload Time: {weapon_info['reload_time']:.1f}s",
            f"Accuracy: {weapon_info['accuracy'] * 100:.1f}%"
        ]
        
        # Draw background
        info_height = len(info_text) * 25 + 10
        pygame.draw.rect(screen, (0, 0, 0, 180), (10, 10, 250, info_height))
        
        # Draw text
        for i, line in enumerate(info_text):
            text_surf = font.render(line, True, WHITE)
            screen.blit(text_surf, (20, 20 + i * 25))

def draw_target_distance(screen, player, camera):
    # Get mouse position and calculate world coordinates
    mouse_x, mouse_y = pygame.mouse.get_pos()
    world_mouse_x = mouse_x + camera.x
    world_mouse_y = mouse_y + camera.y
    
    # Calculate distance to target
    distance = math.hypot(world_mouse_x - player.x, world_mouse_y - player.y)
    
    # Display distance
    distance_text = f"Target Distance: {distance:.1f} units"
    distance_surf = font.render(distance_text, True, WHITE)
    screen.blit(distance_surf, (SCREEN_WIDTH - distance_surf.get_width() - 10, SCREEN_HEIGHT - 40))

def main():
    # Initialize game objects
    player = Player(MAP_WIDTH/2, MAP_HEIGHT/2)
    camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
    bullets = []
    
    # Create only the sniper weapon at the center of the map
    weapons = [
        Weapon(MAP_WIDTH/2 + 200, MAP_HEIGHT/2, "Sniper_Gun"),
    ]
    
    running = True
    hovered_weapon = None
    show_target_line = False
    
    while running:
        current_time = pygame.time.get_ticks()
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    player.shoot(bullets, current_time)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    show_target_line = not show_target_line
        
        # Get keyboard state
        keys = pygame.key.get_pressed()
        
        # Handle escape key to exit
        if keys[pygame.K_ESCAPE]:
            running = False
        
        # Update player
        player.update(keys, camera)
        
        # Update camera
        camera.update(player.x, player.y)
        
        # Check for weapon pickup
        hovered_weapon = None
        for weapon in weapons:
            if weapon.check_collision(player):
                hovered_weapon = weapon.type
                if keys[pygame.K_e]:
                    player.current_weapon = weapon.type
                    weapon.picked_up = True
        
        # Update bullets
        for bullet in bullets[:]:
            bullet.update()
            if not bullet.active:
                bullets.remove(bullet)
        
        # Draw everything
        screen.fill((100, 100, 100))  # Gray background
        
        # Draw map grid
        draw_map(screen, camera)
        
        # Draw aiming line if enabled
        if show_target_line and player.current_weapon:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            pygame.draw.line(screen, (255, 0, 0, 100), 
                             (player.x - camera.x, player.y - camera.y), 
                             (mouse_x, mouse_y), 1)
        
        # Draw weapons
        for weapon in weapons:
            weapon.draw(screen, camera)
        
        # Draw bullets
        for bullet in bullets:
            bullet.draw(screen, camera)
        
        # Draw player
        player.draw(screen, camera)
        
        # Draw minimap
        draw_minimap(screen, player, weapons, bullets)
        
        # Display weapon pickup prompt
        if hovered_weapon:
            prompt_text = f"Press E to pick up {hovered_weapon.replace('_Gun', '')}"
            prompt_surf = font.render(prompt_text, True, WHITE)
            screen.blit(prompt_surf, (SCREEN_WIDTH/2 - prompt_surf.get_width()/2, SCREEN_HEIGHT - 50))
        
        # Display current weapon info
        display_weapon_info(screen, player.current_weapon)
        
        # Display target distance
        draw_target_distance(screen, player, camera)
        
        # Display controls
        controls_text = "Controls: WASD to move, Mouse to aim, Left-click to shoot, E to pick up weapon, T to toggle aim line"
        controls_surf = font.render(controls_text, True, WHITE)
        screen.blit(controls_surf, (10, SCREEN_HEIGHT - 30))
        
        # Update display
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()