import pygame
from config import WIDTH, HEIGHT, BLACK, WHITE
from classes.P2PNetwork import P2PNetwork
from classes.Player import Player
import sys

class Game:
    def __init__(self, instance_id=None):
        pygame.init()
        self.window = pygame.display.set_mode((WIDTH, HEIGHT))
        
        # Nastavení titulku okna, pokud je zadáno ID instance
        title = f"P2P Multiplayer Hra"
        if instance_id is not None:
            title += f" - Instance {instance_id}"
        pygame.display.set_caption(title)
        
        # Po inicializaci nastavíme okno na správnou pozici (pokud je zadáno ID instance)
        if instance_id is not None:
            # Posunutí okna vpravo pro druhou a další instance
            import os
            if os.name == 'nt':  # Windows
                try:
                    import ctypes
                    user32 = ctypes.windll.user32
                    screen_width = user32.GetSystemMetrics(0)
                    x_pos = instance_id * (WIDTH // 2)
                    if x_pos + WIDTH > screen_width:
                        x_pos = 0
                        y_pos = HEIGHT
                    else:
                        y_pos = 0
                    os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x_pos},{y_pos}"
                    pygame.display.set_mode((WIDTH, HEIGHT))
                except Exception as e:
                    print(f"Nepodařilo se nastavit pozici okna: {e}")
        
        self.clock = pygame.time.Clock()
        self.network = P2PNetwork(instance_id)
        self.running = True
    
    def run(self):
        # Spuštění síťové komunikace
        self.network.start()
        
        # Hlavní herní smyčka
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            # Ovládání hráče
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -5
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = 5
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy = -5
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy = 5
            
            if dx != 0 or dy != 0:
                self.network.move_player(dx, dy)
            
            # Vykreslení
            self.window.fill(BLACK)
            
            # Vykreslení všech hráčů - použijeme kopii slovníku s thread-safe přístupem
            try:
                with self.network.players_lock:
                    players_copy = self.network.players.copy()
                
                for player_id, player in players_copy.items():
                    player.draw(self.window)
            except Exception as e:
                print(f"Chyba při vykreslování hráčů: {e}")
            
            # Zobrazení informací
            font = pygame.font.SysFont("Arial", 24)
            
            # Moje ID
            my_id_text = font.render(f"ID: {self.network.node_id[:8]}", True, WHITE)
            self.window.blit(my_id_text, (10, 10))
            
            # Můj port
            port_text = font.render(f"Port: {self.network.port}", True, WHITE)
            self.window.blit(port_text, (10, 40))
            
            # Zobrazení informace o vypnutém timeoutu (pokud je vypnutý)
            if hasattr(self.network, 'inactive_timeout_disabled') and self.network.inactive_timeout_disabled:
                timeout_text = font.render("Odpojování neaktivních hráčů: VYPNUTO", True, (0, 255, 0))
                self.window.blit(timeout_text, (WIDTH - 350, 10))
            
            # Počet připojených hráčů
            try:
                with self.network.players_lock:
                    num_players = len(self.network.players)
                    player_ids = [pid[:6] for pid in self.network.players.keys()]
                
                players_text = font.render(f"Hráči: {num_players} {player_ids}", True, WHITE)
                self.window.blit(players_text, (10, 70))
            except Exception as e:
                players_text = font.render(f"Hráči: čtení... ({str(e)[:10]})", True, WHITE)
                self.window.blit(players_text, (10, 70))
            
            # Počet známých peerů
            try:
                peers_text = font.render(f"Peeři: {len(self.network.known_peers)}", True, WHITE)
                self.window.blit(peers_text, (10, 100))
            except:
                peers_text = font.render(f"Peeři: čtení...", True, WHITE)
                self.window.blit(peers_text, (10, 100))
            
            pygame.display.update()
            self.clock.tick(60)
        
        # Ukončení
        self.network.shutdown()
        pygame.quit()
        