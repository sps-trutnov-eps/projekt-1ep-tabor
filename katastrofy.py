import pygame
import asyncio
import threading
import time
import json
import random
from websocket import create_connection
import websockets

# --- Nastavení Pygame ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# --- Třída stromu ---
class Tree:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.base_y = y
        self.alive = True
        self.color = (34, 139, 34)
        self.shaking_offset = 0

    def draw(self, screen):
        if self.alive:
            pygame.draw.rect(screen, self.color, (self.x, self.y, 20, 40))

    def shake(self):
        # Třesení - střídavý offset +/- 5 px
        self.shaking_offset = 5 if (time.time() * 10) % 2 < 1 else -5
        self.y = self.base_y + self.shaking_offset

    def blow_away(self):
        self.x += 5
        if self.x > WIDTH:
            self.alive = False

    def stop_shaking(self):
        # Už netřeseme, ale necháme pozici, kde jsme
        self.y = self.y  # žádná změna, jen zrušíme offset

# --- Websocket Server ---

clients = set()
current_catastrophe = None
catastrophe_end_time = 0

async def notify_catastrophe():
    if current_catastrophe:
        message = json.dumps({
            "type": "catastrophe_start",
            "catastrophe": current_catastrophe,
            "end_time": catastrophe_end_time
        })
        await asyncio.wait([client.send(message) for client in clients])

async def server_handler(websocket, path):
    global current_catastrophe, catastrophe_end_time
    clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if data["action"] == "start_catastrophe":
                current_catastrophe = data["catastrophe"]
                catastrophe_end_time = time.time() + 10  # katastrofa trvá 10 sekund
                print(f"Server: Start katastrofy '{current_catastrophe}'")
                await notify_catastrophe()
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.remove(websocket)

def start_server_loop():
    asyncio.set_event_loop(asyncio.new_event_loop())
    start_server = websockets.serve(server_handler, "localhost", 6789)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    print("Server běží na ws://localhost:6789")
    loop.run_forever()


# --- Websocket klient a Pygame ---

def ws_client_loop(shared_state):
    """
    Připojí se na server a poslouchá zprávy.
    Zprávy nastavují aktuální katastrofu.
    """
    try:
        ws = create_connection("ws://localhost:6789")
        shared_state['ws'] = ws
        while True:
            message = ws.recv()
            data = json.loads(message)
            if data["type"] == "catastrophe_start":
                shared_state['aktivni_katastrofa'] = data["catastrophe"]
                shared_state['cas_konce_katastrofy'] = data["end_time"]
                print(f"Klient: Přijata katastrofa '{shared_state['aktivni_katastrofa']}'")
    except Exception as e:
        print(f"Chyba websocket klienta: {e}")

def send_start_catastrophe(shared_state, cat_type):
    try:
        ws = shared_state.get('ws')
        if ws:
            msg = json.dumps({"action": "start_catastrophe", "catastrophe": cat_type})
            ws.send(msg)
            print(f"Klient: Posílám start katastrofy '{cat_type}'")
    except Exception as e:
        print(f"Chyba při odeslání zprávy: {e}")

def auto_catastrophe_loop(shared_state):
    while True:
        time.sleep(120)  # každé 2 minuty
        cat = random.choice(["Zemětřesení", "Tornádo"])
        send_start_catastrophe(shared_state, cat)


def main():
    # Spustit websocket server v pozadí
    threading.Thread(target=start_server_loop, daemon=True).start()

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Katastrofy Multiplayer - Trvalý efekt")
    clock = pygame.time.Clock()

    trees = [Tree(x * 50 + 100, HEIGHT - 80) for x in range(10)]

    # Sdílený stav mezi vlákny
    shared_state = {
        "aktivni_katastrofa": None,
        "cas_konce_katastrofy": 0,
        "ws": None,
    }

    # Spustit websocket klienta a automatické katastrofy na pozadí
    threading.Thread(target=ws_client_loop, args=(shared_state,), daemon=True).start()
    threading.Thread(target=auto_catastrophe_loop, args=(shared_state,), daemon=True).start()

    running = True
    shaking_trees = set()  # stromům které se právě třesou
    while running:
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        now = time.time()
        aktivni = shared_state["aktivni_katastrofa"]
        konec = shared_state["cas_konce_katastrofy"]

        if aktivni and now < konec:
            if aktivni == "Zemětřesení":
                # při zemětřesení stromy třesou
                for tree in trees:
                    if tree.alive:
                        tree.shake()
                        shaking_trees.add(tree)
            elif aktivni == "Tornádo":
                # při tornádu stromy odletí a zmizí trvale
                for tree in trees:
                    if tree.alive:
                        tree.blow_away()
                        if not tree.alive:
                            if tree in shaking_trees:
                                shaking_trees.remove(tree)
        else:
            # Katastrofa skončila, u zemětřesení už netřeseme stromy, ale necháme je kde jsou
            if aktivni == "Zemětřesení":
                for tree in shaking_trees:
                    tree.stop_shaking()
                shaking_trees.clear()

            shared_state["aktivni_katastrofa"] = None

        # Vykreslení
        screen.fill((135, 206, 235))  # modrá obloha

        for tree in trees:
            tree.draw(screen)

        font = pygame.font.SysFont(None, 36)
        if shared_state["aktivni_katastrofa"]:
            text = font.render(f"Katastrofa: {shared_state['aktivni_katastrofa']}", True, (255, 0, 0))
            screen.blit(text, (20, 20))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
