import pygame
import random
import math

# Inicializace Pygame
pygame.init()
pygame.font.init()

font1 = pygame.font.Font(None, 48)
font2 = pygame.font.Font(None, 28)

# Nastavení velikosti okna
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Pygame Hráč - WASD Ovládání")

# Barvy
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
EXPLOSION_COLOR = (255, 165, 0)

# promenne
grenades_inv = 0

# Třída pro hráče
class Player:
    def __init__(self, x, y, size, speed):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed
        self.health = 10
        self.grenades = 0
        self.has_grenade = False
        self.last_grenade_time = 0

    def move(self, keys):
        if keys[pygame.K_a]:  # Pohyb doleva
            self.x -= self.speed
        if keys[pygame.K_d]:  # Pohyb doprava
            self.x += self.speed
        if keys[pygame.K_w]:  # Pohyb nahoru
            self.y -= self.speed
        if keys[pygame.K_s]:  # Pohyb dolů
            self.y += self.speed

        # Udržení hráče v rámci obrazovky
        self.x = max(0, min(self.x, screen_width - self.size))
        self.y = max(0, min(self.y, screen_height - self.size))

    def draw(self, screen):
        pygame.draw.rect(screen, RED, (self.x, self.y, self.size, self.size))
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)
    
    def update(self):
        player_rect = self.get_rect()
        
        self.num_grenade()
        
        for medkit_inst in medkits:
            medkit_rect = medkit_inst.get_rect()
            
            if player_rect.colliderect(medkit_rect):
                self.health += 25
                medkit_inst.x = random.randint(0, screen_width - medkit_inst.size)
                medkit_inst.y = random.randint(0, screen_height - medkit_inst.size)
                if self.health >= 100:
                    self.health = 100
            
        for grenade_inst in grenades:
            grenade_rect = grenade_inst.get_rect()
            
            if player_rect.colliderect(grenade_rect):
                self.grenades += 1
                grenade_inst.x = random.randint(0, screen_width - grenade_inst.size)
                grenade_inst.y = random.randint(0, screen_height - grenade_inst.size)
    
    def num_grenade(self):
        if self.grenades > 0:
            self.has_grenade = True
        else:
            self.has_grenade = False
        
    def throw_grenade(self, velocity_x, velocity_y):
        current_time = pygame.time.get_ticks()
        if self.grenades > 0 and current_time - self.last_grenade_time >= 3000:
            thrown_grenade = Grenade_projectile(self.x, self.y, velocity_x, velocity_y)
            self.grenades -= 1
            self.last_grenade_time = current_time
            return thrown_grenade
        return None
        
            
    
class Medkit:
    def __init__(self, x=0, y=0, size=0):
        self.x = x
        self.y = y
        self.size = size
        
    def draw(self, screen):
        pygame.draw.rect(screen, GREEN, (self.x, self.y, self.size, self.size))
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)
    
class Grenade:
    def __init__(self, x=0, y=0, size=0):
        self.x = x
        self.y = y
        self.size = size
    
    def draw(self, screen):
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.size, self.size))
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)
    
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
        self.explosion_radius = 300
        self.explosion_damage = 5
        self.explosion_time = 0
        self.explosion_duration = 500

    def update(self):
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
                self.explode()
    
    def draw(self, screen):
        if self.state == 'stopped' or self.state == 'moving':
            pygame.draw.circle(screen, BLACK, (self.x, self.y), self.size)
        
        elif self.state == 'exploded':
            pygame.draw.circle(screen, EXPLOSION_COLOR, (self.x, self.y), self.explosion_radius, 3)
    
    def explode(self):
        player_rect = player.get_rect()
        distance = math.sqrt((self.x - player.x) ** 2 + (self.y - player.y) ** 2)
        
        if distance <= self.explosion_radius:
            # Player is within the explosion radius, deal damage
            player.health -= self.explosion_damage
            if player.health < 0:
                player.health = 0
    
    

# Vytvoření hráče
player = Player(screen_width // 2 - 25, screen_height // 2 - 25, 50, 5)

medkit_inst = Medkit()
grenade_inst = Grenade()
medkits = [
    Medkit(100, 100, 50)
    ]
grenades = [
    Grenade(200, 500, 50)
   ]

thrown_grenades = []

# Hlavní herní smyčka
running = True
while running:
    # Zpracování událostí
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    keys = pygame.key.get_pressed()
    
    if keys[pygame.K_SPACE] and player.has_grenade:
        thrown_grenade = player.throw_grenade(5, -5)
        if thrown_grenade:
            thrown_grenades.append(thrown_grenade)
    
    current_time = pygame.time.get_ticks()
    cooldown_time = max(0, 4000 - (current_time - player.last_grenade_time)) // 1000    
            
    health_bar = font1.render(f"Health: {player.health}", True, (0, 0, 0))
    grenades_txt = font2.render(f"Grenades: {player.grenades}", True, (0, 0, 0))
    grenades_cd = font2.render(f"{cooldown_time}s", True, (0, 0, 0))

    player.move(keys)

    screen.fill(WHITE)
    
    screen.blit(health_bar, ((screen_width - health_bar.get_width())//2, 50))
    screen.blit(grenades_txt, ((screen_width - 160), 50))
    if cooldown_time > 0:
        screen.blit(grenades_cd, ((screen_width - 160 + (grenades_txt.get_width()//2)), 30))
    
    player.update()

    player.draw(screen)
    for medkit_inst in medkits:
        medkit_inst.draw(screen)
    
    for grenade_inst in grenades:
        grenade_inst.draw(screen)
    
    for thrown_grenade in thrown_grenades:
        thrown_grenade.update()
        thrown_grenade.draw(screen)
        if thrown_grenade.state == 'exploded' and pygame.time.get_ticks() - thrown_grenade.explosion_time > 500:
            thrown_grenades.remove(thrown_grenade)

    pygame.display.flip()

    pygame.time.Clock().tick(60)

pygame.quit()
