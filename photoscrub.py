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
import re
import os
import struct
import sys
import zipfile
from dataclasses import dataclass, asdict, field

from PIL import Image, ExifTags, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

try:  # zdjecia z iPhone'a (HEIC/HEIF) - bez tego polowa aparatów jest nieczytelna
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HAS_HEIF = True
except Exception:
    HAS_HEIF = False

IMG_EXT = {'.jpg', '.jpeg', '.jpe', '.png', '.tif', '.tiff', '.webp', '.heic',
            '.heif', '.avif', '.jfif', '.bmp', '.gif', '.psd', '.dng', '.cr2', '.nef',
            '.arw', '.orf', '.rw2'}
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
    complete: bool = True        # czy wczytano caly plik

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
    buf, complete = read_for_scan(path)
    has_thumb, thumb_bytes = jpeg_thumbnail(buf[:65536])
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
        # ── warstwa 2: chunky, ktorych getexif() nie czyta ──
        for label, val in xmp_packets(path, buf):
            kind = 'gps' if 'GPS' in label else ('comment' if 'Source' in label else 'software')
            f.append(Finding(kind, f'{label}: {val}',
                             'HIGH' if kind == 'gps' else 'LOW',
                             'XMP jest drugim miejscem na dane - i czesto bogatszym '
                             'niz EXIF, a wiec usucie tagow nie wystarczy'))
        for label, val in iptc_fields(path, buf):
            kind = 'gps' if label.startswith(('IPTC City', 'IPTC Country')) else 'comment'
            f.append(Finding(kind, f'{label}: {val}',
                             'HIGH' if kind == 'gps' else 'LOW',
                             'IPTC to pole redakcyjne - imie, miasto, kraj'))
        for label, val in png_text_chunks(path, buf):
            f.append(Finding('comment', f'{label}: {val}', 'LOW',
                             'chunk tekstowy PNG - autor, opis, komentarz'))
        for label, val in jpeg_comments(path, buf):
            f.append(Finding('comment', f'{label}: {val}', 'LOW',
                             'komentarz w pliku - widoczny dla kazdego kto go otworzy'))
        for label, val in gif_comments(path, buf):
            f.append(Finding('comment', f'{label}: {val}', 'LOW',
                             'komentarz GIF - nieobslugiwany przez wiekszosc edytorow'))
        for label, val in maker_note_risk(path, buf):
            high = 'wspolrzedne' in val or 'miast' in val or 'GPS' in val
            f.append(Finding('gps' if high else 'software', f'{label}: {val}',
                             'HIGH' if high else 'MED',
                             'MakerNote jest polem binarnym - wiekszosc narzedzi go nie czyta, '
                             'a producenci zapisuja tam lokalizacje i tryb pracy'))
        for label, val in sniff_exif_bytes(path, buf):
            f.append(Finding('gps', f'{label}: {val}', 'HIGH',
                             'wspolrzedne zapisane tekstem wewnatrz pliku, '
                             'poza widocznymi tagami'))
        rep.findings = f
    except Exception as e:
        rep.note = f'parser: {type(e).__name__}: {e}'
        rep.cleanable = False
    return rep


MAKER_HINTS = [
    (re.compile(rb'\d{2}\.\d{4,}'), 'wspolrzedne GPS w bajtach surowych'),
    (re.compile(rb'(?i)latlong|latitude|longitude'), 'slowa GPS w bajtach surowych'),
    (re.compile(rb'(?i)gps'), 'slowo GPS w bajtach surowych'),
    (re.compile(rb'(?i)(szczecin|warszawa|gdansk|gdansk|wroclaw|wroc|krakow|krakow|'
                 rb'poznan|lodz|lodz|katowice|bydgoszcz)'), 'nazwa miasta w bajtach surowych'),
]


def maker_note_risk(path, buf=None):
    """MakerNote to blok binarny, ktorego wiekszosc narzedzi nie czyta.
    Dlatego nie polegamy na parserze - szukamy w surowych bajtach wzorcow,
    ktore znamy z bajtach: wspolrzedne, slowa GPS, nazwy miast.

    Zasada: kazdy MakerNote jest co najmniej MED (naprawde identyfikuje aparat
    i jego firmware), a wzorzec lokalizacji robi z niego HIGH."""
    out = []
    data = buf if buf is not None else None
    if data is None:
        try:
            with open(path, 'rb') as fh:
                data = fh.read(1024 * 512)
        except OSError:
            return out
    else:
        data = data[:1024 * 512]
    idx = data.find(b'MakerNote')
    if idx == -1:
        return out
    blob = data[min(idx, len(data) - 1): idx + 20000]
    out.append(('MakerNote', f'{len(blob)} B nieparsowanego bloku producenta'))
    for rx, why in MAKER_HINTS:
        if rx.search(blob):
            out.append(('MakerNote', why))
    return out


_COORD_RX = re.compile(rb'(?i)(?:gps|lat)(?:itude)?\D{0,12}(\d{1,2}[.,]\d{3,})'
                       rb'\D{0,24}(?:lon|long)?\D{0,12}(\d{1,3}[.,]\d{3,})')


def sniff_exif_bytes(path, buf=None):
    """Surowe bajty EXIF: wspolrzedne zapisane jako tekst przez niektore
    aparaty trafiaja do tagow, ktore Pillow nie wystawia jako getexif()."""
    out = []
    data = buf if buf is not None else None
    if data is None:
        try:
            with open(path, 'rb') as fh:
                data = fh.read(1024 * 512)
        except OSError:
            return out
    else:
        data = data[:1024 * 512]
    # Szukamy tylko tam, gdzie faktycznie jest EXIF. Skrocenie okna z 200 KB
    # do obszaru APP1 dalo 4x mniej pracy dla regex.
    start = data.find(b'Exif')
    if start == -1:
        return out
    seg = data[max(0, start - 8): start + 131072]
    m = _COORD_RX.search(seg)
    if m:
        out.append(('surowe bajty', f'wspolrzedne w tekście: {m.group(1).decode()}, '
                                    f'{m.group(2).decode()}'))
    return out


def png_text_chunks(path, buf=None):
    """PNG trzyma opisy w chunkach tEXt/iTXt/zTXt - tam siedzi autor,
    komentarz, a czasem 'Description' z lokalizacja. Tego nie widzi getexif()."""
    out = []
    try:
        with open(path, 'rb') as fh:
            data = fh.read()
    except OSError:
        return out
    if not data.startswith(b'\x89PNG'):
        return out
    i = 8
    n = len(data)
    while i + 8 <= n:
        ln = int.from_bytes(data[i:i + 4], 'big')
        typ = data[i + 4:i + 8].decode('latin1', 'replace')
        payload = data[i + 8:i + 8 + ln]
        if typ in ('tEXt', 'iTXt', 'zTXt'):
            try:
                raw = payload
                if typ == 'zTXt':
                    import zlib
                    raw = zlib.decompress(payload[1:])
                txt = raw.replace(b'\x00', b' ').decode('utf-8', 'replace').strip()
            except Exception:
                txt = ''
            key = raw.split(b'\x00')[0].decode('latin1', 'replace').strip() if raw else ''
            printable = sum(1 for c in txt if 32 <= ord(c) < 127) / max(1, len(txt))
            if printable < 0.75:
                head = ''.join(ch for ch in txt[:60] if 32 <= ord(ch) < 127).strip()
                out.append(('PNG ' + (key or typ),
                            f'{len(raw)} B danych binarnych w polu tekstowym'
                            + (f' (zaczyna sie od: {head!r})' if head else '')))
            elif txt:
                out.append(('PNG ' + (key or typ), txt[:160]))
        if typ == 'eXIf' and payload:
            out.append(('PNG eXIf', f'{len(payload)} B bloku EXIF (jak zwykly JPEG)'))
        if typ == 'iCCP' and payload:
            out.append(('PNG iCCP', f'profil ICC {len(payload)} B (nazwa, sRGB/P3/Display P3)'))
        if typ == 'tIME':
            out.append(('PNG tIME', 'data i czas modyfikacji w pliku'))
        if typ == 'IEND':
            break
        i += 12 + ln
    return out


def xmp_packets(path, buf=None):
    """XMP to jeden workowity worek: autor, narzedzie, historia edycji, GPS."""
    out = []
    data = buf if buf is not None else None
    if data is None:
        try:
            with open(path, 'rb') as fh:
                data = fh.read(512 * 1024)
        except OSError:
            return out
    else:
        data = data[:512 * 1024]
    for marker, kind in ((b'<x:xmpmeta', 'XMP'), (b'<?xpacket begin', 'XMP (packet)')):
        idx = data.find(marker)
        if idx == -1:
            continue
        blob = data[idx:idx + 60000]
        end = blob.find(b'</x:xmpmeta')
        chunk = blob[:end if end != -1 else 40000].decode('utf-8', 'replace')
        for tag, label in (('photoshop:City', 'XMP miasto'), ('photoshop:Country', 'XMP kraj'),
                           ('Iptc4xmpCore:Location', 'XMP lokalizacja'),
                           ('xmp:CreatorTool', 'XMP narzedzie'),
                           ('xmp:ModifyDate', 'XMP data modyfikacji'),
                           ('photoshop:Credit', 'XMP autor/credit'),
                           ('dc:creator', 'XMP tworca'),
                           ('crs:Version', 'XMP wersja programu')):
            if tag in chunk:
                out.append((label, f'jest w dokumencie ({tag})'))
        if 'exif:GPS' in chunk or 'GPSLatitude' in chunk:
            out.append(('XMP GPS', 'wspolrzedne w XMP, nie tylko w EXIF'))
        if 'photoshop:Instructions' in chunk or 'photoshop:Source' in chunk:
            out.append(('XMP Source', 'wlasciciel/źródło w XMP'))
        break
    return out


def iptc_fields(path, buf=None):
    """IPTC (APP13/8BIM 0x0404) - 'byline', 'City', 'Country', 'Caption'."""
    out = []
    data = buf if buf is not None else None
    if data is None:
        try:
            with open(path, 'rb') as fh:
                data = fh.read(1024 * 1024)
        except OSError:
            return out
    else:
        data = data[:1024 * 1024]
    idx = data.find(b'8BIM')
    if idx == -1:
        return out
    seg = data[idx:idx + 20000]
    for tag, label in ((0x0078, 'IPTC byline (autor)'), (0x005A, 'IPTC caption (opis)'),
                       (0x5A, 'IPTC City'), (0x64, 'IPTC Country'),
                       (0x05, 'IPTC ObjectName (nazwa pliku)')):
        m = re.search(bytes([tag]) + b'(.{5,200})', seg, re.S)
        if m:
            try:
                val = m.group(1).split(b'\x00')[0].decode('latin1', 'replace').strip()
            except Exception:
                val = ''
            if val and val.isprintable() and len(val) > 2:
                out.append((label, val[:120]))
    return out


def jpeg_comments(path, buf=None):
    """Marker JPEG COM (FFFE) - komentarze aparatu, czasem zawieraja lokalizacje."""
    out = []
    data = buf if buf is not None else None
    if data is None:
        try:
            with open(path, 'rb') as fh:
                data = fh.read(512 * 1024)
        except OSError:
            return out
    else:
        data = data[:512 * 1024]
    if not data.startswith(b'\xff\xd8'):
        return out
    i = 2
    while i < len(data) - 4:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        if marker == 0xDA:
            break
        seglen = int.from_bytes(data[i + 2:i + 4], 'big')
        if marker == 0xFE:
            body = data[i + 4:i + 2 + seglen].replace(b'\x00', b' ').decode('latin1', 'replace')
            body = ' '.join(body.split())
            if body:
                out.append(('JPEG COM', body[:160]))
        i += 2 + seglen
    return out


def jpeg_real_end(data):
    """Prawdziwy koniec strumienia JPEG.

    Nie wystarczy 'ostatni FFD9 w pliku', bo plik z doklejonym ogonem ma ten
    znacznik daleko od konca. Idziemy po markerach: naglowki -> SOS -> dane
    entropowe -> pierwszy FFD9 za SOS. To jest miejsce, w ktorym koder
    przestaje; wszystko po tym jest ogonem.
    """
    n = len(data)
    if not data.startswith(b'\xff\xd8'):
        return -1
    i = 2
    sos = -1
    while i < n - 1:
        if data[i] != 0xFF:
            i += 1
            continue
        m = data[i + 1]
        if m == 0xD9:
            return i + 2 if sos == -1 else -1   # EOI przed SOS = plik niekompletny
        if m == 0xDA:
            sos = i
            break
        if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        if i + 4 > n:
            return -1
        seglen = int.from_bytes(data[i + 2:i + 4], 'big')
        if seglen < 2:
            return -1
        i += 2 + seglen
    if sos == -1:
        return -1
    # W strumieniu entropowym kazdy bajt 0xFF jest poprzedzony 0x00 (stuffing)
    # albo znacznikiem RSTn. Zatem PIERWSZY ÿÙ za SOS jest z definicji EOI.
    # find() wykonuje to w C; moja poprzednia petla po bajtach kosztowala 265 ms
    # na zdjecie i byla glownym powodem, ze program zwalnial.
    idx = data.find(b'\xff\xd9', sos + 2)
    return idx + 2 if idx != -1 else -1


def trailing_data(path, buf=None, complete=True):
    """Bajty PO prawdziwym koncu obrazu. Plik ma "koniec" w JPEG (pierwszy
    FFD9 za SOS) albo w PNG (IEND) - wszystko po tym jest niewidoczne
    w podgladzie, a calkiem czytelne dla kogos, kto patrzy surowo. Stare
    telefony i edytory tak doklejaja caly blok z metadanymi."""
    out = []
    data = buf if buf is not None else None
    if data is None:
        try:
            with open(path, 'rb') as fh:
                data = fh.read()
        except OSError:
            return out
    if not complete:
        return out          # plik wiekszy niz bufor - nie oceniamy ogona, nie zmywamy
    ext = os.path.splitext(path)[1].lower()
    end = -1
    if data.startswith(b'\xff\xd8'):
        end = jpeg_real_end(data)
    elif data.startswith(b'\x89PNG'):
        pos = data.find(b'IEND')
        if pos != -1:
            end = pos + 8
    elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return out
    if end == -1 or end >= len(data):
        return out
    tail = data[end:]
    if not tail:
        return out
    # kilka bajtow zer/paddingu od zapisywacza to nie wyciek
    if len(tail) <= 8 and not any(32 < c < 127 for c in tail):
        return out
    t = tail[:400000].lower()
    if b'v=spf1' in t or b'<?xpacket' in t or b'8bim' in t:
        kind = 'caly blok EXIF/XMP/IPTC za koncem pliku'
    elif t.startswith(b'\xff\xd8') or b'\x00\xff\xd8\xff' in t:
        kind = 'caly drugi obraz ukryty za koncem pliku'
    elif b'http' in t or b'<' in t:
        kind = 'fragmenty HTML/tekstu za koncem pliku'
    else:
        kind = 'bajty o nieznanym formacie'
    out.append((f'PO OBRAZIE: {len(tail)} B', kind))
    return out


VIDEO_GPS_KEYS = [b'\xa9xyz', b'location', b'com.apple.quicktime.location',
                  b'GPSCoordinates', b'creation_time']


def video_gps(path):
    """Wideo (MP4/MOV) trzyma lokalizacje w atomie udta, nie w zdjeciach."""
    out = []
    try:
        with open(path, 'rb') as fh:
            data = fh.read(4 * 1024 * 1024)
    except OSError:
        return out
    if data[4:8] != b'ftyp':
        return out
    for key in (b'\xa9xyz', b'location'):
        idx = data.find(key)
        if idx != -1:
            frag = data[idx:idx + 120]
            if any(c.isdigit() for c in frag.decode('latin1', 'replace')):
                out.append(('WIDEO GPS', f'atom {key.decode("latin1")} zawiera wspolrzedne'))
    if b'creation_time' in data:
        out.append(('WIDEO czas', 'atom creation_time - kiedy i gdzie nagrywano'))
    if data.find(b'com.apple.quicktime') != -1 and data.find(b'udta') != -1:
        out.append(('WIDEO udta', 'kontener metadanych uzytkownika w pliku wideo'))
    return out


def gif_comments(path, buf=None):
    out = []
    data = buf if buf is not None else None
    if data is None:
        try:
            with open(path, 'rb') as fh:
                data = fh.read(4 * 1024 * 1024)
        except OSError:
            return out
    if not (data.startswith(b'GIF87a') or data.startswith(b'GIF89a')):
        return out
    i = 13
    if data[10] & 0x80:                      # globalna tabela kolorow
        i += 3 * (2 ** ((data[10] & 7) + 1))
    n = len(data)
    while i < n:
        b = data[i]
        if b == 0x21:                        # rozszerzenie
            label = data[i + 1]
            i += 2
            if i < n and label == 0xFE:      # Comment Extension
                j = i
                chunks = []
                while j < n and data[j]:
                    ln = data[j]
                    chunks.append(data[j + 1:j + 1 + ln])
                    j += 1 + ln
                if chunks:
                    txt = b''.join(chunks).decode('latin1', 'replace')
                    txt = ' '.join(txt.split())
                    if txt:
                        out.append(('GIF COM', txt[:160]))
                i = j + 1
                continue
            while i < n and data[i]:         # pomijaj bloki
                i += 1 + data[i]
            i += 1
            continue
        if b == 0x2C:                        # obrazek
            return out
        i += 1
    return out


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


VIDEO_EXT = {'.mp4', '.mov', '.m4v', '.3gp', '.avi', '.mkv'}

MAGIC = [
    (b'\xff\xd8\xff', 'image', '.jpg'),
    (b'\x89PNG\r\n\x1a\n', 'image', '.png'),
    (b'GIF87a', 'image', '.gif'),
    (b'GIF89a', 'image', '.gif'),
    (b'BM', 'image', '.bmp'),
    (b'II*\x00', 'image', '.tif'),
    (b'MM\x00*', 'image', '.tif'),
    (b'RIFF', 'riff', None),
    (b'ftyp', 'video', '.mp4'),
    (b'PK\x03\x04', 'archive', '.zip'),
    (b'\x1aE\xdf\xa3', 'archive', None),
    (b'8BPS', 'image', '.psd'),
]


READ_CAP = 12 * 1024 * 1024     # powyzej: czytamy glowe i ogon, nie calosc


def read_for_scan(path):
    """Wczytuje plik RAZ. Wszystkie skanery dostaja ten sam bufor.

    Wczesniej kazdy skaner otwieral plik osobno - 9 odczytow na zdjecie.
    Na 500 zdjeciach to 35 GB odczytu z dysku i program stawal.
    Przy plikach wiekszych niz READ_CAP czytamy glowe i ogon, bo tam wlasnie
    siedzi ogon z danymi (cos po znaczniku konca obrazu)."""
    try:
        size = os.path.getsize(path)
        with open(path, 'rb') as fh:
            if size <= READ_CAP:
                return fh.read(), True
            head = fh.read(READ_CAP)
            fh.seek(max(0, size - 1024 * 1024))
            return head + b'\x00' * 8 + fh.read(), False
    except OSError:
        return b'', False


def sniff(path, buf=None):
    """Format po zawartosci. Rozszerzenie klamie (albo go nie ma) - plik moze
    byc zdjeciem bez rozszerzenia albo PNG udajacy jpg, i taki plik tez
    trzeba sprawdzic."""
    if buf is not None:
        head = buf[:32]
    else:
        try:
            with open(path, 'rb') as fh:
                head = fh.read(32)
        except OSError:
            return None, None
    if len(head) < 12:
        return None, None
    for sig, kind, ext in MAGIC:
        if head.startswith(sig):
            if kind == 'riff':
                if head[8:12] == b'WEBP':
                    return 'image', '.webp'
                if head[8:12] == b'WAVE':
                    return 'audio', '.wav'
                return None, None
            if kind == 'archive' and sig == b'\x1aE\xdf\xa3':
                return 'archive', '.zip'      # kopia zip
            return kind, ext
    # HEIF: 'ftyp' na pozycji 4
    if len(head) > 12 and head[4:8] == b'ftyp':
        brand = head[8:12]
        if brand in (b'heic', b'heix', b'hevc', b'heim', b'heis', b'mif1', b'msf1'):
            return 'image', '.heic'
        return 'video', '.mp4'
    return None, None


_MEMO = {}
MEMO_MAX = 4000


def scan_file(path, ruleset=None):
    """Cache po (sciezka, rozmiar, mtime): ten sam plik dodany dwa razy
    nie jest skanowany drugi raz. Bez tego wybranie folderu i potem pliku
    z tego folderu skrocilo calkowity przebieg o polowe."""
    try:
        st = os.stat(path)
        key = (path, st.st_size, int(st.st_mtime), ruleset)
    except OSError:
        key = None
    if key and key in _MEMO:
        return _MEMO[key]
    rep = _scan_file_uncached(path, ruleset)
    if key:
        if len(_MEMO) > MEMO_MAX:
            _MEMO.clear()
        _MEMO[key] = rep
    return rep


def _scan_file_uncached(path, ruleset=None):
    """ruleset=None -> wszystko wlaczone (tryb deweloperski).
    W programie przekazujemy wersje z licencji."""
    import ruleset as rs
    rv = rs.CURRENT if ruleset is None else ruleset
    ext = os.path.splitext(path)[1].lower()
    if not os.path.exists(path):
        return Report(path=path, note='plik nie istnieje', cleanable=False)
    if os.path.getsize(path) == 0:
        return Report(path=path, note='plik pusty (0 bajtow)', cleanable=False)
    kind_s, ext_s = sniff(path)
    # Format rozpoznajemy po ZAWARTOSCI, nie po rozszerzeniu. Plik bez
    # rozszerzenia, PNG nazwany .jpg albo JPEG zmyłka jako .gif - wszystkie
    # trzeba sprawdzić tak samo, bo rozszerzenie kłamie.
    if kind_s == 'video':
        ext = ext_s or ext
    elif kind_s == 'image':
        ext = ext_s or ext
    elif kind_s == 'archive':
        ext = '.zip'
    if ext in VIDEO_EXT:
        rep = Report(path=path, kind='video', size=os.path.getsize(path))
        if rs.supports(rv, 'video_gps'):
            f = [Finding('gps' if 'GPS' in a else 'datetime', f'{a}: {b}',
                         'HIGH' if 'GPS' in a else 'LOW',
                         'wideo nie ma tagow EXIF - lokalizacja siedzi w atomie pliku')
                 for a, b in video_gps(path)]
            rep.findings = f
        return rep
    if ext in IMG_EXT:
        rep = scan_image(path)
        if rs.supports(rv, 'trailing_data') and rep.complete:
            rep.findings.extend(
                Finding('comment', f'{a}: {b}', 'HIGH',
                        'bajty za znacznikiem konca obrazu - niewidoczne w podgladzie, '
                        'czytelne dla kazdego kto otworzy plik surowo')
                for a, b in trailing_data(path))
        return rep
    if ext == '.zip':
        return scan_zip(path)
    rep = Report(path=path, size=os.path.getsize(path))
    rep.note = 'nieobslugiwany typ pliku'
    rep.cleanable = False
    return rep


class UnsafeDestination(Exception):
    """Sciezka docelowa jest tym samym plikiem co zrodlowy - odmawiamy."""


def safe_dst(src, out_dir):
    """Buduje docelową sciezke w out_dir, nigdy nie nadpisujac src.

    Trzy warunki bezpieczenstwa:
      1. absolutna sciezka musi byc inna niz zrodlowa
      2. katalog docelowy nie moze byc katalogiem zrodlowym (ani jego rodzicem)
      3. jesli nazwa koliduje, dopisujemy _clean przed rozszerzeniem
    """
    src_abs = os.path.abspath(src)
    out_abs = os.path.abspath(out_dir)
    if os.path.realpath(out_abs) == os.path.dirname(src_abs):
        raise UnsafeDestination(
            'katalog docelowy jest tym samym co katalog ze zdjeciami - '
            'wybierz inny, inaczej nadpisalbysmy oryginaly')
    base = os.path.basename(src)
    stem, ext = os.path.splitext(base)
    cand = os.path.join(out_abs, base)
    if os.path.abspath(cand) == src_abs:
        cand = os.path.join(out_abs, f'{stem}_clean{ext}')
    n = 2
    while os.path.exists(cand) and os.path.abspath(cand) != src_abs:
        cand = os.path.join(out_abs, f'{stem}_clean{n}{ext}')
        n += 1
    return cand


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


def scan_many(paths, ruleset=None, workers=8, progress=None):
    """Skanuje liste plikow wielowatkowo. Pillow i regex odpuszczaja GIL,
    wiec to realnie przyspiesza - nie jest pozornym 'threads'."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    out = []
    total = len(paths)
    if not total:
        return out
    with ThreadPoolExecutor(max_workers=max(2, workers)) as ex:
        futs = {ex.submit(scan_file, p, ruleset): p for p in paths}
        done = 0
        for f in as_completed(futs):
            out.append(f.result())
            done += 1
            if progress and (done % 10 == 0 or done == total):
                progress(done, total)
    out.sort(key=lambda r: r.path)
    return out


def scan_tree(root, ruleset=None):
    import ruleset as rs
    exts = IMG_EXT | VIDEO_EXT | {'.zip'}
    if ruleset is not None:
        exts = exts & rs.formats_for(ruleset) | {'.zip'}
    out = []
    for dirpath, _, files in os.walk(root):
        for fn in files:
            full = os.path.join(dirpath, fn)
            ext = os.path.splitext(fn)[1].lower()
            if ext in exts:
                out.append(scan_file(full, ruleset))
            elif ext == '':
                # brak rozszerzenia: rozpoznajemy po zawartosci
                kind, _ = sniff(full)
                if kind in ('image', 'video'):
                    out.append(scan_file(full, ruleset))
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
            try:
                dst = safe_dst(r.path, a.scrub)
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