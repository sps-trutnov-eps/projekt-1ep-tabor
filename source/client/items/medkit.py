import pygame
import random

### Samotná třída pro medkit

class Medkit:
    def __init__(self, x=0, y=0, size=80):
        self.x = x  # Pozice na mapě (ne na obrazovce)
        self.y = y  # Pozice na mapě (ne na obrazovce)
        self.size = size

        try:
            self.image = pygame.image.load("images/medkit.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, (size, size))
        except Exception as e:
            print(f"Chyba při načítání medkitu: {e}")
            self.image = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (255, 0, 0), (0, 0, size, size))
            pygame.draw.rect(self.image, (255, 255, 255), (size//4, size//4, size//2, size//2))
            pygame.draw.line(self.image, (255, 255, 255), (size//2, size//4), (size//2, size*3//4), 3)
    
    def draw(self, screen, camera_x, camera_y, SCREEN_WIDTH, SCREEN_HEIGHT):
        screen_x = int(self.x - camera_x + SCREEN_WIDTH // 2)
        screen_y = int(self.y - camera_y + SCREEN_HEIGHT // 2)
        
        if (-self.size <= screen_x <= SCREEN_WIDTH + self.size and 
            -self.size <= screen_y <= SCREEN_HEIGHT + self.size):
            screen.blit(self.image, (screen_x - self.size // 2, screen_y - self.size // 2))
    
    def get_rect(self):
        return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)

### Funkce pro vygenerování medkitů na mapě

def generate_medkits(medkit_amount, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT, BOUNDARY_WIDTH, medkits=[]):
    for _ in range(medkit_amount):  # Vytvoří 5 medkitů rozptýlených po mapě
        tile_x = random.randint(BOUNDARY_WIDTH + 2, MAP_WIDTH - BOUNDARY_WIDTH - 2)
        tile_y = random.randint(BOUNDARY_WIDTH + 2, MAP_HEIGHT - BOUNDARY_WIDTH - 2)

        medkit_x = tile_x * TILE_SIZE + TILE_SIZE // 2
        medkit_y = tile_y * TILE_SIZE + TILE_SIZE // 2

        medkits.append(Medkit(medkit_x, medkit_y, size=80))

    return medkits[:]

### Funkce pro kontrolu kolizí mezí hráčem a medkitem

def check_medkit_collision(player_x, player_y, player_radius, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT, BOUNDARY_WIDTH, heal_player=None, medkits=[]):
    player_rect = pygame.Rect(player_x - player_radius, player_y - player_radius,
                              player_radius * 2, player_radius * 2)

    for medkit in medkits:
        if player_rect.colliderect(medkit.get_rect()):
            # Přidání zdraví
            heal_player(25)

            # Přesunutí medkitu na novou náhodnou pozici
            # Použijeme dlaždice pro lepší umístění (mimo zdi a objekty)
            new_tile_x = random.randint(BOUNDARY_WIDTH + 2, MAP_WIDTH - BOUNDARY_WIDTH - 2)
            new_tile_y = random.randint(BOUNDARY_WIDTH + 2, MAP_HEIGHT - BOUNDARY_WIDTH - 2)

            # Převedení pozice dlaždice na pozici v herním světě
            medkit.x = new_tile_x * TILE_SIZE + TILE_SIZE // 2
            medkit.y = new_tile_y * TILE_SIZE + TILE_SIZE // 2

            return True
    return False


