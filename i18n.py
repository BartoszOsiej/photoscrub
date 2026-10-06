"""Język interfejsu: polski (domyślny) i angielski.

Wersja sklepowa wymaga angielskiego, bo Microsoft Store weryfikuje
listing i kluczowe frazy, a klient spoza Polski dostaje interfejs,
którego nie rozumie. Nie usuwam polskiego - jest po polsku napisany
i tak zostanie.

Wybór języka:
  1. PHOTOSCRUB_LANG=en      wymuszenie (testy w CI)
  2. system operacyjny       LANG / LC_ALL (na Windows: jezyk interfejsu)
  3. polski                   fallback

Nie używam gettext/Qt .ts - to slownik + funkcja t() (oraz tr() dla tekstow
z backendu). Czytelne, bez plikow .qm i katalogu lokalizacji do dnia,
w ktorym bedzie ich 500.
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
    'rules_newer': 'Rules v{rv} · newer rules v{u} available — {items}',
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
                   '*.heif *.avif *.gif *.bmp *.mp4 *.mov *.m4v *.zip);;All files (*)',
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
    'passive_offline': 'Pasywnie i offline. Oryginały zostają tam, gdzie są.',
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
                   '*.heif *.avif *.gif *.bmp *.mp4 *.mov *.m4v *.zip);;Wszystkie pliki (*)',
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
    'clean_toast': ('Czysta kopia w:\\n{dst}\\nOryginał nietknięty, '
                    'z metadanych zniknęło {freed}.',
                    'Clean copy in:\\n{dst}\\nOriginal untouched, '
                    '{freed} of metadata removed.'),
    'clean_done_toast': ('Kopie w {out} — oryginały nietknięte, '
                         'z metadanych zniknęło {freed}.',
                         'Copies in {out} — originals untouched, '
                         '{freed} of metadata removed.'),
    'scanning_top_risk': ('Najwyższe ryzyko publikacji: {top}/100. Reguły v{rv}',
                          'Highest publishing risk: {top}/100. Rules v{rv}'),
    'phone_got': ('Otrzymano {n} plików — ', 'Received {n} files — '),
    'phone_now': ('skanuję teraz', 'scanning now'),
    'worst': ('NAJGORSZY', 'WORST'),
    'worst_short': ('najg.', 'worst'),
    'sev_line': ('{cls} · pewność {pct}%', '{cls} · {pct}% confidence'),
    'stat_risk': ('ryzyko /100', 'risk /100'),
    # nazwy kategorii znacznikow - backend zwraca je po polsku,
    # wiec klucz tez jest polski: i18n.t('cat_' + cat)
    'cat_lokalizacja': ('lokalizacja', 'LOCATION'),
    'cat_tozsamosc': ('tozsamosc', 'IDENTITY'),
    'cat_sprzet': ('sprzet', 'DEVICE'),
    'cat_czas': ('czas', 'TIME'),
    'cat_tekst': ('tekst', 'TEXT'),
    'cat_prawa': ('prawa', 'RIGHTS'),
    'cat_inne': ('inne', 'OTHER'),
    'btn_folder': ('Wybierz folder', 'Choose folder'),
    'btn_files': ('Dodaj pliki', 'Add files'),
    'btn_phone': ('Z telefonu', 'From phone'),
    'menu_phone2': ('Zdjecia z telefonu', 'Photos from phone'),
    'menu_theme2': ('Przelacz motyw', 'Switch theme'),
    'menu_lang': ('Język', 'Language'),
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

# Strona telefonu (HTML) + komunikaty dynamiczne (czyszczenie, serwer)
EXTRA4 = {
    # ── chrome UI: menu, tooltipy, dialogi, toasty ──
    'tagline': ('zanim wrzucisz to do sieci', 'before you post it online'),
    'menu_file': ('&Plik', '&File'),
    'menu_actions': ('&Akcje', '&Actions'),
    'theme_tooltip': ('Jasny / ciemny motyw (Ctrl+T)', 'Light / dark theme (Ctrl+T)'),
    'phone_tooltip': ('Wyślij zdjęcia z iPhone albo Androida (Ctrl+M)',
                      'Send photos from iPhone or Android (Ctrl+M)'),
    'ctx_clean_file': ('Usuń metadane z tego pliku', 'Remove metadata from this file'),
    'ctx_show_path': ('Pokaż ścieżkę', 'Show path'),
    'understood': ('Rozumiem', 'Got it'),
    'activation_key': ('Klucz aktywacyjny', 'Activation key'),
    'paste_clipboard': ('Wklej ze schowka', 'Paste from clipboard'),
    'theme_status': ('Motyw: {which}', 'Theme: {which}'),
    'light': ('jasny', 'light'),
    'dark': ('ciemny', 'dark'),
    'other_addresses': ('Inne adresy: ', 'Other addresses: '),
    'phone_sub': ('Telefon otworzy zwykłą stronę i sam poprosi o dostęp do '
                  'galerii. Nic nie wychodzi poza twoją sieć domową.',
                  'The phone opens a normal page and asks for access to your '
                  'gallery. Nothing leaves your home network.'),
    'link_key': ('klucz: ', 'key: '),
    'scan_now': ('Skanuj teraz', 'Scan now'),
    'phone_wifi_hint': (
        'Telefon i komputer muszą być w tej samej sieci Wi-Fi. '
        'Link działa tylko na twoim komputerze — klucz w adresie '
        'chroni przed wysłaniem plików przez inne programy w sieci.',
        'Phone and computer must be on the same Wi-Fi. The link only works '
        'on your computer — the key in the address stops other programs on '
        'the network from sending files.'),
    'mkdir_failed': ('Nie udało się utworzyć folderu', 'Could not create the folder'),
    'clean_file_failed': ('Nie udało się wyczyścić pliku', 'Could not clean the file'),
    'copy_ready': ('Czysta kopia w:\n{dst}\nOryginał nietknięty, '
                   'oszczędność {freed} metadanych.',
                   'Clean copy in:\n{dst}\nOriginal untouched, '
                   '{freed} of metadata removed.'),
    'save_here_title': ('Zapisz czyste kopie TUTAJ (inny folder niż zdjęcia)',
                        'Save clean copies HERE (a different folder than the photos)'),
    'stopped': ('Zatrzymane', 'Stopped'),
    'same_folder': ('To jest ten sam folder ze zdjęciami. Wybierz inny — '
                    'oryginały nigdy nie są nadpisywane.',
                    'That is the same folder as the photos. Pick another one — '
                    'originals are never overwritten.'),
    'removing': ('Usuwam… {done}/{total}', 'Removing… {done}/{total}'),
    'stop': ('Zatrzymaj', 'Stop'),
    'stopping_now': ('Zatrzymuję po bieżącym pliku…',
                     'Stopping after the current file…'),
    'aborted_by_user': ('zatrzymano przez użytkownika', 'stopped by the user'),
    'bad_key': ('zly klucz — otworz link z programu',
                'wrong key — open the link from the app'),
    'too_big': ('plik za duży — limit to 512 MB',
                'file too large — the limit is 512 MB'),
    'empty_request': ('puste żądanie — wybierz pliki',
                      'empty request — pick some files'),
    'no_dest_folder': ('brak folderu docelowego', 'no destination folder'),
    # ── koniec chrome UI ──
    # strona telefonu
    'pp_title': ('photoscrub — wyślij zdjęcia', 'photoscrub — send photos'),
    'pp_h1': ('Wyślij zdjęcia', 'Send photos'),
    'pp_sub': ('Wybierz pliki w galerii telefonu. Trafią prosto na komputer,\n                bez chmury i bez wysyłania gdziekolwiek.',
               'Pick files in the phone gallery. They go straight to the computer,\n                no cloud, no sending anywhere.'),
    'pp_pick': ('Wybierz z galerii', 'Choose from gallery'),
    'pp_waiting': ('Czekam na pliki…', 'Waiting for photos…'),
    'pp_warn': ('Zwykłe zdjęcia z telefonu nie mają metadanych EXIF.\n                Jeśli chcesz sprawdzić w oryginale, włącz "Użyj oryginałów" w aplikacji\n                aparatu przed wysłaniem.',
                'Photos from the phone camera usually have no EXIF.\n                To check the originals, turn on "Keep originals" in the\n                camera app before sending.'),
    'pp_too_big': ('plik za duży ({a} > {b})', 'file too large ({a} > {b})'),
    'pp_sending': ('Wysyłam {name} — {loaded} z {total} ({pc}%)',
                   'Sending {name} — {loaded} of {total} ({pc}%)'),
    'pp_done': ('Na komputerze: {done} z {total} plików',
                'On the computer: {done} of {total} files'),
    'pp_failed': (', nie udało się: {n}', ', failed: {n}'),
    'pp_timeout': ('przekroczono czas', 'timed out'),
    'pp_unreach': ('nie mogę połączyć się z komputerem', 'cannot reach your computer'),
    # serwer błedy
    'not_found': ('Nie. Otwórz link z programu.',
                  'Not found. Open the link from the app.'),
    'no_boundary': ('brak granicy multipart', 'missing multipart boundary'),
    'bad_boundary': ('błędna granica multipart', 'invalid multipart boundary'),
    'upload_read_fail': ('nie udało się odczytać wysyłki', 'could not read the upload'),
    'upload_interrupted': ('przerwane wysyłanie', 'upload interrupted'),
    'no_files_picked': ('brak plikow — wybierz zdjecia w galerii', 'no files — pick photos in the gallery'),
    'phone_unreach': ('cannot reach your computer', 'cannot reach your computer'),
    # aktywacja
    'key_paste_msg': ('Wklej klucz, który dostałeś mailem.',
                      'Paste the key you received by email.'),
    # toast czyszczenia
    'files_in': ('plików zapisanych w:', 'files written to:'),
    # wideo backend (model.py:111 nieużywane)
    'video_not_scrubbed': ('{name} — wideo (reguły v{rv} nie czyścią wideo)',
                           '{name} — video (rules v{rv} do not clean video)'),
}
PL.update({k: v[0] for k, v in EXTRA4.items()})
EN.update({k: v[1] for k, v in EXTRA4.items()})

TABLES = {'pl': PL, 'en': EN}

LANG = 'pl'


def _norm(v):
    v = v.split(':')[0].split('.')[0].lower()        # en_US.UTF-8 -> en
    if v in TABLES:
        return v
    if v.startswith('en'):
        return 'en'
    if v.startswith('pl'):
        return 'pl'
    return None


def _env_lang():
    """Twardy override: PHOTOSCRUB_LANG (dev, testy, CI)."""
    v = os.environ.get('PHOTOSCRUB_LANG')
    return _norm(v) if v else None


def _sys_lang():
    """Jezyk systemu: LANG/LC_* na Unixie, jezyk interfejsu na Windows."""
    for var in ('LC_ALL', 'LC_MESSAGES', 'LANG'):
        v = os.environ.get(var)
        if v:
            got = _norm(v)
            if got:
                return got
    # Windows nie zna zmiennej LANG - tam jedynym sygnalem jest jezyk
    # interfejsu Windows.
    if os.name == 'nt':
        try:
            import ctypes
            primary = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
            if primary == 0x09:      # en
                return 'en'
            if primary == 0x15:      # pl
                return 'pl'
        except Exception:
            pass
    return None


def _pref_path():
    return os.path.join(os.path.expanduser('~'), '.config', 'photoscrub',
                        'lang')


def _pref_lang():
    """Wybor uzytkownika z menu (zapisywany na stalo)."""
    try:
        with open(_pref_path()) as f:
            got = _norm(f.read().strip())
        if got:
            return got
    except OSError:
        pass
    return None


def save_lang(lang):
    """Zapisuje wybor jezyka z menu - po restarcie program w nim startuje."""
    if lang not in TABLES:
        return False
    try:
        d = os.path.dirname(_pref_path())
        os.makedirs(d, exist_ok=True)
        with open(_pref_path(), 'w') as f:
            f.write(lang)
    except OSError:
        pass
    return True


def _detect():
    """Jezyk z env, potem z systemu. Brak -> polski (CLI)."""
    return _env_lang() or _sys_lang() or 'pl'


def init(lang=None, default=None):
    """Ustawia jezyk.

    *lang* - wymuszenie (testy). *default* - jezyk startowy, gdy ani env,
    ani uzytkownik nic nie wybrali. GUI sprzedajemy po angielsku, wiec
    Window przekazuje default='en': sprzedany program startuje po angielsku
    niezaleznie od tego, na jakim komputerze stoi.
    """
    global LANG
    LANG = _env_lang() or _pref_lang() or default or _sys_lang() or 'pl'
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

# ── teksty z backendu ────────────────────────────────────────────────────────
# Backend (photoscrub, ruleset, license) produkuje opisy po polsku, bo tak
# powstaly: RISK['gps'][1], nazwy znacznikow, bledy licencji. Kluczem tutaj
# jest TEN SAM polski tekst, wiec nie musze ruszac modelu ani JSONow.
# Po polsku zwracam wejscie bez zmian, po angielsku szukam w EN_BACKEND.
# Brak wpisu = tekst zostaje po polsku: polski opis w angielskim UI jest
# lepszy niz [klucz] albo puste pole.
EN_BACKEND = {
    # ── photoscrub.RISK: dlaczego to wyciek ──
    'dokladne wspolrzedne - mapa, adres domu, miejsce pracy':
        'exact coordinates - a map, home address, workplace',
    'numer seryjny aparatu/telefonu - identyfikuje urzadzenie i Ciebie':
        'camera/phone serial number - identifies the device, and you',
    'dane obiektywu': 'lens data',
    'oprogramowanie, ktore wykonalo zdjecie - wersje, nazwa urzadzenia':
        'software that took the photo - versions, device name',
    'dokladny czas - kiedy i w jakiej kolejnosci robiles zdjecia':
        'exact time - when and in what order you took the photos',
    'autor / wlasciciel': 'author / owner',
    'dane wlasnosciowe': 'ownership data',
    ' miniatureka wbudowana w plik - czesto CALY oryginal w 160x120':
        ' thumbnail embedded in the file - often the ENTIRE original at 160x120',
    'dane XMP, potrafia zawierac historie edycji':
        'XMP data, can carry an edit history',
    'komentarz z aparatu': 'camera comment',

    # ── dlaczego dany blok jest wyciekiem ──
    'XMP jest drugim miejscem na dane - i czesto bogatszym niz EXIF, '
    'a wiec usucie tagow nie wystarczy':
        'XMP is a second place for the data - often richer than EXIF, so '
        'stripping tags is not enough',
    'IPTC to pole redakcyjne - imie, miasto, kraj':
        'IPTC is an editorial field - name, city, country',
    'chunk tekstowy PNG - autor, opis, komentarz':
        'PNG text chunk - author, description, comment',
    'komentarz w pliku - widoczny dla kazdego kto go otworzy':
        'comment inside the file - visible to anyone who opens it',
    'komentarz GIF - nieobslugiwany przez wiekszosc edytorow':
        'GIF comment - ignored by most editors, read by tools',
    'MakerNote jest polem binarnym - wiekszosc narzedzi go nie czyta, '
    'a producenci zapisuja tam lokalizacje i tryb pracy':
        'MakerNote is a binary blob - most tools skip it, and manufacturers '
        'store location and camera state there',
    'wspolrzedne zapisane tekstem wewnatrz pliku, poza widocznymi tagami':
        'coordinates written as text inside the file, outside the visible tags',
    'wideo nie ma tagow EXIF - lokalizacja siedzi w atomie pliku':
        'video has no EXIF tags - location lives in the container atom',
    'bajty za znacznikiem konca obrazu - niewidoczne w podgladzie, '
    'czytelne dla kazdego kto otworzy plik surowo':
        'bytes after the end-of-image marker - invisible in a preview, '
        'readable by anyone who opens the file raw',
    'nazwy plikow wewnatrz archiwum: uzytkownicy, pelne sciezki, daty':
        'file names inside the archive: usernames, full paths, dates',
    'pliki ._tar sa ukrytym duplikatem uzytkownika i sciezka w nazwie':
        '._ files are a hidden duplicate of the user with the path in the name',

    # ── opisy znacznikow / chunkow (wartosc findingu) ──
    '{n} B miniatureki w pliku': '{n} B thumbnail inside the file',
    'wspolrzedne obecne ({err})': 'coordinates present ({err})',
    '{n} B nieparsowanego bloku producenta':
        '{n} B of unparsed vendor block',
    'wspolrzedne GPS w bajtach surowych': 'GPS coordinates in raw bytes',
    'slowa GPS w bajtach surowych': 'GPS words in raw bytes',
    'slowo GPS w bajtach surowych': 'the word GPS in raw bytes',
    'nazwa miasta w bajtach surowych': 'a city name in raw bytes',
    'wspolrzedne w tekście: {lat}, {lon}': 'coordinates as text: {lat}, {lon}',
    '{n} B danych binarnych w polu tekstowym':
        '{n} B of binary data in a text field',
    ' (zaczyna sie od: {head})': ' (starts with: {head})',
    '{n} B bloku EXIF (jak zwykly JPEG)': '{n} B EXIF block (like a normal JPEG)',
    'profil ICC {n} B (nazwa, sRGB/P3/Display P3)':
        'ICC profile {n} B (name, sRGB/P3/Display P3)',
    'data i czas modyfikacji w pliku': 'file modification date and time',
    'XMP miasto': 'XMP city',
    'XMP kraj': 'XMP country',
    'XMP lokalizacja': 'XMP location',
    'XMP narzedzie': 'XMP tool',
    'XMP data modyfikacji': 'XMP modify date',
    'XMP autor/credit': 'XMP author/credit',
    'XMP tworca': 'XMP creator',
    'XMP wersja programu': 'XMP software version',
    'jest w dokumencie ({tag})': 'present in the document ({tag})',
    'wspolrzedne w XMP, nie tylko w EXIF':
        'coordinates in XMP, not only in EXIF',
    'wlasciciel/źródło w XMP': 'owner/source in XMP',
    'IPTC byline (autor)': 'IPTC byline (author)',
    'IPTC caption (opis)': 'IPTC caption (description)',
    'IPTC ObjectName (nazwa pliku)': 'IPTC ObjectName (file name)',
    'PO OBRAZIE: {n} B': 'AFTER THE IMAGE: {n} B',
    'caly blok EXIF/XMP/IPTC za koncem pliku':
        'a whole EXIF/XMP/IPTC block after the end of the file',
    'caly drugi obraz ukryty za koncem pliku':
        'a second, complete image hidden after the end of the file',
    'fragmenty HTML/tekstu za koncem pliku':
        'fragments of HTML/text after the end of the file',
    'bajty o nieznanym formacie': 'bytes in an unknown format',
    'atom {key} zawiera wspolrzedne': 'atom {key} contains coordinates',
    'atom creation_time - kiedy i gdzie nagrywano':
        'atom creation_time - when and where it was recorded',
    'kontener metadanych uzytkownika w pliku wideo':
        'user metadata container in the video file',
    '{n} plikow smieci w archiwum ({names}...)':
        '{n} junk files in the archive ({names}...)',
    '{n} ukrytych plikow (._ / kropka)': '{n} hidden files (._ / dotfile)',

    # ── note raportu ──
    'nie mozna odczytac: {err}': 'cannot read it: {err}',
    'parser: {name}: {err}': 'parser: {name}: {err}',
    'zip: {err}': 'zip: {err}',
    'plik nie istnieje': 'file does not exist',
    'plik pusty (0 bajtow)': 'file is empty (0 bytes)',
    'nieobslugiwany typ pliku': 'unsupported file type',

    # ── CLI ──
    'POMINIETO {path}: {why}': 'SKIPPED {path}: {why}',
    'wyczyszczono {n} plikow -> {out}': 'cleaned {n} files -> {out}',
    '{total} plikow z danymi do usuniecia z {n}':
        '{total} files with data to remove out of {n}',

    # ── ruleset: nazwy i opisy pokazywane w programie ──
    'podstawowe': 'basic',
    'pelne': 'full',
    'GPS, numer seryjny, autor i ukryta miniatureka w JPEG.':
        'GPS, serial number, author and the thumbnail hidden in the JPEG.',
    'Wszystko z v1 plus XMP, IPTC, chunki PNG, komentarze JPEG, '
    'dane doklejone po obrazie, GPS w wideo i HEIC z iPhone\'a. '
    'Wykrywa tez adresy i telefony w wolnym tekście.':
        'Everything in v1 plus XMP, IPTC, PNG chunks, JPEG comments, data '
        'appended after the image, GPS in video and HEIC from iPhone. It also '
        'finds addresses and phone numbers in free text.',
    'Zdjecia z iPhone\'a (.HEIC)': 'Photos from iPhone (.HEIC)',
    'HEIC/HEIF otwierane i czytane': 'HEIC/HEIF opened and read',
    'Adres domu w opisie': 'Home address in the description',
    '15 wzorcow: ulica, kod pocztowy, telefon, e-mail':
        '15 patterns: street, postcode, phone, e-mail',
    'XMP i IPTC': 'XMP and IPTC',
    'miedawaj ukrywaja GPS, mialko i kraj':
        'often hide GPS, city and country',
    'Dane doklejone PO obrazie': 'Data appended AFTER the image',
    'czesc plikow ma bajty po znaczniku konca':
        'some files carry bytes after the end marker',
    'GPS w wideo': 'GPS in video',
    'MP4/MOV: atom udta': 'MP4/MOV: udta atom',

    # ── license: bledy widoczne w oknie aktywacji ──
    'podpis nieaktualny - klucz nie pochodzi z tego programu':
        'signature out of date - this key was not issued by this program',
    'klucz uszkodzony ({err})': 'key damaged ({err})',
    'ten klucz jest do innego produktu': 'this key belongs to another product',
    'klucz wygasł': 'key expired',
    'klucz aktywowany na innej maszynie ({mid})':
        'key already activated on another machine ({mid})',
    'klucz aktywowany na innej maszynie':
        'key already activated on another machine',
    'brak klucza': 'no key',
    'aktywny': 'active',
    'poza okresem grace ({days} dni)': 'outside grace period ({days} days)',
    'surowe bajty': 'raw bytes',
    'WIDEO GPS': 'VIDEO GPS',
    'WIDEO czas': 'VIDEO time',
    'WIDEO udta': 'VIDEO udta',
}


def tr(txt, **kw):
    """Tlumaczenie tekstu z backendu: kluczem jest polski oryginal.

    Dziala jak t(), ale nie wymaga wczesniejszego zdefiniowania klucza -
    backend produkuje opisy w trakcie skanowania, po init(), wiec moge
    tlumaczyc w locie. Brak tlumaczenia zostawia tekst po polsku.
    """
    if txt is None:
        return txt
    out = txt if LANG == 'pl' else EN_BACKEND.get(txt, txt)
    if kw:
        try:
            return out.format(**kw)
        except (KeyError, IndexError):
            return out
    return out
