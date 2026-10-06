#!/usr/bin/env python3
"""photoscrub — licencjonowanie.

Model:
  • Jedna opłata, jeden klucz, wszystko odblokowane (skan + czyszczenie).
  • Klucz to podpisany Ed25519em payload. Podpis jest w samym kluczu, wiec
    działa offline i nie da się go podrobić bez prywatnego klucza.
  • Klucz jest związany z maszyną (machine_id) — jedna instalacja, jeden komputer.
  • 7 dni grace offline: klucz działa bez internetu, ale nie w nieskończoność.

Weryfikacja jest lokalna — zero serwerów, zero kosztów, zero telemetrii.
Jeśli kiedyś potrzebujesz cofnięcia klucza (zwrot w Polar), dojdzie serwer;
na razie odwołanie jest tylko u Ciebie w ~/.secrets/photoscrub/issued.json.
"""
import base64
import i18n
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import uuid

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# ── klucz publiczny dołączony do programu (bezpieczny do publikacji) ──────────
PUBLIC_KEY_HEX = '967b91b5336b0a995709683fe8cc918f845c6352fc243b16e62b2147ca82f578'

SERVER = 'https://talus-license-server.<twoja-domena>.workers.dev'
GRACE_SECONDS = 7 * 24 * 3600
PREFIX = 'PHOTOSCRUB-'


def _home():
    if os.name == 'nt':
        base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
    else:
        base = os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
    p = os.path.join(base, 'photoscrub')
    os.makedirs(p, exist_ok=True)
    return p


def store_path():
    return os.path.join(_home(), 'license.json')


def machine_id():
    """Stabilny identyfikator maszyny. Windows: MachineGuid z rejestru."""
    if platform.system() == 'Windows':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r'SOFTWARE\Microsoft\Cryptography') as k:
                return winreg.QueryValueEx(k, 'MachineGuid')[0]
        except Exception:
            pass
    for path in ('/etc/machine-id', '/var/lib/dbus/machine-id'):
        try:
            with open(path) as fh:
                v = fh.read().strip()
                if v:
                    return v
        except OSError:
            continue
    h = hashlib.sha256()
    for cmd in (['uname', '-a'], ['hostname']):
        try:
            h.update(subprocess.run(cmd, capture_output=True, timeout=5).stdout)
        except Exception:
            pass
    h.update(uuid.getnode().to_bytes(8, 'little'))
    return h.hexdigest()


def is_pretty(key):
    k = (key or '').strip().upper().replace(' ', '')
    return k.startswith(PREFIX)


def decode_pretty(key):
    """PHOTOSCRUB-XXXXX-XXXXX-... -> canonicalne base64(payload).base64(sig)

    Uzywamy RFC 4648 base32 (A-Z, 2-7). Jest bezstratny - bez zabawy z bitami.
    Dlatego klucz jest dlugi (~280 znakow) i to jest cena pracy offline:
    podpis musi siedziec w samym kluczu, inaczej kazde uruchomienie
    wymagalo serwera.
    """
    body = (key or '').strip().upper().replace(' ', '')[len(PREFIX):]
    body = body.replace('-', '')
    pad = '=' * (-len(body) % 8)
    raw = base64.b32decode(body + pad)
    return raw.decode()


def encode_pretty(canonical):
    """canonicalne -> PHOTOSCRUB-XXXXX-... (wysylasz klientowi, klient wkleja)"""
    b32 = base64.b32encode(canonical.encode()).decode().rstrip('=')
    return PREFIX + '-'.join(b32[i:i + 5] for i in range(0, len(b32), 5))


def purchased_ruleset(payload):
    """Zakupiona wersja regul. Brak pola = 1 (najstarsze licencje)."""
    try:
        return max(1, int(payload.get('r', 1)))
    except (TypeError, ValueError):
        return 1


def verify(canonical, expect_product='photoscrub'):
    """Sprawdza podpis + pola. Zwraca (ok, payload|error)."""
    try:
        pb, sb = canonical.split('.', 1)
        payload_b = base64.urlsafe_b64decode(pb + '=' * (-len(pb) % 4))
        sig_b = base64.urlsafe_b64decode(sb + '=' * (-len(sb) % 4))
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUBLIC_KEY_HEX)).verify(sig_b, payload_b)
        p = json.loads(payload_b)
    except InvalidSignature:
        return False, i18n.tr('podpis nieaktualny - klucz nie pochodzi z tego programu')
    except (ValueError, KeyError, Exception) as e:
        return False, i18n.tr('klucz uszkodzony ({err})', err=type(e).__name__)
    if p.get('p') != expect_product:
        return False, i18n.tr('ten klucz jest do innego produktu')
    exp = p.get('e') or 0
    try:
        if exp and time.time() > float(exp):
            return False, i18n.tr('klucz wygasł')
    except (TypeError, ValueError):
        pass
    return True, p


def save(canonical):
    with open(store_path(), 'w') as fh:
        json.dump({'key': canonical, 'saved_at': time.time()}, fh)
    try:
        os.chmod(store_path(), 0o600)
    except OSError:
        pass


def load():
    try:
        with open(store_path()) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def activate(key):
    """Sprawdza klucz lokalnie i zapisuje. Weryfikacja podpisu = jedyna brama."""
    canonical = decode_pretty(key) if is_pretty(key) else key.strip()
    ok, payload = verify(canonical)
    if not ok:
        return False, payload
    mid = payload.get('m')
    here = machine_id()[:16]
    if mid and mid != here:
        return False, i18n.tr('klucz aktywowany na innej maszynie ({mid})',
                              mid=mid[:8] + '...')
    save(canonical)
    return True, payload


def state():
    """'ok' | 'grace' | powod blady. Zwraca (status, info, payload|None)."""
    blob = load()
    if not blob:
        return 'brak', i18n.tr('brak klucza'), None
    ok, payload = verify(blob['key'])
    if not ok:
        return 'bledny', payload, None
    mid = payload.get('m')
    if mid and mid != machine_id()[:16]:
        return 'bledny', i18n.tr('klucz aktywowany na innej maszynie'), None
    age = time.time() - blob.get('saved_at', 0)
    if age < GRACE_SECONDS:
        return 'ok', payload.get('o') or i18n.tr('aktywny'), payload
    return 'grace', i18n.tr('poza okresem grace ({days} dni)',
                                days=f'{(age - GRACE_SECONDS) / 86400:.0f}'), payload


def _cli(argv):
    import argparse
    ap = argparse.ArgumentParser('photoscrub-license')
    ap.add_argument('action', choices=['show', 'activate', 'machine'])
    ap.add_argument('key', nargs='?')
    a = ap.parse_args(argv)
    if a.action == 'machine':
        print(machine_id())
        return 0
    if a.action == 'activate':
        ok, msg = activate(a.key or input('Klucz: '))
        print(('OK: ' + str(msg)) if ok else ('BLAD: ' + str(msg)))
        return 0 if ok else 1
    st, info, _ = state()
    print(f'status: {st}')
    print(f'info:   {info}')
    print(f'plik:   {store_path()}')
    return 0


if __name__ == '__main__':
    sys.exit(_cli(sys.argv[1:]))