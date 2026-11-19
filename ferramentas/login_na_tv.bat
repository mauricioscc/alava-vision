@echo off
rem ============================================================================
rem  Alava Vision - fazer login num site no Chrome da TV (ferramentas\login_na_tv.bat) - v0.15.0
rem
rem  Para quando o painel avisar "o site pediu login" (ex.: Acessorias com a sessao expirada).
rem  O captcha nao passa com o player controlando o Chrome, entao o login e feito com o
rem  player FECHADO, no mesmo perfil do Chrome que a TV usa (data\browser-profile):
rem    1. fecha o Alava Vision (servidor, player e o Chrome da TV)
rem    2. abre o Chrome da TV no site: faca o login, resolva o captcha, marque "manter conectado"
rem    3. quando voce FECHAR esse Chrome, o Alava Vision abre de novo sozinho
rem
rem  Uso: dois cliques (abre o Acessorias)  ou  login_na_tv.bat https://outro-site.com.br
rem  Rodar no COMPUTADOR DA TV. Nao mexe em playlists nem configuracoes.
rem  COMO REVERTER: apague este arquivo (nada mais depende dele).
rem ============================================================================
setlocal
title Alava Vision - Login no Chrome da TV
cd /d "%~dp0.."
set "DIR=%CD%"
set "URL=%~1"
if "%URL%"=="" set "URL=https://app.acessorias.com"
set "PORT=8080"
if exist ".env" for /f "usebackq tokens=1,* delims==" %%a in (".env") do if /i "%%a"=="PORT" set "PORT=%%b"
set "PORT=%PORT: =%"

set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" (
  echo  ERRO: Google Chrome nao encontrado neste computador.
  pause
  exit /b 1
)

echo.
echo  LOGIN NO CHROME DA TV
echo  =====================
echo  Site: %URL%
echo.
echo [1/3] Fechando o Alava Vision...
powershell -NoProfile -ExecutionPolicy Bypass -File "ferramentas\parar_alava_vision.ps1" -Dir "%DIR%" -Port %PORT%

echo [2/3] Abrindo o Chrome da TV. Faca o login, resolva o captcha e marque "manter conectado".
echo       QUANDO TERMINAR, FECHE O CHROME: o Alava Vision abre de novo sozinho.
start "" /wait "%CHROME%" --user-data-dir="%DIR%\data\browser-profile" --no-first-run --new-window "%URL%"

echo [3/3] Abrindo o Alava Vision de novo...
start "Alava Vision" /min cmd /c ""%DIR%\iniciar_alava_vision.bat""
timeout /t 3 >nul
exit /b 0
