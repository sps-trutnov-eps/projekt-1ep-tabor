import pygame
import time
from config import PLAYER_SIZE, WHITE

class Player:
    def __init__(self, x, y, id, color):
        self.x = x
        self.y = y
        self.id = id
        self.color = color
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.last_update = time.time()
    
    def move(self, dx, dy, screen_width, screen_height):
        # Kontrola hranic obrazovky
        if 0 <= self.x + dx <= screen_width - PLAYER_SIZE:
            self.x += dx
        if 0 <= self.y + dy <= screen_height - PLAYER_SIZE:
            self.y += dy
        self.rect = pygame.Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)
        self.last_update = time.time()
    
    def draw(self, win):
        pygame.draw.rect(win, self.color, self.rect)
        font = pygame.font.SysFont("Arial", 20)
        # Zobrazení zkráceného ID pro přehlednost
        short_id = str(self.id)[:8]
        text = font.render(short_id, True, WHITE)
        win.blit(text, (self.x + 5, self.y + PLAYER_SIZE//4))
        