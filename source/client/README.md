# Tábor - Herní Klient

Tento projekt obsahuje klientskou část multiplayerové hry "Tábor" - bojové hry s prvky PvE v prostředí letního tábora. Aplikace kombinuje mapové prostředí, pokročilý zbraňový systém, systém zdraví a síťovou komunikaci pro více hráčů současně.

## Serverová architektura

Klient komunikuje s WebSocket serverem, který je zodpovědný za:

1. Přijímání připojení od klientů
2. Udržování seznamu aktivních hráčů a jejich pozic
3. Distribuci aktualizací pozic všem připojeným klientům
4. Správu odpojených klientů

Server je možné hostovat lokálně nebo využít cloudové služby jako Render.com.

## Instalace

Pro správné fungování klienta potřebujete nainstalovat následující balíčky:

```bash
pip install -r requirements.txt
```

nebo jednotlivě:

```bash
pip install pygame==2.5.2
pip install aiohttp==3.8.5
pip install asyncio
pip install requests
```

## Spuštění klienta

Nejprve je vhodné probudit herní server (pokud je hostovaný v cloudu):

```bash
python wake_up.py
```

Pro spuštění hlavní hry:

```bash
python main.py
```

V souboru `main.py` můžete nastavit adresu serveru úpravou proměnné `SERVER_URL`:

```python
# Pro server hostovaný na Render.com:
SERVER_URL = "wss://projekt-1ep-tabor.onrender.com/ws"
# Pro lokální server:
# SERVER_URL = "ws://localhost:5555/ws"
```

## Soubory projektu

- `main.py` - Hlavní herní soubor obsahující celou implementaci hry
- `wake_up.py` - Utilita pro probuzení serveru hostovaného v cloudu
- `items/medkit.py` - Modul pro správu medkitů a PvE prvků
- `images/` - Složka s texturami zbraní, hráčů a předmětů
- `requirements.txt` - Seznam Python závislostí

## Ovládání

- **Pohyb hráče**: Šipky nebo klávesy WASD
- **Střelba**: Levé tlačítko myši
- **Změna zbraně**: Kolečko myši nahoru/dolů
- **Otáčení**: Pohyb myší (hráč se automaticky otáčí směrem k kurzoru)
- **Sběr medkitů**: Automatický při doteku
- **Ukončení hry**: ESC nebo zavření okna

## Funkce hry

1. **Herní mapa**: Prostorná 2D mapa s okrajovými hranicemi, vodicí mřížkou a podporou pro objekty a textury
2. **Pokročilý systém zbraní**: Výběr ze 4 různých zbraní s unikátními vlastnostmi a projektily
3. **Multiplayerová komunikace**: Zobrazení ostatních hráčů v reálném čase s plynulou interpolací pohybu
4. **Projektilový systém**: Vizuálně odlišené projektily pro každou zbraň s různými vlastnostmi
5. **PvE prvky**: Systém medkitů pro obnovu zdraví rozptýlených po mapě
6. **Kolizní systém**: Detekce kolizí s hranicemi mapy, objekty a předměty
7. **Síťová optimalizace**: Měření odezvy serveru a inteligentní keep-alive komunikace
8. **Diagnostické informace**: Zobrazení FPS, pozice hráče, stavu připojení a dalších užitečných dat
9. **Pokrovilé ovládání**: Plynulé otáčení směrem k myši, přepínání zbraní kolečkem myši

## Zbraňový a projektilový systém

Hra obsahuje 4 unikátní zbraně s různými taktikami použití:

- **Kuše (Crossbow)**: 
  - Poškození: 25 HP
  - Cooldown: 30 snímků (~0.5s)
  - Projektily: Žluté, rychlé, střední dosah
  
- **Raketomet (Rocket Launcher)**: 
  - Poškození: 50 HP  
  - Cooldown: 60 snímků (~1s)
  - Projektily: Oranžové, pomalé, dlouhý dosah, velké

- **Brokovnice (Shotgun)**: 
  - Poškození: 35 HP
  - Cooldown: 45 snímků (~0.75s) 
  - Projektily: Bílé, velmi rychlé, krátký dosah

- **Odstřelovačka (Sniper)**: 
  - Poškození: 75 HP
  - Cooldown: 90 snímků (~1.5s)
  - Projektily: Cyan, nejrychlejší, nejdelší dosah, malé

Každá zbraň má vlastní vizuální projektily s realistickými balistickými vlastnostmi.

## Síťová komunikace

Klient komunikuje se serverem pomocí WebSocket protokolu, což poskytuje:

- Obousměrnou komunikaci v reálném čase
- Nízkou latenci
- Efektivní přenos dat

## PvE prvky a herní mechaniky

### Systém medkitů
- **Automatické generování**: 5 medkitů náhodně umístěných po mapě
- **Sběr**: Automatický při kolizi s hráčem (+10 zdraví)
- **Respawn**: Medkity se po sebrání přesunou na nové náhodné pozice
- **Vizuální označení**: Červené kříže s bílým pozadím

### Herní svět
- **Velikost mapy**: 100x100 dlaždic (4000x4000 pixelů)
- **Hranice**: Neprůchodné okraje s postupným ztmavováním
- **Vodicí mřížka**: Vizuální pomůcka pro orientaci na mapě
- **Kamera**: Sleduje hráče s plynulým pohybem

### Teknické detaily
- **Engine**: Pygame 2.5.2
- **Framerate**: 60 FPS
- **Rozlišení**: 800x600 pixelů (fixní)
- **Síťový protokol**: WebSocket pro real-time komunikaci

## Probuzení serveru

Cloudové služby jako Render.com často po nějaké době nečinnosti uspávají bezplatné instance. Skript `wake_up.py` slouží k:

1. Ověření dostupnosti serveru
2. Opakovaným pokusům o probuzení serveru po dobu až 10 minut
3. Poskytnutí zpětné vazby uživateli o stavu serveru

Doporučujeme před spuštěním hlavní hry vždy nejprve spustit `wake_up.py` a počkat na úspěšné probuzení serveru.

## Diagnostické informace

Na obrazovce klienta se zobrazují užitečné informace:

- Stav připojení
- Počet připojených hráčů
- ID hráče (přiděleno serverem)
- Odezva serveru (v ms)
- FPS
- Stav pohybu
- Aktuální pozice hráče
- Aktuální zbraň a její cooldown

## Řešení problémů

- **Server neodpovídá**: Bezplatné služby na Render.com se uspávají po 15 minutách nečinnosti. Použijte skript `wake_up.py` pro probuzení serveru.

- **Vysoká latence**: Na bezplatném plánu Render.com je určitá latence normální. Pro lokální vývoj a testování doporučujeme použít lokální server.

- **Problémy s připojením**: Ověřte, že server běží a používáte správnou adresu serveru.

- **Problémy s načítáním textur**: Ujistěte se, že adresářová struktura obsahuje složky `gun` a `images` s potřebnými obrázky.
