@echo off
title Alava Vision - Servidor
cd /d "%~dp0"
echo Iniciando Alava Vision...
pip install -r requirements.txt -q
python -m uvicorn server:app --host 0.0.0.0 --port 8080 --reload
pause
