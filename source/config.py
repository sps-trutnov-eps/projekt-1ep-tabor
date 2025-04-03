# Herní konfigurace
WIDTH, HEIGHT = 400, 300
PLAYER_SIZE = 40
PLAYER_SPEED = 5

# Barvy
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
COLORS = [RED, GREEN, BLUE, YELLOW, PURPLE, CYAN]

# Síťové nastavení
BASE_UDP_PORT = 5555  # Základní port - bude se inkrementovat pro každou instanci
BROADCAST_PORT = 5556
BROADCAST_INTERVAL = 1.0  # Interval pro vysílání přítomnosti (v sekundách)
UPDATE_INTERVAL = 0.05  # Interval pro odesílání aktualizací (v sekundách)
# Pro testování na jednom počítači vypneme odpojování neaktivních hráčů
# Nastavením na 0 nebo negativní hodnotu vypneme tuto funkci úplně
INACTIVE_TIMEOUT = -1  # Vypnuto - hráči nebudou nikdy odpojeni kvůli neaktivitě
