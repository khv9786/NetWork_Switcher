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
    "bg":     "#FAFAFA",
    "card":   "#FFFFFF",
    "text":   "#262626",
    "sub":    "#8E8E8E",
    "border": "#DBDBDB",
    "ok":     "#27AE60",
    "err":    "#E74C3C",
    # Instagram gradient stops
    "g0": (0x83, 0x3A, 0xB4),  # purple
    "g1": (0xC1, 0x35, 0x84),  # mid-pink
    "g2": (0xE1, 0x30, 0x6C),  # red-pink
    "g3": (0xF7, 0x77, 0x37),  # orange
}

IG_STOPS = [C["g0"], C["g1"], C["g2"], C["g3"]]


def _ig_color(t):
    """t in [0,1] → Instagram gradient hex color"""
    stops = IG_STOPS
    t = max(0.0, min(1.0, t))
    idx = t * (len(stops) - 1)
    i = min(int(idx), len(stops) - 2)
    frac = idx - i
    r1, g1, b1 = stops[i]
    r2, g2, b2 = stops[i + 1]
    return f"#{int(r1+(r2-r1)*frac):02x}{int(g1+(g2-g1)*frac):02x}{int(b1+(b2-b1)*frac):02x}"


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


# ── Gradient Canvas Button ─────────────────────────────────────────────────
class GradButton(tk.Canvas):
    W, H = 280, 48

    def __init__(self, parent, text, command, **kw):
        super().__init__(parent, width=self.W, height=self.H,
                         highlightthickness=0, bg=C["bg"], cursor="hand2", **kw)
        self._text = text
        self._cmd = command
        self._enabled = True
        self._render()
        self.bind("<Button-1>", lambda e: self._enabled and self._cmd())
        self.bind("<Enter>",    lambda e: self._enabled and self._render(hover=True))
        self.bind("<Leave>",    lambda e: self._enabled and self._render(hover=False))

    def _render(self, hover=False, disabled=False):
        self.delete("all")
        for x in range(self.W):
            t = x / self.W
            if disabled:
                color = "#CCCCCC"
            else:
                r1, g1, b1 = [int(c, 16) for c in [_ig_color(t)[1:3], _ig_color(t)[3:5], _ig_color(t)[5:7]]]
                if hover:
                    r1 = min(255, int(r1 * 1.12))
                    g1 = min(255, int(g1 * 1.12))
                    b1 = min(255, int(b1 * 1.12))
                color = f"#{r1:02x}{g1:02x}{b1:02x}"
            self.create_line(x, 0, x, self.H, fill=color)
        fg = "#AAAAAA" if disabled else "white"
        self.create_text(self.W // 2, self.H // 2, text=self._text,
                         fill=fg, font=("Segoe UI", 11, "bold"))

    def set_enabled(self, val):
        self._enabled = val
        self._render(disabled=not val)
        if not val:
            self.unbind("<Enter>")
            self.unbind("<Leave>")
        else:
            self.bind("<Enter>", lambda e: self._render(hover=True))
            self.bind("<Leave>", lambda e: self._render(hover=False))


# ── Profile Tab Button ─────────────────────────────────────────────────────
class TabBtn(tk.Canvas):
    H = 36

    def __init__(self, parent, text, command, **kw):
        self._text = text
        self._cmd = command
        self._active = False
        w = max(80, len(text) * 14 + 24)
        super().__init__(parent, width=w, height=self.H,
                         highlightthickness=0, bg=C["bg"], cursor="hand2", **kw)
        self._width = w
        self._render()
        self.bind("<Button-1>", lambda e: self._cmd())

    def _render(self):
        self.delete("all")
        if self._active:
            for x in range(self._width):
                self.create_line(x, 0, x, self.H, fill=_ig_color(x / self._width))
            fg = "white"
        else:
            self.create_rectangle(0, 0, self._width, self.H, fill=C["border"], outline="")
            fg = C["sub"]
        self.create_text(self._width // 2, self.H // 2, text=self._text,
                         fill=fg, font=("Segoe UI", 10, "bold" if self._active else "normal"))

    def set_active(self, val):
        self._active = val
        self._render()


# ── Field Row in Info Card ─────────────────────────────────────────────────
class FieldRow(tk.Frame):
    def __init__(self, parent, label, **kw):
        super().__init__(parent, bg=C["card"], **kw)
        tk.Label(self, text=label, width=7, anchor="w",
                 bg=C["card"], fg=C["sub"], font=("Segoe UI", 9)).pack(side="left")
        self._val = tk.Label(self, text="", anchor="w",
                             bg=C["card"], fg=C["text"], font=("Segoe UI", 11, "bold"))
        self._val.pack(side="left")

    def set(self, text, dim=False):
        self._val.config(text=text, fg=C["sub"] if dim else C["text"])


# ── Main App ───────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self, config):
        super().__init__()
        self.config_data = config
        self.adapter = config.get("adapter", "이더넷")
        self.profiles = config.get("profiles", [])
        self.sel = 0

        self.title("NetSwitcher")
        self.geometry("360x520")
        self.resizable(False, False)
        self.configure(bg=C["bg"])
        self._build()
        self._select(0)

    def _build(self):
        # ── Gradient Header ──────────────────────────────────────
        hdr = tk.Canvas(self, width=360, height=72, highlightthickness=0)
        hdr.pack(fill="x")
        for x in range(360):
            hdr.create_line(x, 0, x, 72, fill=_ig_color(x / 360))
        hdr.create_text(180, 36, text="NetSwitcher",
                        fill="white", font=("Segoe UI", 18, "bold"))

        # ── Adapter chip ─────────────────────────────────────────
        chip_frame = tk.Frame(self, bg=C["bg"])
        chip_frame.pack(pady=(12, 0))
        tk.Label(chip_frame, text="어댑터", bg=C["bg"],
                 fg=C["sub"], font=("Segoe UI", 8)).pack(side="left", padx=(0, 4))
        chip = tk.Label(chip_frame, text=self.adapter,
                        bg=C["border"], fg=C["text"],
                        font=("Segoe UI", 9, "bold"), padx=8, pady=2)
        chip.pack(side="left")

        # ── Profile Tab Buttons ───────────────────────────────────
        tab_wrap = tk.Frame(self, bg=C["bg"])
        tab_wrap.pack(pady=14, padx=20, fill="x")
        self.tabs = []
        for i, p in enumerate(self.profiles):
            def _cmd(idx=i): self._select(idx)
            t = TabBtn(tab_wrap, p["name"], _cmd)
            t.pack(side="left", padx=4)
            self.tabs.append(t)

        # ── Info Card ─────────────────────────────────────────────
        outer = tk.Frame(self, bg=C["border"])
        outer.pack(padx=20, fill="x", ipady=1, ipadx=1)
        inner = tk.Frame(outer, bg=C["card"], padx=18, pady=14)
        inner.pack(fill="both")

        self._name_lbl = tk.Label(inner, text="", anchor="w",
                                  bg=C["card"], fg=C["text"],
                                  font=("Segoe UI", 15, "bold"))
        self._name_lbl.pack(fill="x", pady=(0, 10))

        # gradient underline under name
        uline = tk.Canvas(inner, width=280, height=2, highlightthickness=0, bg=C["card"])
        uline.pack(fill="x", pady=(0, 10))
        for x in range(320):
            uline.create_line(x, 0, x, 2, fill=_ig_color(x / 320))

        self._fields = {}
        for key, label in [("ip", "IP"), ("subnet", "서브넷"), ("gateway", "게이트웨이"),
                            ("dns", "DNS"), ("dns2", "DNS 2")]:
            row = FieldRow(inner, label)
            row.pack(fill="x", pady=3)
            self._fields[key] = row

        # ── Apply Button ──────────────────────────────────────────
        btn_frame = tk.Frame(self, bg=C["bg"])
        btn_frame.pack(pady=18)
        self._apply_btn = GradButton(btn_frame, "적   용   하   기", self._on_apply)
        self._apply_btn.pack()

        # ── Status ────────────────────────────────────────────────
        self._status_cv = tk.Canvas(self, width=300, height=22,
                                    highlightthickness=0, bg=C["bg"])
        self._status_cv.pack()
        self._set_status("준비", C["sub"])

    def _select(self, idx):
        self.sel = idx
        for i, t in enumerate(self.tabs):
            t.set_active(i == idx)
        p = self.profiles[idx]
        self._name_lbl.config(text=p["name"])
        self._fields["ip"].set(p.get("ip", ""))
        self._fields["subnet"].set(p.get("subnet", ""))
        self._fields["gateway"].set(p.get("gateway", ""))
        self._fields["dns"].set(p.get("dns", ""))
        dns2 = p.get("dns2", "")
        self._fields["dns2"].set(dns2 if dns2 else "—", dim=not dns2)

    def _set_status(self, text, color):
        self._status_cv.delete("all")
        self._status_cv.create_oval(4, 6, 14, 16, fill=color, outline="")
        self._status_cv.create_text(20, 11, text=text, anchor="w",
                                    fill=color, font=("Segoe UI", 9))

    def _on_apply(self):
        p = self.profiles[self.sel]
        dns2_line = f"\nDNS 2   {p['dns2']}" if p.get("dns2") else ""
        msg = (f"'{p['name']}' 설정을 적용할까요?\n\n"
               f"IP        {p['ip']}\n"
               f"서브넷  {p['subnet']}\n"
               f"GW       {p['gateway']}\n"
               f"DNS     {p['dns']}{dns2_line}")
        if not messagebox.askyesno("네트워크 전환", msg, icon="question"):
            return

        self._apply_btn.set_enabled(False)
        self._set_status("적용 중...", _ig_color(0.5))
        self.update()

        try:
            apply_profile(self.adapter, p)
            self._set_status(f"✓  {p['name']} 적용 완료", C["ok"])
            messagebox.showinfo("완료", f"'{p['name']}' 설정이 적용되었습니다.")
        except RuntimeError as e:
            self._set_status("✗  오류 발생", C["err"])
            messagebox.showerror("오류", str(e))
        finally:
            self._apply_btn.set_enabled(True)


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
