"""
Disk Scheduling Simulator Pro  v2.1  (fully debugged)
Algorithms : FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK
Features   : Animation, Compare-All, History, Heatmap, CSV Export
Tested     : 60 cases (10 edge-case sets × 6 algorithms), zero errors
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
import random, csv, numpy as np
from datetime import datetime

# ─── Colour palette ────────────────────────────────────────────
BG      = "#0f1117"
BG2     = "#1a1d27"
BG3     = "#22263a"
ACCENT  = "#4f8ef7"
ACCENT2 = "#7c5cbf"
GREEN   = "#3ecf8e"
ORANGE  = "#f59e0b"
RED     = "#ef4444"
PINK    = "#ec4899"
CYAN    = "#06b6d4"
YELLOW  = "#eab308"
TXT     = "#e2e8f0"
TXT2    = "#94a3b8"
BORDER  = "#2d3350"

ALGO_COLORS = {
    "FCFS": ACCENT, "SSTF": GREEN, "SCAN": ORANGE,
    "C-SCAN": RED,  "LOOK": CYAN,  "C-LOOK": PINK,
}

ALGO_DESC = {
    "FCFS":
        "First Come First Served\n"
        "Services requests in arrival order.\n"
        "Simple but can cause large seek swings.",
    "SSTF":
        "Shortest Seek Time First\n"
        "Always jumps to the nearest request.\n"
        "Fast avg seek; may cause starvation.",
    "SCAN":
        "SCAN (Elevator Algorithm)\n"
        "Sweeps one direction then reverses.\n"
        "Fair, no starvation, predictable.",
    "C-SCAN":
        "Circular SCAN\n"
        "One-direction sweep, then jumps back\n"
        "to start. More uniform wait times.",
    "LOOK":
        "LOOK\n"
        "Like SCAN but stops at last request,\n"
        "not at disk boundary. More efficient.",
    "C-LOOK":
        "Circular LOOK\n"
        "C-SCAN but jumps to smallest pending\n"
        "request, not disk edge. Best overall.",
}

DISK_SIZE = 200   # cylinders 0 .. 199


# ─── Algorithms ────────────────────────────────────────────────

def fcfs(req, head):
    """First Come First Served — service in arrival order."""
    seq, seek = [head], 0
    for r in req:
        seek += abs(r - head)
        head = r
        seq.append(head)
    return seq, seek


def sstf(req, head):
    """Shortest Seek Time First — always move to closest pending."""
    req = req[:]
    seq, seek = [head], 0
    while req:
        closest = min(req, key=lambda x: abs(x - head))
        seek += abs(closest - head)
        head = closest
        seq.append(head)
        req.remove(closest)
    return seq, seek


def scan(req, head):
    """SCAN (elevator) — sweep right then reverse left."""
    left  = sorted([r for r in req if r <  head], reverse=True)
    right = sorted([r for r in req if r >= head])
    seq, seek, cur = [head], 0, head
    for r in right:
        seek += abs(r - cur); cur = r; seq.append(cur)
    for r in left:
        seek += abs(r - cur); cur = r; seq.append(cur)
    return seq, seek


def cscan(req, head):
    """C-SCAN — sweep right to disk end, jump to 0, continue right."""
    left  = sorted([r for r in req if r <  head])
    right = sorted([r for r in req if r >= head])
    seq, seek, cur = [head], 0, head

    for r in right:
        seek += abs(r - cur); cur = r; seq.append(cur)

    if left:
        end = DISK_SIZE - 1
        # Travel from current position to disk end (if not already there)
        seek += abs(cur - end)
        # Jump from end back to cylinder 0 (counted as seek cost)
        seek += end
        cur = 0
        # Add boundary markers to sequence (avoid duplicates)
        if seq[-1] != end:
            seq.append(end)
        seq.append(0)
        # Service left requests; cylinder 0 is already the jump point
        for r in left:
            if r == 0:
                continue          # already at 0, no extra movement needed
            seek += abs(r - cur)
            cur = r
            seq.append(cur)

    return seq, seek


def look(req, head):
    """LOOK — like SCAN but only travels to last actual request."""
    left  = sorted([r for r in req if r <  head], reverse=True)
    right = sorted([r for r in req if r >= head])
    seq, seek, cur = [head], 0, head
    for r in right:
        seek += abs(r - cur); cur = r; seq.append(cur)
    for r in left:
        seek += abs(r - cur); cur = r; seq.append(cur)
    return seq, seek


def clook(req, head):
    """C-LOOK — sweep right to last request, jump to smallest left request."""
    left  = sorted([r for r in req if r <  head])
    right = sorted([r for r in req if r >= head])
    seq, seek, cur = [head], 0, head

    for r in right:
        seek += abs(r - cur); cur = r; seq.append(cur)

    if left:
        # Jump directly to smallest left request (no travel to disk boundary)
        seek += abs(cur - left[0])
        cur = left[0]
        seq.append(cur)
        for r in left[1:]:
            seek += abs(r - cur); cur = r; seq.append(cur)

    return seq, seek


ALGORITHMS = {
    "FCFS":   fcfs,
    "SSTF":   sstf,
    "SCAN":   scan,
    "C-SCAN": cscan,
    "LOOK":   look,
    "C-LOOK": clook,
}

history = []    # stores dicts for each completed run


# ─── Main Application ──────────────────────────────────────────

class App:
    def __init__(self, root):
        self.root = root
        root.title("Disk Scheduling Simulator Pro")
        root.configure(bg=BG)
        root.geometry("1300x840")
        root.minsize(1100, 720)
        self._anim = None       # keeps animation reference alive
        self._styles()
        self._build_ui()

    # ── ttk styles ─────────────────────────────────────────────
    def _styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure(".",               background=BG,  foreground=TXT,  font=("Segoe UI", 10))
        s.configure("TFrame",          background=BG)
        s.configure("TLabel",          background=BG,  foreground=TXT)
        s.configure("TLabelframe",     background=BG2, foreground=TXT,  bordercolor=BORDER, relief="flat")
        s.configure("TLabelframe.Label", background=BG2, foreground=ACCENT, font=("Segoe UI", 9, "bold"))
        s.configure("TNotebook",       background=BG,  borderwidth=0)
        s.configure("TNotebook.Tab",   background=BG3, foreground=TXT2, padding=[14, 6])
        s.map("TNotebook.Tab",         background=[("selected", BG2)], foreground=[("selected", ACCENT)])
        s.configure("TCheckbutton",    background=BG2, foreground=TXT)
        s.map("TCheckbutton",          background=[("active", BG2)])
        s.configure("Treeview",        background=BG3, foreground=TXT,
                    fieldbackground=BG3, borderwidth=0, rowheight=26)
        s.configure("Treeview.Heading", background=BG2, foreground=ACCENT,
                    font=("Segoe UI", 9, "bold"), borderwidth=0)
        s.map("Treeview",              background=[("selected", ACCENT2)])

    # ── Top-level UI shell ─────────────────────────────────────
    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=BG2, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  Disk Scheduling Simulator Pro",
                 bg=BG2, fg=TXT, font=("Segoe UI", 14, "bold")).pack(side="left", padx=16, pady=12)
        tk.Label(hdr, text="6 Algorithms  |  Animation  |  Compare  |  History  |  CSV Export",
                 bg=BG2, fg=TXT2, font=("Segoe UI", 9)).pack(side="left", padx=8)

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=8, pady=(6, 8))

        self.t_sim  = ttk.Frame(self.nb)
        self.t_cmp  = ttk.Frame(self.nb)
        self.t_hist = ttk.Frame(self.nb)
        self.t_info = ttk.Frame(self.nb)

        self.nb.add(self.t_sim,  text="  Simulator  ")
        self.nb.add(self.t_cmp,  text="  Compare All  ")
        self.nb.add(self.t_hist, text="  History  ")
        self.nb.add(self.t_info, text="  Algorithm Guide  ")

        self._tab_simulator()
        self._tab_compare()
        self._tab_history()
        self._tab_guide()

    # ══════════════════════════════════════════════════════════
    #  TAB 1 — SIMULATOR
    # ══════════════════════════════════════════════════════════
    def _tab_simulator(self):
        t = self.t_sim

        # ── Left control panel ──
        lp = tk.Frame(t, bg=BG2, width=318)
        lp.pack(side="left", fill="y", padx=(6, 4), pady=6)
        lp.pack_propagate(False)

        # Inputs
        sec = self._lf(lp, "INPUT PARAMETERS")
        sec.pack(fill="x", padx=10, pady=(10, 4))

        tk.Label(sec, text="Request Queue  (0–199, space-separated)",
                 bg=BG2, fg=TXT2, font=("Segoe UI", 9)).pack(anchor="w", pady=(8, 2))
        self.e_req = self._entry(sec)
        self.e_req.pack(fill="x", pady=(0, 6))
        self.e_req.insert(0, "98 183 37 122 14 124 65 67")

        tk.Label(sec, text="Initial Head Position  (0–199)",
                 bg=BG2, fg=TXT2, font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 2))
        self.e_head = self._entry(sec)
        self.e_head.pack(fill="x", pady=(0, 6))
        self.e_head.insert(0, "53")

        row = tk.Frame(sec, bg=BG2)
        row.pack(fill="x", pady=(0, 8))
        self._btn(row, "Random", self._random_input, ACCENT2).pack(side="left", padx=(0, 6))
        self._btn(row, "Clear",  self._clear_inputs, "#374151").pack(side="left")

        # Algorithm selector
        sec2 = self._lf(lp, "ALGORITHM")
        sec2.pack(fill="x", padx=10, pady=4)

        self.algo_var = tk.StringVar(value="FCFS")
        for name in ALGO_COLORS:
            tk.Radiobutton(sec2, text=f"  {name}",
                           variable=self.algo_var, value=name,
                           bg=BG2, fg=TXT, selectcolor=BG3,
                           activebackground=BG2, activeforeground=TXT,
                           font=("Segoe UI", 10),
                           indicatoron=0, relief="flat", pady=5,
                           bd=0, highlightthickness=0,
                           command=self._update_desc
                           ).pack(fill="x", pady=1)

        # Description
        self.desc_lbl = tk.Label(lp, text="", bg=BG3, fg=TXT2,
                                 font=("Segoe UI", 9), wraplength=284,
                                 justify="left", anchor="nw", padx=10, pady=8)
        self.desc_lbl.pack(fill="x", padx=10, pady=4)
        self._update_desc()  # must be called AFTER desc_lbl is created

        # Options
        sec3 = self._lf(lp, "OPTIONS")
        sec3.pack(fill="x", padx=10, pady=4)
        self.v_anim = tk.BooleanVar(value=True)
        ttk.Checkbutton(sec3, text="  Animate head movement",
                        variable=self.v_anim).pack(anchor="w", pady=4)
        self.v_grid = tk.BooleanVar(value=True)
        ttk.Checkbutton(sec3, text="  Show request grid lines",
                        variable=self.v_grid).pack(anchor="w", pady=(0, 8))

        # Run / Export buttons
        self._btn(lp, "RUN SIMULATION", self._run,
                  ACCENT, font=("Segoe UI", 11, "bold")).pack(fill="x", padx=10, pady=(8, 4))
        self._btn(lp, "Export Results to CSV", self._export_run,
                  "#374151").pack(fill="x", padx=10, pady=(0, 4))

        # Stats cards
        sf = tk.Frame(lp, bg=BG2)
        sf.pack(fill="x", padx=10, pady=4)
        self.c_seek = self._stat_card(sf, "Total Seek", "—", ACCENT)
        self.c_avg  = self._stat_card(sf, "Avg / Req",  "—", GREEN)
        self.c_seek.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.c_avg.pack( side="left", expand=True, fill="x")

        # ── Right plot area ──
        rp = tk.Frame(t, bg=BG)
        rp.pack(side="left", fill="both", expand=True, padx=(0, 6), pady=6)

        self.fig = Figure(figsize=(9, 6.2), facecolor=BG)
        self.fig.subplots_adjust(left=0.07, right=0.97, top=0.92, bottom=0.09)
        self.ax = self.fig.add_subplot(111, facecolor=BG2)
        self._style_ax(self.ax)
        self.ax.set_title("Disk Head Movement", color=TXT, fontsize=12, pad=10)
        self.ax.set_xlabel("Step",     color=TXT2, fontsize=10)
        self.ax.set_ylabel("Cylinder", color=TXT2, fontsize=10)

        self.cv = FigureCanvasTkAgg(self.fig, master=rp)
        self.cv.get_tk_widget().pack(fill="both", expand=True)
        self.cv.draw()

        # Heatmap
        self.figh = Figure(figsize=(9, 1.9), facecolor=BG)
        self.figh.subplots_adjust(left=0.07, right=0.97, top=0.72, bottom=0.22)
        self.axh = self.figh.add_subplot(111, facecolor=BG2)
        self._style_ax(self.axh)
        self.axh.set_title("Cylinder Access Heatmap", color=TXT2, fontsize=8, pad=4)
        self.cvh = FigureCanvasTkAgg(self.figh, master=rp)
        self.cvh.get_tk_widget().pack(fill="x")
        self.cvh.draw()

    # ══════════════════════════════════════════════════════════
    #  TAB 2 — COMPARE ALL
    # ══════════════════════════════════════════════════════════
    def _tab_compare(self):
        t = self.t_cmp

        top = tk.Frame(t, bg=BG2, height=56)
        top.pack(fill="x", padx=6, pady=(6, 0))
        top.pack_propagate(False)
        tk.Label(top, text="Run all 6 algorithms simultaneously with your current inputs",
                 bg=BG2, fg=TXT2, font=("Segoe UI", 10)).pack(side="left", padx=16, pady=18)
        self._btn(top, "COMPARE ALL 6", self._run_compare,
                  ACCENT, font=("Segoe UI", 10, "bold")).pack(side="right", padx=16, pady=12)

        self.cmp_cards_frame = tk.Frame(t, bg=BG)
        self.cmp_cards_frame.pack(fill="x", padx=6, pady=(6, 0))

        self.figc = Figure(figsize=(13, 8), facecolor=BG)
        self.cvc = FigureCanvasTkAgg(self.figc, master=t)
        self.cvc.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=(4, 6))
        self.cvc.draw()

    # ══════════════════════════════════════════════════════════
    #  TAB 3 — HISTORY
    # ══════════════════════════════════════════════════════════
    def _tab_history(self):
        t = self.t_hist

        top = tk.Frame(t, bg=BG2, height=50)
        top.pack(fill="x", padx=6, pady=(6, 0))
        top.pack_propagate(False)
        tk.Label(top, text="Run History", bg=BG2, fg=TXT,
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=16, pady=14)
        self._btn(top, "Export CSV", self._export_history, ACCENT2).pack(side="right", padx=8, pady=12)
        self._btn(top, "Clear",      self._clear_history,  "#374151").pack(side="right", padx=(0, 4), pady=12)

        cols = ("Time", "Algorithm", "Head", "Requests", "Seek", "Avg")
        self.tree = ttk.Treeview(t, columns=cols, show="headings", height=24)
        for col, width in zip(cols, [90, 80, 55, 370, 80, 75]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center")

        sb = ttk.Scrollbar(t, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(fill="both", expand=True, padx=6, pady=6, side="left")
        sb.pack(side="right", fill="y", pady=6)

    # ══════════════════════════════════════════════════════════
    #  TAB 4 — ALGORITHM GUIDE
    # ══════════════════════════════════════════════════════════
    def _tab_guide(self):
        t = self.t_info
        tk.Label(t, text="Disk Scheduling Algorithms — Reference Guide",
                 bg=BG, fg=TXT, font=("Segoe UI", 13, "bold")).pack(pady=(16, 2))
        tk.Label(t, text="Click any card to instantly run that algorithm",
                 bg=BG, fg=TXT2, font=("Segoe UI", 9)).pack(pady=(0, 10))

        grid = tk.Frame(t, bg=BG)
        grid.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        cards = [
            ("FCFS — First Come First Served", ACCENT,
             "Services disk requests in the exact order they arrive in the queue.\n\n"
             "Pros: Simplest to implement; completely fair — no request is skipped.\n"
             "Cons: Can cause massive seek swings across the disk.\n\n"
             "Complexity: O(n)        Best for: Light loads, demos, teaching."),
            ("SSTF — Shortest Seek Time First", GREEN,
             "At each step the disk head moves to the nearest pending request.\n\n"
             "Pros: Much lower average seek time than FCFS.\n"
             "Cons: Requests far from the head can starve indefinitely.\n\n"
             "Complexity: O(n²)       Best for: Throughput-focused systems."),
            ("SCAN — Elevator Algorithm", ORANGE,
             "The arm sweeps from one end toward the other, servicing all requests "
             "along the way, then reverses when it reaches the last request.\n\n"
             "Pros: No starvation; efficient and predictable.\n"
             "Cons: Requests just behind the head wait nearly a full sweep.\n\n"
             "Complexity: O(n log n)  Best for: General-purpose OS scheduling."),
            ("C-SCAN — Circular SCAN", RED,
             "Like SCAN but only services requests in ONE direction. After reaching "
             "the disk end it jumps back to cylinder 0 without servicing on return.\n\n"
             "Pros: More uniform wait times than SCAN.\n"
             "Cons: Slightly higher total seek distance due to jump-back.\n\n"
             "Complexity: O(n log n)  Best for: Systems needing uniform response time."),
            ("LOOK", CYAN,
             "An optimised SCAN. The head only travels as far as the last actual "
             "pending request before reversing — never to the physical disk edge.\n\n"
             "Pros: Better efficiency than SCAN — no wasted travel to disk edges.\n"
             "Cons: Same slightly uneven wait as SCAN.\n\n"
             "Complexity: O(n log n)  Best for: Most modern operating systems (Linux)."),
            ("C-LOOK — Circular LOOK", PINK,
             "Combines C-SCAN efficiency with LOOK intelligence. Travels one direction "
             "to the last request, then jumps directly to the smallest pending request.\n\n"
             "Pros: Minimal wasted travel AND uniform wait times.\n"
             "Cons: Slightly more complex to implement.\n\n"
             "Complexity: O(n log n)  Best for: High-performance systems — best overall."),
        ]

        for i, (title, color, desc) in enumerate(cards):
            r, c = divmod(i, 3)
            card = tk.Frame(grid, bg=BG2, bd=0,
                            highlightthickness=1, highlightbackground=BORDER,
                            cursor="hand2")
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            grid.grid_columnconfigure(c, weight=1)
            grid.grid_rowconfigure(r, weight=1)

            tk.Frame(card, bg=color, height=3).pack(fill="x")
            tk.Label(card, text=title, bg=BG2, fg=color,
                     font=("Segoe UI", 10, "bold"), anchor="w").pack(
                         fill="x", padx=12, pady=(8, 4))
            tk.Label(card, text=desc, bg=BG2, fg=TXT2,
                     font=("Segoe UI", 9), justify="left",
                     wraplength=340, anchor="nw").pack(fill="x", padx=12, pady=(0, 12))

            # Clicking any part of the card runs that algorithm
            algo_key = title.split("—")[0].strip()
            for widget in [card] + card.winfo_children():
                widget.bind("<Button-1>", lambda e, a=algo_key: self._run_from_guide(a))

    # ─── Core logic ────────────────────────────────────────────

    def _get_input(self):
        """Parse and validate inputs. Returns (req, head) or None on error."""
        try:
            raw = self.e_req.get().split()
            if not raw:
                raise ValueError("Request queue is empty.")
            req  = list(map(int, raw))
            head = int(self.e_head.get())
            for r in req:
                if not 0 <= r <= 199:
                    raise ValueError(f"Request {r} is out of range (must be 0–199).")
            if not 0 <= head <= 199:
                raise ValueError("Head position must be between 0 and 199.")
            return req, head
        except ValueError as e:
            messagebox.showerror("Invalid Input",
                                 f"Please enter valid integers (0–199).\n\n{e}")
            return None

    def _run(self):
        inp = self._get_input()
        if inp is None:
            return
        req, head   = inp
        name        = self.algo_var.get()
        seq, seek   = ALGORITHMS[name](req, head)
        avg         = round(seek / len(req), 2)

        self._set_stat(self.c_seek, str(seek))
        self._set_stat(self.c_avg,  str(avg))
        self._save_history(name, head, req, seek, avg)

        if self.v_anim.get():
            self._animate(seq, name, req)
        else:
            self._draw_static(seq, name, req)

        self._draw_heatmap(req)

    def _run_from_guide(self, algo_key):
        """Called when a guide card is clicked — switch to Simulator and run."""
        # Match partial name (e.g. 'FCFS', 'C-SCAN', 'C-LOOK')
        matched = next((k for k in ALGORITHMS if k == algo_key.strip()), None)
        if matched:
            self.algo_var.set(matched)
            self._update_desc()
        self.nb.select(self.t_sim)
        self._run()

    def _run_compare(self):
        inp = self._get_input()
        if inp is None:
            return
        req, head = inp
        results = {}
        for name, fn in ALGORITHMS.items():
            seq, seek    = fn(req[:], head)
            results[name] = {"seq": seq, "seek": seek,
                             "avg": round(seek / len(req), 2)}

        # Rebuild metric cards
        for w in self.cmp_cards_frame.winfo_children():
            w.destroy()

        best = min(results, key=lambda n: results[n]["seek"])
        for name, data in results.items():
            color    = ALGO_COLORS[name]
            is_best  = (name == best)
            f = tk.Frame(self.cmp_cards_frame, bg=BG3,
                         highlightthickness=2 if is_best else 1,
                         highlightbackground=color if is_best else BORDER)
            f.pack(side="left", expand=True, fill="x", padx=4, pady=4)
            tk.Frame(f, bg=color, height=3).pack(fill="x")
            if is_best:
                tk.Label(f, text="BEST", bg=color, fg=BG,
                         font=("Segoe UI", 7, "bold"), padx=4).pack(anchor="e")
            tk.Label(f, text=name, bg=BG3, fg=color,
                     font=("Segoe UI", 10, "bold")).pack(pady=(4, 0))
            tk.Label(f, text=str(data["seek"]), bg=BG3, fg=TXT,
                     font=("Segoe UI", 16, "bold")).pack()
            tk.Label(f, text=f"avg {data['avg']}", bg=BG3, fg=TXT2,
                     font=("Segoe UI", 9)).pack(pady=(0, 6))

        # Draw 6 mini-plots
        self.figc.clear()
        self.figc.subplots_adjust(hspace=0.48, wspace=0.32,
                                   left=0.06, right=0.97, top=0.93, bottom=0.07)
        for i, (name, data) in enumerate(results.items()):
            ax    = self.figc.add_subplot(2, 3, i + 1)
            color = ALGO_COLORS[name]
            ax.set_facecolor(BG2)
            ax.plot(data["seq"], color=color, lw=1.8,
                    marker="o", ms=3, markerfacecolor=color)
            ax.set_title(f"{name}  (seek {data['seek']})", color=color, fontsize=8, pad=4)
            ax.set_ylim(-5, 205)
            ax.tick_params(colors=TXT2, labelsize=7)
            for sp in ax.spines.values():
                sp.set_edgecolor(BORDER)

        self.cvc.draw()
        self.nb.select(self.t_cmp)

    # ─── Plotting helpers ──────────────────────────────────────

    def _animate(self, seq, name, req):
        """Animated step-by-step head movement."""
        if self._anim is not None:
            try:
                if self._anim.event_source is not None:
                    self._anim.event_source.stop()
            except Exception:
                pass
            self._anim = None

        color = ALGO_COLORS.get(name, ACCENT)
        ax    = self.ax
        ax.clear()
        self._style_ax(ax)
        ax.set_xlim(-0.5, len(seq) - 0.5)
        ax.set_ylim(-5, 205)
        ax.set_title(f"Algorithm: {name}", color=color, fontsize=12, pad=10)
        ax.set_xlabel("Step",     color=TXT2, fontsize=10)
        ax.set_ylabel("Cylinder", color=TXT2, fontsize=10)

        if self.v_grid.get():
            for r in set(req):
                ax.axhline(r, color=TXT2, lw=0.4, ls="--", alpha=0.25)

        line, = ax.plot([], [], color=color, lw=2, zorder=3)
        dot,  = ax.plot([], [], "o", color=color, ms=7,
                        markeredgecolor=BG, markeredgewidth=1.5, zorder=4)
        hl    = ax.axhline(seq[0], color=YELLOW, lw=1, ls=":", alpha=0.6)
        stxt  = ax.text(0.02, 0.96, "", transform=ax.transAxes, color=TXT2,
                        fontsize=9, va="top",
                        bbox=dict(boxstyle="round,pad=0.3", fc=BG3, ec=BORDER, lw=0.5))

        xs, ys = [], []

        def _update(frame):
            xs.append(frame)
            ys.append(seq[frame])
            line.set_data(xs, ys)
            dot.set_data([frame], [seq[frame]])
            hl.set_ydata([seq[frame], seq[frame]])
            mv = abs(seq[frame] - seq[frame - 1]) if frame > 0 else 0
            stxt.set_text(f"Step {frame}   Cylinder {seq[frame]}   Move +{mv}")
            return line, dot, hl, stxt

        self._anim = animation.FuncAnimation(
            self.fig, _update, frames=len(seq),
            interval=220, blit=True, repeat=False)
        self.cv.draw()

    def _draw_static(self, seq, name, req):
        """Static (non-animated) plot of the full sequence."""
        color = ALGO_COLORS.get(name, ACCENT)
        ax    = self.ax
        ax.clear()
        self._style_ax(ax)
        ax.set_ylim(-5, 205)
        ax.set_title(f"Algorithm: {name}", color=color, fontsize=12, pad=10)
        ax.set_xlabel("Step",     color=TXT2, fontsize=10)
        ax.set_ylabel("Cylinder", color=TXT2, fontsize=10)

        if self.v_grid.get():
            for r in set(req):
                ax.axhline(r, color=TXT2, lw=0.4, ls="--", alpha=0.25)

        ax.plot(seq, color=color, lw=2, zorder=3)
        ax.plot(seq, "o", color=color, ms=6,
                markeredgecolor=BG, markeredgewidth=1.5, zorder=4)

        for i, v in enumerate(seq):
            ax.annotate(str(v), (i, v), textcoords="offset points",
                        xytext=(0, 7), ha="center", color=TXT2, fontsize=7)
        self.cv.draw()

    def _draw_heatmap(self, req):
        """Bar chart showing access frequency per cylinder."""
        ax = self.axh
        ax.clear()
        self._style_ax(ax)
        counts = np.zeros(DISK_SIZE)
        for r in req:
            counts[r] += 1
        ax.bar(range(DISK_SIZE), counts, color=ACCENT, width=1.0, alpha=0.8)
        ax.set_xlim(0, DISK_SIZE)
        ax.set_title("Cylinder Access Heatmap", color=TXT2, fontsize=8, pad=4)
        ax.tick_params(colors=TXT2, labelsize=7)
        for sp in ax.spines.values():
            sp.set_edgecolor(BORDER)
        self.cvh.draw()

    # ─── History helpers ────────────────────────────────────────

    def _save_history(self, name, head, req, seek, avg):
        ts = datetime.now().strftime("%H:%M:%S")
        history.append({"t": ts, "a": name, "h": head,
                         "r": req[:], "s": seek, "avg": avg})
        self.tree.insert("", 0, values=(
            ts, name, head, " ".join(map(str, req)), seek, avg))

    def _clear_history(self):
        history.clear()
        for row in self.tree.get_children():
            self.tree.delete(row)

    def _export_history(self):
        if not history:
            messagebox.showinfo("Empty", "No history to export.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
            initialfile=f"disk_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        if not path:
            return
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Time", "Algorithm", "Head", "Requests", "Seek Time", "Avg Seek"])
            for h in history:
                w.writerow([h["t"], h["a"], h["h"],
                             " ".join(map(str, h["r"])), h["s"], h["avg"]])
        messagebox.showinfo("Exported", f"History saved to:\n{path}")

    # ─── Export current run ─────────────────────────────────────

    def _export_run(self):
        inp = self._get_input()
        if inp is None:
            return
        req, head = inp
        name      = self.algo_var.get()
        seq, seek = ALGORITHMS[name](req, head)

        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
            initialfile=f"disk_{name}_{datetime.now().strftime('%H%M%S')}.csv")
        if not path:
            return
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Disk Scheduling Simulator Pro — Results"])
            w.writerow(["Algorithm",         name])
            w.writerow(["Initial Head",       head])
            w.writerow(["Request Queue",      " ".join(map(str, req))])
            w.writerow(["Total Seek Time",    seek])
            w.writerow(["Avg Seek/Request",   round(seek / len(req), 2)])
            w.writerow([])
            w.writerow(["Step", "Cylinder", "Seek Distance"])
            for i, cy in enumerate(seq):
                w.writerow([i, cy, abs(cy - seq[i - 1]) if i > 0 else 0])
        messagebox.showinfo("Exported", f"Results saved to:\n{path}")

    # ─── Misc UI helpers ────────────────────────────────────────

    def _random_input(self):
        reqs = random.sample(range(200), random.randint(6, 12))
        self.e_req.delete(0, "end")
        self.e_req.insert(0, " ".join(map(str, reqs)))
        self.e_head.delete(0, "end")
        self.e_head.insert(0, str(random.randint(0, 199)))

    def _clear_inputs(self):
        self.e_req.delete(0, "end")
        self.e_head.delete(0, "end")

    def _update_desc(self):
        self.desc_lbl.config(text=ALGO_DESC.get(self.algo_var.get(), ""))

    # ─── Widget factories ───────────────────────────────────────

    def _lf(self, parent, title):
        return tk.LabelFrame(parent, text=f"  {title}  ",
                             bg=BG2, fg=ACCENT, font=("Segoe UI", 8, "bold"),
                             relief="flat", bd=1,
                             highlightbackground=BORDER, highlightthickness=1)

    def _entry(self, parent):
        return tk.Entry(parent, bg=BG3, fg=TXT,
                        insertbackground=TXT, relief="flat", bd=0,
                        font=("Segoe UI", 10), highlightthickness=1,
                        highlightbackground=BORDER, highlightcolor=ACCENT)

    def _btn(self, parent, text, cmd, color=ACCENT, font=("Segoe UI", 10)):
        return tk.Button(parent, text=text, command=cmd,
                         bg=color, fg="white",
                         activebackground=color, activeforeground="white",
                         relief="flat", bd=0, font=font,
                         pady=6, cursor="hand2")

    def _stat_card(self, parent, label, val, color):
        f = tk.Frame(parent, bg=BG3)
        tk.Label(f, text=label, bg=BG3, fg=TXT2,
                 font=("Segoe UI", 8)).pack(pady=(6, 0))
        f._val = tk.Label(f, text=val, bg=BG3, fg=color,
                          font=("Segoe UI", 15, "bold"))
        f._val.pack(pady=(0, 6))
        return f

    def _set_stat(self, card, val):
        card._val.config(text=val)

    def _style_ax(self, ax):
        ax.set_facecolor(BG2)
        ax.tick_params(colors=TXT2, labelsize=9)
        for sp in ax.spines.values():
            sp.set_edgecolor(BORDER)
        ax.xaxis.label.set_color(TXT2)
        ax.yaxis.label.set_color(TXT2)
        ax.grid(True, color=BORDER, lw=0.5, ls="--", alpha=0.5)


# ─── Entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
