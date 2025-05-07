# Návod k použití herního serveru

Toto je jednoduchý WebSocket server pro multiplayerovou hru, navržený pro hostování na platformě Render.com. Server umožňuje více hráčům sdílet své pozice v reálném čase.

## Funkce

- WebSocket komunikace pro přenos dat v reálném čase
- HTTP server pro monitoring a zdravotní kontroly
- Automatické přiřazení ID každému hráči
- Sdílení pozic všech hráčů
- Robustní zpracování chyb a odpojení klientů

## Lokální spuštění

Pro spuštění serveru na lokálním počítači:

```
python server.py
```

Server bude dostupný na `http://localhost:5555` a WebSocket endpoint na `ws://localhost:5555/ws`.

## Endpointy

- **/** - Základní informace o serveru a stavu
- **/status** - JSON s informacemi o připojených klientech
- **/ws** - WebSocket endpoint pro připojení klientů

## Protokol komunikace

### Připojení klienta

Klient se připojí na WebSocket endpoint `/ws`:

```javascript
const ws = new WebSocket("wss://projekt-1ep-tabor.onrender.com/ws");
```

### Odesílání dat na server

Klient odesílá svou pozici jako JSON objekt:

```javascript
ws.send(JSON.stringify({
  x: 100,  // X souřadnice
  y: 200   // Y souřadnice
}));
```

### Příjem dat ze serveru

Server odesílá zpět všechny pozice hráčů jako JSON objekt, kde klíčem je ID hráče a hodnotou je pole souřadnic:

```javascript
{
  "hrac1": [100, 200],
  "hrac2": [150, 250],
  "hrac3": [300, 100]
}
```

## Řešení problémů

### Vysoká latence

- Bezplatný plán Render.com může mít vyšší latenci
- Pro produkční použití zvažte přechod na placený plán

### Klienti se nemohou připojit

- Ověřte, že používají správný protokol (`wss://` pro Render.com)
- Zkontrolujte, že URL obsahuje endpoint `/ws`
- Server může být v režimu spánku - navštivte hlavní URL pro jeho probuzení

## Testování serveru

Pro otestování serveru můžete použít přiložené testovací skripty nebo webový nástroj [WebSocket King](https://websocketking.com/).
