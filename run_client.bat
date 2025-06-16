@echo off
REM Prechod do slozky klienta
cd /d "%~dp0source\client"

REM Instalace zavislosti, pokud chybi slozka venv
if not exist venv (
    echo Vytvarim virtualni prostredi...
    python -m venv venv
)

REM Aktivace virtualniho prostredi
call venv\Scripts\activate.bat

REM Aktualizace pip
python -m pip install --upgrade pip

REM Instalace pozadavku
pip install -r requirements.txt

REM Spusteni klienta
python main.py

REM Pauza po ukonceni aplikace
pause
