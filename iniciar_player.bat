@echo off
rem Alava Vision - Player (v0.6.4)
rem Porta do servidor: PORT no .env (o player le sozinho; padrao 8080)
rem Abre a TV sempre no monitor 2 (padrao). Para outro monitor: PLAYER_MONITOR no .env
rem ou adicione --monitor N abaixo. Para ver a numeracao: python player.py --list-monitors
title Alava Vision - Player
cd /d "%~dp0"
python player.py
pause
