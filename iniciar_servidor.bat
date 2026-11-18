@echo off
title Alava Vision - Servidor
cd /d "%~dp0"
rem Porta: PORT no .env (padrao 8080)
set "PORT=8080"
if exist ".env" for /f "usebackq tokens=1,* delims==" %%a in (".env") do if /i "%%a"=="PORT" set "PORT=%%b"
set "PORT=%PORT: =%"
echo Iniciando Alava Vision na porta %PORT%...
pip install -r requirements.txt -q
python -m uvicorn server:app --host 0.0.0.0 --port %PORT% --reload
pause
