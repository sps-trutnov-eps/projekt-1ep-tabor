import pygame
import random
import time
import math

# Inicializace Pygame
pygame.init()

# Konstanty
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SIZE = 30
POWERUP_SIZE = 20
PLAYER_SPEED = 5
POWERUP_TYPES = ["sprint", "shield", "invisible", "bounce"]
POWERUP_COLORS = {
    "sprint": (255, 255, 0),    # žlutá
    "shield": (0, 0, 255),      # modrá
    "invisible": (200, 200, 200), # šedá    
    "bounce": (255, 0, 255)     # purpurová
}
POWERUP_COUNT = 8

# Nastavení obrazovky
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Power-Up Game")
clock = pygame.time.Clock()

# Třída hráče
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = PLAYER_SIZE // 2
        self.color = (255, 0, 0)  # červená
        self.speed = PLAYER_SPEED
        self.active_powerups = {}  # slovník s časovači power-upů
        self.is_invisible = False
        self.has_shield = False
        self.is_frozen = False
        self.can_bounce = False

    def move(self, dx, dy):
        if self.is_frozen:
            return
            
        self.x += dx * self.speed
        self.y += dy * self.speed
        
        # Omezení pohybu na obrazovku
        self.x = max(self.radius, min(self.x, SCREEN_WIDTH - self.radius))
        self.y = max(self.radius, min(self.y, SCREEN_HEIGHT - self.radius))

    def draw(self):
        if self.is_invisible:
            # Průhledný kruh pro neviditelnost
            s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 0, 0, 100), (self.radius, self.radius), self.radius)
            screen.blit(s, (self.x - self.radius, self.y - self.radius))
        else:
            pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
            
        # Vykreslení štítu
        if self.has_shield:
            pygame.draw.circle(screen, (0, 0, 255), (self.x, self.y), self.radius + 5, 3)
            
        # Vykreslení efektu sprintu
        if "sprint" in self.active_powerups:
            pygame.draw.circle(screen, (255, 255, 0), (self.x, self.y), self.radius + 8, 2)
            
        # Vykreslení efektu bounce
        if self.can_bounce:
            pygame.draw.circle(screen, (255, 0, 255), (self.x, self.y), self.radius + 12, 2)

    def apply_powerup(self, powerup_type):
        current_time = time.time()
        duration = 5  # sekundy
        
        if powerup_type == "sprint":
            self.speed = PLAYER_SPEED * 2
            self.active_powerups["sprint"] = current_time + duration
        elif powerup_type == "shield":
            self.has_shield = True
            self.active_powerups["shield"] = current_time + duration
        elif powerup_type == "invisible":
            self.is_invisible = True
            self.active_powerups["invisible"] = current_time + duration
        elif powerup_type == "freeze":
            self.is_frozen = True
            self.active_powerups["freeze"] = current_time + duration/2  # zmrazení je kratší
        elif powerup_type == "bounce":
            self.can_bounce = True
            self.active_powerups["bounce"] = current_time + duration

        print(f"Aktivován power-up: {powerup_type} na {duration} sekund!")

    def update_powerups(self):
        current_time = time.time()
        powerups_to_remove = []

        for powerup_type, end_time in self.active_powerups.items():
            if current_time >= end_time:
                powerups_to_remove.append(powerup_type)

        for powerup_type in powerups_to_remove:
            self.active_powerups.pop(powerup_type)
            
            # Resetování efektů
            if powerup_type == "sprint":
                self.speed = PLAYER_SPEED
                print("Sprint deaktivován!")
            elif powerup_type == "shield":
                self.has_shield = False
                print("Štít deaktivován!")
            elif powerup_type == "invisible":
                self.is_invisible = False
                print("Neviditelnost deaktivována!")
            elif powerup_type == "freeze":
                self.is_frozen = False
                print("Rozmrazení!")
            elif powerup_type == "bounce":
                self.can_bounce = False
                print("Bounce deaktivován!")

# Třída power-up
class PowerUp:
    def __init__(self):
        self.respawn()
    
    def respawn(self):
        self.x = random.randint(POWERUP_SIZE, SCREEN_WIDTH - POWERUP_SIZE)
        self.y = random.randint(POWERUP_SIZE, SCREEN_HEIGHT - POWERUP_SIZE)
        self.type = random.choice(POWERUP_TYPES)
        self.color = POWERUP_COLORS[self.type]
        self.radius = POWERUP_SIZE // 2
        self.active = True
    
    def draw(self):
        if self.active:
            pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
            
    def check_collision(self, player):
        if not self.active:
            return False
            
        distance = math.sqrt((player.x - self.x) ** 2 + (player.y - self.y) ** 2)
        if distance < player.radius + self.radius:
            self.active = False
            return True
        return False

# Vytvoření hráče a power-upů
player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
powerups = [PowerUp() for _ in range(POWERUP_COUNT)]

# Hlavní herní smyčka
running = True
last_respawn_time = time.time()

while running:
    # Zpracování událostí
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Pohyb hráče
    keys = pygame.key.get_pressed()
    movement_x = 0
    movement_y = 0
    
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        movement_y = -1
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        movement_y = 1
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        movement_x = -1
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        movement_x = 1
        
    # Pro diagonální pohyb normalizujeme vektor
    if movement_x != 0 and movement_y != 0:
        magnitude = math.sqrt(movement_x**2 + movement_y**2)
        movement_x /= magnitude
        movement_y /= magnitude
        
    player.move(movement_x, movement_y)
    
    # Aktualizace power-upů
    player.update_powerups()
    
    # Kontrola kolizí s power-upy
    for powerup in powerups:
        if powerup.check_collision(player):
            player.apply_powerup(powerup.type)
    
    # Respawn power-upů
    current_time = time.time()
    if current_time - last_respawn_time > 3:  # každé 3 sekundy
        inactive_powerups = [p for p in powerups if not p.active]
        if inactive_powerups:
            inactive_powerups[0].respawn()
        last_respawn_time = current_time
    
    # Vymazání obrazovky
    screen.fill((50, 50, 50))
    
    # Vykreslení hráče a power-upů
    player.draw()
    for powerup in powerups:
        powerup.draw()
        
    # Zobrazení informací o aktivních power-upech
    font = pygame.font.SysFont(None, 24)
    y_offset = 10
    text = font.render(f"Rychlost: {player.speed}", True, (255, 255, 255))
    screen.blit(text, (10, y_offset))
    y_offset += 25
    
    for powerup_type in player.active_powerups:
        remaining = player.active_powerups[powerup_type] - time.time()
        text = font.render(f"{powerup_type}: {remaining:.1f}s", True, POWERUP_COLORS[powerup_type])
        screen.blit(text, (10, y_offset))
        y_offset += 25
    
    # Aktualizace obrazovky
    pygame.display.flip()
    clock.tick(60)

# Ukončení Pygame
pygame.quit()