#!/usr/bin/env python3
"""Wydawanie kluczy photoscrub (uruchamiasz TY, na swoim kompie, po sprzedaży).

Klucz prywatny lezy w ~/.secrets/photoscrub/signing_key.json i NIGDY nie trafia
do repo ani do programu. Do programu wchodzi tylko klucz publiczny.

    python3 tools/issue.py --email klient@example.com --name "Jan Kowalski"
    python3 tools/issue.py --email ... --name ... --machine <machine_id>
    python3 tools/issue.py --email ... --name ... --trial          # 14 dni, 0 zl
"""
import argparse
import base64
import hashlib
import json
import os
import secrets
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402

SECRETS = os.path.expanduser('~/.secrets/photoscrub')
KEYFILE = f'{SECRETS}/signing_key.json'
LEDGER = f'{SECRETS}/issued.json'
PUBLIC_KEY_HEX = None  # wklejany z issue.py do license.py po generate


def load_or_create_keypair():
    os.makedirs(SECRETS, exist_ok=True)
    os.chmod(SECRETS, 0o700)
    if os.path.exists(KEYFILE):
        with open(KEYFILE) as fh:
            return json.load(fh)
    sk = Ed25519PrivateKey.generate()
    hexpriv = sk.private_bytes_raw().hex()
    hexpub = sk.public_key().public_bytes_raw().hex()
    blob = {'private_key_hex': hexpriv, 'public_key_hex': hexpub,
            'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    with open(KEYFILE, 'w') as fh:
        json.dump(blob, fh, indent=1)
    os.chmod(KEYFILE, 0o600)
    return blob


def sign(payload, priv_hex):
    sk = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(priv_hex))
    raw = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode()
    sig = sk.sign(raw)
    return base64.urlsafe_b64encode(raw).decode().rstrip('=') + '.' + \
        base64.urlsafe_b64encode(sig).decode().rstrip('=')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--generate', action='store_true', help='utworz para kluczy')
    ap.add_argument('--email', required=False)
    ap.add_argument('--name', required=False)
    ap.add_argument('--machine', help='machine_id klienta (bez tego klucz jest wolny)')
    ap.add_argument('--trial', action='store_true')
    ap.add_argument('--days', type=int, default=0, help='0 = bezterminowy')
    ap.add_argument('--ruleset', type=int, default=1,
                    help='zakupiona wersja regul (1 = podstawowe, 2 = pelne)')
    a = ap.parse_args()

    kp = load_or_create_keypair()
    if a.generate:
        print(f'klucz publiczny (wklej do license.py): {kp["public_key_hex"]}')
        print(f'klucz prywatny zapisany w {KEYFILE} (0600, poza repo)')
        return 0

    if not a.email:
        ap.error('--email wymagane')

    now = int(time.time())
    # Krotkie pola = krotszy klucz. Klucz jest wklejany do programu, wiec liczy sie
    # kazdy bajt: 8 znakow nazwa firmy moze poczekac na fakture.
    payload = {
        'p': 'photoscrub',
        'l': uuid.uuid4().hex[:8],
        't': 'tr' if a.trial else 'fu',
        'o': (a.name or '')[:24],
        'i': now,
        'e': now + (a.days * 86400 if a.days else 0),
        'm': (a.machine or '')[:16] or None,
        'r': a.ruleset,
    }
    canonical = sign(payload, kp['private_key_hex'])

    # czytelna forma do wyslania
    import license as lic
    pretty = lic.encode_pretty(canonical)

    rec = {'canonical': canonical, 'pretty': pretty, 'payload': payload,
           'issued_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))}
    led = []
    if os.path.exists(LEDGER):
        with open(LEDGER) as fh:
            led = json.load(fh)
    led.append(rec)
    with open(LEDGER, 'w') as fh:
        json.dump(led, fh, indent=1)
    os.chmod(LEDGER, 0o600)

    print(f'\nKLUCZ DKLIENTA ({payload["t"]}):\n\n{pretty}\n')
    print(f'customer: {a.email}')
    print(f'bound to machine: {a.machine or "NIE (wolny klucz)"}')
    print(f'expires: {"brak" if not payload["e"] else time.strftime("%Y-%m-%d", time.gmtime(payload["e"]))}')
    print(f'\nwpisany do {LEDGER}')


if __name__ == '__main__':
    main()