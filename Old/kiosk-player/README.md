# Kiosk Player

Três arquivos: `server.py` (painel + API), `admin.html` (painel), `player.py` (Chrome em kiosk).

## Instalar
```bash
pip install -r requirements.txt
playwright install chromium
# Linux: se faltar biblioteca -> playwright install-deps chromium
```

## Rodar
Terminal 1 (servidor/painel):
```bash
ADMIN_PASSWORD=suasenha python server.py     # Windows: set ADMIN_PASSWORD=suasenha && python server.py
```
Abra `http://IP-DO-SERVIDOR:8080/` (usuário `admin`), cadastre as páginas e salve.

Terminal 2 (player, na sessão gráfica que tem a TV):
```bash
DISPLAY=:0 python player.py --screen-x 1920     # Linux
python player.py --screen-x 1920                # Windows
```
`--screen-x` = largura do monitor principal (a TV estendida começa depois dele). Só a TV? Use `0`.

## Dicas
- Mudou algo no painel? O player percebe em ~5s, sem reiniciar.
- Iniciar junto com o PC: Linux → serviço systemd (user) ou autostart do desktop; Windows → Agendador de Tarefas "ao fazer logon".
- Linux sem tela física (headless puro): precisa de uma sessão gráfica (X11/Wayland) logada para a TV aparecer.
- O player abre o Google Chrome instalado (modo `cdp`), evitando bloqueios de captcha/login. Se não achar o Chrome: `--browser-path "C:\...\chrome.exe"` ou `--channel msedge`. O modo antigo continua disponível com `--mode playwright`.
- Login e cookies ficam salvos na pasta `perfil`: logue uma vez na TV e a sessão persiste. Se vinha usando versões antigas, apague a pasta `perfil` uma vez.
- Para fechar o player: Alt+F4 ou Ctrl+C no terminal.
