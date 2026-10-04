#!/usr/bin/env python3
"""photoscrub — Qt6. Działa tak samo na Windows i Linux.

Dlaczego Qt a nie Tkinter: Tk nie ma warstwy układu (pack przydziela miejsce w
kolejności wywołań — stąd „okno dostaje 58 px i tekst zwija się do jednej litery")
i nie zna skali ekranu na Waylandzie (stąd „wszystko krzywe"). Qt ma oba rozwiązane
od samego początku, do tego prawdziwe style, własny drag&drop i poprawne skalowanie.
"""
import os
import re
import socket
import sys
import threading
import time

from PySide6 import QtCore, QtGui, QtWidgets

import license as lic
import model as mdl
import photoscrub as ps
import ruleset as rs
import theme as T

# Wszystkie wartosci ponizej pochodza z theme.py, a theme.py z realnych
# tokenow Radix Themes / Radix Colors / shadcn (dark). Zadne liczby "na oko".
_QSS_TEMPLATE = """
/* ── baza: Radix typography (base 14px = Text size 2) ── */
QWidget {{
    background:{bg};
    color:{fg};
    /* Jeden kroj w calej aplikacji. Microsoft: "use the default font for
       Windows apps, Segoe UI Variable"; na Linuksie Inter. */
    font-family:'Segoe UI Variable Display','Segoe UI','Inter','Noto Sans',
                 'DejaVu Sans',sans-serif;
    font-size:14px;
    line-height:20px;
}}
QWidget:disabled {{ color:{faint}; }}

/* QLabel musi byc przezroczysty. Regula QWidget background nadawala kazdej
   etykiecie kolor tla aplikacji, wiec w panelach (jasniejszych) kazda etykieta
   malowala ciemniejszy prostokat — wygladalo jak czarne pasy pod tekstem. */
QLabel {{ background:transparent; }}
QCheckBox, QRadioButton {{ background:transparent; }}

QMenuBar {{ background:transparent; color:{muted}; font-size:12px; }}
QMenuBar::item {{ padding:4px 8px; background:transparent; }}
QMenuBar::item:selected {{ background:{panel2}; color:{fg}; }}
QMenu {{ background:{popover}; color:{fg}; border:1px solid {line_strong}; }}
QMenu::item {{ padding:6px 12px; border-radius:{r_sm}px; }}
QMenu::item:selected {{ background:{panel2}; }}
QMenu::separator {{ height:1px; background:{line}; margin:4px 8px; }}

QToolTip {{
    background:{panel}; color:{fg};
    border:1px solid {line};
    border-radius:{r_md}px; padding:8px 10px;
}}

/* ── naglowek ── */
QLabel#brand {{ font-size:14px; font-weight:600; letter-spacing:-0.0025em; }}
QLabel#tagline {{ font-size:12px; color:{faint}; }}
QLabel#title {{ font-size:28px; font-weight:600; letter-spacing:-0.0075em; }}
QLabel#subtitle {{ font-size:14px; color:{muted}; }}
QLabel#panelLabel {{ font-size:12px; font-weight:500; color:{faint};
                    letter-spacing:0.0025em; }}
QLabel#fileName {{ font-size:14px; font-weight:600; }}
QLabel#fileMeta {{ font-size:12px; color:{faint}; }}

/* ── przyciski: shadcn Button (sm/md/lg x soft/ghost/solid) ── */
QPushButton {{
    background:{panel2}; color:{fg};
    border:1px solid {line}; border-radius:{r_md}px;
    padding:8px 12px; font-size:14px; font-weight:400;
    min-height:32px;
}}
QPushButton:hover {{ background:{panel3}; border-color:{line_strong}; }}
QPushButton:pressed {{ background:{panel2}; }}
QPushButton:focus {{ border-color:{ring}; background:{panel3}; }}
QPushButton:disabled {{ background:{panel}; color:{faint}; border-color:{line}; }}

/* ghost = bez wypelnienia, dla akcji drugorzednych (Hick: nie dawaj
   trzech rownych przyciskow na jeden ekran) */
QPushButton[variant="ghost"] {{
    background:transparent; border:1px solid transparent; color:{muted};
    padding:8px 12px;
}}
QPushButton[variant="ghost"]:hover {{ background:{panel2}; color:{fg}; }}

/* solid = jedyna akcja glowna na ekranie */
QPushButton[variant="solid"] {{
    background:{accent}; color:{accent_fg}; border:1px solid {accent};
    border-radius:{r_md}px; padding:10px 16px;
    font-size:14px; font-weight:600; min-height:40px;
}}
QPushButton[variant="solid"]:hover {{ background:{accent_hi}; border-color:{accent_hi}; }}
QPushButton[variant="solid"]:pressed {{ background:{accent}; }}
QPushButton[variant="solid"]:disabled {{
    background:{panel2}; color:{faint}; border-color:{line};
}}

/* ── pasek postepu (Doherty: informacja w <400ms) ── */
QProgressBar {{
    background:{panel2}; border:none; border-radius:{r1}px;
    height:4px; max-height:4px;
}}
QProgressBar::chunk {{ background:{accent}; border-radius:{r1}px; }}

/* ── karty plikow: Card z common region ── */
QFrame#card {{
    background:{panel}; border:1px solid {line};
    border-radius:{r_lg}px;
}}
QFrame#card:hover {{ border-color:{line_strong}; background:{panel2}; }}
QFrame#card[worst="true"] {{ border-color:{danger_line}; }}
QFrame#card[sel="true"] {{ border-color:{accent}; background:{accent_soft}; }}

QLabel#thumb {{ background:{thumb}; border-radius:{r_sm}px; }}
QLabel#cardName {{ font-size:12px; color:{fg}; }}
QLabel#cardBadge {{ font-size:12px; font-weight:600; }}
QLabel#cardRisk {{ font-size:12px; font-weight:600;
                   font-family:'Inter','DejaVu Sans Mono',monospace; }}
QLabel#worstTag {{
    font-size:12px; font-weight:600; color:{danger};
    background:{danger_soft}; border-radius:{r_full}px; padding:2px 8px;
}}

/* ── panel szczegolow ── */
QFrame#side {{
    background:{panel}; border:1px solid {line};
    border-radius:{r_xl}px;
}}
QTextBrowser#detail {{
    background:transparent; border:none;
    font-size:14px; color:{fg};
    selection-background-color:{accent_soft};
}}
QFrame#group {{
    background:{panel2}; border:1px solid {line};
    border-radius:{r_lg}px;
}}
QLabel#groupTitle {{ font-size:12px; font-weight:500; color:{muted}; }}
QLabel#groupKind {{ font-size:14px; font-weight:500; }}
QLabel#groupValue {{ font-size:12px; color:{muted}; }}
QLabel#empty {{ font-size:14px; color:{faint}; }}

/* ── strefa upuszczania ── */
QFrame#drop {{
    background:{bg}; border:1px dashed {line_strong};
    border-radius:{r_2xl}px;
}}
QFrame#drop[hot="true"] {{
    background:{accent_soft}; border:1px solid {accent};
}}
QLabel#dropTitle {{ font-size:20px; font-weight:600; letter-spacing:-0.005em; }}
QLabel#dropSub {{ font-size:14px; color:{muted}; }}
QLabel#dropHint {{ font-size:12px; color:{faint}; }}

/* ── szkielety podczas skanowania ── */
QFrame#skel {{ background:{panel}; border:1px solid {line};
              border-radius:{r_lg}px; }}
QFrame#skelBar {{ background:{panel2}; border-radius:{r_sm}px; }}

QAbstractScrollArea, QScrollArea, QWidget#gridHost {{ background:transparent; }}

/* ── pasek przewijania ── */
QScrollBar:vertical {{ background:transparent; width:8px; margin:0; }}
QScrollBar::handle:vertical {{ background:{line_strong}; border-radius:{r_full}px;
                               min-height:40px; }}
QScrollBar::handle:vertical:hover {{ background:{faint}; }}
QScrollBar:horizontal {{ background:transparent; height:8px; }}
QScrollBar::handle:horizontal {{ background:{line_strong};
                                 border-radius:{r_full}px; min-width:40px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background:none; }}
QScrollBar::handle {{ border:none; }}

/* ── toast ── */
QFrame#toast {{ background:{popover}; border:1px solid {line_strong};
               border-radius:{r_lg}px; }}
QLabel#toastTitle {{ font-size:14px; font-weight:600; }}
QLabel#toastBody {{ font-size:12px; color:{muted}; }}

/* ── dialog / pola ── */
QDialog {{ background:{bg}; }}
QTextEdit, QLineEdit {{
    background:{panel}; color:{fg};
    border:1px solid {line_strong}; border-radius:{r_md}px;
    padding:10px 12px; font-size:14px; selection-background-color:{accent};
}}
QTextEdit:focus, QLineEdit:focus {{ border-color:{ring}; }}
QLabel#hint {{ font-size:12px; color:{faint}; }}
QLabel#dlgTitle {{ font-size:24px; font-weight:600; letter-spacing:-0.00625em; }}
"""

CARD_W = 228   # stal szerokosc karty: kolumny liczone dokladnie, bez
               # zgadywania i bez obcinania prawej kolumny


def thumb_pixels(path, box=(224, 132)):
    """Zwraca surowe bajty RGB + rozmiar - bez QPixmap.

    QPixMap NIE WOLNO tworzyc poza watkiem GUI (Qt tego zabrania i miniatury
    wychodza puste). QImage juz moze. Decoding PIL-a robimy w watku roboczym,
    zeby nie mrozic interfejsu, a zamiane na pixmap zostawiamy GUI.
    """
    from PIL import Image
    try:
        im = Image.open(path)
        im.draft('RGB', (box[0] * 2, box[1] * 2))
        im = im.convert('RGB')
        im.thumbnail(box)
        return im.width, im.height, im.tobytes('raw', 'RGB')
    except Exception:
        return 0, 0, b''


def pixels_to_pixmap(w, h, data):
    """Robie w watku GUI - tu dopiero QPixmap jest dozwolony."""
    if not w or not h:
        return None
    qim = QtGui.QImage(data, w, h, w * 3, QtGui.QImage.Format_RGB888).copy()
    return QtGui.QPixmap.fromImage(qim)


def human(n):
    for u in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or u == 'GB':
            return f'{n:.0f} {u}' if u == 'B' else f'{n:.1f} {u}'
        n /= 1024.0


class Card(QtWidgets.QFrame):
    """Karta pliku — jeden element, jeden klik, jeden komunikat.

    Zasady, ktore tu stosuje:
      Fitts        — cala karta jest celem, nie tylko jej naglowek
      Von Restorff — najgorszy plik ma inny border (worst=true), reszta jest
                     neutralna; sam kolor NIE jest jedynym nośnikiem informacji,
                     bo kazda etykieta ma tekst
      Common region — nazwa + metadane w jednym zamknietym obszarze
    """

    def __init__(self, rep, thumb, label, risk, worst=False, selected=False):
        super().__init__()
        self.rep = rep
        self.setObjectName('card')
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.setAttribute(QtCore.Qt.WA_Hover, True)
        self.setProperty('worst', 'true' if worst else 'false')
        self.setProperty('sel', 'true' if selected else 'false')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        if not rep.findings:
            col = GRN
        elif any(f.risk == 'HIGH' for f in rep.findings):
            col = RED
        else:
            col = AMB

        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(8)

        thumb_box = QtWidgets.QVBoxLayout()
        thumb_box.setContentsMargins(0, 0, 0, 0)
        self.thumb = QtWidgets.QLabel()
        self.thumb.setObjectName('thumb')
        self.thumb.setFixedSize(CARD_W - 24, 132)
        self.thumb.setAlignment(QtCore.Qt.AlignCenter)
        if thumb is not None and not thumb.isNull():
            self.thumb.setPixmap(thumb.scaled(
                self.thumb.width() - 2, self.thumb.height() - 2,
                QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        thumb_box.addWidget(self.thumb)
        v.addLayout(thumb_box)

        # Nazwa pliku skracana do szerokosci karty. Bez tego dlugie nazwy
        # wychodza poza karty i rozjezdzaja kolumne ('poprzesuwane').
        nl = QtWidgets.QLabel()
        nl.setObjectName('cardName')
        nl.setToolTip(rep.path)
        nl.setText(QtGui.QFontMetrics(nl.font()).elidedText(
            os.path.basename(rep.path), QtCore.Qt.ElideMiddle, CARD_W - 24))
        v.addWidget(nl)

        row = QtWidgets.QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        b = QtWidgets.QLabel()
        b.setObjectName('cardBadge')
        b.setStyleSheet(f'color:{col};')
        # skracamy etykiete, nie pole rozciagajace - dlugi wyraz wypychal
        # liczbe ryzyka poza karty
        b.setText(QtGui.QFontMetrics(b.font()).elidedText(
            label, QtCore.Qt.ElideRight, CARD_W - 108))
        row.addWidget(b, 1)
        if worst:
            tag = QtWidgets.QLabel('NAJGORSZY')
            tag.setObjectName('worstTag')
            row.addWidget(tag, 0, QtCore.Qt.AlignRight)
        elif risk is not None:
            r = QtWidgets.QLabel(str(risk))
            r.setObjectName('cardRisk')
            r.setStyleSheet(f'color:{col};')
            row.addWidget(r, 0, QtCore.Qt.AlignRight)
        v.addLayout(row)

        for w in (self, self.thumb, nl):
            w.mousePressEvent = self._press

    def mark_selected(self, on):
        self.setProperty('sel', 'true' if on else 'false')
        self.style().unpolish(self)
        self.style().polish(self)

    def _press(self, _e=None):
        self.clicked.emit(self.rep)

    def contextMenuEvent(self, e):
        # GNOME: "Menu / Shift+F10 - Open context menu for focused location"
        m = QtWidgets.QMenu(self)
        a = m.addAction('Usun metadane z tego pliku')
        a.triggered.connect(lambda: self.clean_one.emit(self.rep))
        m.addSeparator()
        m.addAction('Pokaz sciezke').triggered.connect(
            lambda: QtWidgets.QApplication.clipboard().setText(self.rep.path))
        m.exec(e.globalPos())

    clean_one = QtCore.Signal(object)

    def keyPressEvent(self, e):
        # GNOME: "Return – Activate the focused control or content item".
        # Bez tego siatka kart byla calkowicie niedostepna z klawiatury.
        if e.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter,
                       QtCore.Qt.Key_Space):
            self.clicked.emit(self.rep)
            e.accept()
            return
        super().keyPressEvent(e)

    def focusInEvent(self, e):
        # widoczny fokus (WCAG / GNOME: nie polegaj tylko na kolorze)
        self.setStyleSheet(f'QFrame#card {{ border: 2px solid {ACC};'
                           f' border-radius:{T.RADIUS_LG}px; }}')
        super().focusInEvent(e)

    def focusOutEvent(self, e):
        self.setStyleSheet('')
        super().focusOutEvent(e)

    clicked = QtCore.Signal(object)


class DropZone(QtWidgets.QFrame):
    """Glowna sciezka (Hick: jedna oczywista akcja na ekranie)."""

    clicked = QtCore.Signal()
    files = QtCore.Signal(list)

    def __init__(self):
        super().__init__()
        self.setObjectName('drop')
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.setAcceptDrops(True)
        self.setMinimumHeight(260)

        v = QtWidgets.QVBoxLayout(self)
        v.setAlignment(QtCore.Qt.AlignCenter)
        v.setSpacing(8)

        ico = QtWidgets.QLabel()
        ico.setPixmap(self._icon())
        ico.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(ico)
        v.addSpacing(8)

        t = QtWidgets.QLabel('Upuść zdjęcia lub filmy')
        t.setObjectName('dropTitle')
        t.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(t)

        s = QtWidgets.QLabel('albo kliknij, żeby wybrać pliki')
        s.setObjectName('dropSub')
        s.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(s)
        v.addSpacing(4)

        h = QtWidgets.QLabel('JPG · PNG · TIFF · WEBP · HEIC · AVIF · GIF · MP4')
        h.setObjectName('dropHint')
        h.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(h)

    @staticmethod
    def _icon():
        pm = QtGui.QPixmap(96, 80)
        pm.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor(FG2), 2)
        box = QtGui.QPen(QtGui.QColor(FG2), 2)
        # stos zdjec — dwa obrysy pod spodem, jeden na wierzchu
        for dx, dy in ((10, 14), (6, 7)):
            p.setPen(box)
            p.setBrush(QtGui.QBrush(QtGui.QColor(BG)))
            p.drawRoundedRect(dx, dy, 64, 48, 8, 8)
        p.setBrush(QtGui.QBrush(QtGui.QColor(PANEL2)))
        p.setPen(pen)
        p.drawRoundedRect(2, 0, 64, 48, 8, 8)
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QBrush(QtGui.QColor(ACC)))
        p.drawPolygon(QtGui.QPolygon([
            QtCore.QPoint(6, 42), QtCore.QPoint(24, 20), QtCore.QPoint(36, 34),
            QtCore.QPoint(46, 22), QtCore.QPoint(62, 42)]))
        p.setBrush(QtGui.QBrush(QtGui.QColor(WARN)))
        p.drawEllipse(48, 8, 9, 9)
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
    """Potwierdzenie akcji. Peak-End Rule: koniec musi byc spokojny i jasny."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('toast')
        # pusty layout tworzony RAZ. Wczesniej kazde show_toast() robilo
        # nowy QHBoxLayout(self) na widgete, ktory juz layout mial — Qt
        # krzyczal "already has a layout" i drugi layout byl mieszany.
        self._lay = QtWidgets.QHBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 16, 0)
        self._bar = QtWidgets.QFrame()
        self._bar.setFixedWidth(3)
        self._lay.addWidget(self._bar)
        self._box = QtWidgets.QVBoxLayout()
        self._box.setContentsMargins(16, 12, 0, 12)
        self._box.setSpacing(2)
        self._lay.addLayout(self._box, 1)
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self.hide()

    def show_toast(self, title, body='', kind='info', ms=4600):
        while self._box.count():
            it = self._box.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        col = {'info': ACC, 'ok': GRN, 'warn': AMB, 'err': RED}[kind]
        self._bar.setStyleSheet(f'background:{col}; border-radius:2px;')
        t = QtWidgets.QLabel(title)
        t.setObjectName('toastTitle')
        self._box.addWidget(t)
        if body:
            b = QtWidgets.QLabel(body)
            b.setObjectName('toastBody')
            b.setWordWrap(True)
            self._box.addWidget(b)
        self.adjustSize()
        self.show()
        self.raise_()
        self._timer.start(ms)


def skeleton_grid(host, cols, rows):
    """Szkielety podczas skanowania (Doherty: 400 ms na informacje zwrotne).

    Uzytkownik widzi strukture bez czekania na pierwszy wynik.
    """
    while host.count():
        it = host.takeAt(0)
        if it.widget():
            it.widget().deleteLater()
    for i in range(cols * rows):
        f = QtWidgets.QFrame()
        f.setObjectName('skel')
        f.setFixedSize(CARD_W, 212)
        v = QtWidgets.QVBoxLayout(f)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(10)
        bar = QtWidgets.QFrame()
        bar.setObjectName('skelBar')
        bar.setFixedHeight(132)
        v.addWidget(bar)
        for hgt in (11, 11):
            ln = QtWidgets.QFrame()
            ln.setObjectName('skelBar')
            ln.setFixedHeight(hgt)
            ln.setFixedWidth(CARD_W - 60 if hgt == 11 and ln is not None else 0 or 120)
            v.addWidget(ln)
        host.addWidget(f, i // cols, i % cols)


def findings_groups(rep):
    """Grupuje znaleziska w kategorie (Miller: chunking, nie sciana tekstu).

    Kolejnosc = od najwazniejszego: lokalizacja, tozsamosc, sprzet, prawa,
    czas, reszta. Zwraca [(kategoria, [finding, ...]), ...].
    """
    buckets = {}
    order = []
    for f in rep.findings:
        key = f.kind.lower()
        bucket = ('lokalizacja' if 'gps' in key or 'lokal' in key else
                  'tozsamosc' if any(w in key for w in
                                     ('copyright', 'author', 'owner', 'serial',
                                      'credit', 'tozsam')) else
                  'sprzet' if any(w in key for w in
                                  ('software', 'model', 'make', 'lens', 'device',
                                   'body', 'camera')) else
                  'czas' if 'date' in key or 'time' in key else
                  'tekst' if any(w in key for w in
                                 ('comment', 'description', 'title',
                                  'caption')) else 'inne')
        if bucket not in buckets:
            buckets[bucket] = []
            order.append(bucket)
        buckets[bucket].append(f)
    rank = ['lokalizacja', 'tozsamosc', 'sprzet', 'prawa', 'czas', 'tekst',
            'inne']
    order.sort(key=lambda k: rank.index(k) if k in rank else 99)
    return [(k, buckets[k]) for k in order]


class _ScrollFilter(QtCore.QObject):
    """Filtr zdarzen kola myszy i gestow touchpada.

    Trzyma sie zasady: przewijamy strone kart tym samym filtrem, niezaleznie
    od tego, gdzie jest kursor (karta, panel, tlo). Skoki sa krotkie
    (1 kolko = ~1/3 strony), zeby nie przewijac na wylot.
    """

    def __init__(self, win):
        super().__init__(win)
        self.win = win

    def eventFilter(self, obj, ev):
        if ev.type() != QtCore.QEvent.Wheel:
            return False
        if self.win.stack.currentWidget() is not self.win.scroll:
            return False      # na ekranie startowym scroll niepotrzebny
        bar = self.win.scroll.verticalScrollBar()
        if bar.maximum() <= 0:
            return True      # nic do przewijania — zdarzenie zjedzone

        delta = 0
        if ev.angleDelta().y():
            delta = ev.angleDelta().y()
        elif ev.pixelDelta().y():
            # gest touchpada: 1 "krok" ~ 40 px, minimum 12 px zeby
            # plynny, minimalny ruch nie byl niewidoczny
            delta = ev.pixelDelta().y() * 120 / 40
        if delta == 0:
            return True

        bar.setValue(bar.value() - int(delta))
        ev.accept()
        return True


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('photoscrub')
        # GNOME: "smallest recommended display size for GNOME on desktop is
        # currently 1024x600px, and this size should be supported by all apps".
        self.resize(1280, 860)
        self.setMinimumSize(T.MIN_WINDOW_W, T.MIN_WINDOW_H)
        self.setAcceptDrops(True)
        self.rows = []
        self._thumbs = {}
        self.selected = None
        self.ruleset = rs.CURRENT
        self._clean_abort = False
        self._cleaner = None
        self._cancel = None
        self._phone_srv = None
        self._phone_dir = None
        self._cards = {}
        self._last_w = self.width()
        self._recol_busy = False

        c = QtWidgets.QWidget()
        self.setCentralWidget(c)
        root = QtWidgets.QVBoxLayout(c)
        root.setContentsMargins(24, 20, 24, 20)   # wielokrotnosci 4
        root.setSpacing(0)

        root.addLayout(self._header())
        root.addSpacing(24)

        self.title = QtWidgets.QLabel('Zobacz, co Twoje zdjęcia zdradzają')
        self.title.setObjectName('title')
        root.addWidget(self.title)
        self.subtitle = QtWidgets.QLabel(
            'Paswywnie i offline. Oryginały zostają tam, gdzie są.')
        self.subtitle.setObjectName('subtitle')
        root.addWidget(self.subtitle)
        root.addSpacing(24)

        self.stats = self._stats()
        root.addLayout(self.stats)
        root.addSpacing(16)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setFixedHeight(4)
        self.progress.hide()
        root.addWidget(self.progress)
        root.addSpacing(16)

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
        self.grid_host = QtWidgets.QWidget()
        self.grid = QtWidgets.QGridLayout(self.grid_host)
        self.grid.setSpacing(16)
        self.grid.setContentsMargins(0, 0, 8, 0)
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
        # GNOME adaptive: "sidebars should never look excessively wide or
        # narrow in relation to the main window area" — panel jest staly, ale
        # przy bardzo waskim oknie ustępuje miejsca siatce kart.
        self.side.setFixedWidth(T.SIDE_W)
        self.side.setMinimumWidth(280)
        self.side.setMaximumWidth(T.SIDE_W)
        sv = QtWidgets.QVBoxLayout(self.side)
        sv.setContentsMargins(20, 20, 20, 20)
        sv.setSpacing(8)

        lbl = QtWidgets.QLabel('SZCZEGÓŁY')
        lbl.setObjectName('panelLabel')
        sv.addWidget(lbl)
        sv.addSpacing(4)

        self.file_name = QtWidgets.QLabel('—')
        self.file_name.setObjectName('fileName')
        self.file_name.setWordWrap(True)
        sv.addWidget(self.file_name)
        self.file_meta = QtWidgets.QLabel('')
        self.file_meta.setObjectName('fileMeta')
        sv.addWidget(self.file_meta)
        sv.addSpacing(8)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setStyleSheet(f'color:{LINE}; background:{LINE};'
                          f' max-height:1px; min-height:1px; border:none;')
        sv.addWidget(sep)
        sv.addSpacing(8)

        self.detail = QtWidgets.QTextBrowser()
        self.detail.setObjectName('detail')
        self.detail.setOpenExternalLinks(False)
        sv.addWidget(self.detail, 1)

        # Jak to dziala jest informacja drugorzedna (Hick) - schowana pod
        # jednym przyciskiem zamiast zajmowac 1/3 panelu na ekranie.
        more = QtWidgets.QPushButton('Jak to działa')
        more.setProperty('variant', 'ghost')
        more.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        more.clicked.connect(self._about)
        sv.addWidget(more)
        body.addWidget(self.side)

        foot = QtWidgets.QHBoxLayout()
        foot.setSpacing(16)
        self.foot_extra = QtWidgets.QHBoxLayout()
        self.foot_extra.setSpacing(8)
        foot.addLayout(self.foot_extra)
        self.cta = QtWidgets.QPushButton('Usuń metadane')
        self.cta.setProperty('variant', 'solid')
        self.cta.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.cta.setEnabled(False)
        self.cta.clicked.connect(self.clean)
        foot.addWidget(self.cta)
        self.status = QtWidgets.QLabel('')
        self.status.setObjectName('subtitle')
        foot.addWidget(self.status, 1)
        self.count = QtWidgets.QLabel('')
        self.count.setObjectName('panelLabel')
        foot.addWidget(self.count)
        root.addSpacing(16)
        root.addLayout(foot)

        self.toast = Toast(c)
        self.toast.setFixedWidth(600)

        self._reset_detail()
        self._worker = None
        self._thread = None
        self._build_menu()
        # Pasek menu ma byc niewidoczny — aplikacja nie ma pliku, a skroty
        # i tak sa w menu kontekstowym oraz w tooltipach.
        self.menuBar().setVisible(False)
        self._install_scroll_filter()
        QtCore.QTimer.singleShot(120, self._gate)

    # ── naglowek ──────────────────────────────────────────────────────────────
    def _header(self):
        h = QtWidgets.QHBoxLayout()
        h.setSpacing(12)
        logo = QtWidgets.QLabel()
        pm = QtGui.QPixmap(28, 28)
        pm.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(QtGui.QPen(QtGui.QColor(ACC), 2))
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawEllipse(2, 2, 24, 24)
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QBrush(QtGui.QColor(ACC)))
        p.drawEllipse(10, 10, 8, 8)
        p.end()
        logo.setPixmap(pm)
        h.addWidget(logo)

        names = QtWidgets.QVBoxLayout()
        names.setSpacing(0)
        n = QtWidgets.QLabel('photoscrub')
        n.setObjectName('brand')
        names.addWidget(n)
        tg = QtWidgets.QLabel('zanim wrzucisz to do sieci')
        tg.setObjectName('tagline')
        names.addWidget(tg)
        h.addLayout(names)
        h.addStretch(1)

        for text, slot, key in (('Wybierz folder', self.add_folder,
                                 'Ctrl+Shift+D'),
                                ('Dodaj pliki', self.add_files, 'Ctrl+O')):
            b = QtWidgets.QPushButton(text)
            b.setProperty('variant', 'ghost')
            b.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            b.clicked.connect(slot)
            # skrot widoczny w tooltip - inaczej nikt o nim nie wie
            b.setToolTip(f'{text} ({key})')
            h.addWidget(b)
        h.addSpacing(4)
        self._theme_name = 'dark'
        self._theme_btn = QtWidgets.QPushButton()
        self._theme_btn.setProperty('variant', 'ghost')
        self._theme_btn.setFixedWidth(36)
        self._theme_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self._theme_btn.setToolTip('Jasny / ciemny motyw (Ctrl+T)')
        self._theme_btn.clicked.connect(self.toggle_theme)
        h.addWidget(self._theme_btn)
        self._paint_theme_icon()

        phone = QtWidgets.QPushButton('Z telefonu')
        phone.setProperty('variant', 'ghost')
        phone.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        phone.setToolTip('Wyslij zdjecia z iPhone albo Androida (Ctrl+M)')
        phone.clicked.connect(self._from_phone)
        h.addWidget(phone)
        about = QtWidgets.QPushButton('?')
        about.setProperty('variant', 'ghost')
        about.setFixedWidth(32)
        about.setToolTip('Jak to działa')
        about.clicked.connect(self._about)
        h.addWidget(about)
        return h

    # ── scroll: gesty touchpada + kolo myszy ──────────────────────────────
    def _install_scroll_filter(self):
        """Poprawne przewijanie dla myszy I touchpada.

        Problem: Qt wysyla gesty touchpada jako pixelDelta (dokladne
        przesuniecie w pikselach), a QScrollArea reaguje glownie na
        angleDelta. Na Waylandzie przez XWayland dwa palce potrafily dawac
        "zero reakcji" albo przeskakiwane o pelna strone. Ten filtr
        sprowadza oba rodzaje zdarzen do jednej sciezki i przyciemnione
        strony, zeby przewijalo sie plynnie.
        """
        self._scroll_filter = _ScrollFilter(self)
        self.installEventFilter(self._scroll_filter)

        # ten sam filtr na scroll area i jego viewport — kolo musi dzialac
        # takze wtedy, gdy kursor jest na karcie, a nie na tle
        for wid in (self.scroll, self.scroll.viewport()):
            wid.installEventFilter(self._scroll_filter)
        self.scroll.verticalScrollBar().installEventFilter(self._scroll_filter)
        self.scroll.horizontalScrollBar().installEventFilter(self._scroll_filter)

        # krótsze skoki (3 linie zamiast 3*? domyslnej) + pełna strona
        sb = self.scroll.verticalScrollBar()
        sb.setSingleStep(24)
        sb.setPageStep(max(120, self.scroll.viewport().height() - 24))
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    # ── menu glowne (F10) + skroty (GNOME guidelines/keyboard) ────────────
    def _build_menu(self):
        # GNOME: "F10 - Open primary or secondary menu". Uzytkownik musi
        # miec jeden place, gdzie widzi WSZYSTKIE akcje i ich skroty.
        m = self.menuBar()
        # pasek jest wlasciwie niewidoczny (tlo = tlo aplikacji, brak ramek),
        # a jego rola to F10 + skroty. GNOME: "F10 - open primary menu".
        m.setNativeMenuBar(False)
        f = m.addMenu('&Plik')
        a = f.addAction('Dodaj pliki...', self.add_files)
        a.setShortcut('Ctrl+O')
        a = f.addAction('Wybierz folder...', self.add_folder)
        a.setShortcut('Ctrl+Shift+D')
        f.addSeparator()
        f.addAction('Zamknij', self.close).setShortcut('Ctrl+Q')
        sm = m.addMenu('&Akcje')
        a = sm.addAction('Skanuj ponownie',
                         lambda: self.add_paths([r.path for r, _ in self.rows]))
        a.setShortcut('Ctrl+R')
        a = sm.addAction('Usun metadane', self.clean)
        a.setShortcut('Ctrl+E')
        sm.addSeparator()
        sm.addAction('Zdjecia z telefonu', self._from_phone).setShortcut('Ctrl+M')
        sm.addAction('Przelacz motyw', self.toggle_theme).setShortcut('Ctrl+T')
        sm.addAction('Jak to dziala', self._about).setShortcut('F1')
        return m

    def keyPressEvent(self, e):
        # GNOME: "Esc - Close the current container, if it is transient".
        if e.key() == QtCore.Qt.Key_Escape:
            if self.selected is not None and len(self.rows) > 1:
                self.show_detail(self.rows[0][0])
            else:
                self.close()
            e.accept()
            return
        super().keyPressEvent(e)

    # ── statystyki (chunking: 5 liczb, nie 12) ───────────────────────────────
    def _stats(self):
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(32)
        self.stat_vals = {}
        tiles = (('files', 'plików', DIM), ('dirty', 'z danymi', RED),
                 ('high', 'pilne', RED), ('clean', 'czyste', GRN),
                 ('risk', 'ryzyko /100', AMB))
        for key, label, col in tiles:
            box = QtWidgets.QVBoxLayout()
            box.setSpacing(0)
            v = QtWidgets.QLabel('0')
            v.setObjectName('title')
            v.setStyleSheet(f'color:{col}; font-size:24px; font-weight:600;'
                            f' letter-spacing:-0.00625em;')
            l = QtWidgets.QLabel(label)
            l.setObjectName('panelLabel')
            box.addWidget(v)
            box.addWidget(l)
            holder = QtWidgets.QWidget()
            holder.setFixedWidth(132)
            holder.setLayout(box)
            row.addWidget(holder)
            self.stat_vals[key] = (v, l)
        row.addStretch(1)
        return row

    def _set_stat(self, key, value, label=None):
        v, l = self.stat_vals[key]
        v.setText(str(value))
        if label:
            l.setText(label)

    def _reset_detail(self):
        self.file_name.setText('—')
        self.file_meta.setText('')
        self.detail.setHtml(
            f'<p style="color:{FAINT}">Kliknij kartę zdjęcia, żeby zobaczyć, '
            'co dokładnie ujawnia i dlaczego to problem.</p>')

    def _about(self):
        d = QtWidgets.QDialog(self)
        d.setWindowTitle('Jak to działa')
        d.setModal(True)
        d.setFixedWidth(560)
        v = QtWidgets.QVBoxLayout(d)
        v.setContentsMargins(28, 28, 28, 28)
        v.setSpacing(12)
        t = QtWidgets.QLabel('Jak to działa')
        t.setObjectName('dlgTitle')
        v.addWidget(t)
        b = QtWidgets.QTextBrowser()
        b.setObjectName('detail')
        b.setHtml(
            f'<p>photoscrub czyta <b>bajty pliku</b> i <b>DNS</b> — nic więcej. '
            'Nie ma skanowania, nie ma konta, nie ma połączenia z serwerem.</p>'
            f'<p>Oryginałów nigdy nie modyfikujemy. Zapisujemy czyste kopie '
            'w innym folderze.</p>'
            f'<p>Najbardziej podstępny wyciek to miniaturka wbudowana w JPEG — '
            'często jest w niej całe oryginalne zdjęcie, w rozdzielczości pełnej.</p>'
            f'<p>Wynik ryzyka (0–100) liczy nasz własny model: 15 cech pliku, '
            'klasyfikator logistyczny wytrenowany na 8000 syntetycznych '
            'profilach. To nie jest model językowy — nie zmyśla, liczy.</p>')
        v.addWidget(b, 1)
        ok = QtWidgets.QPushButton('Rozumiem')
        ok.setProperty('variant', 'solid')
        ok.clicked.connect(d.accept)
        v.addWidget(ok)
        d.exec()

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
                self.status.setText(
                    f'Reguły v{rv} · nowsze reguły v{u["version"]} dostępne — '
                    + ' · '.join(n for n, _ in u['new'][:3]))
                self.status.setStyleSheet(f'color:{AMB}')
            else:
                self.status.setText(f'licencja aktywna · reguły v{rv}')
                self.status.setStyleSheet(f'color:{GRN}')
            return
        self._activate(info if st != 'brak' else 'Wklej klucz, który dostałeś '
                                               'mailem.')

    def _activate(self, message):
        d = QtWidgets.QDialog(self)
        d.setWindowTitle('photoscrub — aktywacja')
        d.setModal(True)
        d.setFixedWidth(560)
        v = QtWidgets.QVBoxLayout(d)
        v.setContentsMargins(28, 28, 28, 28)
        v.setSpacing(12)
        t = QtWidgets.QLabel('Klucz aktywacyjny')
        t.setObjectName('dlgTitle')
        v.addWidget(t)
        m = QtWidgets.QLabel(message)
        m.setObjectName('subtitle')
        m.setWordWrap(True)
        v.addWidget(m)
        e = QtWidgets.QTextEdit()
        e.setPlaceholderText('PHOTOSCRUB-XXXXX-…')
        e.setFixedHeight(120)
        v.addWidget(e)
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(8)
        paste = QtWidgets.QPushButton('Wklej ze schowka')
        paste.clicked.connect(lambda: e.insertPlainText(
            QtWidgets.QApplication.clipboard().text()))
        row.addWidget(paste)
        row.addStretch(1)
        ok = QtWidgets.QPushButton('Aktywuj')
        ok.setProperty('variant', 'solid')
        row.addWidget(ok)
        v.addLayout(row)
        out = QtWidgets.QLabel('')
        out.setStyleSheet(f'color:{RED};')
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

    # ── wejscie ──────────────────────────────────────────────────────────────
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        self.add_paths([u.toLocalFile() for u in e.mimeData().urls()])

    def add_files(self):
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Wybierz zdjęcia i filmy', '',
            'Zdjęcia i filmy (*.jpg *.jpeg *.png *.tif *.tiff *.webp *.heic '
            '*.heif *.avif *.gif *.bmp *.mp4 *.mov *.m4v);;Wszystkie pliki (*)')
        if paths:
            self.add_paths(paths)

    def add_folder(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Wybierz folder ze zdjęciami')
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
        self.rows = []
        self._thumbs = {}
        self.selected = None
        self.cta.setEnabled(False)
        self.status.setText(f'Sprawdzam {len(uniq)} plików…')
        self.status.setStyleSheet(f'color:{DIM}')
        self.progress.show()
        self.progress.setValue(0)
        self.stack.setCurrentWidget(self.scroll)
        skeleton_grid(self.grid, max(2, (self.scroll.viewport().width() or 700)
                                     // (CARD_W + 16)), 2)
        self._reset_detail()
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

    def _on_done(self, reps, thumbs):
        self.progress.hide()
        self._worker = None
        if self._thread:
            self._thread.quit()
            self._thread = None
        self._fill(reps, thumbs)

    # ── render ────────────────────────────────────────────────────────────────
    def resizeEvent(self, e):
        super().resizeEvent(e)
        # UWAGA: resize → przelicz kolumny → render → zmiana rozmiaru layoutu →
        # resize → … To byla petla, ktora wieszala aplikacje i przesuwala karty.
        w = self.width()
        if abs(w - self._last_w) < 80 or self._recol_busy or not self.rows:
            return
        self._last_w = w
        self._recol_busy = True
        QtCore.QTimer.singleShot(120, self._recols)

    def _recols(self):
        try:
            sel = self.selected
            self._render()
            if sel:
                QtCore.QTimer.singleShot(30,
                                         lambda: self.show_detail(sel, True))
        finally:
            self._recol_busy = False

    def _fill(self, reps, thumbs=None):
        self._thumbs = {}
        for r, t in zip(reps, thumbs or []):
            if isinstance(t, tuple) and len(t) == 3:
                self._thumbs[r.path] = pixels_to_pixmap(*t)
        # Porzadek: najgorliwsze pliki na gorze (progressive disclosure).
        scored = [(r, mdl.score(r)) for r in reps]
        scored.sort(key=lambda x: (-(x[1]['risk'] if x[1] else -1),
                                   -len(x[0].findings), x[0].path))
        self.rows = scored
        self._render()
        if self.rows:
            worst = self.rows[0][0]
            self.show_detail(worst)
            card = self._cards.get(worst.path)
            if card:
                card.mark_selected(True)
        else:
            self.status.setText('')
            self.stack.setCurrentWidget(self.drop)

    def _render(self):
        while self.grid.count():
            it = self.grid.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        self._cards = {}
        rows = self.rows
        if not rows:
            self.title.setText('Zobacz, co Twoje zdjęcia zdradzają')
            self.title.setStyleSheet(f'color:{FG}')
            self.subtitle.setText('Paswywnie i offline. Oryginały zostają tam, '
                                  'gdzie są.')
            for k in self.stat_vals:
                self._set_stat(k, 0)
            self.cta.setEnabled(False)
            self.count.setText('')
            self.stack.setCurrentWidget(self.drop)
            return

        dirty = [x for x in rows if x[0].findings]
        high = [x for x in rows if any(f.risk == 'HIGH' for f in x[0].findings)]
        clean = len(rows) - len(dirty)
        risks = [s['risk'] for _, s in rows if s]
        top = max(risks) if risks else 0

        self.stack.setCurrentWidget(self.scroll)
        if dirty:
            self.title.setText(f'{len(dirty)} z {len(rows)} plików ujawnia dane')
            self.title.setStyleSheet(f'color:{FG}')
            self.subtitle.setText(
                f'Najwyższe ryzyko publikacji: {top}/100. Reguły v'
                f'{self.ruleset} · zero skanowania, zero sieci.')
        else:
            self.title.setText('Te pliki są czyste')
            self.title.setStyleSheet(f'color:{GRN}')
            self.subtitle.setText('Nic do usuwania — możesz je wrzucać na '
                                  'serwer.')
        self._set_stat('files', len(rows))
        self._set_stat('dirty', len(dirty))
        self._set_stat('high', len(high))
        self._set_stat('clean', clean)
        self._set_stat('risk', top)
        self.count.setText(f'{len(rows)} plików')
        self.status.setText('')

        vw = self.scroll.viewport().width() or (self.width() - 480)
        gap = 16
        # ile kolumn REALNIE sie zmiesci — nie "na oko", tylko dzielenie
        cols = max(2, min(6, int((vw + gap) // (CARD_W + gap))))
        self._cols = cols
        # grid_host dostaje dokladnie tyle szerokosci, ile zajmuja karty +
        # odstepy. Bez tego ostatnia kolumna wychodziza za viewport i jest
        # obcinana ("poprzesuwane").
        self.grid_host.setFixedWidth(cols * CARD_W + (cols - 1) * gap)
        for c in range(cols):
            self.grid.setColumnStretch(c, 0)
            self.grid.setColumnMinimumWidth(c, 0)

        worst_path = rows[0][0].path if rows[0][0].findings else None
        for i, (r, s) in enumerate(rows):
            card = Card(r, self._thumbs.get(r.path), *self._badge(s, r),
                        worst=(r.path == worst_path))
            card.setFixedWidth(CARD_W)
            card.clicked.connect(self.show_detail)
            card.clean_one.connect(self._clean_one)
            # Filtr scrolla musi byc na karcie OD RAZU. Wczesniej instalo-
            # walismy go przed utworzeniem kart (po wyczyszczeniu slownika),
            # wiec na zadna nie trafial i gest nad karta nic nie robil.
            card.installEventFilter(self._scroll_filter)
            self.grid.addWidget(card, i // cols, i % cols)
            self._cards[r.path] = card
        self.cta.setEnabled(bool(dirty))

    def _badge(self, s, rep=None):
        if rep is not None and rep.note:
            return rep.note, None
        if not s:
            return 'brak reguł', None
        short = {'bezpieczne': 'bezpieczne', 'tylko metadane': 'metadane',
                 'lokalizacja': 'LOKALIZACJA', 'tozsamosc': 'TOŻSAMOŚĆ'}
        return short.get(s['class'], s['class']), s['risk']

    def show_detail(self, rep, keep_name=False):
        prev = self._cards.get(self.selected.path) if self.selected else None
        if prev:
            prev.mark_selected(False)
        self.selected = rep
        card = self._cards.get(rep.path)
        if card:
            card.mark_selected(True)

        s = mdl.score(rep)
        self.file_name.setText(os.path.basename(rep.path))
        self.file_meta.setText(
            f'{human(os.path.getsize(rep.path))} · {os.path.dirname(rep.path)}')
        if not rep.findings:
            self.detail.setHtml(
                f'<p style="color:{GRN}">Czyste. Nic do usuwania.</p>')
            return

        head = ''
        if s:
            head = (f'<p style="color:{AMB};font-size:20px;font-weight:600;'
                    f'margin:0 0 2px 0">RYZYKO {s["risk"]}/100</p>'
                    f'<p style="color:{DIM};margin:0">{s["class"]} · '
                    f'pewność {s["confidence"] * 100:.0f}%</p>')
        parts = [head]
        for cat, items in findings_groups(rep):
            col = {'lokalizacja': RED, 'tozsamosc': RED, 'sprzet': AMB,
                   'czas': DIM, 'tekst': DIM}.get(cat, DIM)
            parts.append(
                f'<p style="color:{col};font-size:12px;font-weight:500;'
                f'margin:16px 0 4px 0">{cat.upper()}</p>')
            for f in items:
                fc = RED if f.risk == 'HIGH' else (AMB if f.risk == 'MED'
                                                    else DIM)
                parts.append(
                    f'<p style="margin:0"><span style="color:{fc};'
                    f'font-weight:500">{f.kind}</span> '
                    f'<span style="color:{FG}">{f.value}</span>'
                    + (f'<br><span style="color:{FAINT}">{f.why}</span>'
                       if f.why else '') + '</p>')
        if rep.note:
            parts.append(f'<p style="color:{FAINT};margin-top:16px">'
                         f'({rep.note})</p>')
        self.detail.setHtml(''.join(parts))
        self.detail.verticalScrollBar().setValue(0)

    # ── motyw jasny / ciemny ────────────────────────────────────────────────
    def _paint_theme_icon(self):
        """Ikona przelacznika: ksiezyc (gdy teraz ciemny) / slonce."""
        import math
        pm = QtGui.QPixmap(20, 20)
        pm.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        c = QtGui.QColor(FG2)
        p.setPen(QtGui.QPen(c, 1.6))
        if self._theme_name == 'dark':
            # pelny ksiegzyc + cien wypelniajacy fzyg
            p.setBrush(QtCore.Qt.NoBrush)
            p.drawEllipse(5, 5, 11, 11)
            p.setBrush(QtGui.QBrush(c))
            p.drawEllipse(2, 2, 11, 11)
        else:
            # slonec: dysk + promienie
            p.setBrush(QtGui.QBrush(c))
            p.drawEllipse(6, 6, 8, 8)
            p.setBrush(QtCore.Qt.NoBrush)
            for a in range(0, 360, 45):
                rad = math.radians(a)
                p.drawLine(QtCore.QPointF(10 + 8.0 * math.cos(rad),
                                          10 + 8.0 * math.sin(rad)),
                           QtCore.QPointF(10 + 10.5 * math.cos(rad),
                                          10 + 10.5 * math.sin(rad)))
        p.end()
        self._theme_btn.setIcon(QtGui.QIcon(pm))
        self._theme_btn.setText('')

    def toggle_theme(self):
        global QSS, TOKENS, BG, PANEL, PANEL2, PANEL3, LINE, FG, FG2, DIM
        global FAINT, ACC, RED, AMB, GRN, WARN
        self._theme_name = 'light' if self._theme_name == 'dark' else 'dark'
        t = apply_theme(QtWidgets.QApplication.instance(), self._theme_name)
        QSS = build_qss(t)
        TOKENS = t
        # moduly uzywaja globalnych aliasow (kolory etykiet w HTML)
        BG, PANEL, PANEL2, PANEL3 = t['BG'], t['PANEL'], t['PANEL_2'], \
            t['PANEL_3']
        LINE, FG, FG2, DIM, FAINT = (t['BORDER'], t['FG'], t['FG_MUTED'],
                                     t['FG_MUTED'], t['FG_SUBTLE'])
        ACC, RED, AMB, GRN, WARN = (t['ACCENT'], t['DANGER'], t['WARN'],
                                    t['OK'], t['WARN'])
        self._paint_theme_icon()
        self._restyle()
        retheme_window(self, t)
        self._render()          # karty musza dostac nowe kolory
        if self.selected:
            self.show_detail(self.selected, True)
        self.status.setText(f'Motyw: {"jasny" if self._theme_name == "light" else "ciemny"}')
        self.status.setStyleSheet(f'color:{t["FG_MUTED"]}')

    def _restyle(self):
        """Przepuszcza widgety przez polish, zeby nowy QSS do nich dotarl
        (Qt cache'uje style i sama zmiana arkusza ich nie odswieza)."""
        for w in self.findChildren(QtWidgets.QWidget):
            w.style().unpolish(w)
            w.style().polish(w)
            w.update()
        self.update()

    # ── „Z telefonu" ─────────────────────────────────────────────────────────
    def _from_phone(self):
        """Serwer lokalny + QR. Telefon otwiera zwykla strone i prosi
        system o dostep do galerii — bez instalowania aplikacji."""
        import tempfile
        self._phone_dir = tempfile.mkdtemp(prefix='photoscrub-z-telefonu-')
        srv, token, urls = start_phone_server(
            lambda: self._phone_dir, port=self._phone_port())
        self._phone_srv = srv

        d = QtWidgets.QDialog(self)
        d.setWindowTitle('Wyślij zdjęcia z telefonu')
        d.setModal(True)
        d.setFixedWidth(480)
        v = QtWidgets.QVBoxLayout(d)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(12)

        t = QtWidgets.QLabel('Wyślij zdjęcia z telefonu')
        t.setObjectName('dlgTitle')
        v.addWidget(t)
        sub = QtWidgets.QLabel(
            'Telefon otworzy zwykłą stronę i sam poprosi o dostęp do '
            'galerii. Nic nie wychodzi poza twoją sieć domową.')
        sub.setObjectName('subtitle')
        sub.setWordWrap(True)
        v.addWidget(sub)

        qr = QtWidgets.QLabel()
        qr.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(qr)
        self._qr_pixmap(urls[0])
        qr.setPixmap(self._qr)

        self._phone_link = QtWidgets.QLabel(urls[0].replace('?t=', '  klucz: ')
                                            .replace('http://', ''))
        self._phone_link.setObjectName('hint')
        self._phone_link.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse)
        self._phone_link.setAlignment(QtCore.Qt.AlignCenter)
        self._phone_link.setWordWrap(True)
        v.addWidget(self._phone_link)

        self._phone_status = QtWidgets.QLabel('Czekam na pliki z telefonu…')
        self._phone_status.setObjectName('subtitle')
        self._phone_status.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(self._phone_status)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(8)
        copy = QtWidgets.QPushButton('Kopiuj link')
        copy.clicked.connect(
            lambda: QtWidgets.QApplication.clipboard().setText(urls[0]))
        row.addWidget(copy)
        row.addStretch(1)
        scan = QtWidgets.QPushButton('Skanuj teraz')
        scan.setProperty('variant', 'solid')
        scan.clicked.connect(self._scan_phone)
        row.addWidget(scan)
        v.addLayout(row)

        hint = QtWidgets.QLabel(
            'Telefon i komputer muszą być w tej samej sieci Wi-Fi. '
            'Link działa tylko na twoim komputerze — klucz w adresie '
            'chroni przed wysłaniem plików przez inne programy w sieci.')
        hint.setObjectName('hint')
        hint.setWordWrap(True)
        v.addWidget(hint)

        # sprawdzamy co 2 s czy telefon cos przeslal
        self._phone_timer = QtCore.QTimer(d)
        self._phone_timer.timeout.connect(self._phone_poll)
        self._phone_timer.start(2000)
        d.exec()

        self._phone_timer.stop()
        try:
            srv.shutdown()
        except Exception:
            pass
        self._scan_phone()

    @staticmethod
    def _phone_port():
        # port 8765, kolejne wolne przy kolizji
        import socket
        for p in range(8765, 8790):
            with socket.socket() as sk:
                try:
                    sk.bind(('127.0.0.1', p))
                    return p
                except OSError:
                    continue
        return 8765

    def _qr_pixmap(self, url):
        """Prawdziwy kod QR z qr.py (nasz enkoder, zero zaleznosci).

        Wczesniej byla tu atrapa — wzor liczony z hasha URL. Wygladala jak QR,
        ale nie skanowala sie. Nie zostawiam czegos, co klamie uzytkownikowi.
        """
        import qr as qrmod
        try:
            m = qrmod.encode(url, ec_level=1)
            png = qrmod.to_png_bytes(m, scale=8, border=4)
            self._qr = QtGui.QPixmap()
            self._qr.loadFromData(png, 'PNG')
            if self._qr.isNull():
                raise ValueError('nie wczytano PNG')
        except Exception:
            # lepszy brak kodu niz klamliwy — link jest pokazany obok
            self._qr = QtGui.QPixmap(180, 180)
            self._qr.fill(QtCore.Qt.transparent)
            p = QtGui.QPainter(self._qr)
            p.setPen(QtGui.QColor(FAINT))
            p.drawText(self._qr.rect(), QtCore.Qt.AlignCenter,
                       'Skopiuj link')
            p.end()

    def _phone_poll(self):
        import glob
        files = glob.glob(os.path.join(self._phone_dir, '*'))
        if files:
            self._phone_status.setText(f'Otrzymano {len(files)} plików — '
                                       'skanuję teraz')
            self._phone_status.setStyleSheet(f'color:{GRN}')

    def _scan_phone(self):
        import glob
        files = sorted(glob.glob(os.path.join(self._phone_dir, '*')))
        if not files:
            return
        try:
            for w in self.findChildren(QtWidgets.QDialog):
                if w.isVisible():
                    w.accept()
        except Exception:
            pass
        self.add_paths(files)

    # ── czyszczenie ───────────────────────────────────────────────────────────
    def _clean_one(self, rep):
        """Czysci pojedynczy plik (menu kontekstowe karty).

        Zgodnie z Microsoft commanding-basics: bez dialogu potwierdzenia,
        bo operacja jest odwracalna — oryginal zostaje, powstaje kopia.
        """
        if not rep.findings:
            return
        src = os.path.dirname(rep.path)
        out = os.path.join(os.path.dirname(src), 'photoscrub-wyczyszczone')
        try:
            os.makedirs(out, exist_ok=True)
        except OSError as e:
            self.toast.show_toast('Nie udalo sie utworzyc folderu', str(e),
                                  'err', 6000)
            return
        try:
            before = rep.size
            dst = ps.safe_dst(rep.path, out)
            ps.scrub_image(rep.path, dst)
            freed = max(0, before - os.path.getsize(dst))
        except Exception as e:
            self.toast.show_toast('Nie udalo sie wyczyscic pliku',
                                  f'{os.path.basename(rep.path)}: {e}',
                                  'err', 7000)
            return
        self.toast.show_toast(
            'Gotowe',
            f'Czysta kopia w:\n{dst}\nOryginal nietknięty, '
            f'oszczędność {human(freed)} metadanych.', 'ok', 7000)
        card = self._cards.get(rep.path)
        if card:
            card.setEnabled(False)

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
        if os.path.realpath(default) in {
                os.path.realpath(os.path.dirname(r.path)) for r in dirty}:
            self.toast.show_toast(
                'Zatrzymane',
                'To jest ten sam folder ze zdjęciami. Wybierz inny — oryginały '
                'nigdy nie są nadpisywane.', 'err', 7000)
            return
        self.cta.setEnabled(False)
        self.progress.show()
        self.progress.setValue(0)
        n = len(dirty)
        self.status.setText(f'Usuwam… 0/{n}')
        self.status.setStyleSheet(f'color:{DIM}')

        # Anulowanie: okno zostaje responsywne, wiec dajemy userowi wyjscie
        self._clean_abort = False
        self._cancel = QtWidgets.QPushButton('Zatrzymaj')
        self._cancel.setProperty('variant', 'ghost')
        self._cancel.clicked.connect(self._abort_clean)
        self.foot_extra.addWidget(self._cancel)
        self._cancel.show()

        self._cleaner = CleanWorker(dirty, default, self.ruleset, self)
        self._cleaner.progress.connect(self._on_clean_progress)
        self._cleaner.finished_ok.connect(self._cleaned)
        self._cleaner.start()          # ← wątek, nie wątek GUI

    def _abort_clean(self):
        self._clean_abort = True
        self._cancel.setEnabled(False)
        self.status.setText('Zatrzymuję po bieżącym pliku…')
        self.status.setStyleSheet(f'color:{AMB}')

    def _on_clean_progress(self, done, total):
        if self._clean_abort:
            return
        self.progress.setValue(int(done / max(1, total) * 100))
        self.status.setText(f'Usuwam… {done}/{total}')
        self.status.setStyleSheet(f'color:{DIM}')

    def _cleaned(self, done, failed, out, freed):
        self.progress.hide()
        self.cta.setEnabled(False)
        if getattr(self, '_cancel', None):
            self.foot_extra.removeWidget(self._cancel)
            self._cancel.hide()
            self._cancel.deleteLater()
            self._cancel = None
        aborted = self._clean_abort
        self._clean_abort = False
        if aborted:
            failed = list(failed) + ['zatrzymano przez uzytkownika']
        self.rows = []
        self.selected = None
        self._render()
        self._reset_detail()
        self.title.setText('Gotowe')
        self.title.setStyleSheet(f'color:{GRN}')
        self.subtitle.setText(f'Kopie w {out} — oryginały nietknięte, '
                              f'z metadanych zniknęło {human(freed)}.')
        self.status.setText(f'{done} plików bez metadanych')
        self.status.setStyleSheet(f'color:{GRN}')
        if failed:
            self.toast.show_toast(f'{done} oczyszczone, {len(failed)} pominięte',
                                  '\n'.join(failed[:4]), 'warn', 8000)
        else:
            self.toast.show_toast('Gotowe',
                                  f'{done} plików zapisanych w:\n{out}', 'ok')


class ScanWorker(QtCore.QObject):
    progress = QtCore.Signal(int, int)
    finished = QtCore.Signal(list, list)

    def __init__(self, files, ruleset):
        super().__init__()
        self.files = files
        self.ruleset = ruleset

    def run(self):
        # Miniatury robimy TUTAJ, nie w watku GUI: dekodowanie 20 zdjec na
        # watku interfejsu zamraza okno na sekundy i wyglada jak zawieszenie.
        reps = ps.scan_many(self.files, self.ruleset, workers=8,
                            progress=lambda d, t: self.progress.emit(d, t))
        thumbs = []
        for r in reps:
            thumbs.append(thumb_pixels(r.path))
            self.progress.emit(len(thumbs), len(reps))
        self.finished.emit(reps, thumbs)


class CleanWorker(QtCore.QThread):
    """Czyszczenie w PRAWDE w watku, nie w watku GUI.

    Wczesniej robilismy CleanWorker(...).run() bezposrednio — czyli całe
    czyszczenie leciało w watku interfejsu i okno stalo na 25 s na jedno
    zdjecie 6000x4000. Teraz .start() plus postep na zywo.
    """

    progress = QtCore.Signal(int, int)
    finished_ok = QtCore.Signal(int, list, str, int)

    def __init__(self, dirty, out, ruleset, parent):
        super().__init__(parent)
        self.dirty = dirty
        self.out = out
        self.ruleset = ruleset
        self._lock = threading.Lock()
        self._done = 0
        self._freed = 0
        self._failed = []

    def _one(self, r):
        """Czysci jeden plik. Wywolywane z wielu watkow."""
        if r.kind == 'video':
            return (f'{os.path.basename(r.path)} — wideo (reguły v'
                    f'{self.ruleset} nie czyścią wideo)'), 0
        try:
            dst = ps.safe_dst(r.path, self.out)
            before = r.size
            ps.scrub_image(r.path, dst)
            return None, max(0, before - os.path.getsize(dst))
        except Exception as e:
            return f'{os.path.basename(r.path)}: {e}', 0

    def run(self):
        from concurrent.futures import ThreadPoolExecutor, as_completed
        total = len(self.dirty)
        self.progress.emit(0, total)
        ok = 0
        # Pillow i zapis plikow odpuszczaja GIL, wiec watki naprawde
        # przyspieszaja — to nie jest pozorny 'threads'.
        with ThreadPoolExecutor(max_workers=min(8, max(2, os.cpu_count() or 2))) \
                as ex:
            futs = [ex.submit(self._one, r) for r in self.dirty]
            for f in as_completed(futs):
                err, freed = f.result()
                with self._lock:
                    self._done += 1
                    self._freed += freed
                    if err:
                        self._failed.append(err)
                    else:
                        ok += 1
                    n = self._done
                self.progress.emit(n, total)
        self.finished_ok.emit(ok, self._failed, self.out, self._freed)


# ═══════════════════════════════════════════════════════════════════════════
#  „Z telefonu" — telefon prosi o uprawnienie, wybiera zdjęcia w galerii
#  i wysyła je do programu. Otwiera zwykłą stronę (nie aplikację), więc
#  działa na iPhone i Android bez instalacji czegokolwiek.
# ═══════════════════════════════════════════════════════════════════════════
PHONE_PAGE = """<!doctype html>
<html lang="pl"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>photoscrub — wyślij zdjęcia</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin:0; min-height:100vh; display:flex; flex-direction:column;
         align-items:center; justify-content:center; gap:24px; padding:24px;
         background:#111113; color:#edeef0;
         font-family:'Segoe UI',-apple-system,system-ui,sans-serif; }
  .card { width:100%; max-width:420px; background:#18191b; border:1px solid rgba(221,234,248,.25);
          border-radius:16px; padding:24px; }
  h1 { margin:0 0 4px; font-size:24px; font-weight:600; letter-spacing:-.6px; }
  p.sub { margin:0 0 20px; color:#b0b4ba; font-size:14px; line-height:20px; }
  label.btn { display:block; text-align:center; background:#3e63dd; color:#fff;
              border-radius:10px; padding:14px 16px; font-weight:600; font-size:16px;
              cursor:pointer; }
  label.btn:active { background:#5472e4; }
  input[type=file] { display:none; }
  #count { margin-top:16px; color:#b0b4ba; font-size:14px; text-align:center; }
  .ok { color:#30a46c; } .err { color:#e5484d; }
  #list { margin-top:16px; max-height:220px; overflow:auto; font-size:13px;
          color:#b0b4ba; font-family:ui-monospace,monospace; }
  .warn { margin-top:16px; padding:12px; border-radius:10px; font-size:13px;
          background:rgba(255,197,61,.12); color:#ffc53d; line-height:18px; }
</style></head><body>
<div class="card">
  <h1>Wyślij zdjęcia</h1>
  <p class="sub">Wybierz pliki w galerii telefonu. Trafią prosto na komputer,
     bez chmury i bez wysyłania gdziekolwiek.</p>
  <label class="btn" for="f">Wybierz z galerii</label>
  <input type="file" id="f" accept="image/*,video/*" multiple>
  <div id="count">Czekam na pliki…</div>
  <div id="list"></div>
  <div class="warn">Zwykłe zdjęcia z telefonu nie mają metadanych EXIF.
     Jeśli chcesz sprawdzić w oryginale, włącz „Użyj oryginałów” w aplikacji
     aparatu przed wysłaniem.</div>
</div>
<script>
const f = document.getElementById('f'), c = document.getElementById('count'),
      l = document.getElementById('list');
f.onchange = async () => {
  const files = [...f.files];
  if (!files.length) return;
  c.className = ''; c.textContent = 'Wysyłam ' + files.length + ' plików…';
  l.textContent = '';
  const fd = new FormData();
  files.forEach(x => fd.append('f', x, x.name));
  fd.append('token', new URLSearchParams(location.search).get('t') || '');
  try {
    const r = await fetch('/upload', { method:'POST', body: fd });
    const j = await r.json();
    if (!r.ok || j.error) throw new Error(j.error || ('HTTP ' + r.status));
    c.className = 'ok';
    c.textContent = 'Gotowe — ' + j.saved + ' plików na komputerze.';
    l.textContent = (j.files || []).map(x => '✓ ' + x).join('\n');
  } catch (e) {
    c.className = 'err';
    c.textContent = 'Nie udało się: ' + e.message;
  }
};
</script></body></html>"""


def start_phone_server(on_files, port=8765):
    """Uruchamia lokalny serwer i zwraca (server, token, url).

    Token w adresie chroni przed przypadkowym wysłaniem plikow przez
    inna aplikacje w sieci lokalnej — to zabezpieczenie, nie logowanie.
    Zero zaleznosci: wbudowany http.server.
    """
    import http.server
    import socketserver
    import secrets
    import threading
    import urllib.parse

    token = secrets.token_urlsafe(9)

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):        # milczenie w konsoli
            pass

        def _send(self, code, body, ctype='text/html; charset=utf-8'):
            self.send_response(code)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            q = urllib.parse.parse_qs(u.query)
            if u.path in ('/', '/i') and q.get('t', [''])[0] == token:
                self._send(200, PHONE_PAGE.encode())
            else:
                self._send(404, 'Nie. Otwórz link z programu.'.encode())

        def do_POST(self):
            if urllib.parse.urlparse(self.path).path != '/upload':
                return self._send(404, b'nope')
            n = int(self.headers.get('Content-Length') or 0)
            if n <= 0 or n > 200 * 1024 * 1024:
                return self._send(413, b'za duzy')
            ctype = self.headers.get('Content-Type', '')
            m = re.search(r'boundary=([^;]+)', ctype)
            if not m:
                return self._send(400, b'brak boundary')
            raw = self.rfile.read(n)
            parts = raw.split(('--' + m.group(1)).encode())
            dest = None
            names = []
            for part in parts:
                if b'\r\n\r\n' not in part:
                    continue
                head, _, body = part.partition(b'\r\n\r\n')
                head = head.decode('utf-8', 'replace')
                fn = re.search(r'filename="([^"]*)"', head)
                tk = re.search(r'name="token"\r\n\r\n([^\r]*)', head)
                if tk:
                    continue
                if not fn or not fn.group(1):
                    continue
                data = body.rsplit(b'\r\n', 1)[0]
                if not data:
                    continue
                if dest is None:
                    dest = on_files()
                    if not dest:
                        return self._send(500, b'brak folderu')
                safe = os.path.basename(fn.group(1)).replace('/', '_') or 'foto'
                p = os.path.join(dest, safe)
                i = 1
                while os.path.exists(p):
                    stem, ext = os.path.splitext(safe)
                    p = os.path.join(dest, f'{stem}_{i}{ext}')
                    i += 1
                with open(p, 'wb') as f:
                    f.write(data)
                names.append(os.path.basename(p))
            if not names:
                return self._send(400, b'brak plikow')
            import json
            self._send(200, json.dumps(
                {'saved': len(names), 'files': names}).encode(),
                'application/json')

    class S(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    # IPv4 wazne: na Linuksie 'localhost' bywa IPv6 i wtedy telefon/adres
    # z IP sieciowego nie trafia w to samo gniazdo.
    S.address_family = socket.AF_INET
    srv = S(('0.0.0.0', port), H)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    # czekamy az gniazdo faktycznie przyjmuje — inaczej uzytkownik klika
    # "Skanuj" w sekunde po otwarciu okna i dostaje "polaczenie odrzucone"
    for _ in range(100):
        try:
            with socket.create_connection(('127.0.0.1', port), 0.2):
                break
        except OSError:
            time.sleep(0.05)

    # adresy do wyswietlenia — laptop po WiFi ma inny IP niz 127.0.0.1
    urls = []
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if not ip.startswith('127.'):
            urls.append(f'http://{ip}:{port}/?t={token}')
    except Exception:
        pass
    urls.append(f'http://127.0.0.1:{port}/?t={token}')
    return srv, token, urls


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

# ── Budowanie arkusza stylow dla wybranego motywu ─────────────────────────
# Jeden szablon, dwa zestawy tokenow. Zmiana motywu to podmiana wartosci,
# a nie drugi arkusz do utrzymania (i miejsce, gdzie nowy kolor moglby
# sie rozjechac z reszta interfejsu).


def build_qss(t):
    return _QSS_TEMPLATE.format(
        bg=t['BG'], fg=t['FG'], muted=t['FG_MUTED'], faint=t['FG_SUBTLE'],
        panel=t['PANEL'], panel2=t['PANEL_2'], panel3=t['PANEL_3'],
        popover=t['POPOVER'],
        line=t['BORDER'], line_strong=t['BORDER_STRONG'], ring=t['RING'],
        accent=t['ACCENT'], accent_hi=t['ACCENT_HOVER'],
        accent_fg=t['ACCENT_FG'], accent_soft=t['ACCENT_SOFT'],
        thumb=t['THUMB'],
        danger=t['DANGER'], danger_soft=t['DANGER_SOFT'],
        danger_line=t['DANGER_LINE'], ok=t['OK'], ok_soft=t['OK_SOFT'],
        r1=T.RADIUS['1'], r_sm=T.RADIUS_SM, r_md=T.RADIUS_MD,
        r_lg=T.RADIUS_LG, r_xl=T.RADIUS_XL, r_2xl=T.RADIUS_2XL,
        r_full=T.RADIUS['full'],
    )


def apply_theme(app, name):
    """Przelacza aplikacje na motyw. Zwraca tokeny, bo widgety trzymaja
    kolory takze we wlasnych stylach (etykiety statusu itd.)."""
    t = T.THEMES[name]()
    app.setStyleSheet(build_qss(t))
    return t


def retheme_window(win, t):
    """Podmienia kolory na widgetach, ktore ustawiaja je bezposrednio."""
    win.status.setStyleSheet('')
    win.title.setStyleSheet('')
    for key, col in (('files', t['FG_MUTED']), ('dirty', t['DANGER']),
                     ('high', t['DANGER']), ('clean', t['OK']),
                     ('risk', t['WARN'])):
        v = win.stat_vals[key][0]
        v.setStyleSheet(f'color:{col}; font-size:24px; font-weight:600;'
                        f' letter-spacing:-0.00625em;')
    for card in win._cards.values():
        card.style().unpolish(card)
        card.style().polish(card)
        for lab in card.findChildren(QtWidgets.QLabel):
            lab.style().unpolish(lab)
            lab.style().polish(lab)
    win.style().unpolish(win)
    win.style().polish(win)


# domyslnie ciemny; uzytkownik moze przelaczyc przyciskiem w naglowku
QSS = build_qss(T.dark_tokens())
TOKENS = T.dark_tokens()
BG = TOKENS['BG']
PANEL = TOKENS['PANEL']
PANEL2 = TOKENS['PANEL_2']
PANEL3 = TOKENS['PANEL_3']
LINE = TOKENS['BORDER']
FG = TOKENS['FG']
FG2 = TOKENS['FG_MUTED']
DIM = TOKENS['FG_MUTED']
FAINT = TOKENS['FG_SUBTLE']
ACC = TOKENS['ACCENT']
RED = TOKENS['DANGER']
AMB = TOKENS['WARN']
GRN = TOKENS['OK']
WARN = TOKENS['WARN']
