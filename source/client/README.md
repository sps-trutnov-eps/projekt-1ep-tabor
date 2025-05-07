# Multiplayer Herní Klient

Tento projekt obsahuje jednoduchého multiplayer herního klienta, který komunikuje se serverem pomocí WebSocket protokolu. Aplikace umožňuje pohyb hráče v herním prostředí a zobrazuje ostatní připojené hráče v reálném čase.

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
```

## Spuštění klienta

Pro spuštění základního klienta:

```bash
python client.py
```

V souboru `client.py` můžete nastavit adresu serveru úpravou proměnné `SERVER_URL`:

```python
# Pro server hostovaný na Render.com:
SERVER_URL = "wss://projekt-1ep-tabor.onrender.com/ws"
# Pro lokální server:
# SERVER_URL = "ws://localhost:5555/ws"
```

## Ovládání

- Pohyb hráče: šipky nebo klávesy WASD
- Ukončení hry: zavření okna

## Funkce klienta

1. **Plynulý pohyb hráče**: Implementace interpolace zajišťuje plynulý pohyb hráče na obrazovce.
2. **Stálé aktualizace ostatních hráčů**: Pozice ostatních hráčů se aktualizují i když se místní hráč nepohybuje.
3. **Stabilní pozice po zastavení**: Když přestanete mačkat směrové klávesy, váš hráč zůstane stát přesně na místě bez nežádoucích pohybů.
4. **Měření odezvy serveru**: Klient zobrazuje aktuální latenci komunikace se serverem.
5. **Zobrazení FPS**: Pro monitorování výkonu aplikace.

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

## Diagnostické informace

Na obrazovce klienta se zobrazují užitečné informace:
- Stav připojení
- Počet připojených hráčů
- ID hráče (přiděleno serverem)
- Odezva serveru (v ms)
- FPS
- Stav pohybu
- Aktuální pozice hráče

## Testování

Pro testování serveru můžete použít pokročilejší testovací nástroje:

```bash
python test_client.py
```

nebo výkonnější testovací klient:

```bash
python test_client_advanced.py --host projekt-1ep-tabor.onrender.com --test basic
```

Pro více informací o možnostech testování spusťte:

```bash
python test_client_advanced.py --help
```

## Řešení problémů

- **Server neodpovídá**: Bezplatné služby na Render.com se uspávají po 15 minutách nečinnosti. Zkuste nejprve otevřít stránku serveru v prohlížeči pro "probuzení" služby.

- **Vysoká latence**: Na bezplatném plánu Render.com je určitá latence normální. Pro lokální vývoj a testování doporučujeme použít lokální server.

- **Problémy s připojením**: Ověřte, že server běží a používáte správnou adresu serveru.
