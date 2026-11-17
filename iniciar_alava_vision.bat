@echo off
rem ============================================================================
rem  Alava Vision - inicia tudo (v0.4.0)
rem  1. Sobe o servidor/painel em segundo plano (janela minimizada)
rem  2. Espera o servidor responder em http://127.0.0.1:8080
rem  3. Abre o player em tela cheia no monitor da TV (padrao: monitor 2)
rem
rem  Painel: http://localhost:8080/   |   Monitor da TV: PLAYER_MONITOR no .env
rem  Para iniciar junto com o Windows: coloque um atalho deste arquivo em
rem  shell:startup  (Win+R, digite shell:startup, Enter).
rem ============================================================================
title Alava Vision
cd /d "%~dp0"

start "Alava Vision - Servidor" /min python -m uvicorn server:app --host 0.0.0.0 --port 8080

echo Aguardando o servidor iniciar...
set /a tentativas=0
:aguardar
powershell -NoProfile -Command "try { Invoke-WebRequest http://127.0.0.1:8080/api/playlists -UseBasicParsing -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"
if not errorlevel 1 goto pronto
set /a tentativas+=1
if %tentativas% geq 60 (
  echo O servidor nao respondeu em 60 segundos. Veja a janela "Alava Vision - Servidor".
  pause
  exit /b 1
)
timeout /t 1 /nobreak >nul
goto aguardar

:pronto
echo Servidor no ar. Abrindo o player na TV...
python player.py
pause
