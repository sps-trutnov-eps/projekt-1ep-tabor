# Návod k použití pokročilého testovacího klienta

Tento pokročilý testovací klient umožňuje komplexní testování tvého herního WebSocket serveru. Nabízí různé testy a monitorovací funkce, které ti pomohou ověřit správnou funkčnost a výkon serveru.

## Instalace požadavků

Před použitím klienta potřebuješ nainstalovat potřebné závislosti:

```bash
pip install aiohttp
```

## Základní použití

```bash
python test_client_advanced.py --host projekt-1ep-tabor.onrender.com --test basic
```

Klient automaticky použije správný protokol (`ws://` pro lokální testování, `wss://` pro produkci) a přidá endpoint `/ws`.

## Typy testů

Klient nabízí čtyři hlavní typy testů:

### 1. Základní test (`--test basic`)

Simuluje jednoho hráče, který se pohybuje po herní ploše a komunikuje se serverem.

```bash
python advanced_websocket_client.py --host projekt-1ep-tabor.onrender.com --test basic --moves 30
```

### 2. Zátěžový test (`--test stress`)

Simuluje více hráčů najednou pro otestování, jak server zvládá větší zátěž.

```bash
python advanced_websocket_client.py --host projekt-1ep-tabor.onrender.com --test stress --players 10
```

### 3. Test latence (`--test latency`)

Měří odezvu serveru - jak rychle reaguje na požadavky klienta.

```bash
python advanced_websocket_client.py --host projekt-1ep-tabor.onrender.com --test latency
```

### 4. Monitorování (`--test monitor`)

Dlouhodobé sledování dostupnosti a stability serveru.

```bash
python advanced_websocket_client.py --host projekt-1ep-tabor.onrender.com --test monitor --duration 300 --interval 10
```

### 5. Všechny testy (`--test all`)

Spustí postupně všechny testy.

```bash
python advanced_websocket_client.py --host projekt-1ep-tabor.onrender.com --test all
```

## Další parametry

Klient podporuje řadu dalších parametrů pro přizpůsobení testů:

| Parametr | Popis | Výchozí hodnota |
|----------|-------|-----------------|
| `--host` | Adresa serveru | localhost |
| `--port` | Port serveru (používá se jen pro lokální testování) | 5555 |
| `--players` | Počet hráčů pro zátěžový test | 3 |
| `--moves` | Počet pohybů na hráče | 20 |
| `--delay` | Zpoždění mezi pohyby v sekundách | 0.5 |
| `--pattern` | Vzor pohybu hráčů (random, circle, square) | random |
| `--duration` | Doba monitorování v sekundách | 60 |
| `--interval` | Interval kontrol při monitorování v sekundách | 5 |

## Vzory pohybu

Klient podporuje tři různé vzory pohybu pro hráče:

1. **Náhodný pohyb (`--pattern random`)**
   - Hráč se pohybuje náhodně po herní ploše

2. **Kruhový pohyb (`--pattern circle`)**
   - Hráč se pohybuje po kruhové dráze
   - Užitečné pro vizuální testování a sledování pohybu

3. **Čtvercový pohyb (`--pattern square`)**
   - Hráč se pohybuje po čtvercové dráze
   - Vhodné pro testování hranic herní plochy

## Příklady použití

### Lokální testování

```bash
python advanced_websocket_client.py --host localhost --port 5555 --test basic
```

### Zátěžový test s 20 hráči pohybujícími se po kruhu

```bash
python advanced_websocket_client.py --host projekt-1ep-tabor.onrender.com --test stress --players 20 --pattern circle
```

### 5-minutové monitorování s kontrolou každých 30 sekund

```bash
python advanced_websocket_client.py --host projekt-1ep-tabor.onrender.com --test monitor --duration 300 --interval 30
```

### Kompletní test s rychlými pohyby

```bash
python advanced_websocket_client.py --host projekt-1ep-tabor.onrender.com --test all --delay 0.1
```

## Interpretace výsledků

### Zátěžový test

Sleduj, zda server zvládá současné připojení více hráčů a zda nedochází k výpadkům nebo zpožděním.

### Test latence

- **Průměrná latence** pod 100ms je vynikající
- **Průměrná latence** 100-300ms je přijatelná
- **Průměrná latence** nad 300ms může způsobovat problémy v reálném čase

### Monitorování

Sleduje spolehlivost serveru v čase. Hodnota "Spolehlivost serveru" by měla být co nejblíže 100%.

## Řešení problémů

### Chyby připojení

- Ověř, že server běží
- Zkontroluj, že používáš správnou adresu serveru
- Ujisti se, že server má endpoint `/ws`

### Vysoká latence

- Na bezplatném plánu Render.com je určitá latence normální
- Zvyš hodnotu parametru `--delay` pro snížení zatížení serveru

### Server neodpovídá

- Bezplatné služby na Render.com se uspávají po 15 minutách nečinnosti
- Zkus nejprve otevřít stránku serveru v prohlížeči pro "probuzení" služby
