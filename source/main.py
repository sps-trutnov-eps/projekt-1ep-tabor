import sys
from classes.Game import Game

if __name__ == "__main__":
    # Kontrola, zda byl zadán argument pro ID instance
    instance_id = None
    if len(sys.argv) > 1:
        try:
            instance_id = int(sys.argv[1])
            print(f"Spouštím instanci {instance_id}")
        except ValueError:
            print("Chyba: Argument instance_id musí být celé číslo")
            print("Použití: python main.py [instance_id]")
            sys.exit(1)
    else:
        print("Spouštím instanci bez ID")
    
    # Malá pauza pro přehlednější výstup při spouštění více instancí
    import time
    time.sleep(0.5)
    
    # Spuštění hry
    game = Game(instance_id)
    game.run()
    