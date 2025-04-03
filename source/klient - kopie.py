import pygame
import socket
import json

# Konfigurace
SERVER_IP = "192.168.216.218"  # IP serveru (změň podle sítě)
PORT = 5555
WIDTH, HEIGHT = 800, 600

# Připojení k serveru
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, PORT))

# Pygame inicializace
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Startovní pozice
x, y = 100, 100
speed = 5

running = True
while running:
    screen.fill((0, 0, 0))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]: y -= speed
    if keys[pygame.K_s]: y += speed
    if keys[pygame.K_a]: x -= speed
    if keys[pygame.K_d]: x += speed

    # Posílání dat serveru
    client.send(json.dumps({"x": x, "y": y}).encode())

    # Přijímání dat od serveru
    try:
        data = json.loads(client.recv(1024).decode())
        for pos in data.values():
            pygame.draw.rect(screen, (0, 255, 0), (pos[0], pos[1], 20, 20))
    except:
        pass

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
client.close()
