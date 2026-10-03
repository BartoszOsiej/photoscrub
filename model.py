#!/usr/bin/env python3
"""photoscrub.model — nasz wlasny model ryzyka publikacji.

Nie jest to LLM. Jest to regresja logistyczna wytrenowana lokalnie
(tools/train_model.py) na 8000 syntetycznych profili metadanych. Model ma
~4 KB, dziala offline, i kazda jego decyzja jest liczona ze wspolczynnikow,
ktore da zobaczyc. Nie ma w nim zadnej halucynacji, bo nie generuje tekstu -
tylko klasyfikuje."""
import json
import math
import os
import re

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model.json')
_M = None


def load():
    global _M
    if _M is None:
        try:
            with open(PATH) as fh:
                _M = json.load(fh)
        except (OSError, ValueError):
            _M = None
    return _M


PII = [
    (r'\b(ul|al|pl|os|ulica|aleja)\s*\.\s*\w+', 'ulica z numerem'),
    (r'\b\d+\s?-\s?\d{3}\b', 'kod pocztowy'),
    (r'\b(?:tel|telefon|mobile|tel\.)\s*[:.]', 'numer telefonu w opisie'),
    (r'\b\d{3}[\s-]?\d{3}[\s-]?\d{3}\b', 'numer telefonu'),
    (r'\b\S+@\S+\.\w{2,}\b', 'adres e-mail'),
    (r'\b(mieszkanie|dom|mieszkanca|adres zamieszkania)\b', 'wzmianka o miejscu zamieszkania'),
    (r'\b\d{1,4}\s+[A-Z][a-z]+\s+(3|m)\b', 'adres w stylu "12 Kwiatowa 3"'),
    (r'(?i)\b(prywatne|nie publikowac|do not publish)\b', 'instrukcja "nie publikowac"'),
]


def free_text_pii(findings):
    """Szuka adresow, kodow pocztowych i telefonow w WOLNYM TEKSCIE.
    To najczestszy wyciek i najmniej widoczny: nie ma go w tagach, jest w opisie."""
    hits = []
    for f in findings:
        if f.kind not in ('comment', 'copyright', 'artist'):
            continue
        txt = f.value or ''
        for pat, label in PII:
            if re.search(pat, txt):
                hits.append(label)
    return hits


def features_of(rep):
    """Zamienia findings pliku na wektor 14 cech - identyczna definicja
    jak przy treningu, wiec model widzi to, czego uczyl sie."""
    kinds = {f.kind for f in rep.findings}
    labels = ' '.join(f.value.lower() for f in rep.findings)
    has_gps = 'gps' in kinds
    bits = 0
    if has_gps:
        # ile cyfr po przecinku we wspolrzednych -> ile dokladnosci
        for tok in labels.replace(',', ' ').split():
            if tok.count('.') == 1 and len(tok.split('.')[1]) <= 6 and tok[0].isdigit():
                bits = max(bits, len(tok.split('.')[1]))
    ext = os.path.splitext(rep.path)[1].lower()
    vals = {
        'has_gps': 1.0 if has_gps else 0.0,
        'gps_precision_bits': float(bits),
        'has_thumbnail': 1.0 if 'thumbnail' in kinds else 0.0,
        'has_serial': 1.0 if 'serial' in kinds else 0.0,
        'has_artist': 1.0 if 'artist' in kinds else 0.0,
        'has_software': 1.0 if 'software' in kinds else 0.0,
        'has_lens': 1.0 if 'lens' in kinds else 0.0,
        'has_datetime': 1.0 if 'datetime' in kinds else 0.0,
        'has_xmp': 1.0 if 'xmp' in labels else 0.0,
        'has_iptc': 1.0 if 'iptc' in labels else 0.0,
        'has_png_text': 1.0 if 'png ' in labels else 0.0,
        'has_jpeg_com': 1.0 if 'jpeg com' in labels else 0.0,
        'format_is_jpeg': 1.0 if ext in ('.jpg', '.jpeg', '.jpe', '.jfif') else 0.0,
        'has_exif_block': 1.0 if any(f.kind not in ('comment',) for f in rep.findings) else 0.0,
        'has_free_text_pii': 1.0 if free_text_pii(rep.findings) else 0.0,
    }
    m = load()
    if not m:
        return None
    return [vals.get(name, 0.0) for name in m['features']]


def score(rep):
    """Zwraca (klucz, klasa, pewnosc 0..1, score 0..100)."""
    m = load()
    x = features_of(rep)
    if not m or x is None:
        return None
    W, b = m['W'], m['b']
    z = [sum(W[j][c] * x[j] for j in range(len(x))) + b[c] for c in range(m['n_classes'])]
    mx = max(z)
    e = [math.exp(v - mx) for v in z]
    s = sum(e)
    p = [v / s for v in e]
    c = max(range(len(p)), key=lambda i: p[i])
    # score ryzyka: 0 dla bezpiecznego, 100 dla pelnego ujawnienia
    risk = int(round(min(100, 100 * (0.35 * p[1] + 0.65 * p[2] + 0.8 * p[3]))))
    return {'class': m['classes'][c], 'confidence': round(p[c], 3), 'risk': risk,
            'probs': {m['classes'][i]: round(p[i], 3) for i in range(len(p))},
            'features': {name: v for name, v in zip(m['features'], x) if v}}


def verdict(rep):
    """Czytelna jedna linia dla uzytkownika + twarde 'co zrobic'."""
    s = score(rep)
    if s is None:
        return None
    act = {
        'bezpieczne': 'Nic do usuwania - mozesz wrzucic to gdzie chcesz.',
        'tylko metadane': 'Zero lokalizacji, ale plik mowi kiedy i czym to zrobiono.',
        'lokalizacja': 'Ujawnia GDZIE zdjecie powstalo. Nie wrzucaj tego publicznie.',
        'tozsamosc': 'Ujawnia KTO i JAKIE urzadzenie. Nie wrzucaj tego publicznie.',
    }[s['class']]
    return s, act