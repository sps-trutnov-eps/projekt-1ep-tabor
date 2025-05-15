# Multiplayer CTF Herní Klient

Tento projekt obsahuje multiplayer herního klienta pro hru typu Capture The Flag (CTF) s mapovým prostředím, zbraňovým systémem a síťovou komunikací. Aplikace umožňuje pohyb hráče v herním prostředí, používání různých zbraní a zobrazuje ostatní připojené hráče v reálném čase.

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

- `main.py` - Hlavní herní soubor, který kombinuje všechny funkce (mapu, zbraně a síťovou komunikaci)
- `wake_up.py` - Utilita pro probuzení serveru hostovaného v cloudu
- `client.py` - Původní jednoduchý síťový klient (pouze pro referenci)
- `mapa.py` - Původní samostatný modul mapy (pouze pro referenci)
- `zbrane.py` - Původní samostatný modul zbraní (pouze pro referenci)

## Ovládání

- Pohyb hráče: šipky nebo klávesy WASD
- Střelba: levé tlačítko myši
- Změna zbraně: kolečko myši nahoru/dolů
- Otáčení: pohyb myší (hráč se otáčí směrem k myši)
- Ukončení hry: ESC nebo zavření okna

## Funkce hry

1. **Herní mapa**: Prostorná mapa s okrajovými hranicemi a podporou pro objekty
2. **Systém zbraní**: Výběr z několika zbraní s různými vlastnostmi
3. **Multiplayer**: Zobrazení ostatních hráčů v reálném čase
4. **Plynulý pohyb**: Implementace interpolace zajišťuje plynulý pohyb hráčů na obrazovce
5. **Kolizní systém**: Detekce kolizí s hranicemi mapy a objekty
6. **Měření odezvy**: Klient zobrazuje aktuální latenci komunikace se serverem
7. **Zobrazení FPS**: Pro monitorování výkonu aplikace

## Zbraňový systém

Hra obsahuje tyto zbraně:

- **Kuše (Crossbow)**: Střední poškození, rychlá kadence
- **Raketomet (Rocket Launcher)**: Vysoké poškození, pomalá kadence
- **Brokovnice (Shotgun)**: Střední poškození, střední kadence
- **Odstřelovačka (Sniper)**: Velmi vysoké poškození, velmi pomalá kadence

Každá zbraň má svůj cooldown (doba mezi výstřely) a damage (poškození).

## Síťová komunikace

Klient komunikuje se serverem pomocí WebSocket protokolu, což poskytuje:

- Obousměrnou komunikaci v reálném čase
- Nízkou latenci
- Efektivní přenos dat

### Frekvence komunikace

- **Odesílání dat**:
  - Při pohybu hráče
  - Periodicky každých 100 ms jako "keep-alive" (pro aktualizaci stavu ostatních hráčů)

- **Přijímání dat**:
  - Průběžně v každé iteraci herní smyčky s timeoutem 10 ms

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
