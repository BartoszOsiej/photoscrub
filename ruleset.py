#!/usr/bin/env python3
"""photoscrub.ruleset — wersjonowane reguły detekcji.

To jest JEDYNY mechanizm, przez który cena może w przyszłości rosnąć
o symbolicznego dolara, bez oszukiwania klienta:

  Reguły v1  — podstawowe: EXIF, GPS, serial, miniatureka w JPEG
  Reguły v2  — dodane: XMP, IPTC, chunki PNG, komentarze JPEG, HEIC,
              dane doklejone PO obrazie, GPS w wideo (MP4/MOV)
  Reguły v3  — (zarezerwowane) głębsze: maker notes, analiza profili ICC,
              klastry podobnych plików

Licencja mówi, do której wersji reguł klient zapłacił. Kupnojący tanio dostał
v1 i nadal działa na v1 — nic mu nie zabieramy. Nowa wersja reguł kosztuje
jednego dolara i daje więcej. Stary klient decyduje sam.

Nie ukrywamy przed klientem, że reguły nowe są droższe — mówimy wprost
w programie, co dokładnie dostaje.
"""

import i18n

V1 = 1
V2 = 2

CURRENT = V2

RULES = {
    V1: {
        'name': 'podstawowe',
        'detectors': ['exif', 'gps', 'serial', 'artist', 'software', 'lens',
                      'datetime', 'thumbnail_jpeg'],
        'formats': ['.jpg', '.jpeg', '.jpe', '.tif', '.tiff'],
        'promise': 'GPS, numer seryjny, autor i ukryta miniatureka w JPEG.',
    },
    V2: {
        'name': 'pelne',
        'detectors': ['exif', 'gps', 'serial', 'artist', 'software', 'lens',
                      'datetime', 'thumbnail_jpeg', 'thumbnail_heic',
                      'xmp', 'iptc', 'png_chunks', 'jpeg_comments',
                      'trailing_data', 'video_gps', 'free_text_pii'],
        'formats': ['.jpg', '.jpeg', '.jpe', '.png', '.tif', '.tiff', '.webp',
                    '.heic', '.heif', '.avif', '.jfif', '.bmp', '.gif',
                    '.dng', '.cr2', '.nef', '.arw', '.orf', '.rw2', '.mp4',
                    '.mov', '.m4v', '.3gp'],
        'promise': ('Wszystko z v1 plus XMP, IPTC, chunki PNG, komentarze JPEG, '
                    'dane doklejone po obrazie, GPS w wideo i HEIC z iPhone\'a. '
                    'Wykrywa tez adresy i telefony w wolnym tekście.'),
    },
}

# Co nowego w danej wersji — pokazywane klientowi, ktory ma starsza licencje
UPGRADE_NOTES = {
    V1: [
        ('Zdjecia z iPhone\'a (.HEIC)', 'HEIC/HEIF otwierane i czytane'),
        ('Adres domu w opisie', '15 wzorcow: ulica, kod pocztowy, telefon, e-mail'),
        ('XMP i IPTC', 'miedawaj ukrywaja GPS, mialko i kraj'),
        ('Dane doklejone PO obrazie', 'czesc plikow ma bajty po znaczniku konca'),
        ('GPS w wideo', 'MP4/MOV: atom udta'),
    ],
}


def detectors_for(ruleset):
    return set(RULES.get(ruleset, RULES[CURRENT])['detectors'])


def formats_for(ruleset):
    return set(RULES.get(ruleset, RULES[CURRENT])['formats'])


def supports(ruleset, detector):
    return detector in detectors_for(ruleset)


def promise(ruleset):
    return i18n.tr(RULES.get(ruleset, RULES[CURRENT])['promise'])


def upgrades_available(purchased):
    out = []
    for v in sorted(RULES):
        if v <= purchased:
            continue
        out.append({
            'version': v,
            'name': i18n.tr(RULES[v]['name']),
            'promise': i18n.tr(RULES[v]['promise']),
            'new': [(i18n.tr(t), i18n.tr(d))
                    for t, d in UPGRADE_NOTES.get(v, [])],
        })
    return out