import json
import subprocess
import ctypes
import sys
import os
import tkinter as tk
from tkinter import messagebox

BASE_DIR = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

C = {
    "bg":       "#0B0F1A",
    "header":   "#0D1520",
    "card":     "#111827",
    "card_hl":  "#141D30",
    "border":   "#1C2A3A",
    "cyan":     "#00D4FF",
    "cyan_glow":"#003D52",
    "text":     "#E2E8F0",
    "sub":      "#64748B",
    "ok":       "#10B981",
    "err":      "#EF4444",
}

FONT = "맑은 고딕"


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin():
    params = " ".join(f'"{a}"' for a in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit(0)


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_profile(adapter, profile):
    cmds = [
        f'netsh interface ip set address name="{adapter}" source=static '
        f'addr={profile["ip"]} mask={profile["subnet"]} gateway={profile["gateway"]}',
        f'netsh interface ip set dns name="{adapter}" source=static addr={profile["dns"]} register=primary',
    ]
    if profile.get("dns2"):
        cmds.append(f'netsh interface ip add dns name="{adapter}" addr={profile["dns2"]} index=2')
    for cmd in cmds:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="cp949")
        if r.returncode != 0:
            raise RuntimeError(f"명령 실패:\n{cmd}\n\n{r.stderr or r.stdout}")


# ── Cyan Glow Button ───────────────────────────────────────────────────────
class CyanBtn(tk.Canvas):
    W, H = 72, 28

    def __init__(self, parent, text, command, card_bg=None, **kw):
        self._card_bg = card_bg or C["card"]
        super().__init__(parent, width=self.W, height=self.H,
                         highlightthickness=0, bg=self._card_bg, cursor="hand2", **kw)
        self._text = text
        self._cmd = command
        self._enabled = True
        self._hover = False
        self._filled = False
        self._render()
        self.bind("<Button-1>", lambda e: self._enabled and self._cmd())
        self.bind("<Enter>",    lambda e: self._on_hover(True))
        self.bind("<Leave>",    lambda e: self._on_hover(False))

    def _on_hover(self, val):
        if self._enabled and not self._filled:
            self._hover = val
            self._render()

    def _render(self):
        self.delete("all")
        if not self._enabled:
            self.create_rectangle(1, 1, self.W-1, self.H-1, fill="", outline=C["sub"], width=1)
            self.create_text(self.W//2, self.H//2, text=self._text,
                             fill=C["sub"], font=(FONT, 8))
            return
        if self._filled or self._hover:
            # filled cyan
            self.create_rectangle(0, 0, self.W, self.H, fill=C["cyan_glow"], outline="")
            self.create_rectangle(1, 1, self.W-1, self.H-1, fill=C["cyan"], outline="")
            self.create_text(self.W//2, self.H//2, text=self._text,
                             fill="#0B0F1A", font=(FONT, 8, "bold"))
        else:
            # glow outline
            self.create_rectangle(0, 0, self.W, self.H, fill=C["cyan_glow"], outline="")
            self.create_rectangle(1, 1, self.W-1, self.H-1, fill=self._card_bg, outline=C["cyan"], width=1)
            self.create_text(self.W//2, self.H//2, text=self._text,
                             fill=C["cyan"], font=(FONT, 8, "bold"))

    def set_filled(self, val):
        self._filled = val
        self._render()

    def set_enabled(self, val):
        self._enabled = val
        self._render()

    def update_bg(self, bg):
        self._card_bg = bg
        self.config(bg=bg)
        self._render()


# ── Profile Card ───────────────────────────────────────────────────────────
class ProfileCard(tk.Frame):
    FIELDS = [("IP", "ip"), ("서브넷", "subnet"), ("게이트웨이", "gateway"), ("DNS", "dns")]

    def __init__(self, parent, profile, on_activate, **kw):
        super().__init__(parent, bg=C["card"],
                         highlightbackground=C["border"], highlightthickness=1, **kw)
        self._bg = C["card"]
        self._profile = profile
        self._all_widgets = []

        inner = tk.Frame(self, bg=self._bg, padx=16, pady=12)
        inner.pack(fill="both", expand=True)
        self._all_widgets.append(inner)

        # ── Top row: name + button ──────────────────────────
        top = tk.Frame(inner, bg=self._bg)
        top.pack(fill="x", pady=(0, 10))
        self._all_widgets.append(top)

        self._name = tk.Label(top, text=profile["name"], bg=self._bg, fg=C["text"],
                              font=(FONT, 11, "bold"), anchor="w")
        self._name.pack(side="left")
        self._all_widgets.append(self._name)

        self._btn = CyanBtn(top, "활성화", on_activate, card_bg=self._bg)
        self._btn.pack(side="right")

        # ── Separator ───────────────────────────────────────
        sep = tk.Frame(inner, bg=C["border"], height=1)
        sep.pack(fill="x", pady=(0, 10))

        # ── Info grid (2 columns) ───────────────────────────
        grid = tk.Frame(inner, bg=self._bg)
        grid.pack(fill="x")
        self._all_widgets.append(grid)

        fields = list(self.FIELDS)
        if profile.get("dns2"):
            fields.append(("DNS 2", "dns2"))

        for i, (label, key) in enumerate(fields):
            col = (i % 2) * 3
            row = i // 2
            lbl = tk.Label(grid, text=label, bg=self._bg, fg=C["sub"],
                           font=(FONT, 8), anchor="w", width=7)
            lbl.grid(row=row, column=col, sticky="w", pady=2)
            val = tk.Label(grid, text=profile.get(key, ""), bg=self._bg, fg=C["text"],
                           font=(FONT, 9, "bold"), anchor="w")
            val.grid(row=row, column=col+1, sticky="w", padx=(0, 24), pady=2)
            self._all_widgets += [lbl, val]

    def set_active(self, val):
        bg = C["card_hl"] if val else C["card"]
        border = C["cyan"] if val else C["border"]
        self._bg = bg
        self.config(bg=bg, highlightbackground=border)
        for w in self._all_widgets:
            try:
                w.config(bg=bg)
            except Exception:
                pass
        self._btn.update_bg(bg)
        self._btn.set_filled(val)

    def set_btn_enabled(self, val):
        self._btn.set_enabled(val)


# ── Main App ───────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self, config):
        super().__init__()
        self.config_data = config
        self.adapter = config.get("adapter", "이더넷")
        self.profiles = config.get("profiles", [])

        n = len(self.profiles)
        card_h = 130 + (20 if any(p.get("dns2") for p in self.profiles) else 0)
        h = min(58 + 16 + n * (card_h + 10) + 16 + 32, 680)

        self.title("NetSwitcher")
        self.geometry(f"460x{h}")
        self.resizable(False, False)
        self.configure(bg=C["bg"])
        self._build()

    def _build(self):
        # ── Header ──────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=C["header"], height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="NetSwitcher", bg=C["header"], fg=C["cyan"],
                 font=(FONT, 14, "bold")).pack(side="left", padx=20, pady=14)

        tk.Label(hdr, text=f"  {self.adapter}  ", bg=C["border"], fg=C["sub"],
                 font=(FONT, 8), padx=2, pady=2).pack(side="right", padx=16, pady=16)

        # cyan accent line
        tk.Frame(self, bg=C["cyan"], height=2).pack(fill="x")

        # ── Profile Cards ────────────────────────────────────────────
        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=14, pady=14)

        self._cards = []
        for i, p in enumerate(self.profiles):
            def _activate(idx=i): self._on_activate(idx)
            card = ProfileCard(body, p, _activate)
            card.pack(fill="x", pady=(0, 8))
            self._cards.append(card)

        # ── Status Bar ───────────────────────────────────────────────
        status = tk.Frame(self, bg=C["header"], height=30)
        status.pack(fill="x", side="bottom")
        status.pack_propagate(False)
        self._status = tk.Label(status, text="●  준비", bg=C["header"],
                                fg=C["sub"], font=(FONT, 8), anchor="w")
        self._status.pack(side="left", padx=16)

    def _on_activate(self, idx):
        p = self.profiles[idx]
        dns2_line = f"\nDNS 2     {p['dns2']}" if p.get("dns2") else ""
        msg = (f"'{p['name']}' 설정을 적용할까요?\n\n"
               f"IP          {p['ip']}\n"
               f"서브넷    {p['subnet']}\n"
               f"게이트웨이  {p['gateway']}\n"
               f"DNS       {p['dns']}{dns2_line}")
        if not messagebox.askyesno("네트워크 전환", msg, icon="question"):
            return

        for card in self._cards:
            card.set_btn_enabled(False)
        self._set_status("●  적용 중...", C["cyan"])
        self.update()

        try:
            apply_profile(self.adapter, p)
            for i, card in enumerate(self._cards):
                card.set_active(i == idx)
                card.set_btn_enabled(True)
            self._set_status(f"●  {p['name']} 적용 완료", C["ok"])
            messagebox.showinfo("완료", f"'{p['name']}' 설정이 적용되었습니다.")
        except RuntimeError as e:
            for card in self._cards:
                card.set_active(False)
                card.set_btn_enabled(True)
            self._set_status("●  오류 발생", C["err"])
            messagebox.showerror("오류", str(e))

    def _set_status(self, text, color):
        self._status.config(text=text, fg=color)


if __name__ == "__main__":
    if not is_admin():
        run_as_admin()
    try:
        cfg = load_config()
    except Exception as e:
        tk.Tk().withdraw()
        messagebox.showerror("config.json 오류", str(e))
        sys.exit(1)
    App(cfg).mainloop()
