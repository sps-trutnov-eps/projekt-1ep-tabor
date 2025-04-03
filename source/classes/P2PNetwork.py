import socket
import threading
import pickle
import random
import time
import uuid
import sys
import copy

from classes.Player import Player
from config import (
    WIDTH, HEIGHT, COLORS, BASE_UDP_PORT, BROADCAST_PORT, 
    BROADCAST_INTERVAL, UPDATE_INTERVAL, INACTIVE_TIMEOUT
)

class P2PNetwork:
    def __init__(self, instance_id=None):
        # Vytvoření unikátního ID pro tento uzel
        self.node_id = str(uuid.uuid4())
        self.color_index = random.randint(0, len(COLORS) - 1)
        
        # Nastavení portu instance - pokud je zadán, použije se, jinak se vygeneruje
        # Speciální ošetření pro instanci 1, která má problém
        if instance_id is not None:
            if instance_id == 1:
                # Pro instanci 1 použijeme port s větším offsetem, aby se vyhnulo konfliktu
                self.port = BASE_UDP_PORT + 2000 + instance_id
                print(f"Instance 1 používá speciální port {self.port}")
            else:
                self.port = BASE_UDP_PORT + instance_id
        else:
            self.port = random.randint(BASE_UDP_PORT, BASE_UDP_PORT + 1000)
        
        print(f"Instance běží na portu {self.port}")
        
        # Inicializace hráče
        self.player = Player(
            random.randint(0, WIDTH - 100),
            random.randint(0, HEIGHT - 100),
            self.node_id,
            COLORS[self.color_index]
        )
        
        # Slovník všech známých hráčů (včetně sebe)
        self.players = {self.node_id: self.player}
        self.players_lock = threading.Lock()
        
        # Seznam známých peerů (IP adresa, port)
        self.known_peers = set()
        self.peers_lock = threading.Lock()
        
        # Socket pro příjem a odesílání dat
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Opakovaně zkoušet porty, dokud nenajdeme volný
        max_retries = 10
        for _ in range(max_retries):
            try:
                self.socket.bind(('', self.port))
                print(f"Instance běží na portu {self.port}")
                break
            except OSError as e:
                print(f"Port {self.port} je již používán, zkouším jiný port...")
                self.port = random.randint(BASE_UDP_PORT + 1001, BASE_UDP_PORT + 3000)
        else:
            # Pokud se všechny pokusy nezdařily
            print("Nepodařilo se najít volný port. Ukončuji aplikaci.")
            sys.exit(1)
        
        # Socket pro broadcast
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Stav běhu
        self.running = True
        
        # Informace o stavu odpojování neaktivních hráčů
        self.inactive_timeout_disabled = INACTIVE_TIMEOUT <= 0
        if self.inactive_timeout_disabled:
            print("Automatické odpojování neaktivních hráčů je VYPNUTO")
        
        # Odeslání počáteční broadcastové zprávy bez čekání
        try:
            data = {
                "type": "discovery",
                "node_id": self.node_id,
                "ip": socket.gethostbyname(socket.gethostname()),
                "port": self.port
            }
            self.broadcast_socket.sendto(pickle.dumps(data), ('<broadcast>', BROADCAST_PORT))
            print("Odeslána počáteční broadcastová zpráva")
        except Exception as e:
            print(f"Chyba při počátečním broadcastu: {e}")
    
    def start(self):
        # Spuštění vlákna pro příjem dat
        receive_thread = threading.Thread(target=self.receive_data)
        receive_thread.daemon = True
        receive_thread.start()
        
        # Spuštění vlákna pro broadcast
        broadcast_thread = threading.Thread(target=self.broadcast_presence)
        broadcast_thread.daemon = True
        broadcast_thread.start()
        
        # Spuštění vlákna pro pravidelné aktualizace
        update_thread = threading.Thread(target=self.send_updates)
        update_thread.daemon = True
        update_thread.start()
    
    def broadcast_presence(self):
        """Pravidelně vysílá informaci o přítomnosti tohoto uzlu"""
        scan_interval = 10  # Každých 10 cyklů provedemě aktivní sken
        cycle_count = 0
        
        while self.running:
            try:
                # Informace o tomto uzlu
                data = {
                    "type": "discovery",
                    "node_id": self.node_id,
                    "ip": socket.gethostbyname(socket.gethostname()),
                    "port": self.port
                }
                
                # Odeslání na broadcast adresu
                self.broadcast_socket.sendto(pickle.dumps(data), ('<broadcast>', BROADCAST_PORT))
                
                # Navíc pošleme přímé zprávy všem známým peerům pro zajištění obousměrné komunikace
                with self.peers_lock:
                    peers_copy = self.known_peers.copy()
                
                for peer_address in peers_copy:
                    try:
                        welcome_data = {
                            "type": "welcome",
                            "node_id": self.node_id,
                            "port": self.port,
                            "player": self.player  # Přidáme informace o hráči
                        }
                        self.socket.sendto(pickle.dumps(welcome_data), peer_address)
                    except Exception as e:
                        print(f"Chyba při odesílání welcome zprávy na {peer_address}: {e}")
                
                # Periodicky provádíme aktivní sken
                cycle_count += 1
                if cycle_count >= scan_interval:
                    self.scan_for_peers()
                    cycle_count = 0
                
                time.sleep(BROADCAST_INTERVAL)
            except Exception as e:
                print(f"Chyba při broadcast vysílání: {e}")
    
    def send_updates(self):
        """Pravidelně odesílá aktualizace o pozici hráče všem známým peerům"""
        while self.running:
            if self.known_peers:
                player_data = {
                    "type": "update",
                    "node_id": self.node_id,
                    "player": self.player
                }
                data = pickle.dumps(player_data)
                
                # Kopie seznamu peerů, aby se vyhnulo změnám během iterace
                with self.peers_lock:
                    peers_copy = self.known_peers.copy()
                
                # Odeslání všem známým peerům
                for peer_address in peers_copy:
                    try:
                        ip, port = peer_address
                        self.socket.sendto(data, (ip, port))
                    except Exception as e:
                        print(f"Chyba při odesílání aktualizace na {peer_address}: {e}")
            
            time.sleep(UPDATE_INTERVAL)
    
    def receive_data(self):
        """Přijímá data od ostatních uzlů"""
        # Pokus o nalezení všech peerů v síti - zkusit všechny potenciální porty
        self.scan_for_peers()
        
        # Broadcast port je sdílený mezi všemi instancemi
        # Stačí, když jedna instance poslouchá na broadcast portu
        # Ostatní instance se dozvědí o peerech z přímých zpráv
        
        discovery_socket = None
        try:
            # Vytvoření socketu pro discovery zprávy
            discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            discovery_socket.bind(('', BROADCAST_PORT))
            print(f"Naslouchám na broadcastovém portu {BROADCAST_PORT}")
        except OSError as e:
            print(f"Nelze navázat na broadcastový port {BROADCAST_PORT}, pravděpodobně již používán.")
            print(f"Chyba: {e}")
            print("Nezastavuji aplikaci - budu se spoléhat jen na přímou komunikaci.")
        
        # Nastavení hlavního socketu jako neblokující
        self.socket.setblocking(False)
        
        # Nastavení discovery socketu jako neblokující (pokud existuje)
        if discovery_socket:
            discovery_socket.setblocking(False)
        
        while self.running:
            # Kontrola discovery zpráv (pouze pokud máme discovery socket)
            if discovery_socket:
                try:
                    data, addr = discovery_socket.recvfrom(2048)
                    message = pickle.loads(data)
                    
                    if message["type"] == "discovery" and message["node_id"] != self.node_id:
                        peer_ip = message["ip"]
                        peer_port = message["port"]
                        peer_address = (peer_ip, peer_port)
                        
                        with self.peers_lock:
                            if peer_address not in self.known_peers:
                                print(f"Nalezen nový peer: {peer_ip}:{peer_port}")
                                self.known_peers.add(peer_address)
                                
                                # Odešlete uvítací zprávu, aby nás druhá strana také zaregistrovala
                                welcome_data = {
                                    "type": "welcome",
                                    "node_id": self.node_id,
                                    "port": self.port,
                                    "player": self.player  # Přidáme informace o našem hráči hned v uvítací zprávě
                                }
                                self.socket.sendto(pickle.dumps(welcome_data), peer_address)
                                
                                # Okamžité odeslání aktualizace o našem hráči
                                player_data = {
                                    "type": "update",
                                    "node_id": self.node_id,
                                    "player": self.player
                                }
                                self.socket.sendto(pickle.dumps(player_data), peer_address)
                except:
                    pass
                
            # Kontrola update a uvítacích zpráv
            try:
                data, addr = self.socket.recvfrom(2048)
                message = pickle.loads(data)
                
                if message["node_id"] != self.node_id:  # Ignorujte vlastní zprávy
                    peer_ip = addr[0]
                    
                    if message["type"] == "update":
                        peer_port = addr[1]
                        peer_address = (peer_ip, peer_port)
                        
                        # Přidání peera, pokud ještě není známý
                        with self.peers_lock:
                            if peer_address not in self.known_peers:
                                print(f"Přidán peer z update zprávy: {peer_ip}:{peer_port}")
                                self.known_peers.add(peer_address)
                                
                                # Když máme nový peer, hned mu pošleme informace o nás
                                welcome_data = {
                                    "type": "welcome",
                                    "node_id": self.node_id,
                                    "port": self.port,
                                    "player": self.player
                                }
                                self.socket.sendto(pickle.dumps(welcome_data), peer_address)
                        
                        # Aktualizace informací o hráči
                        with self.players_lock:
                            self.players[message["node_id"]] = message["player"]
                    
                    elif message["type"] == "welcome" or message["type"] == "force_discovery":
                        peer_port = message["port"]
                        peer_address = (peer_ip, peer_port)
                        
                        with self.peers_lock:
                            if peer_address not in self.known_peers:
                                print(f"Přidán peer z {message['type']} zprávy: {peer_ip}:{peer_port}")
                                self.known_peers.add(peer_address)
                        
                        # Pokud zpráva obsahuje informace o hráči, uložíme je
                        if "player" in message:
                            with self.players_lock:
                                self.players[message["node_id"]] = message["player"]
                                print(f"Přidán hráč z {message['type']} zprávy: {message['node_id'][:8]}")
                        
                        # Okamžitě odešleme aktualizaci o našem hráči
                        player_data = {
                            "type": "update",
                            "node_id": self.node_id,
                            "player": self.player
                        }
                        self.socket.sendto(pickle.dumps(player_data), peer_address)
                        
                        # A ještě pošleme zpět welcome s naším hráčem, aby to bylo jisté
                        welcome_back = {
                            "type": "welcome",
                            "node_id": self.node_id,
                            "port": self.port,
                            "player": self.player
                        }
                        self.socket.sendto(pickle.dumps(welcome_back), peer_address)
            except:
                pass
                
            # Kontrola na odpojování neaktivních hráčů - pouze pokud je INACTIVE_TIMEOUT > 0
            if INACTIVE_TIMEOUT > 0:
                current_time = time.time()
                inactive_players = []
                
                # Použijeme kopii slovníku pro bezpečnou iteraci a zámek pro thread-safety
                with self.players_lock:
                    players_copy = self.players.copy()
                
                for player_id, player in players_copy.items():
                    if player_id != self.node_id and current_time - player.last_update > INACTIVE_TIMEOUT:
                        inactive_players.append(player_id)
                
                for player_id in inactive_players:
                    print(f"Hráč {player_id[:8]} odpojen kvůli neaktivitě")
                    with self.players_lock:
                        if player_id in self.players:  # Dodatečná kontrola, jestli tam ještě je
                            del self.players[player_id]
                
            time.sleep(0.01)  # Krátká pauza pro snížení zátěže CPU
    
    def move_player(self, dx, dy):
        """Aktualizuje pozici hráče"""
        self.player.move(dx, dy, WIDTH, HEIGHT)
    
    def scan_for_peers(self):
        """Aktivně vyhledá peery na potenciálních portech"""
        my_ip = socket.gethostbyname(socket.gethostname())
        
        # Seznam portů, které by mohly být použity jinými instancemi
        potential_ports = []
        
        # Zkusíme standardní porty pro instance 0-10
        for i in range(11):
            if BASE_UDP_PORT + i != self.port:  # Přeskočíme vlastní port
                potential_ports.append(BASE_UDP_PORT + i)
        
        # Přidáme speciální port pro instanci 1
        potential_ports.append(BASE_UDP_PORT + 2001)
        
        print(f"Aktivní skenování portů: {potential_ports}")
        
        # Pro každý potenciální port zkusíme poslat discovery zprávu
        for port in potential_ports:
            try:
                peer_address = (my_ip, port)
                discovery_data = {
                    "type": "force_discovery",
                    "node_id": self.node_id,
                    "port": self.port,
                    "player": self.player
                }
                self.socket.sendto(pickle.dumps(discovery_data), peer_address)
                print(f"Odesílám force_discovery na {peer_address}")
            except Exception as e:
                print(f"Chyba při skenování portu {port}: {e}")
    
    def shutdown(self):
        """Ukončí síťovou komunikaci"""
        self.running = False
        time.sleep(0.5)
        self.socket.close()
        self.broadcast_socket.close()
        