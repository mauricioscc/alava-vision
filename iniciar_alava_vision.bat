@echo off
rem ============================================================================
rem  Alava Vision - inicia tudo (v0.7.0)
rem  1. Sobe o servidor/painel em segundo plano (janela minimizada)
rem  2. Espera o servidor responder em http://127.0.0.1:PORT  (PORT do .env, padrao 8080)
rem  3. Abre o player em tela cheia no monitor da TV (padrao: monitor 2)
rem
rem  Painel: http://localhost:PORT/   |   Porta: PORT no .env   |   Monitor da TV: PLAYER_MONITOR no .env
rem  Para iniciar junto com o Windows: coloque um atalho deste arquivo em
rem  shell:startup  (Win+R, digite shell:startup, Enter).
rem ============================================================================
title Alava Vision
cd /d "%~dp0"
rem Porta: PORT no .env (padrao 8080)
set "PORT=8080"
if exist ".env" for /f "usebackq tokens=1,* delims==" %%a in (".env") do if /i "%%a"=="PORT" set "PORT=%%b"
set "PORT=%PORT: =%"

start "Alava Vision - Servidor" /min python -m uvicorn server:app --app-dir "%~dp0." --host 0.0.0.0 --port %PORT%

echo Aguardando o servidor iniciar na porta %PORT%...
set /a tentativas=0
:aguardar
powershell -NoProfile -Command "try { Invoke-WebRequest http://127.0.0.1:%PORT%/api/playlists -UseBasicParsing -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"
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
python "%~dp0player.py"
pause
