import pygame
import random
import time

# Inicializace Pygame
pygame.init()

# Nastavení obrazovky
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Katastrofy s destrukcí objektů!")

# Barvy
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (150, 150, 150)  # Poškozené objekty

# Třída pro objekty na mapě
class Objekt:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)
        self.color = random.choice([RED, BLUE])
        self.damaged = False  # Poškozený stav

    def move_randomly(self):
        """Zemětřesení - objekty poskakují, některé se poškodí, jen malá část zmizí velmi pomalu"""
        destruction_chance = random.random()
        
        if destruction_chance < 0.01:  # Pouze 1 % šance na úplné zničení (10x pomalejší než původně)
            return False
        elif destruction_chance < 0.5:  # 50 % šance na poškození
            self.damaged = True
            self.color = GRAY  # Objekt změní barvu na šedou (poškozený)
        
        # Pohyb objektu při zemětřesení
        self.rect.x += random.randint(-5, 5)
        self.rect.y += random.randint(-5, 5)
        
        return True

    def move_tornado(self):
        """Tornádo - objekty létají chaoticky nahoru, dolů i do stran"""
        if random.random() < 0.4:  # 40 % šance, že objekt začne létat
            self.rect.x += random.randint(-10, 10)  # Pohyb do stran
            self.rect.y -= random.randint(5, 15)  # Pohyb nahoru
            if self.rect.y < -50:  # Malá šance na definitivní zmizení
                return False
        else:
            self.rect.x += random.randint(-5, 5)  # Náhodné pohyby do stran
            if self.rect.y < HEIGHT - 50:  # Padání zpět na zem
                self.rect.y += random.randint(3, 7)  # Pád dolů

        return True

# Vytvoření objektů
objekty = [Objekt(random.randint(100, 700), random.randint(300, 500), 40) for _ in range(10)]

# Proměnná pro sledování aktivní katastrofy
aktivni_katastrofa = None
cas_konce_katastrofy = 0

# Hlavní smyčka hry
running = True
while running:
    screen.fill(WHITE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_k:  # Klávesa K - zemětřesení
                aktivni_katastrofa = "Zemětřesení"
                cas_konce_katastrofy = time.time() + 10
            elif event.key == pygame.K_l:  # Klávesa L - tornádo
                aktivni_katastrofa = "Tornádo"
                cas_konce_katastrofy = time.time() + 10

    # Pokud katastrofa běží, aplikuj efekt
    if aktivni_katastrofa:
        if time.time() < cas_konce_katastrofy:
            if aktivni_katastrofa == "Zemětřesení":
                objekty = [obj for obj in objekty if obj.move_randomly()]
            elif aktivni_katastrofa == "Tornádo":
                objekty = [obj for obj in objekty if obj.move_tornado()]
        else:
            aktivni_katastrofa = None  # Zastavení katastrofy

    # Vykreslení objektů
    for obj in objekty:
        pygame.draw.rect(screen, obj.color, obj.rect)

    pygame.display.flip()
    pygame.time.delay(50)

pygame.quit()
