"""
Alava Vision — Player (player.py) · versão 0.4.0

Abre o Chrome em tela cheia SEMPRE no monitor da TV (por padrão o 2º monitor) e exibe
o conteúdo que o servidor manda exibir AGORA, respeitando a programação do painel.

COMO RODAR (com o servidor já rodando na porta 8080)
    python player.py                          # TV no 2º monitor (padrão)
    python player.py --list-monitors          # mostra a numeração dos monitores e sai
    python player.py --monitor 3              # TV em outro monitor
    python player.py --monitor 1              # testar com uma tela só (ocupa o monitor principal!)
    python player.py --monitor 0 --screen-x 1366 --screen-y -371   # posição manual (modo antigo)
    python player.py --no-watermark           # desliga a marca d'água
    python player.py --wm-opacity 0.7         # transparência da marca (0.65 a 0.85 recomendado)
    Monitor padrão também pode ser definido no .env: PLAYER_MONITOR=2
    Fechar: Ctrl+C no terminal (ou Alt+F4 com o foco na TV).

    Servidor + player juntos: iniciar_alava_vision.bat

COMPORTAMENTO DO MONITOR
    • Ao abrir, o Chrome é posicionado no monitor escolhido e entra em tela cheia (kiosk).
    • A cada 10 s o player confere: se a janela saiu da TV, ela é recolocada.
    • TV desligada/desconectada (monitor sumiu): a janela é minimizada para não cobrir
      o monitor principal. Quando a TV volta, o player a recoloca automaticamente.
    Detalhes em monitors.py.

COMO REVERTER
    Com Git:  git checkout main   (volta tudo para a versão 0.3.0)
    Sem Git:  backup_v0.2.0_20261117/player.py (versão 0.2.0)

MAPA DO CÓDIGO
    Caminhos dos navegadores ........ BROWSER_PATHS
    Abrir Chrome com porta CDP ...... find_browser(), launch_browser(), cdp_up()
    Monitor da TV ................... target_monitor(), browser_pid(), MonitorGuard  (+ monitors.py)
    Consulta ao servidor ............ fetch_state()  → GET /api/player/state
    Janela de horário de mensagens .. time_in_window()
    URL de cada tipo de item ........ item_url()
    Marca d'água Alava .............. watermark_script(), WATERMARK_JS
    Loop de exibição ................ run()
    Parâmetros de linha de comando .. main()
"""
import argparse
import base64
import json
import os
import subprocess
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

import monitors

__version__ = "0.4.0"

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")

IDLE_HTML = """<body style="margin:0;background:#0a0a14;color:#4a5568;font-family:system-ui;
display:flex;align-items:center;justify-content:center;height:100vh;font-size:3vw;text-align:center">
<div>📺<br><span style="font-size:1.8vw;margin-top:16px;display:block">Nenhum item ativo.<br>Acesse o painel para adicionar conteúdo.</span></div></body>"""

BROWSER_PATHS = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
    ],
    "msedge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "/usr/bin/microsoft-edge",
    ],
}


def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)


def fetch_state(server: str) -> dict:
    with urllib.request.urlopen(f"{server}/api/player/state", timeout=5) as r:
        return json.load(r)


def cdp_up(port: int) -> bool:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1)
        return True
    except Exception:
        return False


def find_browser(args) -> str:
    if args.browser_path:
        return args.browser_path
    for path in BROWSER_PATHS.get(args.channel or "chrome", []):
        if os.path.exists(path):
            return path
    raise RuntimeError("Chrome não encontrado. Use --browser-path ou --channel msedge.")


def target_monitor(args) -> dict | None:
    """Monitor da TV (None em modo manual, fora do Windows ou se ele não estiver conectado)."""
    if args.monitor <= 0 or not monitors.IS_WINDOWS:
        return None
    return monitors.pick_monitor(args.monitor)


def launch_browser(args) -> subprocess.Popen | None:
    if cdp_up(args.cdp_port):
        log("Reaproveitando navegador já aberto na porta", args.cdp_port)
        return None
    exe = find_browser(args)
    # Abre já sobre o monitor da TV; o modo kiosk ocupa a tela em que a janela nasce.
    # Se a posição não bater (escala de DPI, TV desligada), o MonitorGuard corrige em seguida.
    mon = target_monitor(args)
    x, y, w, h = ((mon["left"], mon["top"], mon["width"], mon["height"]) if mon
                  else (args.screen_x, args.screen_y, args.width, args.height))
    cmd = [
        exe,
        f"--remote-debugging-port={args.cdp_port}",
        f"--user-data-dir={Path(args.profile).resolve()}",
        "--kiosk",
        f"--window-position={x},{y}",
        f"--window-size={w},{h}",
        "--no-first-run", "--no-default-browser-check", "--noerrdialogs",
        "--disable-infobars", "--disable-session-crashed-bubble",
        "--disable-features=Translate",
        "--autoplay-policy=no-user-gesture-required",
        "--disable-blink-features=AutomationControlled",
        "about:blank",
    ]
    log("Abrindo", exe)
    proc = subprocess.Popen(cmd)
    for _ in range(60):
        if cdp_up(args.cdp_port):
            return proc
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("Navegador abriu mas a porta CDP não respondeu.")


def time_in_window(config: dict) -> bool:
    """Mensagens podem ter janela própria (ex.: 12:00–14:00) além da timeline."""
    start, end = config.get("time_start", ""), config.get("time_end", "")
    if not start or not end:
        return True
    return start <= datetime.now().strftime("%H:%M") <= end


def item_url(item: dict, server: str) -> str:
    t = item["type"]
    if t == "url":
        return item["config"].get("url", "about:blank")
    if t in ("weather", "traffic"):
        return f"{server}/view/{t}"
    return f"{server}/view/{t}/{item['id']}"


# ─── Marca d'água ─────────────────────────────────────────────────────────────
#
# Como funciona: o player injeta este script em TODA página que o Chrome abre
# (sites externos e telas do Alava Vision) via `add_init_script`. Ele cria um
# elemento com Shadow DOM — assim o CSS do site não deforma o logo — preso no
# canto superior esquerdo, acima de tudo (z-index máximo) e sem capturar cliques.
# Os estilos são aplicados por JavaScript (element.style), que continua
# funcionando em sites com Content-Security-Policy que bloqueia <style> inline.
# Limitação: sites com CSP que proíbe imagens `data:` não mostram o logo.
#
# Estilo (pedido: discreto, legível em fundo claro e escuro):
#   • altura 4,2% da tela (≈45 px em 1080p), margens de 2,2% / 1,8%;
#   • opacidade configurável (padrão 0.8);
#   • duas sombras escuras: contorno fino + halo suave, para o logo branco
#     continuar legível sobre páginas brancas.

WATERMARK_JS = """
(() => {
  if (window.top !== window) return;
  const SRC = __SRC__, OPACITY = __OPACITY__;
  const mount = () => {
    if (!document.documentElement || document.getElementById('alava-watermark')) return;
    const host = document.createElement('div');
    host.id = 'alava-watermark';
    host.style.setProperty('all', 'initial');
    const root = host.attachShadow({mode: 'closed'});
    const img = document.createElement('img');
    img.src = SRC;
    img.alt = '';
    Object.assign(img.style, {
      position: 'fixed', top: 'max(2.2vh, 14px)', left: 'max(1.8vw, 16px)',
      height: 'clamp(26px, 4.2vh, 72px)', width: 'auto', maxWidth: 'none',
      margin: '0', padding: '0', border: '0', zIndex: '2147483647',
      opacity: String(OPACITY), pointerEvents: 'none', userSelect: 'none',
      filter: 'drop-shadow(0 1px 2px rgba(0,0,0,.55)) drop-shadow(0 0 10px rgba(0,0,0,.35))',
    });
    root.appendChild(img);
    document.documentElement.appendChild(host);
  };
  mount();
  document.addEventListener('DOMContentLoaded', mount);
  setInterval(mount, 2000);
})();
"""


def watermark_script(logo: Path, opacity: float) -> str | None:
    if not logo.exists():
        log("Logo da marca d'água não encontrado:", logo)
        return None
    mime = "image/svg+xml" if logo.suffix.lower() == ".svg" else "image/png"
    src = f"data:{mime};base64,{base64.b64encode(logo.read_bytes()).decode()}"
    return (WATERMARK_JS.replace("__SRC__", json.dumps(src))
            .replace("__OPACITY__", str(max(0.0, min(1.0, opacity)))))


# ─── Monitor da TV ────────────────────────────────────────────────────────────

def browser_pid(browser, proc: subprocess.Popen | None) -> int | None:
    """PID do processo principal do Chrome (dono da janela), pedido ao próprio Chrome."""
    try:
        info = browser.new_browser_cdp_session().send("SystemInfo.getProcessInfo")
        return next(p["id"] for p in info["processInfo"] if p["type"] == "browser")
    except Exception:
        return proc.pid if proc else None


class MonitorGuard:
    """Confere de tempos em tempos se a janela do player está no monitor da TV."""

    def __init__(self, args, pid: int | None):
        self.number, self.pid = args.monitor, pid
        self.enabled = args.monitor > 0 and monitors.IS_WINDOWS and pid is not None
        self.last_status, self.last_check = None, 0.0

    def check(self, force: bool = False) -> None:
        if not self.enabled or (not force and time.time() - self.last_check < 10):
            return
        self.last_check = time.time()
        status = monitors.ensure_on_monitor(self.pid, self.number)
        if status != self.last_status or status == "moved":
            mon = monitors.pick_monitor(self.number)
            if status == "ok":
                log("Player no", monitors.describe(mon))
            elif status == "moved":
                log("Janela posicionada no", monitors.describe(mon))
            elif status == "no-monitor":
                log(f"Monitor {self.number} não encontrado (TV desligada ou desconectada?). "
                    "Player minimizado, aguardando a TV voltar.")
        self.last_status = status

    def wait_window(self, timeout: float = 15) -> None:
        """Logo após abrir o Chrome a janela demora um pouco para existir."""
        end = time.time() + timeout
        while self.enabled and time.time() < end:
            self.check(force=True)
            if self.last_status not in (None, "no-window"):
                time.sleep(1.5)
                self.check(force=True)  # o kiosk às vezes se reposiciona ao terminar de abrir
                return
            time.sleep(0.5)
        if self.enabled:
            log("Não encontrei a janela do Chrome para posicionar no monitor", self.number)


# ─── Loop de exibição ─────────────────────────────────────────────────────────

def run(args):
    from playwright.sync_api import sync_playwright

    server = f"http://127.0.0.1:{args.port}"
    wm_js = None if args.no_watermark else watermark_script((BASE / args.logo).resolve(), args.wm_opacity)

    proc = None
    with sync_playwright() as p:
        try:
            proc = launch_browser(args)
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{args.cdp_port}")
            ctx = browser.contexts[0] if browser.contexts else browser.new_context()
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.on("dialog", lambda d: d.dismiss())
            if wm_js:
                page.add_init_script(wm_js)

            guard = MonitorGuard(args, browser_pid(browser, proc))
            guard.wait_window()

            state: dict = {"items": []}
            idx = 0
            current_url = None

            while True:
                try:
                    state = fetch_state(server)
                except Exception as e:
                    log("Sem API, usando última programação:", e)

                items = [x for x in state.get("items", [])
                         if x.get("active") and time_in_window(x.get("config", {}))]

                if not items:
                    page.set_content(IDLE_HTML)
                    if wm_js:
                        page.evaluate(wm_js)
                    current_url = None
                    idx = 0
                    for _ in range(5):
                        time.sleep(1)
                        guard.check()
                    continue

                idx %= len(items)
                item = items[idx]
                idx += 1
                duration = max(3, int(item.get("duration", 30)))
                url = item_url(item, server)
                src = state.get("source") or {}
                log(f"[{src.get('name', '?')}] {item['type']} · {item['name']} — {duration}s")

                # Um único item (ex.: sobreposição de clima) não é recarregado a cada ciclo.
                if not (len(items) == 1 and url == current_url):
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=20_000)
                        current_url = url
                    except Exception as e:
                        if "closed" in str(e).lower():
                            raise
                        log("Falha ao navegar, pulando:", str(e).splitlines()[0])
                        current_url = None
                        time.sleep(2)
                        continue

                # Durante a exibição, a cada 5 s pergunta ao servidor se algo mudou:
                # versão (alguém salvou no painel) ou slot (a grade mudou de bloco).
                signature = (state.get("version"), state.get("slot"))
                deadline = time.time() + duration
                last_check = time.time()
                while time.time() < deadline:
                    time.sleep(1)
                    guard.check()
                    if time.time() - last_check < 5:
                        continue
                    last_check = time.time()
                    try:
                        fresh = fetch_state(server)
                    except Exception:
                        continue
                    if (fresh.get("version"), fresh.get("slot")) != signature:
                        log("Programação mudou — trocando conteúdo")
                        idx = 0
                        current_url = None
                        deadline = 0
        finally:
            if proc:
                try:
                    proc.terminate()
                except Exception:
                    pass


def main():
    ap = argparse.ArgumentParser(description=f"Alava Vision Player {__version__}")
    ap.add_argument("--monitor", type=int, default=int(os.getenv("PLAYER_MONITOR", "2")),
                    help="monitor da TV: 1 = principal, 2 = segundo (padrão), 0 = posição manual")
    ap.add_argument("--list-monitors", action="store_true", help="lista os monitores e sai")
    ap.add_argument("--screen-x", type=int, default=0, help="só com --monitor 0: posição X da janela")
    ap.add_argument("--screen-y", type=int, default=0, help="só com --monitor 0: posição Y da janela")
    ap.add_argument("--width", type=int, default=1920, help="só com --monitor 0")
    ap.add_argument("--height", type=int, default=1080, help="só com --monitor 0")
    ap.add_argument("--port", type=int, default=8080, help="porta do servidor Alava Vision")
    ap.add_argument("--channel", default="chrome", help="chrome | msedge")
    ap.add_argument("--browser-path", default="")
    ap.add_argument("--cdp-port", type=int, default=9222)
    ap.add_argument("--profile", default="data/browser-profile")
    ap.add_argument("--logo", default="assets/watermark.png", help="arquivo do logo da marca d'água")
    ap.add_argument("--wm-opacity", type=float, default=0.8, help="opacidade da marca d'água (0 a 1)")
    ap.add_argument("--no-watermark", action="store_true", help="não exibir marca d'água")
    args = ap.parse_args()

    if args.list_monitors:
        for m in monitors.list_monitors() or []:
            print(monitors.describe(m))
        return

    mon = target_monitor(args)
    if args.monitor > 0 and monitors.IS_WINDOWS:
        log(f"Alava Vision Player {__version__} — alvo:",
            monitors.describe(mon) if mon else f"monitor {args.monitor} (não conectado agora)")

    while True:
        try:
            run(args)
        except KeyboardInterrupt:
            log("Player encerrado.")
            break
        except Exception as e:
            log("Player caiu, reiniciando em 5s:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
