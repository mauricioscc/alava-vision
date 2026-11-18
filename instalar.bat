@echo off
rem ============================================================================
rem  Alava Vision - instalar (v0.7.0)
rem  Use uma vez, no computador da TV, depois de baixar o projeto (git clone).
rem  1. Confere o Python (3.10 ou mais novo), o Git e o Chrome
rem  2. Instala as bibliotecas (pip install -r requirements.txt)
rem  3. Cria/edita o .env: senha do painel, porta e monitor da TV
rem     (ferramentas\configurar.py; avisa se a porta ja estiver em uso)
rem  4. Pergunta se deve iniciar com o Windows (startup.bat)
rem  5. Pergunta se deve abrir o sistema agora (iniciar_alava_vision.bat)
rem  Pode ser rodado de novo sem perder nada: o .env existente e a pasta data\
rem  (playlists, programacao, logins do Chrome) sao mantidos.
rem  COMO REVERTER: git checkout <commit> -- instalar.bat
rem ============================================================================
setlocal
title Alava Vision - Instalar
cd /d "%~dp0"
echo.
echo  ALAVA VISION - INSTALACAO
echo  =========================
echo.

echo [1/5] Conferindo o Python...
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto sem_python
for /f "delims=" %%v in ('python --version') do echo   %%v - ok

echo [2/5] Conferindo Git e Chrome...
git --version >nul 2>&1
if errorlevel 1 (echo   AVISO: Git nao encontrado. O sistema funciona, mas o atualizar.bat precisa dele.) else (echo   Git - ok)
set "CHROME="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME=1"
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME=1"
if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME=1"
if defined CHROME (echo   Chrome - ok) else (echo   AVISO: Google Chrome nao encontrado. Instale-o antes de abrir o player.)

echo [3/5] Instalando bibliotecas, pode levar alguns minutos...
python -m pip install -r requirements.txt --disable-pip-version-check
if errorlevel 1 goto erro_pip

echo [4/5] Configurando senha, porta e monitor da TV...
python ferramentas\configurar.py
if errorlevel 1 goto erro_config

echo.
echo [5/5] Iniciar com o Windows
choice /c SN /m "Abrir o Alava Vision sozinho sempre que o Windows ligar"
if errorlevel 2 goto perguntar_abrir
call "%~dp0startup.bat" criar

:perguntar_abrir
echo.
choice /c SN /m "Abrir o Alava Vision agora"
if errorlevel 2 goto fim
start "Alava Vision" /min cmd /c ""%~dp0iniciar_alava_vision.bat""

:fim
echo.
echo  Instalacao concluida.
echo  Para abrir:      iniciar_alava_vision.bat
echo  Para atualizar:  atualizar.bat
echo.
pause
exit /b 0

:sem_python
echo.
echo  ERRO: Python 3.10 ou mais novo nao encontrado.
echo  Instale em https://www.python.org/downloads/ marcando "Add Python to PATH"
echo  e rode este instalador de novo.
echo.
pause
exit /b 1

:erro_pip
echo.
echo  ERRO ao instalar as bibliotecas. Confira a internet e rode o instalador de novo.
echo.
pause
exit /b 1

:erro_config
echo.
echo  Configuracao nao concluida. Rode o instalador de novo quando quiser.
echo.
pause
exit /b 1
