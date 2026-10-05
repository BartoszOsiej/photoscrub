"""Język interfejsu: polski (domyślny) i angielski.

Wersja sklepowa wymaga angielskiego, bo Microsoft Store weryfikuje
listing i kluczowe frazy, a klient spoza Polski dostaje interfejs,
którego nie rozumie. Nie usuwam polskiego - jest po polsku napisany
i tak zostanie.

Wybór języka:
  1. PHOTOSCRUB_LANG=en      wymuszenie (tak ustawia CI dla MSIX)
  2. system operacyjny       LANG / LC_ALL
  3. polski                   fallback

Nie używam gettext/Qt .ts - to 65 napisów zaszytych w kodzie, nie
uzasadnia pliku .qm i katalogu lokalizacji do dnia, w ktorym będzie
ich 500. Slownik + funkcja t() wystarcza i jest czytelna.
"""
import os

# ── angielski ───────────────────────────────────────────────────────────────
EN = {
    # okno / naglowek
    'drop_photos': 'Drop photos or videos',
    'or_click_to_choose': 'or click to choose files',
    'see_what_your_photos_reveal': 'See what your photos reveal',
    'passive_offline': 'Passive and offline. Originals stay where they are.',
    'details': 'DETAILS',
    'how_it_works': 'How it works',
    'remove_metadata': 'Remove metadata',
    'risk': 'RISK',
    'files': 'files',
    'photos': 'photos',
    'clean': 'clean',
    'purity': 'purity',
    'risk_score': 'RISK {score}/100',
    'click_photo_card': 'Click a photo to see exactly what it reveals, and why it matters.',
    'purity_value': 'purity {pct}',
    'cameras': 'camera · lens · {lens}',
    'how_it_works_title': 'How it works',
    'how_it_works_intro': '<p>photoscrub reads the <b>bytes of the file</b> and <b>EXIF</b> '
                          '— nothing else. No scanning, no account, no connection '
                          'to any server.</p>',
    'how_it_works_originals': '<p>We never modify your originals. We write cleaned '
                              'copies to a folder you choose.</p>',
    'how_it_works_thumb': '<p>The sneakiest leak is the thumbnail embedded in a '
                          'JPEG — it often contains the entire original photo, at '
                          'full resolution.</p>',
    'how_it_works_score': '<p>The risk score (0–100) comes from our own model: 15 '
                          'file characteristics, cross-checked against known '
                          'profiles. Not a language model — it counts, it does not '
                          'invent.</p>',
    'read_more': 'Read more',

    # pasek statusu / licencja
    'license_active': 'license active · rules v{rv}',
    'rules_newer': 'Rules v{rv} · newer rules v{new} available — {items}',
    'license_grace': 'outside grace period: {info}',
    'paste_key': 'Paste the key you received by email.',
    'activate': 'Activate',
    'license_title': 'photoscrub — activation',
    'your_machine': 'your machine: {id}',
    'activate_ok': 'Activated.',
    'activate_bad': 'That key did not work: {msg}',

    # wybor plikow
    'choose_files': 'Choose photos and videos',
    'file_filter': 'Photos and videos (*.jpg *.jpeg *.png *.tif *.tiff *.webp *.heic '
                   '*.gif *.mp4 *.mov *.zip);;All files (*)',
    'choose_folder': 'Choose a folder of photos',
    'scanning_n': 'Checking {n} files…',
    'scanning': 'Checking… {done}/{total}',
    'nothing_found': 'Nothing to check here.',
    'cancelled': 'Cancelled',

    # okno telefonu
    'from_phone': 'Send photos from phone',
    'from_phone_sub': 'No install on the phone. The phone opens a web page and '
                      'asks for access to the photo library — your files arrive '
                      'on this computer.',
    'from_phone_qr_hint': 'Point the camera at this code',
    'copy_link': 'Copy link',
    'scan_code': 'Show code',
    'other_addresses': 'Other addresses: {addrs}',
    'waiting_files': 'Waiting for photos from your phone…',
    'got_files': 'Received: {names}',
    'firewall_blocked': 'Firewall is blocking this port — that is why the phone '
                        'will not load the page. One command fixes it (needs your password):',
    'copy_command': 'Copy command',
    'phone_hint': 'Phone and computer must be on the same Wi-Fi network. The link '
                  'works only on your computer — the key in the address stops other '
                  'programs on the network from sending files.',
    'photo_server_down': 'The phone server stopped: {err}',

    # czyszczenie
    'cleaning': 'Cleaning… {done}/{total}',
    'cleaned_n': 'Cleaned {n} files',
    'freed_mb': 'freed {mb} MB',
    'clean_failed': 'Failed: {list}',
    'video_skipped': 'video (rules v{rv} do not clean video)',
    'clean_done': 'Done',

    # komunikaty
    'no_photos': 'No photos there.',
    'theme_dark': 'Dark',
    'theme_light': 'Light',
    'toggle_theme': 'Switch theme',
    'add_files': 'Add files…',
    'add_folder': 'Choose folder…',
    'scan_again': 'Scan again',
    'from_phone_menu': 'Photos from phone',
    'close': 'Close',
    'rescan': 'Rescan',
    'yes': 'Yes',
    'no': 'No',
    'cancel': 'Cancel',
    'close_btn': 'Close',
}

# ── polski (oryginalne napisy) ──────────────────────────────────────────────
PL = {
    'drop_photos': 'Upuść zdjęcia lub filmy',
    'or_click_to_choose': 'albo kliknij, żeby wybrać pliki',
    'see_what_your_photos_reveal': 'Zobacz, co Twoje zdjęcia zdradzają',
    'passive_offline': 'Paswywnie i offline. Oryginały zostają tam, gdzie są.',
    'details': 'SZCZEGÓŁY',
    'how_it_works': 'Jak to działa',
    'remove_metadata': 'Usuń metadane',
    'risk': 'RYZYKO',
    'files': 'plików',
    'photos': 'zdjęcia',
    'clean': 'czyste',
    'purity': 'czystość',
    'risk_score': 'RYZYKO {score}/100',
    'click_photo_card': 'Kliknij kartę zdjęcia, żeby zobaczyć, co dokładnie ujawnia '
                        'i dlaczego to problem.',
    'purity_value': 'czystość {pct}',
    'cameras': 'aparat · obiektyw · {lens}',
    'how_it_works_title': 'Jak to działa',
    'how_it_works_intro': '<p>photoscrub czyta <b>bajty pliku</b> i <b>EXIF</b> — '
                          'nic więcej. Nie ma skanowania, nie ma konta, nie ma '
                          'połączenia z serwerem.</p>',
    'how_it_works_originals': '<p>Oryginałów nigdy nie modyfikujemy. Zapisujemy '
                              'czyste kopie do folderu, który wybierzesz.</p>',
    'how_it_works_thumb': '<p>Najbardziej podstępny wyciek to miniaturka wbudowana '
                          'w JPEG — często jest w niej całe oryginalne zdjęcie, '
                          'w rozdzielczości pełnej.</p>',
    'how_it_works_score': '<p>Wynik ryzyka (0–100) liczy nasz własny model: 15 cech '
                          'pliku, porównanych z profilami. To nie jest model '
                          'językowy — nie zmyśla, liczy.</p>',
    'read_more': 'Czytaj dalej',

    'license_active': 'licencja aktywna · reguły v{rv}',
    'rules_newer': 'Reguły v{rv} · nowsze reguły v{u} dostępne — {items}',
    'license_grace': 'poza okresem grace: {info}',
    'paste_key': 'Wklej klucz, który dostałeś mailem.',
    'activate': 'Aktywuj',
    'license_title': 'photoscrub — aktywacja',
    'your_machine': 'twoja maszyna: {id}',
    'activate_ok': 'Aktywowano.',
    'activate_bad': 'Ten klucz nie zadziałał: {msg}',

    'choose_files': 'Wybierz zdjęcia i filmy',
    'file_filter': 'Zdjęcia i filmy (*.jpg *.jpeg *.png *.tif *.tiff *.webp *.heic '
                   '*.gif *.mp4 *.mov *.zip);;Wszystkie pliki (*)',
    'choose_folder': 'Wybierz folder ze zdjęciami',
    'scanning_n': 'Sprawdzam {n} plików…',
    'scanning': 'Sprawdzam… {done}/{total}',
    'nothing_found': 'Nie ma tu czego sprawdzać.',
    'cancelled': 'Anulowano',

    'from_phone': 'Wyślij zdjęcia z telefonu',
    'from_phone_sub': 'Bez instalacji na telefonie. Telefon otwiera zwykłą stronę '
                      'i prosi o dostęp do galerii — pliki lądują na tym komputerze.',
    'from_phone_qr_hint': 'Skieruj aparat na ten kod',
    'copy_link': 'Kopiuj link',
    'scan_code': 'Pokaż kod',
    'other_addresses': 'Inne adresy: {addrs}',
    'waiting_files': 'Czekam na pliki z telefonu…',
    'got_files': 'Otrzymano: {names}',
    'firewall_blocked': 'Firewall blokuje ten port — dlatego telefon nie ładuje '
                        'strony. Jedna komenda to odblokuje (potrzebne hasło):',
    'copy_command': 'Kopiuj komendę',
    'phone_hint': 'Telefon i komputer muszą być w tej samej sieci Wi-Fi. Link działa '
                  'tylko na twoim komputerze — klucz w adresie chroni przed wysyłaniem '
                  'plików przez inne programy w sieci.',
    'photo_server_down': 'Serwer telefonu się zatrzymał: {err}',

    'cleaning': 'Czyszczę… {done}/{total}',
    'cleaned_n': 'Wyczyszczono {n} plików',
    'freed_mb': 'odzyskano {mb} MB',
    'clean_failed': 'Nie udało się: {list}',
    'video_skipped': 'wideo (reguły v{rv} nie czyścią wideo)',
    'clean_done': 'Gotowe',

    'no_photos': 'Nie ma tam zdjęć.',
    'theme_dark': 'Ciemny',
    'theme_light': 'Jasny',
    'toggle_theme': 'Przełącz motyw',
    'add_files': 'Dodaj pliki…',
    'add_folder': 'Wybierz folder…',
    'scan_again': 'Skanuj ponownie',
    'from_phone_menu': 'Zdjęcia z telefonu',
    'close': 'Zamknij',
    'rescan': 'Skanuj ponownie',
    'yes': 'Tak',
    'no': 'Nie',
    'cancel': 'Anuluj',
    'close_btn': 'Zamknij',
}


# Dodane pozniej - komunikaty z dynamicznymi wartosciami (czyszczenie,
# telefon, wyniki skanu). Trzymam je w osobnym slowniku, bo sa dlugie
# i dotycza innej czesci programu niz interfejs.
EXTRA = {
    'clean_toast': ('Czysta kopia w:\\n{dst}\\nOryginal nietknięty, ',
                    'Clean copy in:\\n{dst}\\nOriginal untouched, {freed} of metadata removed.'),
    'clean_done_toast': ('Kopie w {out} — oryginaly nietknięte, ',
                         'Copies in {out} — originals untouched, {freed} of metadata removed.'),
    'scanning_top_risk': ('Najwyższe ryzyko publikacji: {top}/100. Reguły v{rv}',
                          'Highest publishing risk: {top}/100. Rules v{rv}'),
    'phone_got': ('Otrzymano {n} plików — ', 'Received {n} files — '),
    'phone_now': ('skanuję teraz', 'scanning now'),
    'worst': ('NAJGORSZY', 'WORST'),
    'worst_short': ('najg.', 'worst'),
    'sev_line': ('{cls} · pewność {pct}%', '{cls} · {pct}% confidence'),
    'stat_risk': ('ryzyko /100', 'risk /100'),
    # nazwy kategorii znacznikow - backend zwraca je po polsku
    'cat_location': ('lokalizacja', 'LOCATION'),
    'cat_identity': ('tozsamosc', 'IDENTITY'),
    'cat_device': ('sprzet', 'DEVICE'),
    'cat_time': ('czas', 'TIME'),
    'cat_text': ('tekst', 'TEXT'),
    'btn_folder': ('Wybierz folder', 'Choose folder'),
    'btn_files': ('Dodaj pliki', 'Add files'),
    'btn_phone': ('Z telefonu', 'From phone'),
    'menu_phone2': ('Zdjecia z telefonu', 'Photos from phone'),
    'menu_theme2': ('Przelacz motyw', 'Switch theme'),
    'menu_how2': ('Jak to dziala', 'How it works'),
    'menu_scan2': ('Skanuj ponownie', 'Scan again'),
    'menu_remove2': ('Usun metadane', 'Remove metadata'),
    'phone_title2': ('Wyślij zdjęcia z telefonu', 'Send photos from phone'),
    'clean_summary': ('{done} oczyszczone, {failed} pominięte',
                      '{done} cleaned, {failed} skipped'),
    'clean_count': ('{done} plików zapisanych w:\\n{out}',
                    '{done} files written to:\\n{out}'),
    'scanning_top': ('{len} z {total} plików ujawnia dane',
                     '{len} of {total} photos leak data'),
    'files_n': ('{n} plików', '{n} files'),
    'photos_n': ('{n} zdjęć', '{n} photos'),
    'clean_n': ('{n} czyste', '{n} clean'),
    'freed_meta': ('oszczędność {freed} metadanych.',
                   '{freed} of metadata removed.'),
    'freed_short': ('z metadanych zniknęło {freed}.',
                    '{freed} of metadata removed.'),
    'confidence': ('pewność {pct}%', 'confidence {pct}%'),
    'video_skipped_full': ('{name} — wideo (reguły v{rv} nie czyścią wideo)',
                           '{name} — video (rules v{rv} do not clean video)'),
}
PL.update({k: v[0] for k, v in EXTRA.items()})
EN.update({k: v[1] for k, v in EXTRA.items()})

# Napisy, ktore uzytkownik widzi w normalnym uzyciu (narożniki, pusta
# lista, bledne polaczenie) plus panel "Jak to dziala" - tresc
# sprzedazowa, wiec tlumaczona 1:1.
EXTRA2 = {
    'empty_title': ('Nic do usuwania — możesz je wrzucać na ',
                    'Nothing to clean — you can upload these to '),
    'empty_sub': ('albo wrzucaj dalej. Nie ma skanowania, nie ma konta, '
                  'nie ma połączenia z serwerem.',
                  'or keep adding. No scanning, no account, no server connection.'),
    'top_risk': ('Najwyższe ryzyko publikacji: {top}/100. Reguły v{rv} · '
                 'zero skanowania, zero sieci.',
                 'Highest publishing risk: {top}/100. Rules v{rv} · '
                 'no scanning, no network.'),
    'already_clean': ('Czyste. Nic do usuwania.', 'Clean. Nothing to remove.'),
    'already_clean_title': ('Te pliki są czyste', 'These files are clean'),
    'no_rules': ('brak reguł', 'no rules'),
    'net_error': ('brak połączenia z komputerem', 'cannot reach your computer'),
    'upload_read_fail': ('nie udało się odczytać wysyłki', 'could not read the upload'),
    'clean_failed_part': (', nie udało się: ', ', failed: '),
    'originals_note': ('Oryginały nigdy nie są nadpisywane.',
                       'Originals are never overwritten.'),
    'how_phone_1': ('<p>Telefon łączy się z twoim komputerem po Wi-Fi, przez ',
                    '<p>The phone connects to your computer over Wi-Fi, via '),
    'how_phone_2': ('galerii. Nic nie wychodzi poza twoją sieć domową.',
                    'gallery. Nothing leaves your home network.'),
    'how_phone_3': ('Nie. Otwórz link z programu.',
                    'No. Open the link from the app.'),
    'link_local_only': ('Link działa tylko na twoim komputerze — klucz w adresie ',
                        'The link works only on your computer — the key in the address '),
    'hint_line2': ('chroni przed wysłaniem plików przez inne programy w sieci.',
                   'stops other programs on the network from sending files.'),
    'offline_badge': ('gdzie są.', 'where they are.'),
}
PL.update({k: v[0] for k, v in EXTRA2.items()})
EN.update({k: v[1] for k, v in EXTRA2.items()})

# Etykiety widoczne w kazdym widoku: statystyki na górze i plakietka
# ryzyka na karcie zdjecia. Bez nich angielska wersja wygladala by jak
# polska z doklejonym angielskim tytulem.
EXTRA3 = {
    # statystyki
    'stat_files': ('plików', 'files'),
    'stat_dirty': ('z danymi', 'leaky'),
    'stat_high': ('pilne', 'urgent'),
    'stat_clean': ('czyste', 'clean'),
    'stat_photos': ('zdjęć', 'photos'),
    # plakietki ryzyka - wartosc jest widoczna przed snipem ekranu
    'sev_safe': ('bezpieczne', 'safe'),
    'sev_meta': ('metadane', 'metadata'),
    'sev_location': ('LOKALIZACJA', 'LOCATION'),
    'sev_identity': ('TOŻSAMOŚĆ', 'IDENTITY'),
    'sev_title': ('RYZYKO {risk}/100', 'RISK {risk}/100'),
    'sev_purity': ('czystość {pct}', 'purity {pct}'),
    'sev_camera': ('aparat · obiektyw · {lens}', 'camera · lens · {lens}'),
    'files_n': ('{n} plików', '{n} files'),
    'phone_title': ('Wyślij zdjęcia z telefonu', 'Send photos from phone'),
    'menu_files': ('Dodaj pliki…', 'Add files…'),
    'menu_folder': ('Wybierz folder…', 'Choose folder…'),
    'menu_scan': ('Skanuj ponownie', 'Scan again'),
    'menu_phone': ('Zdjęcia z telefonu', 'Photos from phone'),
    'menu_theme': ('Przełącz motyw', 'Switch theme'),
    'menu_close': ('Zamknij', 'Close'),
}
PL.update({k: v[0] for k, v in EXTRA3.items()})
EN.update({k: v[1] for k, v in EXTRA3.items()})

TABLES = {'pl': PL, 'en': EN}

LANG = 'pl'


def _detect():
    """Jezyk z env, potem z systemu. Brak env -> polski."""
    for var in ('PHOTOSCRUB_LANG', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        v = os.environ.get(var)
        if not v:
            continue
        v = v.split(':')[0].split('.')[0].lower()   # en_US.UTF-8 -> en
        if v in TABLES:
            return v
        if v.startswith('en'):
            return 'en'
        if v.startswith('pl'):
            return 'pl'
    return 'pl'


def init(lang=None):
    global LANG
    LANG = lang if lang in TABLES else _detect()
    return LANG


def set_lang(lang):
    """Zmiana jezyka w locie (przycisk w menu)."""
    global LANG
    if lang in TABLES:
        LANG = lang
        return True
    return False


def get_lang():
    return LANG


def t(key, *fallback, **kw):
    """tlumaczenie; brak klucza -> fallback albo [key], nie wywala UI.

    Zwracam [key] jak zamiast tekstu, bo cichy brak tlumaczenia jest
    niewidoczny, a widoczny nawias klamrowy w interfejsie nie jest.

    *fallback pozwala przekazac wartosc z backendu, np. nazwe kategorii,
    ktora nie ma jeszcze klucza - wtedy pokazujemy ja zamiast [klucz].
    """
    txt = TABLES.get(LANG, PL).get(key)
    if txt is None:
        txt = PL.get(key) or TABLES['en'].get(key)
    if txt is None:
        return fallback[0] if fallback else f'[{key}]'
    if kw:
        try:
            return txt.format(**kw)
        except (KeyError, IndexError):
            return txt
    return txt