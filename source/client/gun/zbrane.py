import pygame
import math
import random

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Weapon Testing Map")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
GREEN = (100, 200, 100)
RED = (200, 100, 100)
BROWN = (139, 69, 19)

# Load images
try:
    player_img = pygame.image.load("player.png").convert_alpha()
    player_img = pygame.transform.scale(player_img, (50, 50))
    
    sniper_img = pygame.image.load("Sniper_Gun.png").convert_alpha()
    sniper_img = pygame.transform.scale(sniper_img, (60, 20))
    
    shotgun_img = pygame.image.load("Shotgun_Gun.png").convert_alpha()
    shotgun_img = pygame.transform.scale(shotgun_img, (50, 20))
    
    rocket_launcher_img = pygame.image.load("RocketLauncher_Gun.png").convert_alpha()
    rocket_launcher_img = pygame.transform.scale(rocket_launcher_img, (70, 25))
    
    crossbow_img = pygame.image.load("Crossbow_Gun.png").convert_alpha()
    crossbow_img = pygame.transform.scale(crossbow_img, (50, 20))
    
except pygame.error:
    print("Warning: Could not load one or more images. Using placeholder graphics.")
    
    # Create placeholder graphics
    player_img = pygame.Surface((50, 50), pygame.SRCALPHA)
    pygame.draw.circle(player_img, (0, 0, 255), (25, 25), 25)
    
    sniper_img = pygame.Surface((60, 20), pygame.SRCALPHA)
    pygame.draw.rect(sniper_img, (100, 100, 100), (0, 0, 60, 20))
    pygame.draw.rect(sniper_img, (80, 80, 80), (45, 0, 15, 20))
    
    shotgun_img = pygame.Surface((50, 20), pygame.SRCALPHA)
    pygame.draw.rect(shotgun_img, (120, 120, 120), (0, 0, 50, 20))
    pygame.draw.rect(shotgun_img, (90, 90, 90), (35, 0, 15, 20))
    
    rocket_launcher_img = pygame.Surface((70, 25), pygame.SRCALPHA)
    pygame.draw.rect(rocket_launcher_img, (150, 150, 150), (0, 0, 70, 25))
    pygame.draw.rect(rocket_launcher_img, (200, 50, 50), (50, 5, 20, 15))
    
    crossbow_img = pygame.Surface((50, 20), pygame.SRCALPHA)
    pygame.draw.rect(crossbow_img, (139, 69, 19), (0, 0, 50, 20))
    pygame.draw.line(crossbow_img, (0, 0, 0), (25, 0), (25, 20), 2)

# Font
font = pygame.font.SysFont('Arial', 20)

# Player class
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 5
        self.angle = 0
        self.equipped_weapon = None
        self.health = 100
        
    def move(self, dx, dy):
        # Calculate potential new position
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed
        
        # Check if new position is within screen bounds
        if 25 <= new_x <= SCREEN_WIDTH - 25:
            self.x = new_x
        if 25 <= new_y <= SCREEN_HEIGHT - 25:
            self.y = new_y
    
    def rotate(self, mouse_pos):
        # Calculate angle between player and mouse
        dx = mouse_pos[0] - self.x
        dy = mouse_pos[1] - self.y
        self.angle = math.atan2(dy, dx)
        
    def draw(self, surface):
        # Draw player
        rotated_player = player_img.copy()
        player_rect = rotated_player.get_rect(center=(self.x, self.y))
        surface.blit(rotated_player, player_rect)
        
        # Draw equipped weapon if any
        if self.equipped_weapon:
            # Position the weapon at the player's location
            weapon_x = self.x + math.cos(self.angle) * 25
            weapon_y = self.y + math.sin(self.angle) * 25
            
            # Rotate the weapon image
            weapon_img = self.equipped_weapon.image
            rotated_weapon = pygame.transform.rotate(weapon_img, -math.degrees(self.angle))
            weapon_rect = rotated_weapon.get_rect(center=(weapon_x, weapon_y))
            
            surface.blit(rotated_weapon, weapon_rect)
            
        # Draw health bar
        pygame.draw.rect(surface, RED, (self.x - 25, self.y - 40, 50, 5))
        pygame.draw.rect(surface, GREEN, (self.x - 25, self.y - 40, self.health / 2, 5))

# Weapon class
class Weapon:
    def __init__(self, name, damage, fire_rate, bullet_speed, bullet_range, bullet_count, image, sound=None):
        self.name = name
        self.damage = damage
        self.fire_rate = fire_rate  # Shots per second
        self.bullet_speed = bullet_speed
        self.bullet_range = bullet_range
        self.bullet_count = bullet_count  # For shotgun pattern
        self.image = image
        self.sound = sound
        self.last_shot_time = 0
        self.is_picked_up = False
        self.x = 0
        self.y = 0
        
    def place(self, x, y):
        self.x = x
        self.y = y
        self.is_picked_up = False
        
    def can_fire(self, current_time):
        return current_time - self.last_shot_time > 1000 / self.fire_rate
    
    def fire(self, start_x, start_y, angle, current_time, bullets):
        if not self.can_fire(current_time):
            return
        
        self.last_shot_time = current_time
        
        if self.name == "Shotgun":
            # Create multiple bullets in a spread pattern
            spread_angle = 0.3  # in radians
            for i in range(self.bullet_count):
                bullet_angle = angle - spread_angle/2 + spread_angle * i / (self.bullet_count - 1)
                dx = math.cos(bullet_angle) * self.bullet_speed
                dy = math.sin(bullet_angle) * self.bullet_speed
                bullets.append(Bullet(start_x, start_y, dx, dy, self.damage, self.bullet_range, self.name))
        else:
            # Create a single bullet
            dx = math.cos(angle) * self.bullet_speed
            dy = math.sin(angle) * self.bullet_speed
            bullets.append(Bullet(start_x, start_y, dx, dy, self.damage, self.bullet_range, self.name))
            
            # Special effect for rocket launcher
            if self.name == "Rocket Launcher":
                bullets[-1].explosive = True
                bullets[-1].explosion_radius = 100
    
    def draw(self, surface):
        if not self.is_picked_up:
            weapon_rect = self.image.get_rect(center=(self.x, self.y))
            surface.blit(self.image, weapon_rect)
            
            # Draw weapon name above
            text = font.render(self.name, True, BLACK)
            text_rect = text.get_rect(center=(self.x, self.y - 30))
            surface.blit(text, text_rect)

# Bullet class
class Bullet:
    def __init__(self, x, y, dx, dy, damage, max_distance, weapon_type):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.damage = damage
        self.start_x = x
        self.start_y = y
        self.max_distance = max_distance
        self.weapon_type = weapon_type
        self.radius = 3
        self.explosive = False
        self.explosion_radius = 0
        
        # Special properties based on weapon type
        if weapon_type == "Sniper":
            self.radius = 2
        elif weapon_type == "Shotgun":
            self.radius = 2
        elif weapon_type == "Rocket Launcher":
            self.radius = 5
        elif weapon_type == "Crossbow":
            self.radius = 3
    
    def update(self):
        self.x += self.dx
        self.y += self.dy
        
        # Check if bullet has traveled its maximum distance
        distance = math.sqrt((self.x - self.start_x)**2 + (self.y - self.start_y)**2)
        if distance > self.max_distance:
            return False
            
        # Check if bullet is out of screen bounds
        if self.x < 0 or self.x > SCREEN_WIDTH or self.y < 0 or self.y > SCREEN_HEIGHT:
            return False
            
        return True
    
    def draw(self, surface):
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius)

# Target class for testing weapons
class Target:
    def __init__(self, x, y, size=30):
        self.x = x
        self.y = y
        self.size = size
        self.health = 100
        self.is_hit = False
        self.hit_time = 0
        
    def check_hit(self, bullet):
        distance = math.sqrt((self.x - bullet.x)**2 + (self.y - bullet.y)**2)
        
        if bullet.explosive and distance <= bullet.explosion_radius:
            # Calculate damage based on distance from explosion center
            blast_factor = 1 - (distance / bullet.explosion_radius)
            damage = bullet.damage * blast_factor
            self.health -= max(0, damage)
            self.is_hit = True
            self.hit_time = pygame.time.get_ticks()
            return True
            
        elif distance < self.size / 2 + bullet.radius:
            self.health -= bullet.damage
            self.is_hit = True
            self.hit_time = pygame.time.get_ticks()
            return True
            
        return False
        
    def draw(self, surface, current_time):
        # Choose target color based on health
        if self.health <= 0:
            color = (100, 100, 100)  # Destroyed target
        else:
            # Flash red if recently hit
            if self.is_hit and current_time - self.hit_time < 200:
                color = (255, 0, 0)
            else:
                self.is_hit = False
                color = (200, 200, 0)  # Normal color
                
        # Draw target
        pygame.draw.circle(surface, color, (self.x, self.y), self.size)
        
        # Fix: Ensure color values don't go below 0
        inner_color = (max(0, color[0]-50), max(0, color[1]-50), max(0, color[2]-50))
        pygame.draw.circle(surface, inner_color, (self.x, self.y), self.size - 5)
        
        # Fix: Ensure color values don't go below 0
        center_color = (max(0, color[0]-100), max(0, color[1]-100), max(0, color[2]-100))
        pygame.draw.circle(surface, center_color, (self.x, self.y), self.size - 10)
        
        # Draw health bar if target is not destroyed
        if self.health > 0:
            pygame.draw.rect(surface, RED, (self.x - 20, self.y - self.size - 10, 40, 5))
            pygame.draw.rect(surface, GREEN, (self.x - 20, self.y - self.size - 10, 40 * (self.health / 100), 5))

# Game class to manage everything
class Game:
    def __init__(self):
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.weapons = []
        self.bullets = []
        self.targets = []
        self.clock = pygame.time.Clock()
        self.running = True
        self.fps = 60
        
        # Create weapons
        self.create_weapons()
        
        # Create targets
        self.create_targets()
        
    def create_weapons(self):
        # Format: name, damage, fire_rate, bullet_speed, bullet_range, bullet_count, image
        sniper = Weapon("Sniper", 80, 1, 20, 1000, 1, sniper_img)
        shotgun = Weapon("Shotgun", 15, 2, 15, 300, 5, shotgun_img)
        rocket_launcher = Weapon("Rocket Launcher", 100, 0.5, 10, 500, 1, rocket_launcher_img)
        crossbow = Weapon("Crossbow", 40, 3, 12, 400, 1, crossbow_img)
        
        # Place weapons on the map
        sniper.place(100, 100)
        shotgun.place(100, 200)
        rocket_launcher.place(100, 300)
        crossbow.place(100, 400)
        
        self.weapons = [sniper, shotgun, rocket_launcher, crossbow]
    
    def create_targets(self):
        # Create some static targets
        for i in range(5):
            self.targets.append(Target(800, 100 + i * 100))
            
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Check if player clicked on a weapon to pick it up
                    for weapon in self.weapons:
                        if not weapon.is_picked_up:
                            distance = math.sqrt((weapon.x - mouse_pos[0])**2 + (weapon.y - mouse_pos[1])**2)
                            if distance < 30:
                                # Drop currently equipped weapon if any
                                if self.player.equipped_weapon:
                                    self.player.equipped_weapon.is_picked_up = False
                                    self.player.equipped_weapon.place(self.player.x, self.player.y)
                                    
                                # Equip new weapon
                                self.player.equipped_weapon = weapon
                                weapon.is_picked_up = True
                                break
                    
                    # Fire weapon if equipped
                    if self.player.equipped_weapon:
                        current_time = pygame.time.get_ticks()
                        start_x = self.player.x + math.cos(self.player.angle) * 35
                        start_y = self.player.y + math.sin(self.player.angle) * 35
                        self.player.equipped_weapon.fire(start_x, start_y, self.player.angle, current_time, self.bullets)
    
    def update(self):
        # Get keys pressed
        keys = pygame.key.get_pressed()
        
        # Move player
        dx = 0
        dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
            
        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
            
        self.player.move(dx, dy)
        
        # Rotate player towards mouse
        mouse_pos = pygame.mouse.get_pos()
        self.player.rotate(mouse_pos)
        
        # Update bullets
        i = 0
        while i < len(self.bullets):
            if not self.bullets[i].update():
                self.bullets.pop(i)
            else:
                # Check for bullet collisions with targets
                for target in self.targets:
                    if target.health > 0 and target.check_hit(self.bullets[i]):
                        # Handle explosion if it's a rocket
                        if self.bullets[i].explosive:
                            # Keep the bullet to render the explosion but mark for removal in next frame
                            self.bullets[i].max_distance = 0
                        else:
                            # Remove the bullet if it hit a target
                            self.bullets.pop(i)
                            break
                else:
                    i += 1
            
        # Fire weapon with space key
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and self.player.equipped_weapon:
            current_time = pygame.time.get_ticks()
            start_x = self.player.x + math.cos(self.player.angle) * 35
            start_y = self.player.y + math.sin(self.player.angle) * 35
            self.player.equipped_weapon.fire(start_x, start_y, self.player.angle, current_time, self.bullets)
            
        # Respawn destroyed targets after a while
        current_time = pygame.time.get_ticks()
        for target in self.targets:
            if target.health <= 0 and current_time - target.hit_time > 3000:
                target.health = 100
    
    def draw(self):
        # Fill the screen with a background color
        screen.fill((200, 230, 200))
        
        # Draw a simple environment
        pygame.draw.rect(screen, GREEN, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Draw obstacles/walls
        pygame.draw.rect(screen, BROWN, (400, 100, 50, 400))
        pygame.draw.rect(screen, GRAY, (600, 200, 200, 50))
        
        # Draw weapons on the ground
        for weapon in self.weapons:
            weapon.draw(screen)
            
        # Draw bullets
        current_time = pygame.time.get_ticks()
        for bullet in self.bullets:
            bullet.draw(screen)
            
            # Draw explosion effect for rocket launcher
            if bullet.explosive and bullet.max_distance == 0:
                pygame.draw.circle(screen, (255, 200, 0), (int(bullet.x), int(bullet.y)), bullet.explosion_radius // 2)
                pygame.draw.circle(screen, (255, 100, 0), (int(bullet.x), int(bullet.y)), bullet.explosion_radius // 3)
            
        # Draw targets
        for target in self.targets:
            target.draw(screen, current_time)
            
        # Draw player
        self.player.draw(screen)
        
        # Draw HUD
        self.draw_hud()
        
        # Update display
        pygame.display.flip()
        
    def draw_hud(self):
        # Draw weapon info if equipped
        if self.player.equipped_weapon:
            weapon = self.player.equipped_weapon
            text = f"Weapon: {weapon.name}"
            text_surface = font.render(text, True, BLACK)
            screen.blit(text_surface, (10, 10))
            
            text = f"Damage: {weapon.damage}"
            text_surface = font.render(text, True, BLACK)
            screen.blit(text_surface, (10, 35))
            
            text = f"Fire Rate: {weapon.fire_rate}/s"
            text_surface = font.render(text, True, BLACK)
            screen.blit(text_surface, (10, 60))
            
            text = f"Range: {weapon.bullet_range}"
            text_surface = font.render(text, True, BLACK)
            screen.blit(text_surface, (10, 85))
            
        # Draw instructions
        instructions = [
            "WASD/Arrows: Move",
            "Mouse: Aim",
            "Left Click/Space: Shoot",
            "Click on weapon to equip"
        ]
        
        for i, instruction in enumerate(instructions):
            text_surface = font.render(instruction, True, BLACK)
            screen.blit(text_surface, (SCREEN_WIDTH - 200, 10 + i * 25))
    
    def run(self):
        while self.running:
            self.clock.tick(self.fps)
            self.handle_events()
            self.update()
            self.draw()
            
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
