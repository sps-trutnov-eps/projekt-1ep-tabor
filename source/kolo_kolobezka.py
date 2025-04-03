import pygame
import sys
import math

# Inicializace Pygame
pygame.init()

# Nastavení obrazovky
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Panáček s kolem - Pohled shora")

# Barvy
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)  # Barva na silnici

# Třída pro panáčka
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 15
        self.speed = 3
        self.on_bicycle = False
        self.direction = 0  # Úhel směru (0 = vpravo, 90 = dolů, atd.)
    
    def draw(self):
        # Vykreslení panáčka jako kruhu s malým ukazatelem směru
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)
        
        # Ukazatel směru (nos)
        nose_x = self.x + math.cos(math.radians(self.direction)) * self.radius
        nose_y = self.y + math.sin(math.radians(self.direction)) * self.radius
        pygame.draw.line(screen, BLACK, (self.x, self.y), (nose_x, nose_y), 3)
    
    def move(self, keys, bicycle):
        old_x, old_y = self.x, self.y
        
        if not self.on_bicycle:
            # Pohyb panáčka
            if keys[pygame.K_LEFT]:
                self.direction = (self.direction - 5) % 360
            if keys[pygame.K_RIGHT]:
                self.direction = (self.direction + 5) % 360
            if keys[pygame.K_UP]:
                self.x += math.cos(math.radians(self.direction)) * self.speed
                self.y += math.sin(math.radians(self.direction)) * self.speed
            if keys[pygame.K_DOWN]:
                self.x -= math.cos(math.radians(self.direction)) * self.speed
                self.y -= math.sin(math.radians(self.direction)) * self.speed
        else:
            # Pohyb na kole - rychlejší a změna směru obtížnější
            if keys[pygame.K_LEFT]:
                self.direction = (self.direction - 3) % 360
            if keys[pygame.K_RIGHT]:
                self.direction = (self.direction + 3) % 360
            if keys[pygame.K_UP]:
                # Dopředu na kole - rychlejší
                self.x += math.cos(math.radians(self.direction)) * bicycle.speed
                self.y += math.sin(math.radians(self.direction)) * bicycle.speed
            if keys[pygame.K_DOWN]:
                # Dozadu na kole - pomalejší
                self.x -= math.cos(math.radians(self.direction)) * (bicycle.speed / 2)
                self.y -= math.sin(math.radians(self.direction)) * (bicycle.speed / 2)
        
        # Hranice obrazovky
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))
        
        # Aktualizace pozice kola, pokud je na něm
        if self.on_bicycle:
            bicycle.x = self.x
            bicycle.y = self.y
            bicycle.direction = self.direction

# Třída pro kolo
class Bicycle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.direction = 0
        self.radius = 20  # Velikost kola při pohledu shora
        self.speed = 6
    
    def draw(self):
        
        # Přední a zadní kolo
        front_x = self.x + math.cos(math.radians(self.direction)) * (self.radius * 0.7)
        front_y = self.y + math.sin(math.radians(self.direction)) * (self.radius * 0.7)
        back_x = self.x - math.cos(math.radians(self.direction)) * (self.radius * 0.7)
        back_y = self.y - math.sin(math.radians(self.direction)) * (self.radius * 0.7)
        
        pygame.draw.circle(screen, BLACK, (int(front_x), int(front_y)), 5)
        pygame.draw.circle(screen, BLACK, (int(back_x), int(back_y)), 5)
        
        # Řídítka
        handlebar_x = front_x + math.cos(math.radians(self.direction + 90)) * 10
        handlebar_y = front_y + math.sin(math.radians(self.direction + 90)) * 10
        pygame.draw.line(screen, BLACK, (front_x, front_y), (handlebar_x, handlebar_y), 2)
        handlebar_x2 = front_x + math.cos(math.radians(self.direction - 90)) * 10
        handlebar_y2 = front_y + math.sin(math.radians(self.direction - 90)) * 10
        pygame.draw.line(screen, BLACK, (front_x, front_y), (handlebar_x2, handlebar_y2), 2)

# Hlavní herní smyčka
def main():
    clock = pygame.time.Clock()
    player = Player(WIDTH // 4, HEIGHT // 2)
    bicycle = Bicycle(WIDTH // 2, HEIGHT // 2)
    
    # Vytvoření silnice/cesty
    path_points = [(100, 100), (600, 100), (600, 500), (100, 500), (100, 100)]
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Interakce s kolem pomocí klávesy E
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    # Zkontroluj vzdálenost mezi panáčkem a kolem
                    distance = math.sqrt((player.x - bicycle.x)**2 + (player.y - bicycle.y)**2)
                    if not player.on_bicycle and distance < 50:
                        player.on_bicycle = True
                        player.x = bicycle.x
                        player.y = bicycle.y
                        player.direction = bicycle.direction
                    elif player.on_bicycle:
                        player.on_bicycle = False
                        # Posun panáčka mírně od kola ve směru, kterým se díval
                        player.x += math.cos(math.radians(player.direction)) * 30
                        player.y += math.sin(math.radians(player.direction)) * 30
        
        # Získat stisknuté klávesy
        keys = pygame.key.get_pressed()
        
        # Pohyb
        player.move(keys, bicycle)
        
        # Vykreslení
        screen.fill(WHITE)
        
        # Vykreslení cesty
        pygame.draw.lines(screen, GRAY, False, path_points, 40)
        
        # Vykreslení kola a panáčka
        if not player.on_bicycle:
            bicycle.draw()
        player.draw()
        if player.on_bicycle:
            bicycle.draw()  # Kreslení kola pod panáčkem, když na něm sedí
        
        # Instrukce
        font = pygame.font.SysFont(None, 24)
        instructions = [
            "Pohyb: šipky (nahoru/dolů = dopředu/dozadu, vlevo/vpravo = zatáčení)",
            "Interakce s kolem: E (nasednout/sesednout)"
        ]
        
        for i, text in enumerate(instructions):
            rendered_text = font.render(text, True, BLACK)
            screen.blit(rendered_text, (10, 10 + i * 25))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()