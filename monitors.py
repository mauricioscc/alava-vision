"""
Alava Vision — Monitores (monitors.py) · versão 0.4.0

Descobre os monitores do Windows e mantém a janela do player no monitor da TV.

COMO TESTAR
    python monitors.py              # lista os monitores na numeração usada pelo player
    python player.py --list-monitors  (mesma lista)

NUMERAÇÃO USADA PELO PLAYER
    1 = monitor principal do Windows
    2, 3… = os demais, da esquerda para a direita (empate: de cima para baixo)
    É por isso que "monitor 2" é sempre o segundo monitor, onde a TV fica ligada pelo HDMI,
    independentemente de resolução, escala ou de como as telas estão arrumadas no Windows.

POR QUE NÃO USAR SÓ --window-position DO CHROME
    A posição em pixels muda de máquina para máquina (resolução, escala de DPI, monitor
    acima/abaixo do outro) e o Windows tira as janelas do monitor quando a TV é desligada.
    Aqui o player lê a geometria real das telas e, se precisar, move a janela pela API do
    Windows (SetWindowPos). Isso funciona mesmo com o Chrome em modo kiosk.

COMO REVERTER
    git checkout main -- player.py  (e apague este arquivo), ou volte para a branch main.

MAPA DO CÓDIGO
    DPI awareness (coordenadas reais) .. bloco "if IS_WINDOWS" no topo
    Lista de monitores ................. list_monitors(), pick_monitor()
    Achar a janela do Chrome ........... find_browser_window()
    Mover / minimizar .................. move_to_monitor(), minimize()
    Verificação periódica .............. ensure_on_monitor()  → "ok" | "moved" | "no-monitor" | "no-window"
"""
import ctypes
import sys

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)

    # Sem isto, com escala de 125%/150% o Windows devolve coordenadas "virtuais" e a janela
    # iria para o lugar errado. Per-monitor v2 = coordenadas físicas reais de cada tela.
    try:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        try:
            ctypes.WinDLL("shcore").SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            pass

    class MONITORINFOEXW(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT), ("rcWork", wintypes.RECT),
                    ("dwFlags", wintypes.DWORD), ("szDevice", wintypes.WCHAR * 32)]

    MONITORENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC,
                                         ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    user32.EnumDisplayMonitors.argtypes = [wintypes.HDC, ctypes.POINTER(wintypes.RECT), MONITORENUMPROC, wintypes.LPARAM]
    user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFOEXW)]
    user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    user32.MonitorFromWindow.restype = wintypes.HMONITOR
    user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                    ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]

SW_SHOWMINNOACTIVE = 7
SW_RESTORE = 9
SWP_NOZORDER, SWP_NOACTIVATE, SWP_FRAMECHANGED = 0x0004, 0x0010, 0x0020
MONITOR_DEFAULTTONEAREST = 2


def list_monitors() -> list[dict]:
    """Monitores na numeração do player: principal = 1, depois esquerda→direita."""
    if not IS_WINDOWS:
        return []
    found = []

    def on_monitor(hmon, _hdc, _rect, _lp):
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(info)
        user32.GetMonitorInfoW(hmon, ctypes.byref(info))
        r = info.rcMonitor
        found.append({"handle": hmon, "device": info.szDevice, "primary": bool(info.dwFlags & 1),
                      "left": r.left, "top": r.top, "width": r.right - r.left, "height": r.bottom - r.top})
        return True

    user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(on_monitor), 0)
    found.sort(key=lambda m: (not m["primary"], m["left"], m["top"]))
    for i, m in enumerate(found, start=1):
        m["number"] = i
    return found


def pick_monitor(number: int) -> dict | None:
    return next((m for m in list_monitors() if m["number"] == number), None)


def describe(m: dict) -> str:
    kind = "principal" if m["primary"] else "secundário"
    return f"monitor {m['number']} ({kind}) {m['width']}x{m['height']} em x={m['left']}, y={m['top']}"


def find_browser_window(pid: int) -> int | None:
    """Janela principal do Chrome do player: a maior janela visível do processo `pid`."""
    if not IS_WINDOWS or not pid:
        return None
    best = {"hwnd": None, "area": -1}

    def on_window(hwnd, _lp):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value != pid or not user32.IsWindowVisible(hwnd):
            return True
        cls = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(hwnd, cls, 64)
        if not cls.value.startswith("Chrome_WidgetWin"):
            return True
        r = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(r))
        area = (r.right - r.left) * (r.bottom - r.top)
        if area > best["area"]:
            best.update(hwnd=hwnd, area=area)
        return True

    user32.EnumWindows(WNDENUMPROC(on_window), 0)
    return best["hwnd"]


def move_to_monitor(hwnd: int, mon: dict) -> None:
    """Traz a janela para o monitor e faz ela ocupar a tela inteira dele."""
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetWindowPos(hwnd, None, mon["left"], mon["top"], mon["width"], mon["height"],
                        SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED)


def minimize(hwnd: int) -> None:
    if not user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_SHOWMINNOACTIVE)


def ensure_on_monitor(pid: int, number: int) -> str:
    """Garante a janela do player no monitor `number`.

    Retorna:
      "ok"         — já está no monitor certo, em tela cheia;
      "moved"      — estava fora (ou minimizada) e foi trazida de volta;
      "no-monitor" — o monitor não existe agora (TV desligada/desconectada): a janela é
                     minimizada para não cobrir o monitor principal de quem usa o computador;
      "no-window"  — janela do Chrome ainda não encontrada.
    """
    hwnd = find_browser_window(pid)
    if not hwnd:
        return "no-window"
    mon = pick_monitor(number)
    if mon is None:
        minimize(hwnd)
        return "no-monitor"
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    on_target = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST) == mon["handle"]
    fills = (r.left, r.top, r.right - r.left, r.bottom - r.top) == (mon["left"], mon["top"], mon["width"], mon["height"])
    if on_target and fills and not user32.IsIconic(hwnd):
        return "ok"
    move_to_monitor(hwnd, mon)
    return "moved"


if __name__ == "__main__":
    mons = list_monitors()
    if not mons:
        print("Detecção de monitores disponível apenas no Windows.")
    for m in mons:
        print(describe(m), f"[{m['device']}]")
