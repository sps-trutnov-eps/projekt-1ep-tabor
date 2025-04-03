@echo off
ECHO Spousteni multiplayerove hry - vice instanci
ECHO ========================================
REM Nastaveni promennych
SET PYTHON_PATH=python
SET GAME_SCRIPT=main.py
REM Zjisteni poctu instanci z argumentu nebo pouziti vychozi hodnoty
IF "%1"=="" (
    SET NUM_INSTANCES=3
) ELSE (
    SET NUM_INSTANCES=%1
)
ECHO Spoustim %NUM_INSTANCES% instanci hry...
REM Cyklus pro spusteni X instanci
FOR /L %%i IN (0,1,%NUM_INSTANCES%) DO (
    IF %%i LSS %NUM_INSTANCES% (
        ECHO Spoustim instanci %%i...
        START "Instance %%i" %PYTHON_PATH% %GAME_SCRIPT% %%i
        TIMEOUT /T 1 > NUL
    )
)
ECHO Vsechny instance byly spusteny.
ECHO Pro ukonceni zavrete jednotliva herni okna.
REM Ponechat okno CMD otevrene
ECHO.
ECHO Tento skript muzete zavrit, instance hry budou pokracovat v behu.
PAUSE
