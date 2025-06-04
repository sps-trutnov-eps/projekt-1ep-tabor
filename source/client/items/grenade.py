import pygame
import math
import random

BLACK = (0, 0, 0)
EXPLOSION_COLOR = (255, 0, 0)

class Grenade:
    def __init__(self, x=0, y=0, size=0):
        self.x = x
        self.y = y
        self.size = size

        try:
            self.image = pygame.image.load("images/grenade.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, (size, size))
        except Exception as e:
            print(f"Chyba při načítání granátu: {e}")
            self.image = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (255, 0, 0), (0, 0, size, size))
            pygame.draw.rect(self.image, (255, 255, 255), (size // 4, size // 4, size // 2, size // 2))
            pygame.draw.line(self.image, (255, 255, 255), (size // 2, size // 4), (size // 2, size * 3 // 4), 3)
    
    def draw(self, screen, camera_x, camera_y, SCREEN_WIDTH, SCREEN_HEIGHT):
        screen_x = int(self.x - camera_x + SCREEN_WIDTH // 2)
        screen_y = int(self.y - camera_y + SCREEN_HEIGHT // 2)

        if (-self.size <= screen_x <= SCREEN_WIDTH + self.size and
            -self.size <= screen_y <= SCREEN_HEIGHT + self.size):
            screen.blit(self.image, (screen_x - self.size // 2, screen_y - self.size // 2))
        
    def get_rect(self):
        return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)
    
class Grenade_projectile:
    def __init__(self, x, y, velocity_x, velocity_y):
        self.x = x
        self.y = y
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.size = 20
        self.start_x = x
        self.start_y = y
        self.state = 'moving'
        self.stop_time = 0 
        self.explosion_radius = 500
        self.explosion_damage = 40
        self.explosion_time = 0
        self.explosion_duration = 500

    def update(self, player_x, player_y, player_size, SCREEN_WIDTH, SCREEN_HEIGHT, take_damage=None):
        if self.state == 'moving':
            self.x += self.velocity_x
            self.y += self.velocity_y
        
            distance_travelled = math.sqrt((self.x - self.start_x)**2 + (self.y - self.start_y)**2)
            
            if distance_travelled >= 500:
                self.state = 'stopped'
                self.stop_time = pygame.time.get_ticks()
        
        elif self.state == 'stopped':
            if pygame.time.get_ticks() - self.stop_time >= 1000:
                self.state = 'exploded'
                self.explosion_time = pygame.time.get_ticks()
                self.explode(player_x, player_y, player_size, SCREEN_WIDTH, SCREEN_HEIGHT, take_damage=take_damage)
    
    def draw(self, screen, camera_x, camera_y, player_size, SCREEN_WIDTH, SCREEN_HEIGHT):
        screen_x = int(self.x - camera_x + SCREEN_WIDTH // 2 - player_size // 2)
        screen_y = int(self.y - camera_y + SCREEN_HEIGHT // 2 - player_size // 2)

        if self.state == 'stopped' or self.state == 'moving':
            pygame.draw.circle(screen, BLACK, (screen_x, screen_y), self.size)
        
        elif self.state == 'exploded':
            pygame.draw.circle(screen, EXPLOSION_COLOR, (screen_x, screen_y), self.explosion_radius, 3)
    
    def explode(self, camera_x, camera_y, player_size, SCREEN_WIDTH, SCREEN_HEIGHT, take_damage=None):
        screen_x = int(self.x - camera_x + SCREEN_WIDTH // 2 - player_size // 2)
        screen_y = int(self.y - camera_y + SCREEN_HEIGHT // 2 - player_size // 2)

        distance = math.sqrt((self.x - camera_x) ** 2 + (self.y - camera_y) ** 2)
        
        if distance <= self.explosion_radius // 2:
            take_damage(self.explosion_damage)
        if distance <= self.explosion_radius:
            take_damage(self.explosion_damage)

def generate_grenades(grenade_amount, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT, BOUNDARY_WIDTH, grenades=[]):
    for _ in range(grenade_amount):  # Vytvoří 5 beden s granáty rozptýlených po mapě
        tile_x = random.randint(BOUNDARY_WIDTH + 2, MAP_WIDTH - BOUNDARY_WIDTH - 2)
        tile_y = random.randint(BOUNDARY_WIDTH + 2, MAP_HEIGHT - BOUNDARY_WIDTH - 2)

        grenade_x = tile_x * TILE_SIZE + TILE_SIZE // 2
        grenade_y = tile_y * TILE_SIZE + TILE_SIZE // 2

        grenades.append(Grenade(grenade_x, grenade_y, size=80))

    return grenades[:]

def check_grenade_collision(player_x, player_y, player_radius, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT, BOUNDARY_WIDTH, add_grenade=None, grenades=[]):
    player_rect = pygame.Rect(player_x - player_radius, player_y - player_radius,
                              player_radius * 2, player_radius * 2)

    for grenade in grenades:
        if player_rect.colliderect(grenade.get_rect()):
            # Přidání granátu
            add_grenade(1)

            # Přesunutí granátu na novou náhodnou pozici
            # Použijeme dlaždice pro lepší umístění (mimo zdi a objekty)
            new_tile_x = random.randint(BOUNDARY_WIDTH + 2, MAP_WIDTH - BOUNDARY_WIDTH - 2)
            new_tile_y = random.randint(BOUNDARY_WIDTH + 2, MAP_HEIGHT - BOUNDARY_WIDTH - 2)

            # Převedení pozice dlaždice na pozici v herním světě
            grenade.x = new_tile_x * TILE_SIZE + TILE_SIZE // 2
            grenade.y = new_tile_y * TILE_SIZE + TILE_SIZE // 2

            return True
    return False

def throw_grenade(velocity_x, velocity_y, player_grenades_amount, player_x, player_y, player_size):
    if player_grenades_amount > 0:
        thrown_grenade = Grenade_projectile((player_x + player_size / 2), (player_y + player_size / 2), velocity_x, velocity_y)
        return thrown_grenade
    return None