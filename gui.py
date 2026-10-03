#!/usr/bin/env python3
"""photoscrub GUI - dla ludzi, ktorzy nie otwieraja terminala.

Zasada: zero kont, zero sieci, zero konfiguracji. Wybierz folder, zobacz co
ucieka, kliknij "Usun", dostaniesz nowy folder. Oryginaly nigdy nie ruszamy.
"""
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import photoscrub as ps

BG = '#0e1218'
PANEL = '#141b26'
FG = '#e8ecf4'
DIM = '#7d8aa3'
ACC = '#4f6ef7'
RED = '#ef6a6a'
AMB = '#f5b742'
GRN = '#34c788'


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('photoscrub - co twoje zdjecia ujawniaja')
        self.configure(bg=BG)
        self.geometry('980x640')
        self.minsize(820, 520)
        self.reports = []
        self._build()
        self.after(80, self._tick)

    # ---------------------------------------------------------------- UI
    def _build(self):
        head = tk.Frame(self, bg=BG)
        head.pack(fill='x', padx=18, pady=(16, 6))
        tk.Label(head, text='photoscrub', bg=BG, fg=FG,
                 font=('Segoe UI', 20, 'bold')).pack(side='left')
        tk.Label(head, text='lokalnie, bez sieci, bez konta', bg=BG, fg=DIM,
                 font=('Segoe UI', 10)).pack(side='left', padx=12)
        self.btn_choose = ttk.Button(head, text='Wybierz folder ze zdjeciami',
                                     command=self.choose)
        self.btn_choose.pack(side='right')

        self.lbl_sum = tk.Label(self, text='Nic jeszcze nie sprawdzone.',
                                bg=BG, fg=DIM, font=('Segoe UI', 11), anchor='w')
        self.lbl_sum.pack(fill='x', padx=18, pady=(2, 8))

        cols = ('file', 'risk', 'leaks')
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=16)
        self.tree.heading('file', text='Plik')
        self.tree.heading('risk', text='Ryzyko')
        self.tree.heading('leaks', text='Co ujawnia')
        self.tree.column('file', width=330)
        self.tree.column('risk', width=70, anchor='center')
        self.tree.column('leaks', width=440)
        self.tree.pack(fill='both', expand=True, padx=18)
        self.tree.bind('<<TreeviewSelect>>', self.show_detail)
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
            self.style.configure('Treeview', background=PANEL, fieldbackground=PANEL,
                                 foreground=FG, rowheight=26)
            self.style.configure('Treeview.Heading', background=PANEL, foreground=DIM)
        except tk.TclError:
            pass

        self.txt = tk.Text(self, height=9, bg=PANEL, fg=FG, relief='flat',
                           font=('Consolas', 10), wrap='word')
        self.txt.pack(fill='x', padx=18, pady=10)

        bot = tk.Frame(self, bg=BG)
        bot.pack(fill='x', padx=18, pady=(0, 16))
        self.btn_clean = tk.Button(bot, text='Usun wszystko (kopie bez metadanych)',
                                   command=self.clean, bg=ACC, fg='#fff',
                                   activebackground='#3d59d8', relief='flat',
                                   font=('Segoe UI', 11, 'bold'), cursor='hand2')
        self.btn_clean.pack(side='left')
        self.btn_clean.configure(state='disabled')
        self.lbl_status = tk.Label(bot, text='', bg=BG, fg=DIM, font=('Segoe UI', 10))
        self.lbl_status.pack(side='left', padx=14)

    # ------------------------------------------------------------ akcje
    def choose(self):
        d = filedialog.askdirectory(title='Wybierz folder ze zdjeciami')
        if not d:
            return
        self.btn_clean.configure(state='disabled')
        self.lbl_status.configure(text='Sprawdzam...', fg=DIM)
        threading.Thread(target=self._scan, args=(d,), daemon=True).start()

    def _scan(self, d):
        try:
            reps = ps.scan_tree(d)
        except Exception as e:
            self.after(0, lambda: self.lbl_status.configure(text=f'blad: {e}', fg=RED))
            return
        self.after(0, self._fill, reps)

    def _fill(self, reps):
        self.reports = [r for r in reps if r.findings]
        self.tree.delete(*self.tree.get_children())
        for r in sorted(self.reports, key=lambda x: -x.risk_score):
            tag = 'HIGH' if r.risk_score >= 20 else ('MED' if r.risk_score >= 6 else 'LOW')
            leaks = ', '.join(f.kind for f in r.findings)
            self.tree.insert('', 'end', iid=r.path, values=(
                os.path.basename(r.path), f'{r.risk_score}', leaks), tags=(tag,))
        for tag, col in (('HIGH', RED), ('MED', AMB), ('LOW', GRN)):
            self.tree.tag_configure(tag, foreground=col)
        n = len(reps)
        self.lbl_sum.configure(
            fg=FG,
            text=f'{len(self.reports)} z {n} plikow ujawnia dane. '
                 f'Kliknij plik, zeby zobaczyc co w srodku.')
        self.txt.delete('1.0', 'end')
        self.txt.insert('1.0',
                        'Najczestszy wyciek, o ktorym ludzie nie wiedza:\n'
                        '  JPEG potrafi niec w sobie druga, miniaturowa kopie calego\n'
                        '  zdjecia (160x120). Usuniecie tagow EXIF tego NIE usuwa.')
        if self.reports:
            self.btn_clean.configure(state='normal')

    def show_detail(self, _evt=None):
        sel = self.tree.selection()
        if not sel:
            return
        r = next((x for x in self.reports if x.path == sel[0]), None)
        if not r:
            return
        self.txt.delete('1.0', 'end')
        self.txt.insert('1.0', f'{r.path}\n{r.size} B\n')
        for f in r.findings:
            self.txt.insert('end', f'  [{f.risk}] {f.kind}: {f.value}\n')
            if f.why:
                self.txt.insert('end', f'         {f.why}\n')
        if r.note:
            self.txt.insert('end', f'  ({r.note})\n')

    def clean(self):
        if not self.reports:
            return
        src_dir = os.path.commonpath([r.path for r in self.reports])
        out = filedialog.askdirectory(title='Zapisz czyste kopie tutaj')
        if not out:
            return
        self.lbl_status.configure(text='Usuwam...', fg=DIM)
        self.btn_clean.configure(state='disabled')

        def work():
            done, failed = 0, []
            for r in self.reports:
                if r.kind != 'image':
                    continue
                dst = os.path.join(out, os.path.basename(r.path))
                try:
                    ps.scrub_image(r.path, dst)
                    done += 1
                except Exception as e:
                    failed.append(f'{os.path.basename(r.path)}: {e}')
            self.after(0, lambda: self._done(done, failed, out))
        threading.Thread(target=work, daemon=True).start()

    def _done(self, done, failed, out):
        msg = f'Gotowe: {done} plikow bez metadanych w\n{out}\n\nOryginaly nietkniete.'
        if failed:
            msg += f'\n\nPominieto {len(failed)}:\n' + '\n'.join(failed[:8])
            messagebox.showwarning('Czesciowo', msg)
        else:
            messagebox.showinfo('Gotowe', msg)
        self.lbl_status.configure(text=f'{done} plikow wyczyszczonych', fg=GRN)
        self.lbl_sum.configure(text='Gotowe. Oryginaly zostaly na miejscu.')
        for r in self.reports:
            r.findings = []
        self.tree.delete(*self.tree.get_children())
        self.reports = []
        self.txt.delete('1.0', 'end')


if __name__ == '__main__':
    App().mainloop()
