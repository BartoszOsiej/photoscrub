#!/usr/bin/env python3
"""photoscrub — Qt6. Działa tak samo na Windows i Linux.

Dlaczego Qt a nie Tkinter: Tk nie ma warstwy układu (pack przydziela miejsce w
kolejności wywołań — stąd „okno dostaje 58 px i tekst zwija się do jednej litery")
i nie zna skali ekranu na Waylandzie (stąd „wszystko krzywe"). Qt ma oba rozwiązane
od samego początku, do tego prawdziwe style, własny drag&drop i poprawne skalowanie.
"""
import os
import sys

from PySide6 import QtCore, QtGui, QtWidgets

import license as lic
import model as mdl
import photoscrub as ps
import ruleset as rs

QSS = """
QWidget { background:#0b0e14; color:#f2f5fa;
         font-family:'Inter','Noto Sans','DejaVu Sans'; font-size:13px; }
QToolTip { background:#141b28; color:#f2f5fa; border:1px solid #243044;
           padding:6px 8px; border-radius:6px; }

/* ── nagłówek ──*/
QLabel#logo { color:#f2f5fa; font-size:17px; font-weight:600; }
QLabel#tagline { color:#4a5568; font-size:12px; }
QLabel#headline { color:#f2f5fa; font-size:30px; font-weight:700; }
QLabel#subline { color:#7b8798; font-size:13px; }
QLabel#panelTitle { color:#4a5568; font-size:11px; font-weight:700; letter-spacing:1px; }
QLabel#fileName { color:#f2f5fa; font-size:14px; font-weight:600; }

/* ── przyciski ──*/
QPushButton { background:#141b28; color:#c7d0de; border:1px solid #243044;
              border-radius:8px; padding:9px 16px; font-size:13px; }
QPushButton:hover { background:#1c2534; border-color:#3d5bff; color:#f2f5fa; }
QPushButton:pressed { background:#141b28; }
QPushButton[cta="true"] { background:#3d5bff; color:#ffffff; border:none;
                         padding:13px 26px; font-size:14px; font-weight:700; }
QPushButton[cta="true"]:hover { background:#5a76ff; }
QPushButton[cta="true"]:disabled { background:#1a2331; color:#4a5568; }
QPushButton[ghost="true"] { background:transparent; border:none; color:#3d5bff;
                           padding:6px 8px; font-size:12px; }

/* ── statystyki ── */
QFrame#tile { background:transparent; }
QLabel#statValue { font-size:26px; font-weight:700; }
QLabel#statLabel { color:#4a5568; font-size:11px; }
QFrame#sep { background:#1a2230; max-height:1px; border:none; }

QProgressBar { background:#141b28; border:none; border-radius:2px; height:3px; }
QProgressBar::chunk { background:#3d5bff; border-radius:2px; }

/* ── karty ── */
QFrame#card { background:#141b28; border:1px solid #1c2534; border-radius:10px; }
QFrame#card:hover { border:1px solid #3d5bff; }
QLabel#cardName { color:#f2f5fa; font-size:12px; }
QLabel#cardBadge { font-size:11px; font-weight:700; }
QLabel#cardRisk { font-size:12px; font-weight:700; }
QLabel#cardThumb { background:#0f1420; border-radius:6px; }

/* ── panel szczegółów ── */
QFrame#side { background:#10151f; border:1px solid #1c2534; border-radius:12px; }
QTextEdit#detail, QTextBrowser#detail { background:#10151f; color:#c7d0de;
        border:none; font-family:'Inter','DejaVu Sans Mono'; font-size:12px; }
QTextBrowser#notes { background:transparent; color:#5d6a80; border:none;
                     font-size:12px; }

/* ── strefa upuszczania ── */
QFrame#drop { background:#0b0e14; border:2px dashed #243044; border-radius:14px; }
QFrame#drop[hot="true"] { background:#111725; border:2px solid #3d5bff; }
QLabel#dropTitle { color:#c7d0de; font-size:15px; font-weight:600; }
QLabel#dropSub { color:#4a5568; font-size:12px; }

/* ── pasek przewijania ── */
QScrollBar:vertical { background:transparent; width:10px; margin:0; }
QScrollBar::handle:vertical { background:#243044; border-radius:4px; min-height:40px; }
QScrollBar::handle:vertical:hover { background:#3d5bff; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background:none; }

/* ── toast ── */
QFrame#toast { background:#141b28; border:1px solid #243044; border-radius:10px; }
QLabel#toastTitle { font-size:13px; font-weight:600; }
QLabel#toastBody { color:#7b8798; font-size:12px; }

QDialog { background:#0b0e14; }
QLineEdit, QTextEdit { background:#141b28; color:#f2f5fa; border:1px solid #243044;
                       border-radius:8px; padding:9px; font-size:13px; }
QLineEdit:focus, QTextEdit:focus { border:1px solid #3d5bff; }
QLabel#hint { color:#4a5568; font-size:11px; }"""

BG = '#0b0e14'
PANEL = '#141b28'
PANEL2 = '#1c2534'
LINE = '#243044'
FG = '#f2f5fa'
FG2 = '#c7d0de'
DIM = '#7b8798'
FAINT = '#4a5568'
ACC = '#3d5bff'
RED = '#ff5c62'
AMB = '#ffb224'
GRN = '#2fd07f'


def human(n):
    for u in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or u == 'GB':
            return f'{n:.0f} {u}' if u == 'B' else f'{n:.1f} {u}'
        n /= 1024.0


class Card(QtWidgets.QFrame):
    clicked = QtCore.Signal(object)
    entered = QtCore.Signal(object)

    def __init__(self, rep, thumb, label, risk):
        super().__init__()
        self.rep = rep
        self.setObjectName('card')
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        if not rep.findings:
            self.col = GRN
        elif any(f.risk == 'HIGH' for f in rep.findings):
            self.col = RED
        else:
            self.col = AMB

        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(9, 9, 9, 9)
        v.setSpacing(6)

        self.thumb = QtWidgets.QLabel()
        self.thumb.setObjectName('cardThumb')
        self.thumb.setFixedHeight(112)
        self.thumb.setAlignment(QtCore.Qt.AlignCenter)
        if thumb is not None:
            self.thumb.setPixmap(thumb)
        v.addWidget(self.thumb)

        name = os.path.basename(rep.path)
        if len(name) > 28:
            stem, ext = os.path.splitext(name)
            name = stem[:18] + '…' + ext[-6:]
        nl = QtWidgets.QLabel(name)
        nl.setObjectName('cardName')
        nl.setToolTip(rep.path)
        v.addWidget(nl)

        row = QtWidgets.QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        b = QtWidgets.QLabel(label)
        b.setObjectName('cardBadge')
        b.setStyleSheet(f'color:{self.col}')
        row.addWidget(b)
        row.addStretch(1)
        if risk is not None:
            r = QtWidgets.QLabel(str(risk))
            r.setObjectName('cardRisk')
            r.setStyleSheet(f'color:{self.col}')
            row.addWidget(r)
        v.addLayout(row)

        for w in (self, self.thumb, nl):
            w.mousePressEvent = self._press
            w.mouseEnterEvent = self._enter

    def _press(self, _e=None):
        self.clicked.emit(self.rep)

    def _enter(self, _e=None):
        self.entered.emit(self.rep)


class DropZone(QtWidgets.QFrame):
    clicked = QtCore.Signal()
    files = QtCore.Signal(list)

    def __init__(self):
        super().__init__()
        self.setObjectName('drop')
        self.setMinimumHeight(150)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.setAcceptDrops(True)
        v = QtWidgets.QVBoxLayout(self)
        v.setAlignment(QtCore.Qt.AlignCenter)
        v.setSpacing(6)

        self.stack = QtWidgets.QLabel()
        self.stack.setPixmap(self._stack_icon())
        self.stack.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(self.stack)

        t = QtWidgets.QLabel('Upuść zdjęcia lub filmy')
        t.setObjectName('dropTitle')
        t.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(t)
        s = QtWidgets.QLabel('albo kliknij, żeby wybrać pliki')
        s.setObjectName('dropSub')
        s.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(s)

    @staticmethod
    def _stack_icon():
        pm = QtGui.QPixmap(64, 52)
        pm.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        for i in range(3):
            x = 6 + i * 9
            y = 6 + i * 5
            p.setPen(QtGui.QPen(QtGui.QColor('#2a3a52'), 2))
            p.setBrush(QtGui.QBrush(QtGui.QColor('#0b0e14')))
            p.drawRoundedRect(x, y, 42, 32, 6, 6)
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(QtGui.QBrush(QtGui.QColor('#243044')))
            p.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 2, y + 22),
                                          QtCore.QPoint(x + 12, y + 12),
                                          QtCore.QPoint(x + 20, y + 20),
                                          QtCore.QPoint(x + 26, y + 13),
                                          QtCore.QPoint(x + 40, y + 24)]))
        p.setPen(QtGui.QPen(QtGui.QColor('#3d5bff'), 2))
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawRoundedRect(6, 6, 42, 32, 6, 6)
        p.end()
        return pm

    def _hot(self, on):
        self.setProperty('hot', 'true' if on else 'false')
        self.style().unpolish(self)
        self.style().polish(self)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            self._hot(True)
            e.acceptProposedAction()

    def dragLeaveEvent(self, _e):
        self._hot(False)

    def dropEvent(self, e):
        self._hot(False)
        paths = [u.toLocalFile() for u in e.mimeData().urls()]
        if paths:
            self.files.emit(paths)
            e.acceptProposedAction()

    def mousePressEvent(self, _e):
        self.clicked.emit()


class Toast(QtWidgets.QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('toast')
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self.hide()

    def show_toast(self, title, body='', kind='info', ms=4600):
        while self.layout().count():
            it = self.layout().takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        col = {'info': ACC, 'ok': GRN, 'warn': AMB, 'err': RED}[kind]
        h = QtWidgets.QHBoxLayout(self)
        h.setContentsMargins(0, 0, 12, 0)
        bar = QtWidgets.QFrame()
        bar.setFixedWidth(3)
        bar.setStyleSheet(f'background:{col}; border-radius:2px;')
        h.addWidget(bar)
        box = QtWidgets.QVBoxLayout()
        box.setContentsMargins(12, 10, 0, 10)
        t = QtWidgets.QLabel(title)
        t.setObjectName('toastTitle')
        t.setStyleSheet(f'color:{FG}')
        box.addWidget(t)
        if body:
            b = QtWidgets.QLabel(body)
            b.setObjectName('toastBody')
            b.setWordWrap(True)
            box.addWidget(b)
        h.addLayout(box, 1)
        self.setStyleSheet(f'QFrame#toast {{ background:{PANEL}; border:1px solid {LINE};'
                           f' border-radius:10px; }}')
        self.show()
        self._timer.start(ms)


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('photoscrub')
        self.resize(1180, 820)
        self.setMinimumSize(1000, 660)
        self.setAcceptDrops(True)
        self.rows = []
        self.selected = None
        self.ruleset = rs.CURRENT

        c = QtWidgets.QWidget()
        self.setCentralWidget(c)
        root = QtWidgets.QVBoxLayout(c)
        root.setContentsMargins(26, 20, 26, 18)
        root.setSpacing(0)

        root.addLayout(self._header())
        self.headline = QtWidgets.QLabel('Upuść pliki, żeby zobaczyć co ujawniają')
        self.headline.setObjectName('headline')
        root.addWidget(self.headline)
        self.subline = QtWidgets.QLabel('Paswywnie. Zero sieci, zero konta. '
                                        'Oryginały zostają tam, gdzie są.')
        self.subline.setObjectName('subline')
        root.addWidget(self.subline)
        root.addSpacing(12)

        self.stats = self._stats()
        root.addLayout(self.stats)
        root.addSpacing(12)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setFixedHeight(3)
        self.progress.hide()
        root.addWidget(self.progress)

        body = QtWidgets.QHBoxLayout()
        body.setSpacing(16)
        root.addLayout(body, 1)

        self.drop = DropZone()
        self.drop.clicked.connect(self.add_files)
        self.drop.files.connect(self.add_paths)
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.hide()
        self.grid_host = QtWidgets.QWidget()
        self.grid = QtWidgets.QGridLayout(self.grid_host)
        self.grid.setSpacing(12)
        self.grid.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.scroll.setWidget(self.grid_host)
        # JEDEN kontener na dwie zawartosci. Dwa osobne widgety w poziomym
        # ukladzie dziela sie polowa szerokosci - karty dostawaly polowe okna
        # i kolumna po prawej byla obcieta.
        self.stack = QtWidgets.QStackedWidget()
        self.stack.addWidget(self.drop)
        self.stack.addWidget(self.scroll)
        body.addWidget(self.stack, 1)

        self.side = QtWidgets.QFrame()
        self.side.setObjectName('side')
        self.side.setFixedWidth(350)
        sv = QtWidgets.QVBoxLayout(self.side)
        sv.setContentsMargins(16, 14, 16, 14)
        sv.setSpacing(8)
        t = QtWidgets.QLabel('SZCZEGÓŁY')
        t.setObjectName('panelTitle')
        sv.addWidget(t)
        self.file_name = QtWidgets.QLabel('—')
        self.file_name.setObjectName('fileName')
        self.file_name.setWordWrap(True)
        sv.addWidget(self.file_name)
        self.detail = QtWidgets.QTextBrowser()
        self.detail.setObjectName('detail')
        self.detail.setOpenExternalLinks(False)
        sv.addWidget(self.detail, 1)
        self._reset_detail()
        sep = QtWidgets.QFrame()
        sep.setObjectName('sep')
        sep.setFixedHeight(1)
        sv.addWidget(sep)
        n = QtWidgets.QLabel('JAK TO DZIAŁA\n\n'
                             '·  Pasywne DNS i bajty pliku. Zero skanowania, zero sieci.\n'
                             '·  Oryginały nigdy nie są modyfikowane — zapisujemy kopie.\n'
                             '·  Najbardziej podstępny wyciek: miniaturka wbudowana '
                             'w JPEG to często całe oryginalne zdjęcie.')
        n.setObjectName('notes')
        n.setWordWrap(True)
        sv.addWidget(n)
        body.addWidget(self.side)

        foot = QtWidgets.QHBoxLayout()
        foot.setSpacing(14)
        self.cta = QtWidgets.QPushButton('Usuń metadane ze wszystkich')
        self.cta.setProperty('cta', True)
        self.cta.setEnabled(False)
        self.cta.clicked.connect(self.clean)
        foot.addWidget(self.cta)
        self.status = QtWidgets.QLabel('')
        self.status.setObjectName('subline')
        foot.addWidget(self.status, 1)
        root.addSpacing(10)
        root.addLayout(foot)

        self.toast = Toast(self)
        self.toast.setParent(c)
        self.toast.setFixedWidth(640)

        self._worker = None
        self._thread = None
        QtCore.QTimer.singleShot(120, self._gate)

    # ── layout helpers ────────────────────────────────────────────────────────
    def _header(self):
        h = QtWidgets.QHBoxLayout()
        logo = QtWidgets.QLabel()
        pm = QtGui.QPixmap(28, 28)
        pm.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(QtGui.QPen(QtGui.QColor(ACC), 2))
        p.drawEllipse(2, 2, 24, 24)
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QBrush(QtGui.QColor(ACC)))
        p.drawEllipse(9, 9, 10, 10)
        p.end()
        logo.setPixmap(pm)
        h.addWidget(logo)
        h.addSpacing(10)
        names = QtWidgets.QVBoxLayout()
        names.setSpacing(0)
        n = QtWidgets.QLabel('photoscrub')
        n.setObjectName('logo')
        names.addWidget(n)
        tg = QtWidgets.QLabel('zanim wrzucisz to do sieci')
        tg.setObjectName('tagline')
        names.addWidget(tg)
        h.addLayout(names)
        h.addStretch(1)
        bf = QtWidgets.QPushButton('Wybierz folder')
        bf.clicked.connect(self.add_folder)
        h.addWidget(bf)
        bfl = QtWidgets.QPushButton('Dodaj pliki')
        bfl.clicked.connect(self.add_files)
        h.addWidget(bfl)
        return h

    def _stats(self):
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(30)
        self.stat_vals = {}
        for key, col in (('files', DIM), ('dirty', RED), ('high', RED),
                         ('clean', GRN), ('risk', AMB)):
            box = QtWidgets.QVBoxLayout()
            box.setSpacing(0)
            v = QtWidgets.QLabel('0')
            v.setObjectName('statValue')
            v.setStyleSheet(f'color:{col}')
            l = QtWidgets.QLabel(key)
            l.setObjectName('statLabel')
            box.addWidget(v)
            box.addWidget(l)
            row.addLayout(box)
            self.stat_vals[key] = (v, l)
        return row

    def _set_stat(self, key, value, label):
        v, l = self.stat_vals[key]
        v.setText(str(value))
        l.setText(label)

    def _reset_detail(self):
        self.file_name.setText('—')
        self.detail.setHtml(
            f'<span style="color:{DIM}">Kliknij kartę zdjęcia, żeby zobaczyć,<br>'
            'co dokładnie ujawnia i dlaczego to problem.</span>')

    # ── licencja ─────────────────────────────────────────────────────────────
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
                self.status.setText(f'poza okresem grace: {info}')
                self.status.setStyleSheet(f'color:{AMB}')
            elif ups:
                u = ups[0]
                self.status.setText(f'Reguły v{rv} · nowsze reguły v{u["version"]} '
                                    f'dostępne — ' + ' · '.join(n for n, _ in u['new'][:3]))
                self.status.setStyleSheet(f'color:{AMB}')
            else:
                self.status.setText(f'licencja aktywna · reguły v{rv}')
                self.status.setStyleSheet(f'color:{GRN}')
            return
        self._activate(info if st != 'brak' else 'Wklej klucz, który dostałeś mailem.')

    def _activate(self, message):
        d = QtWidgets.QDialog(self)
        d.setWindowTitle('photoscrub — aktywacja')
        d.setModal(True)
        d.setFixedWidth(520)
        v = QtWidgets.QVBoxLayout(d)
        v.setContentsMargins(28, 26, 28, 26)
        v.setSpacing(10)
        h = QtWidgets.QLabel('🔑')
        h.setStyleSheet('font-size:30px')
        v.addWidget(h)
        t = QtWidgets.QLabel('Klucz aktywacyjny')
        t.setStyleSheet(f'font-size:24px;font-weight:700;color:{FG}')
        v.addWidget(t)
        m = QtWidgets.QLabel(message)
        m.setStyleSheet(f'color:{DIM};font-size:13px')
        m.setWordWrap(True)
        v.addWidget(m)
        e = QtWidgets.QTextEdit()
        e.setPlaceholderText('PHOTOSCRUB-XXXXX-…')
        e.setFixedHeight(120)
        v.addWidget(e)
        row = QtWidgets.QHBoxLayout()
        paste = QtWidgets.QPushButton('Wklej ze schowka')
        paste.clicked.connect(lambda: e.insertPlainText(
            QtWidgets.QApplication.clipboard().text()))
        row.addWidget(paste)
        row.addStretch(1)
        ok = QtWidgets.QPushButton('Aktywuj')
        ok.setProperty('cta', True)
        row.addWidget(ok)
        v.addLayout(row)
        out = QtWidgets.QLabel('')
        out.setStyleSheet(f'color:{RED}')
        out.setWordWrap(True)
        v.addWidget(out)
        hint = QtWidgets.QLabel(f'twoja maszyna: {lic.machine_id()[:16]}')
        hint.setObjectName('hint')
        v.addWidget(hint)

        def go():
            good, msg = lic.activate(e.toPlainText().strip())
            if good:
                d.accept()
                QtCore.QTimer.singleShot(150, self._gate)
            else:
                out.setText(str(msg))
        ok.clicked.connect(go)
        d.exec()

    # ── wejście ──────────────────────────────────────────────────────────────
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        self.add_paths([u.toLocalFile() for u in e.mimeData().urls()])

    def add_files(self):
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Wybierz zdjęcia i filmy', '',
            'Zdjęcia i filmy (*.jpg *.jpeg *.png *.tif *.tiff *.webp *.heic *.heif '
            '*.avif *.gif *.bmp *.mp4 *.mov *.m4v);;Wszystkie pliki (*)')
        if paths:
            self.add_paths(paths)

    def add_folder(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, 'Wybierz folder ze zdjęciami')
        if d:
            self.add_paths([d])

    def add_paths(self, paths):
        allowed = ps.IMG_EXT | ps.VIDEO_EXT | {'.zip'}
        out = []
        for p in paths:
            if os.path.isdir(p):
                for dp, _, fs in os.walk(p):
                    for f in fs:
                        ext = os.path.splitext(f)[1].lower()
                        if ext in allowed or ext == '':
                            out.append(os.path.join(dp, f))
            else:
                out.append(p)
        seen, uniq = set(), []
        for p in out:
            if p not in seen:
                seen.add(p)
                uniq.append(p)
        if not uniq:
            return
        self.status.setText(f'Sprawdzam {len(uniq)} plików…')
        self.status.setStyleSheet(f'color:{DIM}')
        self.progress.show()
        self.progress.setValue(0)
        self._start(uniq)

    def _start(self, files):
        self._worker = ScanWorker(files, self.ruleset)
        self._thread = QtCore.QThread(self)
        self._worker.moveToThread(self._thread)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_done)
        self._thread.started.connect(self._worker.run)
        self._thread.start()

    def _on_progress(self, done, total):
        self.progress.setValue(int(done / max(1, total) * 100))
        self.status.setText(f'Sprawdzam… {done}/{total}')
        self.status.setStyleSheet(f'color:{DIM}')

    def _on_done(self, reps):
        self.progress.hide()
        self.status.setText('')
        self._worker = None
        if self._thread:
            self._thread.quit()
            self._thread = None
        self._fill(reps)

    # ── render ────────────────────────────────────────────────────────────────
    def resizeEvent(self, e):
        super().resizeEvent(e)
        # liczba kolumn zalezy od szerokosci okna wiec musi sie przeliczyc
        QtCore.QTimer.singleShot(60, self._recols)

    def _recols(self):
        if self.rows:
            sel = self.selected
            self._render()
            if sel:
                QtCore.QTimer.singleShot(40, lambda: self.show_detail(sel, keep_name=True))

    def _fill(self, reps):
        while self.grid.count():
            it = self.grid.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        self.rows = [(r, mdl.score(r)) for r in reps]
        self._render()

    def _render(self):
        while self.grid.count():
            it = self.grid.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        rows = self.rows
        dirty = [x for x in rows if x[0].findings]
        high = [x for x in rows if any(f.risk == 'HIGH' for f in x[0].findings)]
        clean = len(rows) - len(dirty)
        risks = [s['risk'] for _, s in rows if s]
        top = max(risks) if risks else 0

        if not rows:
            self.headline.setText('Upuść pliki, żeby zobaczyć co ujawniają')
            self.subline.setText('Paswywnie. Zero sieci, zero konta. '
                                 'Oryginały zostają tam, gdzie są.')
            self._set_stat('files', 0, 'plików')
            self._set_stat('dirty', 0, 'z danymi')
            self._set_stat('high', 0, 'pilne')
            self._set_stat('clean', 0, 'czyste')
            self._set_stat('risk', 0, 'ryzyko /100')
            self.stack.setCurrentWidget(self.drop)
            self.cta.setEnabled(False)
            self._reset_detail()
            return

        self.stack.setCurrentWidget(self.scroll)
        if dirty:
            self.headline.setText(f'{len(dirty)} plików ujawnia dane')
            self.headline.setStyleSheet(f'color:{FG}')
            self.subline.setText(f'Najgorszy przypadek: {top}/100 ryzyka publikacji. '
                                 f'Reguły v{self.ruleset} · zero skanowania, zero sieci')
        else:
            self.headline.setText('Te pliki są czyste')
            self.headline.setStyleSheet(f'color:{GRN}')
            self.subline.setText('Nic do usuwania.')
        self._set_stat('files', len(rows), 'plików')
        self._set_stat('dirty', len(dirty), 'z danymi')
        self._set_stat('high', len(high), 'pilne')
        self._set_stat('clean', clean, 'czyste')
        self._set_stat('risk', top, 'ryzyko /100')

        vw = self.scroll.viewport().width() or (self.width() - 460)
        cols = max(2, min(6, int(vw // 252)))
        for c in range(cols):
            self.grid.setColumnStretch(c, 1)
        for i, (r, s) in enumerate(rows):
            card = Card(r, self._thumb(r.path), *self._badge(s, r))
            card.setMinimumWidth(200)
            card.setMaximumWidth(320)
            card.clicked.connect(self.show_detail)
            card.entered.connect(self._hover)
            self.grid.addWidget(card, i // cols, i % cols, QtCore.Qt.AlignTop)
        self.cta.setEnabled(bool(dirty))
        if self.selected is None and rows:
            self.show_detail(rows[0][0])

    def _thumb(self, path):
        from PIL import Image
        try:
            im = Image.open(path)
            im.draft('RGB', (400, 240))
            im = im.convert('RGB')
            im.thumbnail((250, 150))
            data = im.tobytes('raw', 'RGB')
            qim = QtGui.QImage(data, im.width, im.height, im.width * 3,
                               QtGui.QImage.Format_RGB888)
            return QtGui.QPixmap.fromImage(qim.scaled(
                250, 150, QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation))
        except Exception:
            return None

    def _badge(self, s, rep=None):
        if rep is not None and rep.note:
            return rep.note, None
        if not s:
            return 'brak reguł', None
        short = {'bezpieczne': 'bezpieczne', 'tylko metadane': 'metadane',
                 'lokalizacja': 'LOKALIZACJA', 'tozsamosc': 'TOŻSAMOŚĆ'}
        return short.get(s['class'], s['class']), s['risk']

    def _hover(self, rep):
        if rep is not self.selected:
            self.show_detail(rep, keep_name=True)

    def show_detail(self, rep, keep_name=False):
        self.selected = rep
        s = mdl.score(rep)
        if not keep_name:
            self.file_name.setText(os.path.basename(rep.path))
        if not rep.findings:
            self.detail.setHtml(f'<span style="color:{GRN}">Czyste. Nic do usuwania.</span>')
            return
        head = ''
        if s:
            head = (f'<div style="color:{AMB};font-size:15px;font-weight:700;margin:10px 0 2px">'
                    f'RYZYKO {s["risk"]}/100</div>'
                    f'<div style="color:{DIM}">{s["class"]} · pewność '
                    f'{s["confidence"] * 100:.0f}%</div>')
        parts = [head, '<hr style="color:#243044">']
        for f in rep.findings:
            col = RED if f.risk == 'HIGH' else (AMB if f.risk == 'MED' else DIM)
            parts.append(
                f'<div style="margin-top:12px"><span style="color:{col};font-weight:700;'
                f'letter-spacing:1px">{f.risk}</span> '
                f'<span style="color:{FG};font-weight:600">{f.kind}</span></div>'
                f'<div style="color:{FG}">{f.value}</div>'
                + (f'<div style="color:{DIM};margin-top:2px">→ {f.why}</div>' if f.why else ''))
        if rep.note:
            parts.append(f'<div style="color:{DIM};margin-top:14px">({rep.note})</div>')
        self.detail.setHtml(''.join(parts))
        self.detail.verticalScrollBar().setValue(0)

    # ── czyszczenie ───────────────────────────────────────────────────────────
    def clean(self):
        dirty = [r for r, _ in self.rows if r.findings]
        if not dirty:
            return
        src = {os.path.realpath(os.path.dirname(r.path)) for r in dirty}
        default = None
        if len(src) == 1:
            d = src.pop()
            cand = os.path.join(os.path.dirname(d), 'photoscrub-wyczyszczone')
            try:
                os.makedirs(cand, exist_ok=True)
                default = cand
            except OSError:
                default = None
        if default is None:
            default = QtWidgets.QFileDialog.getExistingDirectory(
                self, 'Zapisz czyste kopie TUTAJ (inny folder niż zdjęcia)')
            if not default:
                return
        if os.path.realpath(default) in {os.path.realpath(os.path.dirname(r.path))
                                          for r in dirty}:
            self.toast.show_toast('Zatrzymane',
                                  'To jest ten sam folder ze zdjęciami. Wybierz inny — '
                                  'oryginały nigdy nie są nadpisywane.', 'err', 7000)
            return
        self.cta.setEnabled(False)
        self.status.setText('Usuwam…')
        self.status.setStyleSheet(f'color:{DIM}')
        CleanWorker(dirty, default, self.ruleset, self).run()

    def _cleaned(self, done, failed, out, freed):
        self.headline.setText('Gotowe')
        self.headline.setStyleSheet(f'color:{GRN}')
        self.subline.setText(f'Kopie w: {out} — oryginały nietknięte, '
                             f'oszczędność {human(freed)} metadanych')
        self.status.setText(f'{done} plików bez metadanych')
        self.status.setStyleSheet(f'color:{GRN}')
        self.rows = []
        self.selected = None
        self._render()
        self._reset_detail()
        self.subline.setText(f'Kopie w: {out} — oryginały nietknięte, '
                             f'oszczędność {human(freed)} metadanych')
        if failed:
            self.toast.show_toast(f'{done} oczyszczone, {len(failed)} pominięte',
                                  '\n'.join(failed[:4]), 'warn', 8000)
        else:
            self.toast.show_toast('Gotowe', f'{done} plików zapisanych w:\n{out}', 'ok')


class ScanWorker(QtCore.QObject):
    progress = QtCore.Signal(int, int)
    finished = QtCore.Signal(list)

    def __init__(self, files, ruleset):
        super().__init__()
        self.files = files
        self.ruleset = ruleset

    def run(self):
        reps = ps.scan_many(self.files, self.ruleset, workers=8,
                            progress=lambda d, t: self.progress.emit(d, t))
        self.finished.emit(reps)


class CleanWorker(QtCore.QThread):
    def __init__(self, dirty, out, ruleset, parent):
        super().__init__(parent)
        self.dirty = dirty
        self.out = out
        self.ruleset = ruleset

    def run(self):
        done, failed, freed = 0, [], 0
        for r in self.dirty:
            if r.kind == 'video':
                failed.append(f'{os.path.basename(r.path)} — wideo (reguły v'
                              f'{self.ruleset} nie czyścią wideo)')
                continue
            try:
                dst = ps.safe_dst(r.path, self.out)
                before = r.size
                ps.scrub_image(r.path, dst)
                done += 1
                freed += max(0, before - os.path.getsize(dst))
            except Exception as e:
                failed.append(f'{os.path.basename(r.path)}: {e}')
        self.parent()._cleaned(done, failed, self.out, freed)


def main():
    QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(
        QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('photoscrub')
    app.setOrganizationName('Hartwell Labs')
    app.setStyleSheet(QSS)
    w = Window()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()