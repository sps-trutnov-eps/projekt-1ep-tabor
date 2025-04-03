import pygame
import random

# Inicializace Pygame
pygame.init()
pygame.font.init()

font1 = pygame.font.Font(None, 48)

# Nastavení velikosti okna
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Pygame Hráč - WASD Ovládání")

# Barvy
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Třída pro hráče
class Player:
    def __init__(self, x, y, size, speed):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed
        self.health = 10

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
        
        for medkit_inst in medkits:
            medkit_rect = medkit_inst.get_rect()
            
            if player_rect.colliderect(medkit_rect):
                self.health += 25
                medkit_inst.x = random.randint(0, screen_width - medkit_inst.size)
                medkit_inst.y = random.randint(0, screen_height - medkit_inst.size)
                if self.health >= 100:
                    self.health = 100
    
class Medkit:
    def __init__(self, x=0, y=0, size=0):
        self.x = x
        self.y = y
        self.size = size
        
    def draw(self, screen):
        pygame.draw.rect(screen, GREEN, (self.x, self.y, self.size, self.size))
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)
    
    

# Vytvoření hráče
player = Player(screen_width // 2 - 25, screen_height // 2 - 25, 50, 5)

medkit_inst = Medkit()
medkits = [
    Medkit(100, 100, 50)
    ]

# Hlavní herní smyčka
running = True
while running:
    # Zpracování událostí
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    health_bar = font1.render(f"Health: {player.health}", True, (0, 0, 0))

    keys = pygame.key.get_pressed()

    player.move(keys)

    screen.fill(WHITE)
    
    screen.blit(health_bar, ((screen_width - health_bar.get_width())//2, 50))
    
    player.update()

    player.draw(screen)
    for medkit_inst in medkits:
        medkit_inst.draw(screen)

    pygame.display.flip()

    pygame.time.Clock().tick(60)
    
    print(player.health)

pygame.quit()
