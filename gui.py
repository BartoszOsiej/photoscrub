#!/usr/bin/env python3
"""photoscrub — dla ludzi, którzy nie myślą o metadanych.

Jeden ekran. Upuszczasz zdjęcia, widzisz co ujawniają, klikasz jeden przycisk.
Bez konta, bez logowania, bez kreatora z siedmioma krokami.

Wersjonowane reguły (ruleset.py) decydują, co jest wykrywane. Licencja mówi,
którą wersję klient kupił. Nic nie jest ukryte — różnica jest opisana wprost.
"""
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import license as lic
import model as mdl
import photoscrub as ps
import ruleset as rs
from PIL import Image, ImageTk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except Exception:
    DND_FILES = None
    TkinterDnD = None
    HAS_DND = False

# ── paleta ────────────────────────────────────────────────────────────────────
BG = '#0d1117'
PANEL = '#151c27'
PANEL_2 = '#1b2430'
FG = '#e9eef7'
DIM = '#8593a8'
ACC = '#3b5bff'
ACC_HI = '#5470ff'
RED = '#ff5a5f'
AMB = '#ffb02e'
GRN = '#2fd07f'
TITLE_F = ('DejaVu Sans', 22, 'bold')
BODY_F = ('DejaVu Sans', 10)
MONO_F = ('DejaVu Sans Mono', 10)


class Card(tk.Frame):
    def __init__(self, master, rep, thumb, score, on_click):
        super().__init__(master, bg=PANEL)
        self.rep, self.col, self.on_click = rep, None, on_click
        hot = [f for f in rep.findings if f.risk == 'HIGH']
        if not rep.findings:
            self.col = GRN
        elif hot:
            self.col = RED
        else:
            self.col = AMB
        self.box = tk.Frame(self, bg=PANEL, highlightthickness=1,
                            highlightbackground=PANEL_2, cursor='hand2')
        self.box.pack()
        tk.Frame(self.box, bg=self.col, height=3).pack(fill='x')
        inner = tk.Frame(self.box, bg=PANEL, width=200)
        inner.pack()
        self.img = tk.Label(inner, image=thumb, bg=PANEL, bd=0)
        self.img.pack(padx=8, pady=(8, 4))
        name = os.path.basename(rep.path)
        if len(name) > 24:
            name = name[:13] + '…' + name[-9:]
        tk.Label(inner, text=name, bg=PANEL, fg=FG, font=BODY_F,
                 width=24, anchor='w').pack(padx=10, pady=(2, 2))
        if score:
            label, col = score['label'], self.col
            txt = f'{label} · {score["risk"]}'
        else:
            col = DIM
            txt = 'brak reguł'
        self.badge = tk.Label(inner, text=txt, bg=PANEL, fg=col,
                              font=('DejaVu Sans', 9, 'bold'), width=24, anchor='w')
        self.badge.pack(padx=10, pady=(0, 10))
        self.parts = (self, self.box, inner, self.img, self.badge)
        for w in self.parts:
            w.bind('<Button-1>', lambda e: self.on_click(rep))
            w.bind('<Enter>', lambda e: self.box.configure(highlightthickness=2,
                                                            highlightbackground=self.col))
            w.bind('<Leave>', lambda e: self.box.configure(highlightthickness=1,
                                                            highlightbackground=PANEL_2))


class App((TkinterDnD.Tk if HAS_DND else tk.Tk)):
    def __init__(self):
        super().__init__()
        self.title('photoscrub')
        self.configure(bg=BG)
        self.geometry('1060x720')
        self.minsize(900, 580)
        self.rows = []
        self._build()
        self._wire_dnd()
        self.after(120, self._gate)

    # ── licencja + reguły ──────────────────────────────────────────────────────
    def _license(self):
        try:
            st, info, payload = lic.state()
        except Exception:
            return None, None, None
        rv = lic.purchased_ruleset(payload) if payload else 1
        return st, info, rv

    def _gate(self):
        st, info, rv = self._license()
        self.ruleset = rv
        if st in ('ok', 'grace'):
            if st == 'grace':
                self.status.configure(text=f'poza okresem grace: {info}', fg=AMB)
            self._show_upgrade(rv)
            return
        self._show_gate(st, info)

    def _show_gate(self, st, info):
        win = tk.Toplevel(self)
        win.configure(bg=BG)
        win.title('photoscrub — aktywacja')
        win.geometry('470x360')
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        box = tk.Frame(win, bg=BG)
        box.pack(fill='both', expand=True, padx=30, pady=26)
        tk.Label(box, text='Klucz aktywacyjny', bg=BG, fg=FG,
                 font=('DejaVu Sans', 15, 'bold')).pack(anchor='w')
        tk.Label(box, text=info if st != 'brak' else 'Wklej klucz z maila.',
                 bg=BG, fg=RED if st == 'bledny' else DIM, font=BODY_F,
                 wraplength=410, justify='left').pack(anchor='w', pady=(4, 12))
        entry = tk.Text(box, height=6, bg=PANEL, fg=FG, bd=0, relief='flat',
                        font=MONO_F, wrap='char', padx=10, pady=8,
                        highlightthickness=1, highlightbackground=PANEL_2)
        entry.pack(fill='x')
        out = tk.Label(box, text='', bg=BG, fg=RED, font=BODY_F,
                       wraplength=410, justify='left')

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

        row = tk.Frame(box, bg=BG)
        row.pack(anchor='w', pady=(10, 0))
        tk.Button(row, text='Wklej ze schowka', command=paste, bg=PANEL, fg=FG,
                  bd=0, relief='flat', padx=12, pady=6, font=BODY_F,
                  cursor='hand2').pack(side='left')
        tk.Button(row, text='Aktywuj', command=go, bg=ACC, activebackground=ACC_HI,
                  fg='#fff', bd=0, relief='flat', padx=24, pady=8,
                  font=('DejaVu Sans', 11, 'bold'), cursor='hand2').pack(side='left', padx=8)
        out.pack(anchor='w', pady=(10, 0))
        tk.Label(box, text=f'twoja maszyna: {lic.machine_id()[:16]}', bg=BG, fg=DIM,
                 font=('DejaVu Sans Mono', 8)).pack(anchor='w', pady=(10, 0))

    def _show_upgrade(self, purchased):
        ups = rs.upgrades_available(purchased)
        if not ups:
            self.status.configure(text=f'reguły v{purchased}', fg=GRN)
            return
        u = ups[0]
        self.status.configure(
            text=f'reguły v{purchased} · nowsze reguły v{u["version"]} ({u["name"]}) '
                 f'dostępne — ' + ' · '.join(n for n, _ in u['new'][:4]), fg=AMB)
        self.upgrade_bar = tk.Frame(self, bg=BG)
        self.upgrade_bar.pack(fill='x', padx=18, pady=(0, 8))
        card = tk.Frame(self.upgrade_bar, bg=PANEL)
        card.pack(fill='x')
        tk.Label(card, text=f'Nowsze reguły wykrywania — v{u["version"]} ({u["name"]})',
                 bg=PANEL, fg=AMB, font=('DejaVu Sans', 10, 'bold'),
                 anchor='w').pack(anchor='w', padx=14, pady=(10, 2))
        for what, why in u['new']:
            tk.Label(card, text=f'  +  {what} — {why}', bg=PANEL, fg=DIM,
                     font=BODY_F, anchor='w').pack(anchor='w', padx=6)
        tk.Label(card, text=u['promise'], bg=PANEL, fg=DIM, font=BODY_F,
                 anchor='w', wraplength=980, justify='left').pack(anchor='w',
                                                                   padx=14, pady=(8, 10))

    # ── layout ────────────────────────────────────────────────────────────────
    def _build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill='x', padx=24, pady=(18, 0))
        tk.Label(top, text='photoscrub', bg=BG, fg=FG,
                 font=('DejaVu Sans', 14, 'bold')).pack(side='left')
        tk.Label(top, text='co twoje zdjęcia ujawniają', bg=BG, fg=DIM,
                 font=BODY_F).pack(side='left', padx=10)
        tk.Button(top, text='Wybierz folder', command=self.add_folder, bg=PANEL, fg=FG,
                  activebackground=PANEL_2, bd=0, relief='flat', padx=14, pady=7,
                  font=BODY_F, cursor='hand2').pack(side='right')
        tk.Button(top, text='Dodaj zdjęcia', command=self.add_files, bg=PANEL, fg=FG,
                  activebackground=PANEL_2, bd=0, relief='flat', padx=14, pady=7,
                  font=BODY_F, cursor='hand2').pack(side='right', padx=8)

        hero = tk.Frame(self, bg=BG)
        hero.pack(fill='x', padx=24, pady=(18, 2))
        tk.Frame(hero, bg=ACC, width=3).pack(side='left', fill='y', padx=(0, 14))
        inner = tk.Frame(hero, bg=BG)
        inner.pack(side='left', fill='x', expand=True)
        self.verdict = tk.Label(inner, text='Upuść zdjęcia na okno', bg=BG, fg=FG,
                                font=TITLE_F, anchor='w', justify='left')
        self.verdict.pack(anchor='w')
        self.sub = tk.Label(inner, text='albo kliknij "Dodaj zdjęcia". Wszystko zostaje '
                                         'na tym komputerze — nic nie wysyłamy.',
                            bg=BG, fg=DIM, font=BODY_F, anchor='w')
        self.sub.pack(anchor='w', pady=(5, 0))
        self.risk = tk.Label(inner, text='', bg=BG, fg=DIM, font=BODY_F, anchor='w')
        self.risk.pack(anchor='w', pady=(6, 0))

        self.grid_ = tk.Frame(self, bg=BG)
        self.grid_.pack(fill='both', expand=True, padx=18, pady=(12, 12))
        tk.Label(self.grid_, text='Upuść zdjęcia na to okno', bg=BG, fg=DIM,
                 font=('DejaVu Sans', 12)).pack(expand=True)

        self.detail = tk.Text(self, height=10, bg=PANEL, fg=FG, bd=0, relief='flat',
                              font=MONO_F, wrap='word', padx=16, pady=12,
                              highlightthickness=1, highlightbackground=PANEL_2,
                              insertbackground=FG, cursor='arrow')
        self.detail.pack(fill='x', padx=18, pady=(0, 10))
        self.detail.insert('1.0', 'Kliknij zdjęcie, żeby zobaczyć co dokładnie ujawnia.\n')

        bot = tk.Frame(self, bg=BG)
        bot.pack(fill='x', padx=18, pady=(0, 18))
        self.btn = tk.Button(bot, text='Usuń metadane ze wszystkich', command=self.clean,
                             bg=ACC, activebackground=ACC_HI, fg='#fff', bd=0,
                             relief='flat', padx=22, pady=11,
                             font=('DejaVu Sans', 11, 'bold'), cursor='hand2',
                             state='disabled')
        self.btn.pack(side='left')
        self.status = tk.Label(bot, text='', bg=BG, fg=DIM, font=BODY_F)
        self.status.pack(side='left', padx=16)

    # ── drag & drop ───────────────────────────────────────────────────────────
    def _wire_dnd(self):
        if not HAS_DND:
            return
        for w in (self, self.grid_, self.detail, self.verdict):
            try:
                w.drop_target_register(DND_FILES)
                w.dnd_bind('<<Drop>>', self._on_drop)
            except tk.TclError:
                pass

    def _on_drop(self, _event=None):
        try:
            data = self.tk.splitlist(self.dnd_get('DND_DATA'))
        except Exception:
            data = []
        if data:
            self.add_paths([p for p in data if os.path.exists(p)])

    # ── wejście ───────────────────────────────────────────────────────────────
    def add_files(self):
        fs = filedialog.askopenfilenames(
            title='Wybierz zdjęcia',
            filetypes=[('Zdjęcia i wideo', '*.jpg *.jpeg *.png *.tif *.tiff *.webp '
                                           '*.heic *.heif *.avif *.mp4 *.mov *.m4v'),
                       ('Wszystko', '*.*')])
        if fs:
            self.add_paths(list(fs))

    def add_folder(self):
        d = filedialog.askdirectory(title='Wybierz folder')
        if d:
            self.add_paths([d])

    def add_paths(self, paths):
        allowed = ps.IMG_EXT | ps.VIDEO_EXT | {'.zip'}
        files = []
        for p in paths:
            if os.path.isdir(p):
                for dp, _, fs in os.walk(p):
                    for f in fs:
                        if os.path.splitext(f)[1].lower() in allowed:
                            files.append(os.path.join(dp, f))
            elif os.path.splitext(p)[1].lower() in allowed:
                files.append(p)
        if not files:
            return
        self.status.configure(text='Sprawdzam…', fg=DIM)
        threading.Thread(target=self._work, args=(files,), daemon=True).start()

    def _work(self, files):
        rv = getattr(self, 'ruleset', rs.CURRENT)
        reps = [ps.scan_file(f, rv) for f in files]
        thumbs = [self._thumb(r.path) for r in reps]
        self.after(0, self._fill, reps, thumbs)

    def _thumb(self, path, box=(184, 114)):
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

    def _fill(self, reps, thumbs):
        for r, t in zip(reps, thumbs):
            self.rows.append((r, t, mdl.score(r)))
        dirty = [x for x in self.rows if x[0].findings]
        self.verdict.configure(
            text=f'{len(dirty)} zdjęć ujawnia dane' if dirty
            else 'Zadne z tych zdjęć nic nie ujawnia.',
            fg=FG if dirty else GRN)
        self.sub.configure(
            text=f'z {len(self.rows)} plików · {len(self.rows) - len(dirty)} czystych · '
                 f'reguły v{getattr(self, "ruleset", rs.CURRENT)} · lokalnie, nic nie wychodzi z komputera')
        scores = [s['risk'] for _, _, s in self.rows if s]
        if scores:
            top = max(scores)
            self.risk.configure(
                fg=RED if top >= 60 else (AMB if top >= 30 else GRN),
                text=f'najwyższe ryzyko publikacji w tej partii: {top}/100  '
                     f'(model: {len(mdl.load()["features"]) if mdl.load() else 0} cech)')
        for c in list(self.grid_.winfo_children()):
            c.destroy()
        shown = 0
        for r, t, s in self.rows:
            if shown >= 8:
                break
            Card(self.grid_, r, t, self._badge(s), self.show_detail).grid(
                row=shown // 4, column=shown % 4, padx=6, pady=6, sticky='n')
            shown += 1
        if len(self.rows) > shown:
            tk.Label(self.grid_, text=f'+{len(self.rows) - shown} więcej', bg=BG, fg=DIM,
                     font=BODY_F).grid(row=shown // 4, column=shown % 4, padx=6, pady=6)
        if dirty:
            self.btn.configure(state='normal')
        self.detail.delete('1.0', 'end')
        if dirty:
            r, _, s = max(dirty, key=lambda x: x[0].risk_score)
            self.detail.insert('1.0', f'najgorszy: {os.path.basename(r.path)}\n')
            if s:
                self.detail.insert('end', f'model: {s["class"]} · ryzyko {s["risk"]}/100 '
                                          f'· pewność {s["confidence"]:.2f}\n')
            for f in r.findings:
                self.detail.insert('end', f'{f.risk:5} {f.kind:20} {f.value}\n')
                if f.why:
                    self.detail.insert('end', f'                    {f.why}\n')
        else:
            self.detail.insert('1.0', 'Kliknij zdjęcie, żeby zobaczyć szczegóły.\n')

    def _badge(self, s):
        if not s:
            return None
        short = {'bezpieczne': 'bezpieczne', 'tylko metadane': 'metadane',
                 'lokalizacja': 'LOKALIZACJA', 'tozsamosc': 'TOŻSAMOŚĆ'}
        return {'label': short.get(s['class'], s['class']), 'risk': s['risk']}

    def show_detail(self, rep):
        self.detail.delete('1.0', 'end')
        s = mdl.score(rep)
        head = f'{os.path.basename(rep.path)}\n'
        if s:
            head += (f'model: {s["class"]} · ryzyko {s["risk"]}/100 · '
                     f'pewność {s["confidence"]:.2f}\n')
        self.detail.insert('1.0', head)
        if not rep.findings:
            self.detail.insert('end', 'Czyste — nic do usuwania.\n')
            return
        for f in rep.findings:
            self.detail.insert('end', f'{f.risk:5} {f.kind:20} {f.value}\n')
            if f.why:
                self.detail.insert('end', f'                    {f.why}\n')

    # ── czyszczenie ───────────────────────────────────────────────────────────
    def clean(self):
        dirty = [(r, t) for r, t, _ in self.rows if r.findings]
        if not dirty:
            return
        out = filedialog.askdirectory(title='Zapisz czyste kopie TUTAJ (inny folder)')
        if not out:
            return
        src_dirs = {os.path.realpath(os.path.dirname(r.path)) for r, _ in dirty}
        if os.path.realpath(out) in src_dirs:
            messagebox.showerror('Zatrzymane',
                                 'Ten folder zawiera te zdjęcia.\n\nWybierz DRUGI folder — '
                                 'inaczej program nadpisałby oryginały.\n'
                                 'Oryginały nigdy nie są modyfikowane.')
            return
        self.status.configure(text='Usuwam…', fg=DIM)
        self.btn.configure(state='disabled')

        def work():
            done, failed = 0, []
            for r, _ in dirty:
                if r.kind == 'video':
                    failed.append(f'{os.path.basename(r.path)}: wideo (v{picked_ruleset})')
                    continue
                try:
                    ps.scrub_image(r.path, ps.safe_dst(r.path, out))
                    done += 1
                except Exception as e:
                    failed.append(f'{os.path.basename(r.path)}: {e}')
            self.after(0, lambda: self._done(done, failed, out))
        picked_ruleset = getattr(self, 'ruleset', rs.CURRENT)
        threading.Thread(target=work, daemon=True).start()

    def _done(self, done, failed, out):
        msg = f'{done} plików bez metadanych w:\n{out}\n\nOryginały nietknięte.'
        if failed:
            messagebox.showwarning('Częściowo', msg + '\n\nPominięto:\n' +
                                   '\n'.join(failed[:6]))
        else:
            messagebox.showinfo('Gotowe', msg)
        self.status.configure(text=f'{done} plików wyczyszczonych', fg=GRN)
        self.verdict.configure(text='Gotowe. Upuść kolejne zdjęcia.', fg=GRN)
        self.risk.configure(text='')
        for c in list(self.grid_.winfo_children()):
            c.destroy()
        tk.Label(self.grid_, text='Upuść zdjęcia na to okno', bg=BG, fg=DIM,
                 font=('DejaVu Sans', 12)).pack(expand=True)
        self.rows = []
        self.detail.delete('1.0', 'end')
        self.detail.insert('1.0', 'Kliknij zdjęcie, żeby zobaczyć szczegóły.\n')


if __name__ == '__main__':
    App().mainloop()