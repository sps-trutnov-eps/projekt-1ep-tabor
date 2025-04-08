import pygame
import sys
import math

# Inicializace Pygame
pygame.init()

# Nastavení obrazovky
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Panáček s koloběžkou - Pohyblivé pozadí")

# Barvy
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)  # Barva na silnici

# Třída pro kameru/svět
class Camera:
    def __init__(self):
        self.x = 0  # offset x
        self.y = 0  # offset y
        self.world_width = 2000
        self.world_height = 2000
    
    def apply(self, x, y):
        #světové souřadnice na souřadnice obrazovky
        return x - self.x, y - self.y
    
    def update(self, target_x, target_y):
        # Aktualizujte kamery
        self.x = target_x - WIDTH // 2
        self.y = target_y - HEIGHT // 2
        
        #maximalní hranice
        self.x = max(0, min(self.world_width - WIDTH, self.x))
        self.y = max(0, min(self.world_height - HEIGHT, self.y))

# Třída pro panáčka
class Player:
    def __init__(self, x, y):
        self.x = x  #pozice ve světě
        self.y = y
        self.radius = 15
        self.speed = 3
        self.direction = 0  #kam jde(uhel)
        try:
            self.image = pygame.image.load('player-regular.png')
            #správný uhel
            self.image = pygame.transform.rotate(self.image, -90)
            #změna velikosti obrázku kruh z obrázku
            self.image = pygame.transform.scale(self.image, (self.radius*2, self.radius*2))
            #vytvoření originální kopie pro rotaci
            self.original_image = self.image.copy()
        except pygame.error:
            print("Nepodařilo se načíst obrázek. Používám základní tvar.")
            self.image = None
    
    def draw(self, camera):
        # kde vykreslit obrázek
        screen_x, screen_y = camera.apply(self.x, self.y)
        
        if self.image:
            # Rotace obrázku podle směru
            rotated_image = pygame.transform.rotate(self.original_image, -self.direction)
            # Získání nového obdélníku pro rotovaný obrázek
            rect = rotated_image.get_rect(center=(int(screen_x), int(screen_y)))
            # Vykreslení rotovaného obrázku
            screen.blit(rotated_image, rect.topleft)
        else:
            # Záložní řešení, pokud není obrázek
            pygame.draw.circle(screen, RED, (int(screen_x), int(screen_y)), self.radius)
            #nos      
            nose_x = screen_x + math.cos(math.radians(self.direction)) * self.radius
            nose_y = screen_y + math.sin(math.radians(self.direction)) * self.radius
            pygame.draw.line(screen, BLACK, (screen_x, screen_y), (nose_x, nose_y), 3)
    
    def move(self, keys, camera):
        # Pohyb panáčka (pouze když není na koloběžce)
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
        
        # Hranice světa
        self.x = max(self.radius, min(camera.world_width - self.radius, self.x))
        self.y = max(self.radius, min(camera.world_height - self.radius, self.y))

# Třída pro koloběžku
class Scooter:
    def __init__(self, x, y):
        self.x = x  # skutečná pozice ve světě
        self.y = y
        self.direction = 0
        self.radius = 20  # Velikost koloběžky při pohledu shora
        self.speed = 6
        self.is_player_on = False  # Informace o tom, zda je hráč na koloběžce
    
    def draw(self, camera):
        # Získejte pozici na obrazovce z pozice ve světě
        screen_x, screen_y = camera.apply(self.x, self.y)
        
        # Přední a zadní kolečko - pozice ve světě
        front_x_world = self.x + math.cos(math.radians(self.direction)) * (self.radius * 0.7)
        front_y_world = self.y + math.sin(math.radians(self.direction)) * (self.radius * 0.7)
        back_x_world = self.x - math.cos(math.radians(self.direction)) * (self.radius * 0.7)
        back_y_world = self.y - math.sin(math.radians(self.direction)) * (self.radius * 0.7)
        
        # Převod na pozice na obrazovce
        front_x, front_y = camera.apply(front_x_world, front_y_world)
        back_x, back_y = camera.apply(back_x_world, back_y_world)
        
        pygame.draw.circle(screen, BLACK, (int(front_x), int(front_y)), 5)
        pygame.draw.circle(screen, BLACK, (int(back_x), int(back_y)), 5)
        
        # Tyč koloběžky (řídítka) - pozice ve světě
        handlebar_x_world = front_x_world + math.cos(math.radians(self.direction + 90)) * 12
        handlebar_y_world = front_y_world + math.sin(math.radians(self.direction + 90)) * 12
        handlebar_x2_world = front_x_world + math.cos(math.radians(self.direction - 90)) * 12
        handlebar_y2_world = front_y_world + math.sin(math.radians(self.direction - 90)) * 12
        
        # Převod na pozice na obrazovce
        handlebar_x, handlebar_y = camera.apply(handlebar_x_world, handlebar_y_world)
        handlebar_x2, handlebar_y2 = camera.apply(handlebar_x2_world, handlebar_y2_world)
        
        pygame.draw.line(screen, BLACK, (front_x, front_y), (handlebar_x, handlebar_y), 3)
        pygame.draw.line(screen, BLACK, (front_x, front_y), (handlebar_x2, handlebar_y2), 3)
        
        # Deska koloběžky
        pygame.draw.line(screen, BLUE, (front_x, front_y), (back_x, back_y), 6)
    
    def player_interaction(self, player, keys, camera):
        # Funkce pro interakci s hráčem
        if self.is_player_on:
            # Pohyb, když je hráč na koloběžce
            if keys[pygame.K_LEFT]:
                self.direction = (self.direction - 3) % 360
            if keys[pygame.K_RIGHT]:
                self.direction = (self.direction + 3) % 360
            if keys[pygame.K_UP]:
                # Dopředu na koloběžce - rychlejší
                self.x += math.cos(math.radians(self.direction)) * self.speed
                self.y += math.sin(math.radians(self.direction)) * self.speed
            if keys[pygame.K_DOWN]:
                # Dozadu na koloběžce - pomalejší
                self.x -= math.cos(math.radians(self.direction)) * (self.speed / 2)
                self.y -= math.sin(math.radians(self.direction)) * (self.speed / 2)
            
            # Hranice světa
            self.x = max(self.radius, min(camera.world_width - self.radius, self.x))
            self.y = max(self.radius, min(camera.world_height - self.radius, self.y))
            
            # Aktualizace pozice hráče
            player.x = self.x
            player.y = self.y
            player.direction = self.direction
            
            # Sesednutí z koloběžky pomocí klávesy E
            if keys[pygame.K_e]:
                self.is_player_on = False
                # Posun panáčka mírně od koloběžky ve směru, kterým se díval
                player.x += math.cos(math.radians(player.direction)) * 30
                player.y += math.sin(math.radians(player.direction)) * 30
        else:
            # Kontrola, zda hráč může nasednout na koloběžku
            distance = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
            if keys[pygame.K_e] and distance < 50:
                self.is_player_on = True
                player.x = self.x
                player.y = self.y
                player.direction = self.direction

# Třída pro statické objekty ve světě
class WorldObject:
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
    
    def draw(self, camera):
        # Získejte pozici na obrazovce z pozice ve světě
        screen_x, screen_y = camera.apply(self.x, self.y)
        
        # Vykreslení objektu
        pygame.draw.rect(screen, self.color, (screen_x, screen_y, self.width, self.height))

# Hlavní herní smyčka
def main():
    clock = pygame.time.Clock()
    camera = Camera()  # Vytvoření kamery
    
    # Vytvoření hráče a koloběžky ve středu světa
    world_center_x = camera.world_width // 2
    world_center_y = camera.world_height // 2
    player = Player(world_center_x - 100, world_center_y)
    scooter = Scooter(world_center_x + 100, world_center_y)
    
    # Vytvoření statických objektů ve světě
    world_objects = [
        # Silnice - horizontální
        WorldObject(camera.world_width // 4, camera.world_height // 2, 
                  camera.world_width // 2, 40, GRAY),
        # Silnice - vertikální
        WorldObject(camera.world_width // 2, camera.world_height // 4,
                  40, camera.world_height // 2, GRAY),
        # Nějaké budovy
        WorldObject(camera.world_width // 4, camera.world_height // 4, 100, 100, RED),
        WorldObject(3 * camera.world_width // 4, camera.world_height // 4, 150, 80, GREEN),
        WorldObject(camera.world_width // 4, 3 * camera.world_height // 4, 80, 120, BLUE),
        WorldObject(3 * camera.world_width // 4, 3 * camera.world_height // 4, 120, 100, (150, 75, 0))
    ]
    
    running = True
    was_e_pressed = False  # Pro detekci stisknutí klávesy E pouze jednou
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Reset stavu klávesy E při uvolnění
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_e:
                    was_e_pressed = False
        
        # Získat stisknuté klávesy
        keys = pygame.key.get_pressed()
        
        # Zpracování interakce s koloběžkou
        current_e_pressed = keys[pygame.K_e]
        if current_e_pressed and not was_e_pressed:
            # Nové stisknutí klávesy E - interakce s koloběžkou
            distance = math.sqrt((player.x - scooter.x)**2 + (player.y - scooter.y)**2)
            if not scooter.is_player_on and distance < 50:
                scooter.is_player_on = True
                player.x = scooter.x
                player.y = scooter.y
                player.direction = scooter.direction
            elif scooter.is_player_on:
                scooter.is_player_on = False
                # Posun panáčka mírně od koloběžky ve směru, kterým se díval
                player.x += math.cos(math.radians(player.direction)) * 30
                player.y += math.sin(math.radians(player.direction)) * 30
        was_e_pressed = current_e_pressed
        
        # Pohyb
        if scooter.is_player_on:
            # Pohyb koloběžky s hráčem
            if keys[pygame.K_LEFT]:
                scooter.direction = (scooter.direction - 3) % 360
            if keys[pygame.K_RIGHT]:
                scooter.direction = (scooter.direction + 3) % 360
            if keys[pygame.K_UP]:
                # Dopředu na koloběžce - rychlejší
                scooter.x += math.cos(math.radians(scooter.direction)) * scooter.speed
                scooter.y += math.sin(math.radians(scooter.direction)) * scooter.speed
            if keys[pygame.K_DOWN]:
                # Dozadu na koloběžce - pomalejší
                scooter.x -= math.cos(math.radians(scooter.direction)) * (scooter.speed / 2)
                scooter.y -= math.sin(math.radians(scooter.direction)) * (scooter.speed / 2)
            
            # Hranice světa
            scooter.x = max(scooter.radius, min(camera.world_width - scooter.radius, scooter.x))
            scooter.y = max(scooter.radius, min(camera.world_height - scooter.radius, scooter.y))
            
            # Aktualizace pozice hráče
            player.x = scooter.x
            player.y = scooter.y
            player.direction = scooter.direction
            
            # Aktualizace kamery na pozici hráče/koloběžky
            camera.update(scooter.x, scooter.y)
        else:
            # Pohyb samotného hráče
            player.move(keys, camera)
            
            # Aktualizace kamery na pozici hráče
            camera.update(player.x, player.y)
        
        # Vykreslení
        screen.fill(WHITE)
        
        # Vykreslení mřížky pro lepší vizualizaci pohybu pozadí
        grid_size = 50
        for x in range(0, camera.world_width, grid_size):
            if x < camera.x or x > camera.x + WIDTH:
                continue
            screen_x = x - camera.x
            pygame.draw.line(screen, (230, 230, 230), (screen_x, 0), (screen_x, HEIGHT))
        
        for y in range(0, camera.world_height, grid_size):
            if y < camera.y or y > camera.y + HEIGHT:
                continue
            screen_y = y - camera.y
            pygame.draw.line(screen, (230, 230, 230), (0, screen_y), (WIDTH, screen_y))
        
        # Vykreslení objektů světa
        for obj in world_objects:
            obj.draw(camera)
        
        # Vykreslení koloběžky a panáčka
        if not scooter.is_player_on:
            scooter.draw(camera)
            player.draw(camera)
        else:
            scooter.draw(camera)
            player.draw(camera)  # Nejprve vykreslíme hráče
              # Poté koloběžku, aby byla "pod" hráčem
        
        # Vykreslení souřadnic kamery ve světě (pro debugování)
        font = pygame.font.SysFont(None, 24)
        camera_text = f"Kamera: X={int(camera.x)}, Y={int(camera.y)}"
        player_text = f"Hráč (svět): X={int(player.x)}, Y={int(player.y)}"
        rendered_camera = font.render(camera_text, True, BLACK)
        rendered_player = font.render(player_text, True, BLACK)
        screen.blit(rendered_camera, (10, HEIGHT - 60))
        screen.blit(rendered_player, (10, HEIGHT - 30))
        
        # Instrukce
        instructions = [
            "Pohyb: šipky (nahoru/dolů = dopředu/dozadu, vlevo/vpravo = zatáčení)",
            "Interakce s koloběžkou: E (nasednout/sesednout)"
        ]
        
        for i, text in enumerate(instructions):
            rendered_text = font.render(text, True, BLACK)
            screen.blit(rendered_text, (10, 10 + i * 25))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if True == True:
    main()