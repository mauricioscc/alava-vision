"""
Alava Vision — Player (player.py) · versão 0.9.0

Abre o Chrome em tela cheia SEMPRE no monitor da TV (por padrão o 2º monitor) e exibe
o conteúdo que o servidor manda exibir AGORA, respeitando a programação do painel.

COMO RODAR (com o servidor já rodando; porta = PORT do .env, padrão 8080)
    python player.py                          # TV no 2º monitor (padrão)
    python player.py --list-monitors          # mostra a numeração dos monitores e sai
    python player.py --monitor 3              # TV em outro monitor
    python player.py --monitor 1              # testar com uma tela só (ocupa o monitor principal!)
    python player.py --monitor 0 --screen-x 1366 --screen-y -371   # posição manual (modo antigo)
    Monitor padrão também pode ser definido no .env: PLAYER_MONITOR=2
    Fechar: Ctrl+C no terminal (ou Alt+F4 com o foco na TV).

    Servidor + player juntos: iniciar_alava_vision.bat

COMO O PLAYER FICA SABENDO DAS MUDANÇAS (0.8.0)
    • Mantém uma conexão WebSocket aberta em ws://127.0.0.1:PORT/ws/player. O servidor manda o
      estado na hora em que alguém salva no painel ou a programação troca de bloco.
    • Se a conexão cair (servidor reiniciando, servidor antigo sem WebSocket), volta a consultar
      GET /api/player/state a cada 5 s e tenta reconectar sozinho (1 s, 2 s, 4 s… até 30 s).
    • No terminal: "Aviso instantâneo ligado" / "Aviso instantâneo caiu".

COMPORTAMENTO DO MONITOR
    • Ao abrir, o Chrome é posicionado no monitor escolhido e entra em tela cheia (kiosk).
    • A cada 10 s o player confere: se a janela saiu da TV, ela é recolocada.
    • TV desligada/desconectada (monitor sumiu): a janela é minimizada para não cobrir
      o monitor principal. Quando a TV volta, o player a recoloca automaticamente.
    Detalhes em monitors.py.

LOGO DA ALAVA
    O player não insere nada nas páginas. O logo faz parte das telas de clima e trânsito
    (static/weather.html e /view/traffic no server.py); os sites aparecem sem alteração.

COMO REVERTER
    Com Git:  git log --oneline  e  git checkout <commit> -- player.py
    Sem Git:  backup_v0.2.0_20261117/player.py (versão 0.2.0)

MAPA DO CÓDIGO
    Caminhos dos navegadores ........ BROWSER_PATHS
    Abrir Chrome com porta CDP ...... find_browser(), launch_browser(), cdp_up()
    Monitor da TV ................... target_monitor(), browser_pid(), MonitorGuard  (+ monitors.py)
    Consulta ao servidor ............ fetch_state()  → GET /api/player/state (reserva quando o WebSocket cai)
    Aviso instantâneo (WebSocket) ... PushChannel  → ws://127.0.0.1:PORT/ws/player (thread "push")
    Janela de horário de mensagens .. time_in_window()
    Contador que some após o fim .... countdown_visible()   (config.hide_after)
    Vídeo sem repetição ............. plays_once(), VIDEO_ENDED_JS  → avança quando o vídeo acaba
    URL de cada tipo de item ........ item_url()
    Loop de exibição ................ run()
    Parâmetros de linha de comando .. main()
"""
import argparse
import json
import os
import subprocess
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

import monitors

__version__ = "0.9.0"

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


def signature(state: dict) -> tuple:
    """O que importa para saber se a TV precisa trocar de conteúdo."""
    return state.get("version"), state.get("slot")


class PushChannel:
    """Conexão WebSocket com o servidor, numa thread própria.

    O Playwright só pode ser usado pela thread principal, então esta thread não mexe na tela:
    ela guarda o último estado recebido em `latest` e acende `changed`. O loop de exibição
    confere esses dois a cada segundo.
    """

    def __init__(self, port: int):
        self.url = f"ws://127.0.0.1:{port}/ws/player"
        self.latest: dict | None = None
        self.connected = False
        self.changed = threading.Event()
        threading.Thread(target=self._loop, name="push", daemon=True).start()

    def current(self) -> dict | None:
        """Último estado recebido, ou None se a conexão não está ativa (aí use o HTTP)."""
        latest = self.latest  # lido uma vez só: a thread pode zerá-lo a qualquer momento
        return latest if self.connected else None

    def wait(self, seconds: float) -> bool:
        """Espera até `seconds` ou até chegar um aviso. True = chegou aviso."""
        hit = self.changed.wait(seconds)
        self.changed.clear()
        return hit

    def _loop(self) -> None:
        from websockets.sync.client import connect

        delay, ever_connected, warned = 1, False, False
        while True:
            try:
                with connect(self.url, open_timeout=5) as ws:
                    self.connected, ever_connected, delay = True, True, 1
                    log("Aviso instantâneo ligado (WebSocket conectado)")
                    for msg in ws:
                        self.latest = json.loads(msg)
                        self.changed.set()
            except Exception as e:
                if not ever_connected and not warned:
                    log("Aviso instantâneo indisponível (servidor fora do ar ou de versão antiga), "
                        "consultando a cada 5 s:", str(e).splitlines()[0])
                    warned = True
            if self.connected:
                log("Aviso instantâneo caiu — consultando a cada 5 s até reconectar")
            self.connected, self.latest = False, None
            time.sleep(delay)
            delay = min(delay * 2, 30)


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


def countdown_visible(item: dict) -> bool:
    """Contador com "sumir depois do fim" ligado deixa de ser exibido quando a hora chega."""
    cfg = item.get("config", {})
    if item.get("type") != "countdown" or not cfg.get("hide_after"):
        return True
    try:
        return datetime.now() < datetime.fromisoformat(cfg.get("target", ""))
    except ValueError:
        return True   # data inválida: mostra o item (a própria tela avisa sem números)


def plays_once(item: dict) -> bool:
    """Vídeo com "Repetir" desligado: toca uma vez e o player avança quando ele acaba."""
    return item.get("type") == "video" and item.get("config", {}).get("loop", True) is False


VIDEO_ENDED_JS = "() => { const v = document.querySelector('video'); return !!(v && v.ended); }"


def item_url(item: dict, server: str) -> str:
    t = item["type"]
    if t == "url":
        return item["config"].get("url", "about:blank")
    if t in ("weather", "traffic"):
        return f"{server}/view/{t}"
    return f"{server}/view/{t}/{item['id']}"


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

def run(args, push: PushChannel):
    from playwright.sync_api import sync_playwright

    server = f"http://127.0.0.1:{args.port}"

    proc = None
    with sync_playwright() as p:
        try:
            proc = launch_browser(args)
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{args.cdp_port}")
            ctx = browser.contexts[0] if browser.contexts else browser.new_context()
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.on("dialog", lambda d: d.dismiss())

            guard = MonitorGuard(args, browser_pid(browser, proc))
            guard.wait_window()

            state: dict = {"items": []}
            idx = 0
            current_url = None

            while True:
                pushed = push.current()
                if pushed:
                    state = pushed               # já veio pelo WebSocket, sem perguntar
                else:
                    try:
                        state = fetch_state(server)
                    except Exception as e:
                        log("Sem API, usando última programação:", e)

                items = [x for x in state.get("items", [])
                         if x.get("active") and time_in_window(x.get("config", {})) and countdown_visible(x)]

                if not items:
                    page.set_content(IDLE_HTML)
                    current_url = None
                    idx = 0
                    for _ in range(5):
                        hit = push.wait(1)       # conteúdo novo no painel aparece na hora
                        guard.check()
                        if hit:
                            break
                    continue

                idx %= len(items)
                item = items[idx]
                idx += 1
                duration = max(3, int(item.get("duration", 30)))
                url = item_url(item, server)
                src = state.get("source") or {}
                log(f"[{src.get('name', '?')}] {item['type']} · {item['name']} — {duration}s")

                # Um único item (ex.: sobreposição de clima) não é recarregado a cada ciclo.
                # Exceção: vídeo sem repetição precisa recomeçar do início a cada volta.
                once = plays_once(item)
                if once or not (len(items) == 1 and url == current_url):
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

                # Durante a exibição, confere se algo mudou: versão (alguém salvou no painel)
                # ou slot (a grade mudou de bloco). Com o WebSocket ligado, o aviso chega na
                # hora; sem ele, pergunta ao servidor a cada 5 s.
                shown = signature(state)
                deadline = time.time() + duration
                last_check = time.time()
                while time.time() < deadline:
                    push.wait(1)
                    guard.check()
                    if once:
                        try:
                            if page.evaluate(VIDEO_ENDED_JS):
                                log("Vídeo terminou — próximo item")
                                break
                        except Exception:
                            pass  # página trocando ou fechada: segue pelo tempo normal
                    fresh = push.current()
                    if not fresh:
                        if time.time() - last_check < 5:
                            continue
                        last_check = time.time()
                        try:
                            fresh = fetch_state(server)
                        except Exception:
                            continue
                    if signature(fresh) != shown:
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
    ap.add_argument("--port", type=int, default=int(os.getenv("PORT", "8080")),
                    help="porta do servidor Alava Vision (padrão: PORT do .env ou 8080)")
    ap.add_argument("--channel", default="chrome", help="chrome | msedge")
    ap.add_argument("--browser-path", default="")
    ap.add_argument("--cdp-port", type=int, default=9222)
    ap.add_argument("--profile", default="data/browser-profile")
    args = ap.parse_args()

    if args.list_monitors:
        for m in monitors.list_monitors() or []:
            print(monitors.describe(m))
        return

    mon = target_monitor(args)
    if args.monitor > 0 and monitors.IS_WINDOWS:
        log(f"Alava Vision Player {__version__} — alvo:",
            monitors.describe(mon) if mon else f"monitor {args.monitor} (não conectado agora)")

    push = PushChannel(args.port)  # uma só conexão, mesmo se o player reiniciar
    while True:
        try:
            run(args, push)
        except KeyboardInterrupt:
            log("Player encerrado.")
            break
        except Exception as e:
            log("Player caiu, reiniciando em 5s:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
