#!/usr/bin/env python3
"""Generuje zestaw trudnych zdjec do testowania photoscruba.

Kazdy plik dostaje MAKSIMUM danych: pelny EXIF (aparat, obiektyw, serial,
ISO, przyslona, czas, GPS ze wszystkimi polami), XMP, IPTC, komentarze,
ikone, profile ICC, ukryta miniatureke, a czesc plikow ma jeszcze dane
doklejone PO obrazie i cale dodatkowe zdjecie w srodku pliku.

Cel: znalezc dziury w detekcji, zanim zrobi to ktos inny.
"""
import io
import os
import random
import struct
import time
import zlib

import piexif
from PIL import Image, ImageDraw

OUT = os.path.expanduser('~/zdjecia-testowe/hard')
os.makedirs(OUT, exist_ok=True)
random.seed(99)

NOW = time.localtime()
STAMP = time.strftime('%Y:%m:%d %H:%M:%S', NOW)


def pixels(w, h, seed=0):
    rnd = random.Random(seed)
    im = Image.new('RGB', (w, h))
    px = im.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = ((x * 5 + rnd.randint(0, 24)) % 256,
                        (y * 7 + rnd.randint(0, 24)) % 256,
                        ((x * y // 7) + seed) % 256)
    d = ImageDraw.Draw(im)
    d.text((10, 10), f'TEST {w}x{h} seed={seed}', fill=(255, 255, 255))
    return im


def thumb_bytes(w=160, h=120):
    t = pixels(w, h, 7)
    b = io.BytesIO()
    t.save(b, 'JPEG', quality=80)
    return b.getvalue()


def full_exif(with_gps=True, with_maker=True):
    d = {
        "0th": {
            piexif.ImageIFD.Make: b"Canon",
            piexif.ImageIFD.Model: b"Canon EOS R5 Mark II",
            piexif.ImageIFD.Software: b"Adobe Lightroom Classic 14.2",
            piexif.ImageIFD.Artist: b"Bartosz Osiej",
            piexif.ImageIFD.Copyright: b"(c) 2026 Bartosz Osiej / wszystkie prawa zastrzezone",
            piexif.ImageIFD.DateTime: STAMP.encode(),
            piexif.ImageIFD.HostComputer: b"Linux 7.2 x86_64",
            piexif.ImageIFD.XResolution: (300, 1),
            piexif.ImageIFD.YResolution: (300, 1),
            piexif.ImageIFD.ImageDescription: b"Mieszkanie, ul. Rodla 12 m. 4, Szczecin",
        },
        "Exif": {
            piexif.ExifIFD.ExposureTime: (1, 250),
            piexif.ExifIFD.FNumber: (28, 10),
            piexif.ExifIFD.ISOSpeedRatings: 6400,
            piexif.ExifIFD.DateTimeOriginal: STAMP.encode(),
            piexif.ExifIFD.DateTimeDigitized: STAMP.encode(),
            piexif.ExifIFD.FocalLength: (70, 1),
            piexif.ExifIFD.FocalLengthIn35mmFilm: 70,
            piexif.ExifIFD.LensModel: b"RF24-70mm F2.8 L IS USM",
            piexif.ExifIFD.LensMake: b"Canon",
            piexif.ExifIFD.LensSerialNumber: b"0000c14a22",
            piexif.ExifIFD.BodySerialNumber: b"042051000537",
            piexif.ExifIFD.CameraOwnerName: b"Bartosz Osiej",
            piexif.ExifIFD.UserComment: b"PYC\x00\x00\x00\x08\x00\x05strasznie nie publikowac - adres domu",
            piexif.ExifIFD.WhiteBalance: 1,
            piexif.ExifIFD.Flash: 0,
            piexif.ExifIFD.MeteringMode: 5,
            piexif.ExifIFD.ColorSpace: 65535,
        },
        "GPS": {},
        "Interop": {},
        "1st": {},
        "thumbnail": thumb_bytes(),
    }
    if with_maker:
        # MakerNote jako surowe bajty - ukryty odwiezyci, wiekszosc narzedzi go nie czyta
        d['Exif'][piexif.ExifIFD.MakerNote] = (
            b'\x00\x00Canon\x00\x00\x01\x00\x05\x00\x08\x00\x00' + b'Szczecin 53.441483 -0.128361 ')
    if with_gps:
        d['GPS'] = {
            piexif.GPSIFD.GPSVersionID: (2, 3, 0, 0),
            piexif.GPSIFD.GPSLatitudeRef: b"N",
            piexif.GPSIFD.GPSLatitude: ((53, 1), (26, 1), (2934, 100)),
            piexif.GPSIFD.GPSLongitudeRef: b"W",
            piexif.GPSIFD.GPSLongitude: ((0, 1), (7, 1), (4210, 100)),
            piexif.GPSIFD.GPSAltitudeRef: b"N",
            piexif.GPSIFD.GPSAltitude: (1234, 10),
            piexif.GPSIFD.GPSTimeStamp: ((14, 1), (31, 1), (22, 1)),
            piexif.GPSIFD.GPSDateStamp: b"2026:09:14",
            piexif.GPSIFD.GPSSpeedRef: b"K",
            piexif.GPSIFD.GPSSpeed: (35, 100),
            piexif.GPSIFD.GPSImgDirectionRef: b"T",
            piexif.GPSIFD.GPSImgDirection: (1200, 100),
            piexif.GPSIFD.GPSSatellites: b"09",
            piexif.GPSIFD.GPSStatus: b"A",
            piexif.GPSIFD.GPSMeasureMode: b"2",
            piexif.GPSIFD.GPSDOP: (150, 100),
            piexif.GPSIFD.GPSMapDatum: b"WGS-84",
        }
    return d


XMP = b'''<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:exif="http://ns.adobe.com/exif/1.0/"
    xmlns:aux="http://ns.adobe.com/exif/1.0/aux/"
    xmp:CreatorTool="Adobe Lightroom Classic 14.2"
    xmp:CreateDate="2026-09-14T08:31:22"
    xmp:ModifyDate="2026-09-14T09:02:11"
    xmp:Rating="4"
    photoshop:City="Szczecin"
    photoshop:State="Zachodniopomorskie"
    photoshop:Country="Polska"
    photoshop:Credit="Bartosz Osiej / agencja"
    photoshop:Source="https://hartwell-labs.pl"
    photoshop:Instructions="NIE PUBLIKOWAC - zawiera adres"
    photoshop:History=[{"when":"2026-09-14T09:02:11","action":"Crop"}]
    dc:creator="Bartosz Osiej"
    dc:rights="(c) 2026"
    exif:GPSLatitude="53,26.5233N"
    exif:GPSLongitude="0,7.7017W"
    aux:Lens="RF24-70mm F2.8"/>
 </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>'''


def add_app(data, marker, payload):
    return data[:2] + marker + struct.pack('>H', 2 + 2 + len(payload)) + payload + data[2:]


def seg_app(marker, payload):
    return marker + struct.pack('>H', 2 + 2 + len(payload)) + payload


def com_seg(txt):
    return b'\xff\xfe' + struct.pack('>H', 2 + len(txt)) + txt


def png_chunk(t, data):
    return struct.pack('>I', len(data)) + t + data + struct.pack('>I', zlib.crc32(t + data) & 0xffffffff)


def build():
    made = []

    # 01: JPEG z pelnym EXIF + XMP + komentarze + miniatureka
    p = f'{OUT}/01_jpeg_pelny_metadata.jpg'
    im = pixels(1400, 1000, 1)
    im.save(p, 'JPEG', quality=92, exif=piexif.dump(full_exif()))
    d = open(p, 'rb').read()
    d = (d[:2] + seg_app(b'\xff\xe1', b'http://ns.adobe.com/xap/1.0/\x00' + XMP)
         + com_seg(b'Zrobione iPhone 15 Pro - nie publikowac')
         + com_seg(b'GPS: 53.441483,-0.128361')
         + d[2:])
    open(p, 'wb').write(d)
    made.append(p)

    # 02: JPEG z danymi doklejonymi PO obrazie (caly drugi JPEG + XMP + IPTC)
    p = f'{OUT}/02_jpeg_dane_za_obrazem.jpg'
    im = pixels(1200, 800, 2)
    im.save(p, 'JPEG', quality=90, exif=piexif.dump(full_exif(with_gps=False)))
    d = open(p, 'rb').read()
    tail = b'<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?><x:xmpmeta xmlns:x="adobe:ns:meta/">'
    tail += b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description '
    tail += b'xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/" photoshop:City="Szczecin" '
    tail += b'exif:GPSLatitude="53,26N"/></rdf:RDF></x:xmpmeta>'
    second = io.BytesIO()
    pixels(900, 600, 99).save(second, 'JPEG', quality=85)
    open(p, 'wb').write(d + tail + second.getvalue())
    made.append(p)

    # 03: PNG z tEXt / iTXt / zTXt / tIME / eXIf
    p = f'{OUT}/03_png_chunki.png'
    pixels(1000, 700, 3).save(p, 'PNG')
    d = open(p, 'rb').read()
    i = d.index(b'IDAT') - 4
    extra = (png_chunk(b'tEXt', b'Author\x00Bartosz Osiej, Szczecin')
             + png_chunk(b'tEXt', b'Copyright\x00(c) 2026 wszystkie prawa')
             + png_chunk(b'tEXt', b'Source\x00https://hartwell-labs.pl')
             + png_chunk(b'iTXt', b'Description\x00\x00\x00Mieszkanie, ul. Rodla 12 m. 4, Szczecin')
             + png_chunk(b'iTXt', b'Comment\x00\x00\x00zdjecie z drona, nie publikowac')
             + png_chunk(b'zTXt', b'Disclaimer\x00\x00' + zlib.compress(b'do not publish - adres domu'))
             + png_chunk(b'tIME', struct.pack('>HBBBBB', 2026, 9, 14, 8, 31, 22))
             + png_chunk(b'eXIf', piexif.dump(full_exif(with_maker=False))))
    open(p, 'wb').write(d[:i] + extra + d[i:])
    made.append(p)

    # 04: HEIC (iPhone)
    p = f'{OUT}/04_heic_iphone.heic'
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
        pixels(1200, 900, 4).save(p, exif=piexif.dump(full_exif(with_gps=True)))
        made.append(p)
    except Exception as e:
        print('HEIC pominiete:', e)

    # 05: WEBP z EXIF
    p = f'{OUT}/05_webp_exif.webp'
    pixels(1100, 800, 5).save(p, 'WEBP', quality=90, exif=piexif.dump(full_exif()))
    made.append(p)

    # 06: TIFF pelny
    p = f'{OUT}/06_tiff_pelny.tiff'
    pixels(900, 700, 6).save(p, 'TIFF', exif=piexif.dump(full_exif()))
    made.append(p)

    # 07: PNG ze zdjeciem HEIC w srodku (ukryty kontener)
    p = f'{OUT}/07_png_z_ukrytym_heic.png'
    pixels(800, 600, 7).save(p, 'PNG')
    d = open(p, 'rb').read()
    i = d.index(b'IDAT') - 4
    hidden = b''
    hp = io.BytesIO()
    pixels(300, 200, 77).save(hp, 'JPEG', quality=70)
    hidden = hp.getvalue()
    open(p, 'wb').write(d[:i] + png_chunk(b'tEXt', b'Thumbnail\x00' + hidden[:200]) + d[i:])
    made.append(p)

    # 08: MP4 z atomem lokalizacji i creation_time
    p = f'{OUT}/08_wideo_gps.mp4'
    def box(t, payload):
        return struct.pack('>I', 8 + len(payload)) + t + payload
    xyz = b'\xa9xyz\x00\x00\x13\x8c+53.441483-0.128361+023.0/'
    ct = b'creation_time' + struct.pack('>II', 2026, 9 * 1_000_000 + 14)
    lo = b'com.apple.quicktime.creationdate'
    body = b'\xa9nam' + struct.pack('>I', 8 + len(b'dom Bartosza')) + b'dom Bartosza'
    udta = box(b'udta', box(b'loci', xyz + ct + lo) + body)
    open(p, 'wb').write(box(b'ftyp', b'isom\x00\x00\x02\x00isomiso2mp41')
                       + box(b'moov', udta) + box(b'mdat', b'\x00' * 128))
    made.append(p)

    # 09: JPEG z samym MakerNote (bez niczego innego)
    p = f'{OUT}/09_jpeg_makernote.jpg'
    ex = {"0th": {}, "Exif": {piexif.ExifIFD.MakerNote:
                               b'\x00\x00OLYMPUS\x00\x00\x01\x00\x20\x00\x03\x00\x00'
                               + b'GPS 53.441483 -0.128361'}, "GPS": {}, "1st": {}}
    pixels(700, 500, 9).save(p, 'JPEG', quality=88, exif=piexif.dump(ex))
    made.append(p)

    # 10: zdjecie z samym GPS - minimalne, najczestsze uzycie
    p = f'{OUT}/10_samo_gps.jpg'
    ex = {"0th": {piexif.ImageIFD.Make: b"iPhone 15 Pro"},
          "Exif": {piexif.ExifIFD.LensModel: b"iPhone 15 Pro back camera"},
          "GPS": {piexif.GPSIFD.GPSLatitudeRef: b"N",
                  piexif.GPSIFD.GPSLatitude: ((53, 1), (26, 1), (2934, 100)),
                  piexif.GPSIFD.GPSLongitudeRef: b"W",
                  piexif.GPSIFD.GPSLongitude: ((0, 1), (7, 1), (4210, 100)),
                  piexif.GPSIFD.GPSAltitudeRef: b"N", piexif.GPSIFD.GPSAltitude: (1234, 10)},
          "1st": {}}
    pixels(800, 600, 10).save(p, 'JPEG', quality=90, exif=piexif.dump(ex))
    made.append(p)

    # 11: duze zdjecie (test wydajnosci)
    p = f'{OUT}/11_duze_6000x4000.jpg'
    big = Image.new('RGB', (6000, 4000))
    bp = big.load()
    for y in range(0, 4000, 40):
        for x in range(0, 6000, 40):
            c = ((x // 40) % 255, (y // 40) % 255, ((x + y) // 80) % 255)
            for dy in range(40):
                for dx in range(40):
                    bp[x + dx, y + dy] = c
    big.save(p, 'JPEG', quality=88, exif=piexif.dump(full_exif()))
    made.append(p)

    # 12: zdjecie z adresem w nazwie pliku (dane w warstwie filesystem)
    p = f'{OUT}/12_mieszkanie_ul_Rodla_12m4_Szczecin.jpg'
    pixels(700, 500, 12).save(p, 'JPEG', quality=88, exif=piexif.dump(full_exif(with_gps=False)))
    made.append(p)

    # 13: uszkodzony (obciety) JPEG
    p = f'{OUT}/13_uszkodzony_obciety.jpg'
    pixels(900, 700, 13).save(p, 'JPEG', quality=90, exif=piexif.dump(full_exif()))
    d = open(p, 'rb').read()
    open(p, 'wb').write(d[:len(d) // 2])
    made.append(p)

    # 14: JPEG z zerowa zawartoscia (0 bajtow)
    p = f'{OUT}/14_pusty_zero_bajtow.jpg'
    open(p, 'wb').write(b'')
    made.append(p)

    # 15: mylnie rozszerzenie (to jest PNG w pliku .jpg)
    p = f'{OUT}/15_mylne_rozszerzenie_png_w_jpg.jpg'
    pixels(600, 400, 15).save(p, 'PNG')
    made.append(p)

    # 16: zdjecie bez rozszerzenia
    p = f'{OUT}/16_bez_rozszerzenia'
    pixels(600, 400, 16).save(p, 'JPEG', quality=90, exif=piexif.dump(full_exif(with_maker=False)))
    made.append(p)

    # 17: wielka litera rozszerzenia
    p = f'{OUT}/17_WIELKIE_ROZSZERZENIE.JPG'
    pixels(600, 400, 17).save(p, 'JPEG', quality=90, exif=piexif.dump(full_exif()))
    made.append(p)

    # 18: spacje i polskie znaki w nazwie
    p = f'{OUT}/18 zdjecie z urodzin Ann i Zosi (Szczecin).jpg'
    pixels(600, 400, 18).save(p, 'JPEG', quality=90, exif=piexif.dump(full_exif(with_maker=False)))
    made.append(p)

    # 19: GIF z komentarzem
    p = f'{OUT}/19_gif_komentarzem.gif'
    g = pixels(400, 300, 19).convert('P', palette=Image.ADAPTIVE)
    g.save(p, comment=b'szescic, ul. Rodla 12, zdjecie z imprezy')
    made.append(p)

    # 20: PNG z profilem ICC o nazwie zdradzajacej
    p = f'{OUT}/20_png_profil_icc.png'
    pixels(600, 500, 20).save(p, 'PNG')
    d = open(p, 'rb').read()
    i = d.index(b'IDAT') - 4
    prof = b'\x00\x00\x02\x0clcms\x04@\x00\x00mntrRGB XYZ ' + b'\x00' * 128 + b'CustomStudioProfile'
    open(p, 'wb').write(d[:i] + png_chunk(b'iCCP', prof) + d[i:])
    made.append(p)

    return made


if __name__ == '__main__':
    files = build()
    print(f'wygenerowano {len(files)} plikow w {OUT}\n')
    for f in sorted(files):
        print(f'  {os.path.basename(f):46} {os.path.getsize(f):>9,} B')