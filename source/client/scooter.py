import pygame
import math
import os

class Scooter:
    def __init__(self, x, y):
        self.x = x  # pozice ve světě (v pixelech, ne dlaždicích)
        self.y = y
        self.direction = 0  # směr v stupních
        self.radius = 80
        self.speed = 4  # rychlejší než běžný pohyb hráče
        self.is_player_on = False
        
        # Načtení textury koloběžky (volitelné)
        self.texture = None
        try:
            scooter_img = pygame.image.load(os.path.join("images", "scooter.PNG")).convert_alpha()
            self.texture = pygame.transform.scale(scooter_img, (200, 100))
            print("Textura koloběžky načtena")
        except:
            print("Textura koloběžky nenalezena, použiji základní vykreslení")
    
    def draw(self, screen, camera_x, camera_y):
        from __main__ import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, BLUE
        # Pokud je hráč na koloběžce, koloběžka se vykresluje na pozici hráče (střed obrazovky)
        if self.is_player_on:
            screen_x = SCREEN_WIDTH // 2
            screen_y = SCREEN_HEIGHT // 2
        else:
            # Pokud hráč není na koloběžce, vykreslí se na pozici ve světě
            screen_x = int(self.x - camera_x + SCREEN_WIDTH // 2)
            screen_y = int(self.y - camera_y + SCREEN_HEIGHT // 2)
        
        if self.texture:
            # Rotace textury podle směru
            rotated_texture = pygame.transform.rotate(self.texture, -self.direction)
            rot_rect = rotated_texture.get_rect(center=(screen_x, screen_y))
            screen.blit(rotated_texture, rot_rect.topleft)
        else:
            # Základní vykreslení koloběžky
            # Přední a zadní kolečko
            front_x = screen_x + math.cos(math.radians(self.direction)) * (self.radius * 0.7)
            front_y = screen_y + math.sin(math.radians(self.direction)) * (self.radius * 0.7)
            back_x = screen_x - math.cos(math.radians(self.direction)) * (self.radius * 0.7)
            back_y = screen_y - math.sin(math.radians(self.direction)) * (self.radius * 0.7)
            
            # Kolečka
            pygame.draw.circle(screen, BLACK, (int(front_x), int(front_y)), 10)
            pygame.draw.circle(screen, BLACK, (int(back_x), int(back_y)), 10)
            
            # Deska koloběžky
            pygame.draw.line(screen, BLUE, (front_x, front_y), (back_x, back_y), 10)
            
            # Řídítka
            handlebar_x = front_x + math.cos(math.radians(self.direction + 90)) * 40
            handlebar_y = front_y + math.sin(math.radians(self.direction + 90)) * 40
            handlebar_x2 = front_x + math.cos(math.radians(self.direction - 90)) * 40
            handlebar_y2 = front_y + math.sin(math.radians(self.direction - 90)) * 40
            
            pygame.draw.line(screen, BLACK, (front_x, front_y), (handlebar_x, handlebar_y), 10)
            pygame.draw.line(screen, BLACK, (front_x, front_y), (handlebar_x2, handlebar_y2), 10)

    def check_collision_with_images(self):
        """Kontrola kolize koloběžky s objekty na mapě"""
        scooter_hitbox = pygame.Rect(self.x - self.radius, self.y - self.radius, 
                                   self.radius * 2, self.radius * 2)
        
        for img in images:
            if img['hitbox'].colliderect(scooter_hitbox):
                return True
        return False