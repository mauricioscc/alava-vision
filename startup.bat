@echo off
rem ============================================================================
rem  Alava Vision - iniciar com o Windows (v0.7.0)
rem  Cria (ou remove) o atalho "Alava Vision" na pasta Inicializar do Windows
rem  (Win+R, shell:startup). O atalho abre o iniciar_alava_vision.bat, que sobe
rem  o SERVIDOR (painel, playlists e programacao, salvos em data\database.db) e,
rem  quando ele responde, o PLAYER em tela cheia na TV.
rem
rem    startup.bat           pergunta o que fazer
rem    startup.bat criar     cria/recria o atalho sem perguntar (usado pelo instalar.bat)
rem    startup.bat remover   remove o atalho
rem
rem  O atalho roda quando o usuario entra no Windows. Para a TV voltar sozinha
rem  depois de uma queda de energia, o PC precisa entrar no Windows sem senha
rem  (login automatico) e ter "ligar apos queda de energia" ativado na BIOS.
rem  COMO REVERTER: startup.bat remover
rem ============================================================================
setlocal
cd /d "%~dp0"
set "AV_ALVO=%~dp0iniciar_alava_vision.bat"
set "AV_PASTA=%~dp0."
set "AV_LNK=[IO.Path]::Combine([Environment]::GetFolderPath('Startup'), 'Alava Vision.lnk')"
set "MODO=%~1"
if /i "%MODO%"=="criar" goto criar
if /i "%MODO%"=="remover" goto remover

powershell -NoProfile -Command "if (Test-Path -LiteralPath (%AV_LNK%)) { exit 1 } else { exit 0 }"
if not errorlevel 1 goto criar
echo.
echo  O Alava Vision ja inicia com o Windows.
choice /c RXC /m "R = recriar o atalho, X = parar de iniciar com o Windows, C = cancelar"
if errorlevel 3 goto fim
if errorlevel 2 goto remover

:criar
powershell -NoProfile -Command "$l = %AV_LNK%; $s = (New-Object -ComObject WScript.Shell).CreateShortcut($l); $s.TargetPath = $env:AV_ALVO; $s.WorkingDirectory = (Resolve-Path -LiteralPath $env:AV_PASTA).Path; $s.WindowStyle = 7; $s.Description = 'Alava Vision: servidor e player da TV'; $s.Save()"
if errorlevel 1 (echo   ERRO: nao foi possivel criar o atalho.) else (echo   Pronto: o Alava Vision vai abrir sozinho quando o Windows ligar.)
goto fim

:remover
powershell -NoProfile -Command "$l = %AV_LNK%; if (Test-Path -LiteralPath $l) { Remove-Item -LiteralPath $l }"
echo   Pronto: o Alava Vision nao inicia mais com o Windows.

:fim
if "%MODO%"=="" pause
exit /b 0
