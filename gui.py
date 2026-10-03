#!/usr/bin/env python3
"""photoscrub — UI/UX.

Zasady, które tu obowiązują:
  * jeden ekran, zero kreatorów, zero okienek w trakcie pracy
  * stan pusty mówi CO ZROBIĆ, nie jest pustym prostokątem
  * liczby przed działaniem: ile plików, ile wycieków, ile bajtów
  * „Usuń" pyta tylko wtedy, gdy ktoś wybrałby złą lokalizację
  * wynik jest natychmiastowy i weryfikowalny (pokazujemy co zostało)
"""
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog

from PIL import Image, ImageTk

import license as lic
import model as mdl
import photoscrub as ps
import ruleset as rs

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except Exception:
    DND_FILES = None
    TkinterDnD = None
    HAS_DND = False

# ── paleta ────────────────────────────────────────────────────────────────────
BG = '#0b0e14'
DROP = '#111725'
PANEL = '#141b28'
PANEL_2 = '#1c2534'
LINE = '#243044'
FG = '#f2f5fa'
FG_2 = '#c7d0de'
DIM = '#7b8798'
FAINT = '#4a5568'
ACC = '#3d5bff'
ACC_HI = '#5a76ff'
RED = '#ff5c62'
AMB = '#ffb224'
GRN = '#2fd07f'
SHADOW = '#05070b'

F = 'Inter'
FM = ('Inter', 10)
FMB = ('Inter', 10, 'bold')
SM = ('Inter', 9)
SMB = ('Inter', 9, 'bold')
H1 = ('Inter', 26, 'bold')
H2 = ('Inter', 13, 'bold')
H3 = ('Inter', 11, 'bold')
MONO = ('Inter', 10)


def human(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return f'{n:.0f} {unit}' if unit == 'B' else f'{n:.1f} {unit}'
        n /= 1024.0


class DropZone(tk.Canvas):
    """Strefa upuszczania. Rysowana, nie obrazek wiec skaluje sie z oknem
    i wyglada tak samo na kazdym monitorze."""

    def __init__(self, master, on_click):
        super().__init__(master, bg=BG, highlightthickness=0, height=120)
        self.on_click = on_click
        self.hover = False
        self.text = 'Upuść zdjęcia lub filmy'
        self.sub = 'albo kliknij tutaj, żeby wybrać pliki'
        self.bind('<Button-1>', lambda e: self.on_click())
        for ev in ('<Enter>', '<Motion>'):
            self.bind(ev, self._in)
        self.bind('<Leave>', self._out)
        self.bind('<Configure>', lambda e: self._draw())

    def _in(self, _e=None):
        self.hover = True
        self._draw()

    def _out(self, _e=None):
        self.hover = False
        self._draw()

    def set_empty(self, empty=True):
        self.empty = empty
        self._draw()

    def _draw(self):
        self.delete('all')
        w, h = self.winfo_width() or 900, self.winfo_height() or 120
        if w < 10:
            return
        pad = 18
        r = 14
        col = ACC if self.hover else LINE
        pts = [pad + r, pad, w - pad - r, pad, w - pad, pad, w - pad, pad + r,
               w - pad, h - pad - r, w - pad, h - pad, w - pad - r, h - pad,
               pad + r, h - pad, pad, h - pad, pad, h - pad - r,
               pad, pad + r, pad, pad]
        self.create_polygon(pts, smooth=True, fill=DROP if self.hover else BG,
                            outline=col, width=2 if self.hover else 1,
                            dash=(10, 8) if not self.hover else None)
        # ikona: stos zdjec
        cx, cy = w // 2, h // 2 - 12
        for i, off in enumerate((-14, -7, 0)):
            x = cx + off * 0.6 + (i * 10)
            y = cy + (i * 5)
            self.create_rectangle(x - 13, y - 10, x + 13, y + 10,
                                 outline=ACC if self.hover else FAINT,
                                 fill=DROP if self.hover else BG, width=2)
            self.create_polygon(x - 13, y + 2, x - 5, y - 5, x + 1, y + 3,
                                x + 6, y - 2, x + 13, y + 4,
                                outline='', fill=ACC if self.hover else FAINT)
        self.create_text(cx, h - 34, text=self.text, fill=FG if self.hover else FG_2,
                         font=H3)
        self.create_text(cx, h - 16, text=self.sub, fill=DIM, font=SM)


class Toast:
    """Zamiast okienka systemowego. Nie przerywa pracy, nie zaslania ekranu."""

    def __init__(self, master):
        self.master = master
        self.frame = None
        self.timer = None

    def show(self, title, body='', kind='info', ms=4200):
        self.kill()
        col = {'info': ACC, 'ok': GRN, 'warn': AMB, 'err': RED}[kind]
        self.frame = tk.Frame(self.master, bg=PANEL_2)
        inner = self.frame
        bar = tk.Frame(inner, bg=col, width=3)
        bar.pack(side='left', fill='y')
        box = tk.Frame(inner, bg=PANEL_2)
        box.pack(side='left', fill='both', expand=True, padx=12, pady=10)
        tk.Label(box, text=title, bg=PANEL_2, fg=FG, font=FMB,
                 anchor='w').pack(anchor='w')
        if body:
            tk.Label(box, text=body, bg=PANEL_2, fg=DIM, font=SM, anchor='w',
                     justify='left', wraplength=620).pack(anchor='w', pady=(3, 0))
        close = tk.Label(inner, text='✕', bg=PANEL_2, fg=DIM, font=SM, cursor='hand2')
        close.pack(side='right', padx=10)
        close.bind('<Button-1>', lambda e: self.kill())
        self.frame.pack(side='bottom', fill='x', padx=18, pady=(0, 6))
        self.timer = self.master.after(ms, self.kill)

    def kill(self):
        if self.timer:
            try:
                self.master.after_cancel(self.timer)
            except Exception:
                pass
            self.timer = None
        if self.frame:
            self.frame.destroy()
            self.frame = None


class Card(tk.Frame):
    def __init__(self, master, rep, thumb, label, risk, on_click, on_hover):
        super().__init__(master, bg=BG)
        self.rep = rep
        self.on_hover = on_hover
        if not rep.findings:
            col = GRN
        elif any(f.risk == 'HIGH' for f in rep.findings):
            col = RED
        else:
            col = AMB
        self.col = col
        self.box = tk.Frame(self, bg=PANEL, highlightthickness=1,
                            highlightbackground=PANEL_2, cursor='hand2')
        self.box.pack()
        bar = tk.Frame(self.box, bg=col, height=3)
        bar.pack(fill='x')
        inner = tk.Frame(self.box, bg=PANEL)
        inner.pack()
        self.img = tk.Label(inner, image=thumb, bg=PANEL, bd=0)
        self.img.pack(padx=7, pady=(7, 3))
        name = os.path.basename(rep.path)
        if len(name) > 26:
            stem, ext = os.path.splitext(name)
            name = stem[:16] + '…' + ext[-5:]
        tk.Label(inner, text=name, bg=PANEL, fg=FG, font=SM, width=26,
                 anchor='w').pack(padx=9, pady=(1, 1))
        foot = tk.Frame(inner, bg=PANEL)
        foot.pack(fill='x', padx=9, pady=(0, 8))
        tk.Label(foot, text=label, bg=PANEL, fg=col, font=SMB,
                 anchor='w').pack(side='left')
        if risk is not None:
            tk.Label(foot, text=str(risk), bg=PANEL, fg=col, font=SMB,
                     anchor='e').pack(side='right')
        self.parts = (self, self.box, inner, self.img, bar, foot)
        for w in self.parts:
            w.bind('<Button-1>', lambda e: self.on_click(rep))
            w.bind('<Enter>', self._enter)
            w.bind('<Leave>', self._leave)

    def _enter(self, _e=None):
        self.box.configure(highlightthickness=2, highlightbackground=self.col)
        self.on_hover(self.rep)

    def _leave(self, _e=None):
        self.box.configure(highlightthickness=1, highlightbackground=PANEL_2)


class App((TkinterDnD.Tk if HAS_DND else tk.Tk)):
    PAD = 22

    def __init__(self):
        super().__init__()
        self.title('photoscrub')
        self.configure(bg=BG)
        self.geometry('1120x780')
        self.minsize(940, 620)
        self.rows = []
        self.selected = None
        self._build()
        self._wire_dnd()
        self._keys()
        self.toast = Toast(self)
        self.after(120, self._gate)

    # ── licencja ──────────────────────────────────────────────────────────────
    def _license(self):
        try:
            st, info, payload = lic.state()
        except Exception:
            return None, None, 1
        return st, info, (lic.purchased_ruleset(payload) if payload else 1)

    def _gate(self):
        st, info, rv = self._license()
        self.ruleset = rv
        if st in ('ok', 'grace'):
            ups = rs.upgrades_available(rv)
            if st == 'grace':
                self.status.configure(text=f'poza okresem grace: {info}', fg=AMB)
            elif ups:
                self._upgrade_bar(ups[0])
            else:
                self.status.configure(text=f'licencja aktywna · reguły v{rv}', fg=GRN)
            return
        self._activate_dialog(st, info)

    def _upgrade_bar(self, u):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill='x', padx=self.PAD, pady=(6, 0))
        card = tk.Frame(bar, bg=PANEL)
        card.pack(fill='x')
        tk.Frame(card, bg=AMB, width=3).pack(side='left', fill='y')
        box = tk.Frame(card, bg=PANEL)
        box.pack(side='left', fill='x', expand=True, padx=12, pady=9)
        tk.Label(box, text=f'Dostępne są nowsze reguły — v{u["version"]} ({u["name"]})',
                 bg=PANEL, fg=AMB, font=SMB, anchor='w').pack(anchor='w')
        tk.Label(box, text=' · '.join(f'{w}' for w, _ in u['new']), bg=PANEL, fg=DIM,
                 font=SM, anchor='w').pack(anchor='w', pady=(3, 0))
        tk.Button(box, text='Szczegóły', command=lambda: self._upgrade_details(u),
                  bg=PANEL_2, activebackground=LINE, fg=FG_2, bd=0, relief='flat',
                  padx=10, pady=4, font=SM, cursor='hand2').pack(anchor='w', pady=(7, 0))

    def _upgrade_details(self, u):
        self.toast.show(f'Reguły v{u["version"]} ({u["name"]})', u['promise'], 'warn', 9000)

    def _activate_dialog(self, st, info):
        win = tk.Toplevel(self)
        win.configure(bg=BG)
        win.title('photoscrub — aktywacja')
        win.geometry('520x420')
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        box = tk.Frame(win, bg=BG)
        box.pack(fill='both', expand=True, padx=34, pady=30)
        tk.Label(box, text='🔑', bg=BG, fg=AMB, font=('Inter', 26)).pack(anchor='w')
        tk.Label(box, text='Klucz aktywacyjny', bg=BG, fg=FG, font=H1).pack(anchor='w', pady=(6, 4))
        tk.Label(box, text=info if st != 'brak' else 'Wklej klucz, który dostałeś mailem.',
                 bg=BG, fg=RED if st == 'bledny' else DIM, font=FM, wraplength=440,
                 justify='left').pack(anchor='w', pady=(0, 12))
        entry = tk.Text(box, height=7, bg=PANEL, fg=FG, bd=0, relief='flat',
                        font=MONO, wrap='char', padx=12, pady=10,
                        highlightthickness=1, highlightbackground=LINE)
        entry.pack(fill='x')
        out = tk.Label(box, text='', bg=BG, fg=RED, font=SM, wraplength=440, justify='left')

        def go():
            ok, msg = lic.activate(entry.get('1.0', 'end').strip())
            if ok:
                self.after(200, self._gate)
                win.destroy()
            else:
                out.configure(text=str(msg))

        def paste():
            try:
                entry.insert('1.0', self.clipboard_get())
            except tk.TclError:
                pass

        tk.Button(box, text='Wklej ze schowka', command=paste, bg=PANEL, fg=FG_2,
                  bd=0, relief='flat', padx=12, pady=7, font=SM,
                  cursor='hand2').pack(anchor='w', pady=(10, 0))
        tk.Button(box, text='Aktywuj', command=go, bg=ACC, activebackground=ACC_HI,
                  fg='#fff', bd=0, relief='flat', padx=26, pady=10, font=FMB,
                  cursor='hand2').pack(anchor='w', pady=(12, 0))
        out.pack(anchor='w', pady=(10, 0))
        tk.Label(box, text=f'twoja maszyna: {lic.machine_id()[:16]}', bg=BG, fg=FAINT,
                 font=('Inter', 8)).pack(anchor='w', pady=(12, 0))

    # ── layout ────────────────────────────────────────────────────────────────
    def _build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill='x', padx=self.PAD, pady=(18, 0))
        mark = tk.Canvas(top, width=26, height=26, bg=BG, highlightthickness=0)
        mark.create_oval(3, 3, 23, 23, outline=ACC, width=2)
        mark.create_oval(9, 9, 17, 17, fill=ACC)
        mark.pack(side='left')
        name = tk.Frame(top, bg=BG)
        name.pack(side='left', padx=(10, 0))
        tk.Label(name, text='photoscrub', bg=BG, fg=FG, font=FMB).pack(anchor='w')
        tk.Label(name, text='zanim wrzucisz to do sieci', bg=BG, fg=FAINT,
                 font=SM).pack(anchor='w')

        self.btn_folder = self._btn(top, 'Wybierz folder', self.add_folder)
        self.btn_folder.pack(side='right')
        self.btn_files = self._btn(top, 'Dodaj pliki', self.add_files)
        self.btn_files.pack(side='right', padx=8)

        self.verdict = tk.Label(self, text='', bg=BG, fg=FG, font=H1, anchor='w',
                                justify='left')
        self.verdict.pack(anchor='w', padx=self.PAD, pady=(22, 2))
        self.sub = tk.Label(self, text='Upuść pliki w okno albo dodaj je przyciskiem. '
                                       'Nic nie wychodzi z tego komputera.',
                            bg=BG, fg=DIM, font=FM, anchor='w')
        self.sub.pack(anchor='w', padx=self.PAD)

        self.stats = tk.Frame(self, bg=BG)
        self.stats.pack(fill='x', padx=self.PAD, pady=(14, 0))
        self.stat_tiles = {}
        for i, (key, col) in enumerate((('files', DIM), ('dirty', RED),
                                        ('high', RED), ('clean', GRN), ('risk', AMB))):
            t = tk.Frame(self.stats, bg=BG)
            t.pack(side='left', padx=(0, 26))
            v = tk.Label(t, text='0', bg=BG, fg=col, font=('Inter', 17, 'bold'))
            v.pack(anchor='w')
            l = tk.Label(t, text=key, bg=BG, fg=FAINT, font=SM)
            l.pack(anchor='w')
            self.stat_tiles[key] = (v, l)

        self.bar_bg = tk.Frame(self, bg=PANEL_2, height=3)
        self.bar_bg.pack(fill='x', padx=self.PAD, pady=(14, 0))
        self.bar = tk.Frame(self.bar_bg, bg=ACC, height=3, width=0)
        self.bar.place(x=0, y=0, relheight=1, width=0)

        body = tk.Frame(self, bg=BG)
        body.pack(fill='both', expand=True, padx=self.PAD, pady=(12, 0))
        left = tk.Frame(body, bg=BG)
        self.drop = DropZone(left, self.add_files)
        self.drop.pack(fill='x')
        gridwrap = tk.Frame(left, bg=BG)
        gridwrap.pack(fill='both', expand=True, pady=(10, 0))
        self.grid_ = tk.Frame(gridwrap, bg=BG)
        self.grid_.pack(fill='both', expand=True)
        for w in (self, left, gridwrap):
            w.bind('<MouseWheel>', self._wheel)
            w.bind('<Button-4>', lambda e: self._wheel_dir(-1))
            w.bind('<Button-5>', lambda e: self._wheel_dir(1))

        # Kolejnosc ma znaczenie: pack przydziela miejsce w kolejnosci wywolac.
        # Panel szczegolow musi dostac swoja szerokosc ZANIM karty rozrosna
        # na wszystko - inaczej dostaje 58 px i tekst zwija sie do jednej litery.
        right = tk.Frame(body, bg=PANEL, width=340)
        right.pack_propagate(False)
        right.pack(side='right', fill='y', padx=(14, 0))
        self._build_panel(right)
        left.pack(side='left', fill='both', expand=True)

        bot = tk.Frame(self, bg=BG)
        bot.pack(fill='x', padx=self.PAD, pady=(12, 18))
        self.btn = tk.Button(bot, text='Usuń metadane ze wszystkich', command=self.clean,
                             bg=ACC, activebackground=ACC_HI, fg='#fff', bd=0,
                             relief='flat', padx=24, pady=12, font=('Inter', 11, 'bold'),
                             cursor='hand2', state='disabled')
        self.btn.pack(side='left')
        self.btn.configure(state='disabled')
        self.status = tk.Label(bot, text='', bg=BG, fg=DIM, font=SM)
        self.status.pack(side='left', padx=16)

    # ── przewijanie karty ──────────────────────────────────────────────────────
    def _wheel(self, event):
        self.grid_.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    def _wheel_dir(self, d):
        self.grid_.yview_scroll(d, 'units')

    def _scroll(self, *a):
        self.grid_.yview(*a)

    def _btn(self, parent, text, cmd):
        b = tk.Button(parent, text=text, command=cmd, bg=PANEL, activebackground=PANEL_2,
                      fg=FG_2, bd=0, relief='flat', padx=14, pady=8, font=FM,
                      cursor='hand2')
        return b

    def _build_panel(self, right):
        head = tk.Frame(right, bg=PANEL)
        head.pack(fill='x', padx=14, pady=(12, 8))
        tk.Label(head, text='SZCZEGÓŁY', bg=PANEL, fg=FAINT, font=SMB).pack(anchor='w')
        self.detail_name = tk.Label(head, text='—', bg=PANEL, fg=FG, font=FMB,
                                    anchor='w', wraplength=280, justify='left')
        self.detail_name.pack(anchor='w', pady=(4, 0))
        self.detail = tk.Text(right, width=32, bg=PANEL, fg=FG_2, bd=0, relief='flat',
                               font=MONO, wrap='word', padx=14, pady=8,
                               highlightthickness=0, insertbackground=FG, cursor='arrow')
        self.detail.pack(fill='both', expand=True, padx=14, pady=(0, 10))
        self.detail.tag_configure('risk', foreground=AMB)
        self.detail.tag_configure('high', foreground=RED)
        self.detail.tag_configure('low', foreground=DIM)
        self.detail.insert('1.0', 'Kliknij kartę zdjęcia, żeby zobaczyć,\n'
                                 'co dokładnie ujawnia i dlaczego to problem.')

        tk.Frame(right, bg=LINE, height=1).pack(fill='x', padx=14)
        foot = tk.Frame(right, bg=PANEL)
        foot.pack(fill='x', padx=14, pady=(10, 12))
        tk.Label(foot, text='JAK TO DZIAŁA', bg=PANEL, fg=FAINT, font=SMB).pack(anchor='w')
        for txt in ('Pasywne DNS i bajty pliku. Zero skanowania, zero sieci.',
                    'Oryginały nigdy nie są modyfikowane — zapisujemy kopie.',
                    'Najbardziej podstępny wyciek: miniaturka wbudowana w JPEG '
                    'to często całe oryginalne zdjęcie.'):
            tk.Label(foot, text=f'·  {txt}', bg=PANEL, fg=DIM, font=SM, anchor='w',
                     justify='left', wraplength=280).pack(anchor='w', pady=(5, 0))

    def _keys(self):
        self.bind('<Control-o>', lambda e: self.add_files())
        self.bind('<Control-d>', lambda e: self.add_folder())
        self.bind('<Control-r>', lambda e: self._retry())
        self.bind('<Escape>', lambda e: self._clear())

    def _retry(self):
        if self.rows:
            self._scan([r.path for r, _, _ in self.rows])

    def _clear(self):
        self.rows = []
        self._render([])

    # ── drag & drop ───────────────────────────────────────────────────────────
    def _wire_dnd(self):
        if not HAS_DND:
            return
        targets = [self, self.grid_, self.drop, self.verdict, self.detail]
        for w in targets:
            try:
                w.drop_target_register(DND_FILES)
                w.dnd_bind('<<Drop>>', self._on_drop)
            except tk.TclError:
                pass

    def _on_drop(self, _event=None):
        self.drop.set_empty(False)
        try:
            data = self.tk.splitlist(self.dnd_get('DND_DATA'))
        except Exception:
            data = []
        self._scan([p for p in data if os.path.exists(p)])

    # ── wejście ───────────────────────────────────────────────────────────────
    def add_files(self):
        fs = filedialog.askopenfilenames(
            title='Wybierz zdjęcia i filmy',
            filetypes=[('Zdjęcia i filmy', '*.jpg *.jpeg *.png *.tif *.tiff *.webp '
                                           '*.heic *.heif *.avif *.gif *.bmp *.mp4 '
                                           '*.mov *.m4v'), ('Wszystko', '*.*')])
        if fs:
            self._scan(list(fs))

    def add_folder(self):
        d = filedialog.askdirectory(title='Wybierz folder ze zdjęciami')
        if d:
            self._scan([d])

    def _expand(self, paths):
        allowed = ps.IMG_EXT | ps.VIDEO_EXT | {'.zip'}
        out = []
        for p in paths:
            if os.path.isdir(p):
                for dp, _, fs in os.walk(p):
                    for f in fs:
                        full = os.path.join(dp, f)
                        ext = os.path.splitext(f)[1].lower()
                        if ext in allowed or ext == '':
                            out.append(full)
            else:
                out.append(p)
        seen, uniq = set(), []
        for p in out:
            if p not in seen:
                seen.add(p)
                uniq.append(p)
        return uniq

    def _scan(self, paths):
        files = self._expand(paths)
        if not files:
            return
        self.status.configure(text=f'Sprawdzam {len(files)} plików…', fg=DIM)
        self.drop.set_empty(False)
        threading.Thread(target=self._work, args=(files,), daemon=True).start()

    def _work(self, files):
        rv = getattr(self, 'ruleset', rs.CURRENT)
        reps = ps.scan_many(files, rv, workers=8, progress=self._progress)
        self.after(0, self._thumbs, reps)

    def _progress(self, done, total):
        def upd():
            self.status.configure(text=f'Sprawdzam… {done}/{total}', fg=DIM)
            w = self.bar_bg.winfo_width()
            if w > 0:
                self.bar.configure(width=max(1, int(w * done / max(1, total))))
        self.after(0, upd)

    def _thumbs(self, reps):
        thumbs = [self._thumb(r.path) for r in reps]
        self.after(0, self._fill, reps, thumbs)

    def _thumb(self, path, box=(190, 118)):
        try:
            im = Image.open(path)
            im.draft('RGB', (box[0] * 2, box[1] * 2))
            im = im.convert('RGB')
            im.thumbnail(box)
            bgim = Image.new('RGB', box, PANEL_2)
            bgim.paste(im, ((box[0] - im.width) // 2, (box[1] - im.height) // 2))
            return ImageTk.PhotoImage(bgim)
        except Exception:
            return ImageTk.PhotoImage(Image.new('RGB', box, PANEL_2))

    # ── render ────────────────────────────────────────────────────────────────
    def _fill(self, reps, thumbs):
        for r, t in zip(reps, thumbs):
            self.rows.append((r, t, mdl.score(r)))
        self._render(self.rows)

    def _render(self, rows):
        self.bar.configure(width=0)
        for c in list(self.grid_.winfo_children()):
            c.destroy()
        dirty = [x for x in rows if x[0].findings]
        high = [x for x in rows if any(f.risk == 'HIGH' for f in x[0].findings)]
        clean = len(rows) - len(dirty)
        risks = [s['risk'] for _, _, s in rows if s]

        if not rows:
            self.verdict.configure(text='Upuść pliki, żeby zobaczyć co ujawniają', fg=FG)
            self.sub.configure(text='Paswywnie. Zero sieci, zero konta. '
                                    'Oryginały zostają tam, gdzie są.')
            self.drop.pack(fill='x')
            self._set_stats(0, 0, 0, 0, 0)
            self.status.configure(text='', fg=DIM)
            return

        self.drop.pack_forget()
        top = max(risks) if risks else 0
        if dirty:
            self.verdict.configure(
                text=f'{len(dirty)} plików ujawnia dane', fg=FG)
            msg = (f'Najgorszy przypadek: {top}/100 ryzyka publikacji.'
                   if top else '')
        else:
            self.verdict.configure(text='Te pliki są czyste', fg=GRN)
            msg = 'Nic do usuwania.'
        self.sub.configure(
            text=f'{msg}  Reguły v{getattr(self, "ruleset", rs.CURRENT)} · '
                 f'zero skanowania, zero sieci · Ctrl+R skanuje ponownie')
        self._set_stats(len(rows), len(dirty), len(high), clean, top)
        if dirty:
            self.btn.configure(state='normal')
        else:
            self.btn.configure(state='disabled')

        # liczba kolumn z REALNEJ szerokosci obszaru kart, nie z wyliczanki:
        # panel szczegolow i marginesy zmieniaja ile naprawde zostaje miejsca
        self.grid_.update_idletasks()
        avail = self.grid_.winfo_width() or 700
        cols = max(2, min(6, (avail - 12) // 246))
        for i, (r, t, s) in enumerate(rows):
            label, risk = self._badge(s, r)
            Card(self.grid_, r, t, label, risk, self.show_detail,
                 self._hover).grid(row=i // cols, column=i % cols, padx=6, pady=6,
                                   sticky='n')
        if self.selected is None and rows:
            self.show_detail(rows[0][0])

    def _set_stats(self, files, dirty, high, clean, risk):
        for key, val in (('files', files), ('dirty', dirty), ('high', high),
                         ('clean', clean), ('risk', risk)):
            v, l = self.stat_tiles[key]
            v.configure(text=str(val))
        lbl = {'files': 'plików', 'dirty': 'z danymi', 'high': 'pilne',
               'clean': 'czyste', 'risk': 'ryzyko /100'}
        for key, (_, l) in self.stat_tiles.items():
            l.configure(text=lbl[key])

    def _badge(self, s, rep=None):
        if rep is not None and rep.note:
            return rep.note, None
        if not s:
            return 'brak reguł', None
        short = {'bezpieczne': 'bezpieczne', 'tylko metadane': 'metadane',
                 'lokalizacja': 'LOKALIZACJA', 'tozsamosc': 'TOŻSAMOŚĆ'}
        return short.get(s['class'], s['class']), s['risk']

    def _hover(self, rep):
        self.show_detail(rep, keep_name=True)

    def show_detail(self, rep, keep_name=False):
        self.selected = rep
        s = mdl.score(rep)
        self.detail.delete('1.0', 'end')
        if not keep_name:
            self.detail_name.configure(text=os.path.basename(rep.path))
        if s:
            self.detail.insert('end', f'\nRYZYKO {s["risk"]}/100 · {s["class"]}'
                                    f' ({s["confidence"] * 100:.0f}% pewności)\n')
            self.detail.insert('end', '─' * 34 + '\n')
        if not rep.findings:
            self.detail.insert('end', '\nCzyste. Nic do usuwania.\n')
            return
        for f in rep.findings:
            tag = 'PO OBRAZIE:' in f.value or 'WIDEO' in f.value
            self.detail.insert('end', f'\n{f.risk:<5} {f.kind}\n  {f.value}\n')
            if f.why:
                self.detail.insert('end', f'  → {f.why}\n')
        if rep.note:
            self.detail.insert('end', f'\n  ({rep.note})\n')
        self.detail.configure(state='normal')
        self.detail.see('1.0')

    # ── czyszczenie ───────────────────────────────────────────────────────────
    def clean(self):
        dirty = [(r, t) for r, t, _ in self.rows if r.findings]
        if not dirty:
            return
        src_dirs = {os.path.realpath(os.path.dirname(r.path)) for r, _ in dirty}
        default = None
        if len(src_dirs) == 1:
            d = src_dirs.pop()
            default = os.path.join(os.path.dirname(d), 'photoscrub-wyczyszczone')
            try:
                os.makedirs(default, exist_ok=True)
            except OSError:
                default = None
        if default is None:
            default = filedialog.askdirectory(
                title='Zapisz czyste kopie TUTAJ (inny folder niż zdjęcia)')
            if not default:
                return
        if os.path.realpath(default) in {os.path.realpath(os.path.dirname(r.path))
                                         for r, _ in dirty}:
            self.toast.show('Zatrzymane',
                            'To jest ten sam folder ze zdjęciami. Wybierz inny — '
                            'oryginały nigdy nie są nadpisywane.', 'err', 7000)
            return
        self.status.configure(text='Usuwam…', fg=DIM)
        self.btn.configure(state='disabled')
        out = default

        def work():
            done, failed, freed = 0, [], 0
            for r, _ in dirty:
                if r.kind == 'video':
                    failed.append(f'{os.path.basename(r.path)} — wideo (reguły v'
                                  f'{getattr(self, "ruleset", rs.CURRENT)} nie czyścią wideo)')
                    continue
                try:
                    before = r.size
                    ps.scrub_image(r.path, ps.safe_dst(r.path, out))
                    done += 1
                    try:
                        freed += max(0, before - os.path.getsize(ps.safe_dst(r.path, out)))
                    except OSError:
                        pass
                except Exception as e:
                    failed.append(f'{os.path.basename(r.path)}: {e}')
            self.after(0, lambda: self._done(done, failed, out, freed))
        threading.Thread(target=work, daemon=True).start()

    def _done(self, done, failed, out, freed):
        self.status.configure(text=f'{done} plików bez metadanych', fg=GRN)
        self.verdict.configure(text='Gotowe', fg=GRN)
        self.sub.configure(text=f'Kopie w: {out}\nOryginały nietknięte — '
                                f'oszczędność {human(freed)} metadanych.')
        self.rows = []
        self.selected = None
        self._render([])
        if failed:
            self.toast.show(f'{done} oczyszczone, {len(failed)} pominięte',
                            '\n'.join(failed[:4]), 'warn', 8000)
        else:
            self.toast.show('Gotowe', f'{done} plików zapisanych w:\n{out}', 'ok')


if __name__ == '__main__':
    App().mainloop()