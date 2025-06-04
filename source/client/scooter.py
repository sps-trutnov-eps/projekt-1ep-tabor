import pygame
import math
import os

class Scooter:
    def __init__(self, x, y):
        self.x = x  # pozice ve světě (v pixelech, ne dlaždicích)
        self.y = y
        self.direction = 0  # směr v stupních
        self.radius = 80
        self.speed = 8  # rychlejší než běžný pohyb hráče
        self.is_player_on = False
        
        # Nebudeme načítat texturu, použijeme základní vykreslení
        self.texture = None
        print("Koloběžka inicializována bez textury")
    
    def draw(self, screen, camera_x, camera_y):
        """Vykreslí koloběžku bez použití obrázků"""
        # Definujeme barvy lokálně, aby se předešlo importním problémům
        BLACK = (0, 0, 0)
        BLUE = (0, 0, 255)
        GRAY = (128, 128, 128)
        
        # Pokud je hráč na koloběžce, koloběžka se vykresluje na pozici hráče (střed obrazovky)
        if self.is_player_on:
            screen_x = screen.get_width() // 2
            screen_y = screen.get_height() // 2
        else:
            # Pokud hráč není na koloběžce, vykreslí se na pozici ve světě
            screen_x = int(self.x - camera_x + screen.get_width() // 2)
            screen_y = int(self.y - camera_y + screen.get_height() // 2)
        
        # Základní vykreslení koloběžky bez obrázků
        # Výpočet pozic komponentů podle směru
        front_x = screen_x + math.cos(math.radians(self.direction)) * (self.radius * 0.7)
        front_y = screen_y + math.sin(math.radians(self.direction)) * (self.radius * 0.7)
        back_x = screen_x - math.cos(math.radians(self.direction)) * (self.radius * 0.7)
        back_y = screen_y - math.sin(math.radians(self.direction)) * (self.radius * 0.7)
        
        # Kolečka (větší a výraznější)
        pygame.draw.circle(screen, BLACK, (int(front_x), int(front_y)), 12)
        pygame.draw.circle(screen, GRAY, (int(front_x), int(front_y)), 8)
        pygame.draw.circle(screen, BLACK, (int(back_x), int(back_y)), 12)
        pygame.draw.circle(screen, GRAY, (int(back_x), int(back_y)), 8)
        
        # Deska koloběžky (tlustší čára)
        pygame.draw.line(screen, BLUE, (front_x, front_y), (back_x, back_y), 12)
        
        # Řídítka - vertikální tyč
        handle_base_x = front_x + math.cos(math.radians(self.direction + 90)) * 20
        handle_base_y = front_y + math.sin(math.radians(self.direction + 90)) * 20
        handle_top_x = front_x + math.cos(math.radians(self.direction + 90)) * 50
        handle_top_y = front_y + math.sin(math.radians(self.direction + 90)) * 50
        
        # Vertikální tyč řídítek
        pygame.draw.line(screen, BLACK, (front_x, front_y), (handle_top_x, handle_top_y), 6)
        
        # Horizontální řídítka
        handlebar_left_x = handle_top_x + math.cos(math.radians(self.direction)) * 25
        handlebar_left_y = handle_top_y + math.sin(math.radians(self.direction)) * 25
        handlebar_right_x = handle_top_x - math.cos(math.radians(self.direction)) * 25
        handlebar_right_y = handle_top_y - math.sin(math.radians(self.direction)) * 25
        
        pygame.draw.line(screen, BLACK, (handlebar_left_x, handlebar_left_y), 
                        (handlebar_right_x, handlebar_right_y), 8)
        
        # Malé kolečka na koncích řídítek pro detail
        pygame.draw.circle(screen, BLACK, (int(handlebar_left_x), int(handlebar_left_y)), 4)
        pygame.draw.circle(screen, BLACK, (int(handlebar_right_x), int(handlebar_right_y)), 4)
    
    def check_collision_with_images(self):
        """Kontrola kolize koloběžky s objekty na mapě"""
        # Tuto funkci necháme prázdnou, protože potřebujeme import z main
        # Bude implementována v hlavním souboru
        return False
    
    def to_dict(self):
        """Převede koloběžku na dictionary pro síťovou komunikaci"""
        return {
            'x': self.x,
            'y': self.y,
            'direction': self.direction,
            'is_player_on': self.is_player_on
        }
    
    @classmethod
    def from_dict(cls, data):
        """Vytvoří koloběžku z dictionary dat"""
        scooter = cls(data['x'], data['y'])
        scooter.direction = data['direction']
        scooter.is_player_on = data['is_player_on']
        return scooter