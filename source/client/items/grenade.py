import pygame
import math

class Grenade:
    def __init__(self, x=0, y=0, size=0):
        self.x = x
        self.y = y
        self.size = size
        self.image = pygame.image.load("grenade.png").convert_alpha()
    
    def draw(self, screen):
        self.image = pygame.transform.scale(self.image, (self.size, self.size))
        screen.blit(self.image, (self.x, self.y))
        
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
        self.explosion_radius = 500
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