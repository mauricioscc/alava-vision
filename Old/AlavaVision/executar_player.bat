@echo off
title AlavaVision - Player
cd /d "%~dp0"
echo Iniciando AlavaVision Player...
echo.
echo O Player abrira em fullscreen no monitor secundario.
echo Pressione ESC para sair, P para pausar, R para recarregar.
echo.
timeout /t 3 /nobreak >nul
python -m player.app
pause