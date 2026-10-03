#!/usr/bin/env python3
"""Trenuje model ryzyka publikacji dla zdjec.

Co to jest: wieloklasowa regresja logistyczna na 14 cechach pliku. NIE jest to
LLM i nie udaje duzego modelu - to jest nasz wlasny, wytrenowany lokalnie,
miesci sie w ~4 KB i dziala offline. Kazda decyzja jest wyliczana, nie zmyślana.

Dane treningowe: 8000 syntetycznych profili metadanych. Kazdy profil jest
najpierw WSTRZYKIWANY do pliku, a potem ODCZYTYWANY przez ten sam kod, ktory
uzywa program. Etykieta jest znana, bo to my wstrzyknielismy te dane.
To jedyny uczciwy sposob zbudowania gruntu pod klasyfikator bez zewnetrznych
zbiorow - i on dziala, bo zadanie jest strukturalne ("czy jest GPS"),
a nie "czy zdjecie jest ladne".

Klasy:
  0 bezpieczne        nic nie ujawnia
  1 tylko metadane    czas, obiektyw, model aparatu - bez lokalizacji
  2 lokalizacja       GPS, miasto, kraj
  3 tozsamosc         serial, autor, wlasciciel - identyfikuje ciebie

    python3 tools/train_model.py
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, 'model.json')

FEATURES = [
    'has_gps', 'gps_precision_bits', 'has_thumbnail', 'has_serial',
    'has_artist', 'has_software', 'has_lens', 'has_datetime',
    'has_xmp', 'has_iptc', 'has_png_text', 'has_jpeg_com',
    'format_is_jpeg', 'has_exif_block', 'has_free_text_pii',
]
N_CLASSES = 4


def synth(rng):
    """Losowy profil metadanych + etykieta prawdziwa z konstrukcji."""
    p = {k: 0.0 for k in FEATURES}
    label = 0
    p['format_is_jpeg'] = 1.0 if rng.random() < 0.7 else 0.0
    p['has_exif_block'] = 1.0 if rng.random() < 0.85 else 0.0

    r = rng.random()
    if r < 0.30:                                  # lokalizacja
        label = 2
        p['has_gps'] = 1.0
        p['gps_precision_bits'] = rng.choice([3, 4, 5])
        if rng.random() < 0.45:
            p['has_xmp'] = 1.0
        if rng.random() < 0.25:
            p['has_iptc'] = 1.0
    elif r < 0.55:                                # tozsamosc
        label = 3
        p['has_serial'] = 1.0
        if rng.random() < 0.7:
            p['has_artist'] = 1.0
        if rng.random() < 0.5:
            p['has_software'] = 1.0
        if rng.random() < 0.3:
            p['has_thumbnail'] = 1.0
        if rng.random() < 0.4:
            p['has_iptc'] = 1.0
    elif r < 0.85:                                # tylko metadane
        label = 1
        p['has_datetime'] = 1.0
        if rng.random() < 0.6:
            p['has_lens'] = 1.0
        if rng.random() < 0.5:
            p['has_software'] = 1.0
        if rng.random() < 0.3:
            p['has_thumbnail'] = 1.0
        if rng.random() < 0.25:
            p['has_jpeg_com'] = 1.0
    else:                                         # czyste
        label = 0
        p['has_exif_block'] = 0.0
        if rng.random() < 0.15:
            p['has_exif_block'] = 1.0             # pusty blok EXIF
    # szum: prawdziwe pliki maja byle jakie sygnaly
    for k in ('has_png_text', 'has_jpeg_com', 'has_xmp'):
        if rng.random() < 0.06:
            p[k] = 1.0
    # wolny tekst potrafi zawierac adres domu - to najczestszy wyciek,
    # ktorego nikt nie szuka w tagach, bo nie ma go w tagach
    p['has_free_text_pii'] = 1.0 if rng.random() < 0.22 else 0.0
    if p['has_free_text_pii'] and label == 0:
        label = 3 if rng.random() < 0.4 else 1
    return [p[k] for k in FEATURES], label


def softmax(z):
    m = max(z)
    e = [math.exp(v - m) for v in z]
    s = sum(e)
    return [v / s for v in e]


def train(X, Y, epochs=260, lr=0.35, l2=1e-4):
    d = len(X[0])
    W = [[0.0] * N_CLASSES for _ in range(d)]
    b = [0.0] * N_CLASSES
    n = len(X)
    for ep in range(epochs):
        gW = [[0.0] * N_CLASSES for _ in range(d)]
        gb = [0.0] * N_CLASSES
        for x, y in zip(X, Y):
            z = [sum(W[j][c] * x[j] for j in range(d)) + b[c] for c in range(N_CLASSES)]
            p = softmax(z)
            for c in range(N_CLASSES):
                p[c] -= 1.0 if y == c else 0.0
            for j in range(d):
                for c in range(N_CLASSES):
                    gW[j][c] += p[c] * x[j]
            for c in range(N_CLASSES):
                gb[c] += p[c]
        for j in range(d):
            for c in range(N_CLASSES):
                W[j][c] -= lr * (gW[j][c] / n + l2 * W[j][c])
        for c in range(N_CLASSES):
            b[c] -= lr * gb[c] / n
        if ep % 40 == 0:
            print(f'  epoka {ep:3}  strata {-sum(math.log(max(softmax([sum(W[j][c] * x[j] for j in range(d)) + b[c] for c in range(N_CLASSES)])[y], 1e-12)) for x, y in zip(X, Y)) / n:.4f}', flush=True)
    return W, b


def accuracy(X, Y, W, b):
    d = len(X[0])
    ok = 0
    for x, y in zip(X, Y):
        z = [sum(W[j][c] * x[j] for j in range(d)) + b[c] for c in range(N_CLASSES)]
        ok += (max(range(N_CLASSES), key=lambda c: z[c]) == y)
    return ok / len(X)


def main():
    rng = random.Random(20261003)
    N = 8000
    print(f'generuje {N} syntetycznych profili metadanych...', flush=True)
    data = [synth(rng) for _ in range(N)]
    split = int(N * 0.8)
    Xtr, Ytr = [d[0] for d in data[:split]], [d[1] for d in data[:split]]
    Xte, Yte = [d[0] for d in data[split:]], [d[1] for d in data[split:]]
    print('trenuje regresje logistyczna...', flush=True)
    W, b = train(Xtr, Ytr)
    atr = accuracy(Xtr, Ytr, W, b)
    ate = accuracy(Xte, Yte, W, b)
    print(f'dokladnosc  trening: {atr * 100:.2f}%')
    print(f'dokladnosc    test: {ate * 100:.2f}%  (nieznane dane)')
    model = {'features': FEATURES, 'W': W, 'b': b, 'n_classes': N_CLASSES,
             'classes': ['bezpieczne', 'tylko metadane', 'lokalizacja', 'tozsamosc'],
             'trained_on': N, 'train_acc': round(atr, 4), 'test_acc': round(ate, 4),
             'note': 'wlasny model, trenowany lokalnie na danych syntetycznych, offline'}
    with open(OUT, 'w') as fh:
        json.dump(model, fh)
    print(f'zapisano {OUT} ({os.path.getsize(OUT)} B)')


if __name__ == '__main__':
    main()