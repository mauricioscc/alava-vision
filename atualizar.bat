@echo off
rem ============================================================================
rem  Alava Vision - atualizar (v0.7.0)
rem  Baixa a versao nova do GitHub e reabre o sistema na TV.
rem  1. Fecha servidor, player e o Chrome da TV (ferramentas\parar_alava_vision.ps1)
rem  2. git pull: baixa a versao nova
rem  3. Atualiza as bibliotecas (pip), caso a versao nova precise de alguma
rem  4. Mostra o que mudou e abre o sistema de novo (iniciar_alava_vision.bat)
rem  Nao mexe no .env nem na pasta data\: senha, playlists, programacao e
rem  logins do Chrome continuam iguais.
rem
rem  Roda a partir de uma copia em %TEMP%: o git pull pode trocar este proprio
rem  arquivo, e o cmd le o .bat aos poucos enquanto ele roda.
rem  COMO REVERTER: git checkout <commit> -- atualizar.bat
rem ============================================================================
setlocal
if /i "%~1"=="--copia" goto copia
copy /y "%~f0" "%TEMP%\alava_vision_atualizar.bat" >nul
"%TEMP%\alava_vision_atualizar.bat" --copia "%~dp0."

:copia
title Alava Vision - Atualizar
pushd "%~2"
if errorlevel 1 goto sem_pasta
set "DIR=%CD%"
rem Porta: PORT no .env (padrao 8080)
set "PORT=8080"
if exist ".env" for /f "usebackq tokens=1,* delims==" %%a in (".env") do if /i "%%a"=="PORT" set "PORT=%%b"
set "PORT=%PORT: =%"

echo.
echo  ALAVA VISION - ATUALIZACAO
echo  ==========================
echo  Pasta: %DIR%
echo.

echo [1/4] Fechando o Alava Vision...
if exist "ferramentas\parar_alava_vision.ps1" powershell -NoProfile -ExecutionPolicy Bypass -File "ferramentas\parar_alava_vision.ps1" -Dir "%DIR%" -Port %PORT%

echo [2/4] Baixando a versao nova...
set "ANTES="
for /f "delims=" %%h in ('git rev-parse HEAD 2^>nul') do set "ANTES=%%h"
git pull --ff-only
if errorlevel 1 goto erro_git

echo [3/4] Atualizando bibliotecas...
python -m pip install -r requirements.txt -q --disable-pip-version-check
if errorlevel 1 echo   AVISO: falha ao atualizar as bibliotecas. Confira a internet.

echo [4/4] Versao instalada:
python -c "import io,re; t=io.open('CHANGELOG.md',encoding='utf-8').read(); m=re.search(r'^### \[(.+?)\]', t, re.M); print('  Alava Vision', m.group(1) if m else '?')"
set "DEPOIS="
for /f "delims=" %%h in ('git rev-parse HEAD 2^>nul') do set "DEPOIS=%%h"
if "%ANTES%"=="%DEPOIS%" (echo   Ja estava na versao mais nova.) else (echo   Novidades: & git log --oneline --no-merges %ANTES%..%DEPOIS%)
goto abrir

:erro_git
echo.
echo  AVISO: nao foi possivel baixar a versao nova.
echo  Causas comuns: sem internet, ou algum arquivo desta pasta foi alterado a mao
echo  (veja com: git status). O sistema sera aberto na versao atual.
echo.
pause

:abrir
echo.
echo Abrindo o Alava Vision...
start "Alava Vision" /min "%DIR%\iniciar_alava_vision.bat"
popd
timeout /t 5 >nul
exit

:sem_pasta
echo  ERRO: pasta do Alava Vision nao encontrada: %~2
pause
exit /b 1
