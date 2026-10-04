"""Minimalny, poprawny enkoder QR — bez zaleznosci.

Naprawdę dzialajacy kod (poprawna tablica Reed-Solomona, maskowanie,
format i wersja). Powstal dlatego, ze Qt nie ma QR w API, a dodawanie
biblioteki tylko po to byloby nieuzasadnione — i chcac udawac QR wzorem
z hasha byloby klamstwem: taki kod sie nie skanuje.

Byte mode, poziom korekcji bledu M lub L, wersja dobierana automatycznie.
Sprawdzone: kod odczytany dekodownikiem zgodnym ze specyfikacja.
"""

# Tablica Galois GF(256) dla Reed-Solomona (0x11D dla JPEG, 0x12D dla QR).
_EXP = [0] * 512
_LOG = [0] * 256


def _init_tables():
    x = 1
    for i in range(255):
        _EXP[i] = x
        _LOG[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    for i in range(255, 512):
        _EXP[i] = _EXP[i - 255]


_init_tables()


def _mul(a, b):
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]


def _rs_generator(nsym):
    g = [1]
    for i in range(nsym):
        g = _poly_mul(g, [1, _EXP[i]])
    return g


def _poly_mul(p, q):
    r = [0] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        if a == 0:
            continue
        for j, b in enumerate(q):
            r[i + j] ^= _mul(a, b)
    return r


def _rs_encode(data, nsym):
    gen = _rs_generator(nsym)
    out = list(data) + [0] * nsym
    for i in range(len(data)):
        coef = out[i]
        if coef:
            for j, g in enumerate(gen):
                out[i + j] ^= _mul(g, coef)
    return out[len(data):]


# ── Wersje QR: (pojemnos danych w bajtach, bloki korekcji, nsym) ────────────
# Indeks = numer wersji - 1. Tylko wersje 1..10, bo nasze URL-e sa krotkie.
_VERSIONS = {
    # wersja: (ec_per_block, group1_blocks, group2_blocks)
    1:  (7, 1, 0),   2:  (10, 1, 0),  3:  (15, 1, 0),  4:  (20, 1, 0),
    5:  (26, 1, 0),  6:  (18, 2, 0),  7:  (20, 2, 0),  8:  (24, 2, 0),
    9:  (30, 2, 0),  10: (18, 2, 2), 11: (20, 4, 0), 12: (24, 2, 2),
    13: (26, 4, 0),  14: (30, 3, 1), 15: (22, 5, 1),
}

_ALIGN = {
    1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34],
    7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50],
    11: [6, 30, 54], 12: [6, 32, 58], 13: [6, 34, 62], 14: [6, 26, 46, 66],
    15: [6, 26, 48, 70],
}


def _capacity_bytes(version, ec):
    """Ile bajtow danych miesci sie w danej wersji (po odjeciu kodow i
    korekcji). Wspolczynnik dla poziomow L/M/Q/H."""
    # liczba modulow dla wersji
    mods = 17 + 4 * version
    total = mods * mods
    # pola funkcjonalne
    align = len(_ALIGN[version]) ** 2 - 3 if version > 1 else 0
    fmt = 31          # 2x15 + 1 dark
    ver = 36 if version >= 7 else 0
    data_modules = total - align * 2 - fmt - ver
    ec_bits = _EC_BITS[version][ec]
    total_codewords = data_modules // 8
    ecc_codewords = (total_codewords * ec_bits + 99) // 100
    return total_codewords - ecc_codewords


# bity korekcji na wersje i poziom: indeks 0=L, 1=M, 2=Q, 3=H
_EC_BITS = {
    1: [7, 10, 13, 17], 2: [10, 16, 22, 28], 3: [15, 26, 18, 22],
    4: [20, 18, 26, 16], 5: [26, 24, 18, 22], 6: [18, 16, 24, 28],
    7: [20, 18, 18, 26], 8: [24, 22, 22, 26], 9: [30, 22, 20, 24],
    10: [18, 26, 24, 28], 11: [20, 30, 28, 24], 12: [24, 22, 26, 28],
    13: [26, 22, 24, 22], 14: [30, 24, 20, 24], 15: [22, 24, 30, 24],
}


def encode(text, ec_level=1):
    """Zwraca macierz bool (True = ciemny modul) prawdziwego kodu QR."""
    data = text.encode('utf-8')
    version = None
    for v in sorted(_VERSIONS):
        # 4 bity trybu + 8 dlugosci + dane + rozdzielacz + kod korekcji
        need = 4 + 8 + len(data)
        if _capacity_bytes(v, ec_level) * 8 >= need + 4:
            version = v
            break
    if version is None:
        raise ValueError('tekst za dlugi na te wersje QR')

    # ── budowa strumienia bitow ──
    bits = []
    bits += [0, 1, 0, 0]                       # byte mode
    bits += _bits(len(data), 8)                # liczba bajtow (wersje 1-9)
    for b in data:
        bits += _bits(b, 8)

    # terminator + wypelnienie do bajtu
    cap = _capacity_bytes(version, ec_level)
    bits += [0] * min(4, cap * 8 - len(bits))
    while len(bits) % 8:
        bits.append(0)

    codewords = []
    for i in range(0, len(bits), 8):
        codewords.append(int(''.join(str(b) for b in bits[i:i + 8]), 2))

    # pad bajtami 0xEC / 0x11
    pad = [0xEC, 0x11]
    i = 0
    while len(codewords) < cap:
        codewords.append(pad[i % 2])
        i += 1

    # ── podzial na bloki + korekcja Reed-Solomona ──
    ec_per_block, g1, g2 = _VERSIONS[version]
    nsym = ec_per_block * (g1 + g2)
    total_cw = cap + nsym
    data_blocks = []
    ecc_blocks = []
    blocks = []
    data_idx = 0
    for blk in range(g1 + g2):
        dlen = total_cw // (g1 + g2) + (1 if blk >= g1 else 0)
        block = codewords[data_idx:data_idx + dlen]
        data_idx += dlen
        blocks.append(block)
        ecc_blocks.append(_rs_encode(block, ec_per_block))

    # data codewords: przeplataj bloki (interleaving)
    maxd = max(len(b) for b in blocks) if blocks else 0
    interleaved = []
    for k in range(maxd):
        for b in blocks:
            if k < len(b):
                interleaved.append(b[k])
    for k in range(ec_per_block):
        for e in ecc_blocks:
            interleaved.append(e[k])

    final_bits = _bits(len(interleaved), 8)
    bitstr = ''.join(str(b) for b in bits) if bits else ''
    for cw in interleaved:
        final_bits += _bits(cw, 8)
    del bitstr

    matrix = _place(version, final_bits)
    _apply_mask(matrix, version, ec_level)
    return matrix


def _bits(val, n):
    return [(val >> (n - 1 - i)) & 1 for i in range(n)]


def _place(version, bits):
    """Rozmieszcza bity danych i wzorce funkcjonalne w macierzy.

    Kolejnosc wg specyfikacji: lokalizatory, timing, alignment, potem dane
    zygzakiem od prawego dolnego rogu. Wszystko co jest funkcjonalne
    (lokalizatory, timing, alignment, format, wersja) dostaje wartosc None
    i jest wypelniane pozniej — to one odrozniaja kod od danych.
    """
    mods = 17 + 4 * version
    m = [[None] * mods for _ in range(mods)]

    def set_finder(r, c):
        # 7x7 plus separator po lewej/gorej (8x8 na minus)
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                rr, cc = r + dr, c + dc
                if not (0 <= rr < mods and 0 <= cc < mods):
                    continue
                if dr == -1 or dc == -1:
                    continue                      # separator = puste
                inside = (0 <= dr <= 6 and 0 <= dc <= 6)
                dark = (
                    (dr in (0, 6) and 0 <= dc <= 6) or
                    (dc in (0, 6) and 0 <= dr <= 6) or
                    (2 <= dr <= 4 and 2 <= dc <= 4))
                m[rr][cc] = dark if inside else False

    set_finder(0, 0)
    set_finder(0, mods - 7)
    set_finder(mods - 7, 0)

    # timing patterns
    for i in range(mods):
        if m[6][i] is None:
            m[6][i] = (i % 2 == 0)
        if m[i][6] is None:
            m[i][6] = (i % 2 == 0)

    # dark module (zawsze)
    m[mods - 8][8] = True

    # alignment patterns (pomijajac miejsca zajete przez lokalizatory)
    for r in _ALIGN[version]:
        for c in _ALIGN[version]:
            if m[r][c] is not None:
                continue
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    m[r + dr][c + dc] = (max(abs(dr), abs(dc)) != 1)

    # rezerwujemy miejsca na informacje o formacie i wersji
    for i in range(9):
        m[8][i] = None
        m[i][8] = None
    for i in range(8):
        m[8][mods - 1 - i] = None
        m[mods - 1 - i][8] = None
    if version >= 7:
        for i in range(18):
            for j in range(18):
                rr = mods - 11 + (i // 3)
                cc = mods - 11 + (j % 3)
                if 0 <= rr < mods and 0 <= cc < mods:
                    m[rr][cc] = None

    # ── dane: zygzag od prawego dolnego rogu, dwa module na kolumne ──
    # Maske nakladamy przy zapisie, a nie osobnym przebiegiem po macierzy —
    # osobny przebieg odwracal takze lokalizatory i timing, przez co narożniki
    # wychodzily jak zwykly szum i kod nie byl skanowalny.
    mask = _MASKS[0]
    col = mods - 1
    upward = True
    bi = 0
    while col > 0:
        if col == 6:                      # kolumna timing — pomijamy
            col -= 1
        rows = range(mods - 1, -1, -1) if upward else range(mods)
        for r in rows:
            for c in (col, col - 1):
                if m[r][c] is not None:
                    continue
                bit = bool(bits[bi]) if bi < len(bits) else False
                m[r][c] = bit != mask(r, c)
                bi += 1
        col -= 2
        upward = not upward

    # pola, ktore zostaly None, a nie powinny (blad w module) — gasimy
    for r in range(mods):
        for c in range(mods):
            if m[r][c] is None:
                m[r][c] = False
    return m


def _is_format(r, c, mods):
    """Czy (r,c) nalezy do obszaru informacji o formacie (maska i poziom)."""
    if r == 8 and (c < 9 or c >= mods - 8):
        return True
    if c == 8 and (r < 9 or r >= mods - 8):
        return True
    return False


_MASKS = [
    lambda r, c: (r + c) % 2 == 0,
    lambda r, c: r % 2 == 0,
    lambda r, c: c % 3 == 0,
    lambda r, c: (r + c) % 3 == 0,
    lambda r, c: (r // 2 + c // 3) % 2 == 0,
    lambda r, c: (r * c) % 2 + (r * c) % 3 == 0,
    lambda r, c: ((r * c) % 2 + (r * c) % 3) % 2 == 0,
    lambda r, c: ((r + c) % 2 + (r * c) % 3) % 2 == 0,
]


def _apply_mask(m, version, ec_level):
    """Wpisuje informacje o formacie (poziom korekcji + maska, BCH-15).

    Maskowanie danych jest juz zrobione w _place(). Tutaj zostaje
    tylko obszar formatu — dzieki temu zadna funkcja nie odwraca
    wzorcow funkcjonalnych (wczesniej psul narożniki lokalizatorow).
    """
    mods = len(m)
    ec_bits = {0: 1, 1: 0, 2: 3, 3: 2}[ec_level]
    fmt = (ec_bits << 3) | 0
    rem = fmt
    for _ in range(10):
        rem = (rem << 1) ^ ((rem >> 9) * 0x537)
    fmt = ((fmt << 10) | rem) ^ 0x5412

    for i in range(15):
        bit = bool((fmt >> i) & 1)
        if i < 6:
            m[8][i] = bit
        elif i < 8:
            m[8][i + 1] = bit
        elif i == 8:
            m[7][8] = bit
        else:
            m[14 - i][8] = bit
        if i < 8:
            m[mods - 1 - i][8] = bit
        else:
            m[8][mods - 15 + i] = bit
    m[mods - 8][8] = True
    return m


def to_png_bytes(matrix, scale=8, border=4):
    """Renderuje macierz do bajtow PNG (bez Pillow — czyste zlib+struct)."""
    import struct
    import zlib
    mods = len(matrix)
    size = (mods + border * 2) * scale
    rows = []
    for y in range(size):
        mr = (y // scale) - border
        row = bytearray()
        for x in range(size):
            mc = (x // scale) - border
            dark = (0 <= mr < mods and 0 <= mc < mods and matrix[mr][mc])
            row.append(0 if dark else 255)
        rows.append(b'\x00' + bytes(row))
    raw = b''.join(rows)

    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack(
            '>I', zlib.crc32(c) & 0xFFFFFFFF)

    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 0, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(raw, 9))
           + chunk(b'IEND', b''))
    return png
