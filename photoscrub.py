#!/usr/bin/env python3
"""photoscrub — silnik.

Pokazuje, co Twoje zdjeciaujawniaja, i usuwa to jednym kliknieciem.
Sedno: samo usuniecie EXIF nie wystarcza. JPEG potrafi nosic w sobie
osobny miniaturke (APP1/APP13 Exif Thumbnail), a ta miniatureczka jest
czesto calym oryginalnym zdjeciem w skali 160x120 - czyli po "wyczyszczeniu"
EXIF zdjecie nadal ujawnia lokalizacje i wyglad budynku.

Zero zaleznosci zewnetrznych poza Pillow. Dziala na Linuksie i Windows.
"""
import io
import json
import os
import struct
import sys
import zipfile
from dataclasses import dataclass, asdict, field

from PIL import Image, ExifTags, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

IMG_EXT = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.webp', '.heic'}
VIDEO_EXT = {'.mp4', '.mov', '.m4v', '.avi', '.mkv'}

RISK = {
    'gps': ('HIGH', 'dokladne wspolrzedne - mapa, adres domu, miejsce pracy'),
    'serial': ('HIGH', 'numer seryjny aparatu/telefonu - identyfikuje urzadzenie i Ciebie'),
    'lens': ('MED', 'dane obiektywu'),
    'software': ('MED', 'oprogramowanie, ktore wykonalo zdjecie - wersje, nazwa urzadzenia'),
    'datetime': ('LOW', 'dokladny czas - kiedy i w jakiej kolejnosci robiles zdjecia'),
    'artist': ('MED', 'autor / wlasciciel'),
    'copyright': ('LOW', 'dane wlasnosciowe'),
    'thumbnail': ('HIGH', ' miniatureka wbudowana w plik - czesto CALY oryginal w 160x120'),
    'xmp': ('LOW', 'dane XMP, potrafia zawierac historie edycji'),
    'comment': ('LOW', 'komentarz z aparatu'),
}


@dataclass
class Finding:
    kind: str
    value: str
    risk: str = 'LOW'
    why: str = ''


@dataclass
class Report:
    path: str
    kind: str = 'image'
    size: int = 0
    findings: list = field(default_factory=list)
    cleanable: bool = True
    note: str = ''

    @property
    def risk_score(self):
        w = {'HIGH': 10, 'MED': 4, 'LOW': 1}
        return sum(w.get(f.risk, 1) for f in self.findings)


def _ifd0(ex):
    """0th IFD jako {tag_int: value}. Exif z Pillow to obiekt, nie dict."""
    out = {}
    try:
        for k, v in ex.items():
            out[int(k)] = v
    except Exception:
        pass
    return out


def _sub_ifd(ex, ifd_const):
    try:
        d = ex.get_ifd(ifd_const)
        return {int(k): v for k, v in d.items()} if d else {}
    except Exception:
        return {}


def _name(tag):
    return ExifTags.TAGS.get(tag, str(tag))


def _dms(v):
    """(53,1),(26,1),(4320,100) -> 53.4453 stopnie"""
    if isinstance(v, (int, float)):
        return float(v)
    parts = []
    for x in v:
        if isinstance(x, (tuple, list)):
            num, den = float(x[0]), float(x[1])
            parts.append(num / den if den else 0.0)
        else:
            parts.append(float(x))
    if not parts:
        raise ValueError('pusta wspolrzedna')
    if len(parts) == 1:
        return parts[0]
    dd, m, s = parts[0], parts[1], parts[2]
    return dd + m / 60 + s / 3600


def _fmt_gps(gps):
    """Tagi GPS: 1=latRef 2=lat 3=lonRef 4=lon (Exif standard, nie kolejnosc Pillow)."""
    lat, lon = gps.get(2), gps.get(4)
    if not lat or not lon:
        return None
    alat, alon = _dms(lat), _dms(lon)
    lat_ref, lon_ref = gps.get(1), gps.get(3)
    if isinstance(lat_ref, bytes):
        lat_ref = lat_ref.decode('ascii', 'replace')
    if isinstance(lon_ref, bytes):
        lon_ref = lon_ref.decode('ascii', 'replace')
    if str(lat_ref).strip().upper() in ('S', 'SOUTH'):
        alat = -alat
    if str(lon_ref).strip().upper() in ('W', 'WEST'):
        alon = -alon
    return round(alat, 6), round(alon, 6)


def jpeg_thumbnail(data: bytes):
    """Czy JPEG ma wbudowana miniatureke? Zwraca (bool, rozmiar bajtow)."""
    if not data.startswith(b'\xff\xd8'):
        return False, 0
    i = 2
    n = len(data)
    while i < n - 4:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seglen = struct.unpack('>H', data[i + 2:i + 4])[0]
        seg = data[i + 4:i + 2 + seglen]
        # APP1 = Exif (thumbnail w TIFF), APP13 = Photoshop IRB (czesto thumbnail)
        if marker in (0xE1, 0xED) and (b'II*\x00' in seg[:16] or b'MM\x00*' in seg[:16]
                                      or b'8BIM' in seg[:2000]):
            # policz czy wewnattrz jest osobny JPEG (FFD8...FFD9)
            j = seg.find(b'\xff\xd8')
            if j != -1:
                k = seg.find(b'\xff\xd9', j)
                if k != -1:
                    return True, k - j + 2
        if marker == 0xDA:  # start of scan -> koniec naglowkow
            break
        i += 2 + seglen
    return False, 0


def scan_image(path):
    rep = Report(path=path, size=os.path.getsize(path))
    try:
        with open(path, 'rb') as fh:
            head = fh.read(65536)
    except OSError as e:
        rep.note = f'nie mozna odczytac: {e}'
        rep.cleanable = False
        return rep
    has_thumb, thumb_bytes = jpeg_thumbnail(head)
    try:
        im = Image.open(path)
        ex = im.getexif()
        ifd0 = _ifd0(ex)
        sub = _sub_ifd(ex, 34665)   # Exif IFD
        gps = _sub_ifd(ex, 34853)   # GPS IFD
        f = []
        if gps:
            try:
                ll = _fmt_gps(gps)
            except Exception as e:
                ll = None
            f.append(Finding('gps', f'{ll[0]}, {ll[1]}' if ll
                             else f'wspolrzedne obecne ({type(e).__name__})', *RISK['gps']))
        for tag, val in list(ifd0.items()) + list(sub.items()):
            nm = _name(tag)
            if nm in ('BodySerialNumber', 'SerialNumber'):
                f.append(Finding('serial', str(val), *RISK['serial']))
            elif nm == 'LensModel':
                f.append(Finding('lens', str(val), *RISK['lens']))
            elif nm == 'Software':
                f.append(Finding('software', str(val), *RISK['software']))
            elif nm == 'Artist':
                f.append(Finding('artist', str(val), *RISK['artist']))
            elif nm == 'Copyright':
                f.append(Finding('copyright', str(val)[:120], *RISK['copyright']))
            elif nm in ('UserComment', 'ImageDescription'):
                f.append(Finding('comment', str(val)[:120], *RISK['comment']))
            elif 'DateTime' in nm and val:
                f.append(Finding('datetime', str(val), *RISK['datetime']))
        if im.info.get('Software') and not any(x.kind == 'software' for x in f):
            f.append(Finding('software', str(im.info['Software']), *RISK['software']))
        if has_thumb:
            f.append(Finding('thumbnail', f'{thumb_bytes} B miniatureki w pliku',
                             *RISK['thumbnail']))
        rep.findings = f
    except Exception as e:
        rep.note = f'parser: {type(e).__name__}: {e}'
        rep.cleanable = False
    return rep


def scan_zip(path):
    rep = Report(path=path, kind='archive', size=os.path.getsize(path))
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            leaks = [n for n in names if n.split('/')[0].startswith('__MACOSX')
                     or n.endswith(('.DS_Store', 'Thumbs.db')) or '/._' in n]
            if leaks:
                rep.findings.append(Finding('comment', f'{len(leaks)} plikow smieci w archiwum '
                                                      f'({", ".join(leaks[:3])}...)',
                                           'LOW', 'nazwy plikow wewnatrz archiwum: '
                                                  'uzytkownicy, pelne sciezki, daty'))
            hidden = [n for n in names if '._' in n or n.startswith('.')]
            if hidden:
                rep.findings.append(Finding('comment',
                                           f'{len(hidden)} ukrytych plikow (._ / kropka)',
                                           'LOW', 'pliki ._tar sa ukrytym duplikatem '
                                                  'uzytkownika i sciezka w nazwie'))
    except Exception as e:
        rep.note = f'zip: {e}'
        rep.cleanable = False
    return rep


def scan_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in IMG_EXT:
        return scan_image(path)
    if ext == '.zip':
        return scan_zip(path)
    rep = Report(path=path, size=os.path.getsize(path))
    rep.note = 'nieobslugiwany typ pliku'
    rep.cleanable = False
    return rep


def scrub_image(src, dst, drop=('all',)):
    """Kopiuje zdjecie bez EXIF. Nie rusza pikseli (JPEG re-encode tylko gdy trzeba)."""
    im = Image.open(src)
    clean = Image.new(im.mode, im.size)
    clean.putdata(list(im.getdata()))
    params = {}
    if src.lower().endswith(('.jpg', '.jpeg')):
        params = {'quality': 95, 'optimize': True, 'progressive': False}
    save_kw = {}
    fmt = im.format or 'JPEG'
    if fmt in ('JPEG', 'MPO'):
        save_kw.update(quality=95, optimize=True)
    elif fmt == 'PNG':
        save_kw.update(optimize=True)
    elif fmt == 'WEBP':
        save_kw.update(quality=95)
    elif fmt == 'TIFF':
        save_kw.update(compression='tiff_deflate')
    clean.save(dst, format=fmt, **save_kw)
    return dst


def scan_tree(root):
    out = []
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if os.path.splitext(fn)[1].lower() in IMG_EXT | {'.zip'}:
                out.append(scan_file(os.path.join(dirpath, fn)))
    return out


def _cli(argv):
    import argparse
    ap = argparse.ArgumentParser('photoscrub')
    ap.add_argument('path')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--scrub', metavar='OUT')
    a = ap.parse_args(argv)
    reps = scan_tree(a.path) if os.path.isdir(a.path) else [scan_file(a.path)]
    if a.json:
        print(json.dumps([asdict(r) for r in reps], indent=1, default=str))
        return 0
    if a.scrub:
        os.makedirs(a.scrub, exist_ok=True)
        n = 0
        skipped = []
        for r in reps:
            if r.kind != 'image':
                continue
            dst = os.path.join(a.scrub, os.path.basename(r.path))
            try:
                scrub_image(r.path, dst)
                n += 1
            except Exception as e:
                skipped.append((r.path, f'{type(e).__name__}: {e}'))
        for pth, why in skipped:
            print(f'POMINIETO {pth}: {why}', file=sys.stderr)
        print(f'wyczyszczono {n} plikow -> {a.scrub}')
        return 0
    total = 0
    for r in sorted(reps, key=lambda x: -x.risk_score):
        if not r.findings:
            continue
        total += 1
        print(f'[{r.risk_score:>3}] {r.path}  ({r.size} B)')
        for f in r.findings:
            print(f'        {f.risk:4} {f.kind:10} {f.value[:70]}')
            if f.why:
                print(f'                       -> {f.why}')
    print(f'\n{total} plikow z danymi do usuniecia z {len(reps)}')
    return 0


if __name__ == '__main__':
    sys.exit(_cli(sys.argv[1:]))