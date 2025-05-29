class Medkit:
    def __init__(self, x=0, y=0, size=80):
        self.x = x  # Pozice na mapě (ne na obrazovce)
        self.y = y  # Pozice na mapě (ne na obrazovce)
        self.size = size

        try:
            self.image = pygame.image.load("images/medkit.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, (size, size))
        except Exception as e:
            print(f"Chyba při načítání medkitu: {e}")
            self.image = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (255, 0, 0), (0, 0, size, size))
            pygame.draw.rect(self.image, (255, 255, 255), (size//4, size//4, size//2, size//2))
            pygame.draw.line(self.image, (255, 255, 255), (size//2, size//4), (size//2, size*3//4), 3)
    
    def draw(self, screen, camera_x, camera_y):
        screen_x = int(self.x - camera_x + SCREEN_WIDTH // 2)
        screen_y = int(self.y - camera_y + SCREEN_HEIGHT // 2)
        
        if (-self.size <= screen_x <= SCREEN_WIDTH + self.size and 
            -self.size <= screen_y <= SCREEN_HEIGHT + self.size):
            screen.blit(self.image, (screen_x - self.size // 2, screen_y - self.size // 2))
    
    def get_rect(self):
        return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)