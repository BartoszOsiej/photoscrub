"""photoscrub — tokeny interfejsu.

NIE zgadujemy kolorów ani odstępów. Wszystko poniżej to realne wartości
z systemów, które pokazałeś:

  SPACING      Radix Themes  /themes/docs/theme/spacing
               9-stopniowa skala: 4, 8, 12, 16, 24, 32, 40, 48, 64 px
  RADIUS       Radix Themes  src/styles/tokens/radius.css
               3, 4, 6, 8, 12, 16 px × radius-factor (bierzemy medium = 1.0)
  TYPE         Radix Themes  src/styles/tokens/typography.css
               12/14/16/18/20/24/28/35/60 px z dopasowanym line-height
               i ujemnym letter-spacing dla dużych rozmiarów
  SHADOW       Radix Themes  src/styles/tokens/shadow.css (gałązie dark)
  COLOR        Radix Colors  @radix-ui/colors dark.ts (mauve/slate/indigo/
               red/amber/green + warianty alpha)
  SEMANTYKA    shadcn/ui     /docs/theming — pary background/foreground,
               card, popover, primary, secondary, muted, accent, destructive,
               border, input, ring + skala radiusu liczona z --radius

Motyw: dark (gray = slate, akcent = indigo).
"""

# ── Radix Themes: skala odstępów (px) ───────────────────────────────────────
SPACE = {'1': 4, '2': 8, '3': 12, '4': 16, '5': 24, '6': 32, '7': 40,
         '8': 48, '9': 64}

# ── Radix Themes: skala radiusów (px), radius-factor = 1.0 (medium) ─────────
_R = (3, 4, 6, 8, 12, 16)
RADIUS = {'1': _R[0], '2': _R[1], '3': _R[2], '4': _R[3], '5': _R[4],
          '6': _R[5], 'full': 9999}

# ── shadcn: promień bazowy 0.625rem = 10px i skala pochodna ────────────────
R_BASE = 10
RADIUS_SM = round(R_BASE * 0.6)   # 6
RADIUS_MD = round(R_BASE * 0.8)   # 8
RADIUS_LG = R_BASE                 # 10
RADIUS_XL = round(R_BASE * 1.4)   # 14
RADIUS_2XL = round(R_BASE * 1.8)  # 18

# ── Type ramp ───────────────────────────────────────────────────────────────
# Ten sam uklad wartosci co w `typography.css` Radix Themes, ale z wagami
# i rozmiarami skorygowanymi do type rampu Microsoftu:
#   https://learn.microsoft.com/windows/apps/design/signature-experiences/typography
#      Small 12/16 · Text 14/20 · Text large 18/24 · Subtitle 20/28 · Title 28/36
#      Title large 40/52 · Display 68/92
#   "Use Semibold instead of Bold for emphasis" — dlatego SEMI = 600, a nie 700.
#   "Italic is excluded because it can reduce readability" — nigdy nie kursywa.
# (font-size, line-height, letter-spacing em)
TYPE = {
    '1': (12, 16, 0.0025), '2': (14, 20, 0.0), '3': (16, 24, 0.0),
    '4': (18, 24, -0.0025), '5': (20, 28, -0.005), '6': (24, 30, -0.00625),
    '7': (28, 36, -0.0075), '8': (40, 52, -0.01), '9': (68, 92, -0.025),
}
# Wagi Segoe UI Variable: Light 300, Semilight 350, Regular 400,
# Semibold 600, Bold 700. Uzywamy 300/400/600 — 700 tylko w ostatecznosci.
LIGHT, REGULAR, MEDIUM, SEMI, BOLD = 300, 400, 500, 600, 700
WEIGHT = {'light': LIGHT, 'regular': REGULAR, 'medium': MEDIUM,
          'semibold': SEMI, 'bold': BOLD}

# ── Breakpointy Microsoftu (effective px) ──────────────────────────────────
#   Small: do 640 · Medium: 641–1007 · Large: 1008+
BREAK_SMALL, BREAK_MEDIUM, BREAK_LARGE = 640, 1007, 1008
# GNOME: "smallest recommended display size for GNOME on desktop is 1024x600"
MIN_WINDOW_W, MIN_WINDOW_H = 1024, 640

# ── Grid: wszystko wielokrotnosc 4 px ──────────────────────────────────────
# "The sizes, margins, and positions of UI elements should always be in
#  multiples of 4 epx" — https://learn.microsoft.com/windows/apps/design/layout/
GRID = 4


def snap4(px):
    """Zaokragla do wielokrotnosci 4 px — ostre krawedzie w skali 125/150/175%."""
    return int(round(px / GRID) * GRID)


# ── Szerokosc panelu szczegolow ────────────────────────────────────────────
# GNOME: "sidebars should never look excessively wide or narrow in relation
# to the main window area". Stala szerokosc = nigdy nie wyglada zle.
# 360 px przy czcionce 14 px daje ~44 znaki na linie (Microsoft: 20–60 znakow).
SIDE_W = 360
# ── Szerokosc karty (Fitts: duzy cel = szybsze trafienie) ───────────────────
CARD_W = 228

# ── Radix Colors, dark mode (realne hexy z @radix-ui/colors/src/dark.ts) ───
_SLATE = ['111113', '18191b', '212225', '272a2d', '2e3135', '363a3f',
          '43484e', '5a6169', '696e77', '777b84', 'b0b4ba', 'edeef0']
_INDIGO = ['11131f', '141726', '182449', '1d2e62', '253974', '304384',
           '3a4f97', '435db1', '3e63dd', '5472e4', '9eb1ff', 'd6e1ff']
_RED = ['191111', '201314', '3b1219', '500f1c', '611623', '72232d', '8c333a',
        'b54548', 'e5484d', 'ec5d5e', 'ff9592', 'ffd1d9']
_AMBER = ['16120c', '1d180f', '302008', '3f2700', '4d3000', '5c3d05', '714f19',
          '8f6424', 'ffc53d', 'ffd60a', 'ffca16', 'ffe7b3']
_GREEN = ['0e1512', '121b17', '132d21', '113b29', '174933', '20573e', '28684a',
          '2f7c57', '30a46c', '33b074', '3dd68c', 'b1f1cb']
# warianty alpha (a1…a12) — używamy a3, a6, a10
_SLATE_A = {3: 'ddeaf814', 4: 'ddeaf82a', 5: 'ddeaf840', 6: 'd6ebfd30',
            8: 'ddeaf86b', 10: 'e5edfd7b', 12: 'fcfdffef'}
_RED_A = {3: 'ff173f2d', 6: 'ff3e5668', 10: 'ff6465eb'}
_AMBER_A = {3: 'fa820022', 6: 'fd9b0051', 10: 'ffd60a'}
_GREEN_A = {3: '22ff991e', 6: '44ffaa4b', 10: '43fea4ab'}
_INDIGO_A = {3: '2f62ff3c', 6: '5178fd7c', 10: '5c7efee3'}


def _h(hex6):
    return '#' + hex6


def rgba(hex8, alpha=None):
    """#RRGGBBAA -> rgba(r,g,b,a).

    Qt NIE rozumie 8-cyfrowego hexy (#ddeaf840) — podmienia taki kolor na
    inny po cichu i caly interfejs dostaje obramowania w zoltym. Radix podaje
    alpha jako 8-cyfrowy hex, wiec konwertujemy jawnie na rgba().
    """
    h = hex8.lstrip('#')
    r, g, b = h[0:2], h[2:4], h[4:6]
    a = h[6:8] if len(h) == 8 else 'ff'
    if alpha is not None:
        a = '%02x' % round(alpha * 255)
    return (f'rgba({int(r, 16)},{int(g, 16)},{int(b, 16)},'
            f'{int(a, 16) / 255:.3f})')


# ── Semantyczne tokeny (konwencja shadcn: para background/foreground) ──────
BG = _h(_SLATE[0])                    # --background
FG = _h(_SLATE[11])                   # --foreground
FG_MUTED = _h(_SLATE[10])             # --muted-foreground (rgba ~ .78)
FG_SUBTLE = _h(_SLATE[9])             # helper text
PANEL = _h(_SLATE[1])                 # --card
PANEL_2 = _h(_SLATE[2])               # --secondary / --muted
PANEL_3 = _h(_SLATE[5])               # hover (slate 6)
SURFACE = 'rgba(0,0,0,0.25)'          # Radix: --color-surface
POPOVER = _h(_SLATE[1])               # --popover
# UWAGA: listy sa indeksowane od 0, a numeracja Radix zaczyna sie od 1,
# czyli krok 9 to _X[8]. Niezgodnosc tu to ciezki blad w kolorach akcentu.
ACCENT = _h(_INDIGO[8])               # --primary (indigo 9 = #3e63dd)
ACCENT_HOVER = _h(_INDIGO[9])         # indigo 10 = #5472e4
ACCENT_FG = '#ffffff'                 # --primary-foreground
ACCENT_SOFT = rgba(_INDIGO_A[3])      # tlo akcentu
BORDER = rgba(_SLATE_A[5])            # --border (1px)
BORDER_STRONG = rgba(_SLATE_A[8])
RING = _h(_INDIGO[7])                 # --ring (indigo 8)

DANGER = _h(_RED[8])                  # --destructive (red 9 = #e5484d)
DANGER_FG = '#ffffff'
DANGER_SOFT = rgba(_RED_A[3])
DANGER_LINE = rgba(_RED_A[6])
WARN = _h(_AMBER[8])                  # amber 9 = #ffc53d
WARN_SOFT = rgba(_AMBER_A[3])
OK = _h(_GREEN[8])                    # green 9 = #30a46c
OK_SOFT = rgba(_GREEN_A[3])

# ── Radix shadow-2 / shadow-3 (gałąź dark) ─────────────────────────────────
SHADOW_2 = ('0 0 0 1px #696e77, 0 0 0 0.5px #00000026, 0 1px 1px 0 #0000003d,'
            ' 0 2px 1px -1px #0000003d, 0 1px 3px 0 #00000026')
SHADOW_3 = ('0 0 0 1px #696e77, 0 2px 3px -2px #00000026, 0 3px 8px -2px '
            '#0000003d, 0 4px 12px -4px #00000042')
SHADOW_4 = ('0 0 0 1px #696e77, 0 8px 40px #00000026, 0 12px 32px -16px '
            '#0000003d')
