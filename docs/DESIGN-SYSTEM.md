# Wytyczne UX dla photoscruba — kopalnia wiedzy

Wszystko poniżej to **cytaty/zasady z oficjalnej dokumentacji**, nie moje wymyślanie.
Aplikacja działa na Windows i Linux, więc bierzemy wspólny mianownik trzech systemów:
Windows App Design (Fluent) + GNOME HIG + Apple HIG, oraz wzorce dla danych
(Radix/shadcn, Laws of UX).

Każda reguła ma `→` i mówi, gdzie jest użyta w kodzie. Reguła bez `→` to wytyczna
do zastosowania przy kolejnym komponencie.

---

## 1. Microsoft — fundament desktopu

### 1.1 Pięć zasad Windows 11 (`design-principles`)
> **Effortless** — szybciej i bardziej intuicyjnie, łatwo zrobić to co chcę.
> **Calm** — miękko i bez bałaganu; tło pomaga skupić się.
> **Personal** — dostosowuje się do użytkownika.
> **Familiar** — znany wygląd, krzywa uczenia się zerowa.
> **Complete + Coherent** — spójne doświadczenie na różnych platformach.

→ Cały interfejs jest jeden dark motyw, bez kolorowego bałaganu (Calm).
→ Okno wygląda tak samo na Windows i Linux (Coherent).
→ Drag & drop działa obie rękami: mysz i klawiatura (Effortless).

### 1.2 Type ramp (`signature-experiences/typography`)
Oficjalne wartości w effective pixels:

| Rola | Waga | rozmiar / line-height |
| --- | --- | --- |
| Small | Regular | 12/16 |
| Text | Regular | 14/20 |
| Text strong | **Semibold** | 14/20 |
| Text large | Regular | 18/24 |
| Subtitle | Semibold | 20/28 |
| Title | Semibold | 28/36 |
| Title large | Semibold | 40/52 |
| Display | Semibold | 68/92 |

Zasady z tej samej strony:
> **Use semibold for titles.** „Bold and Italic styles are not part of the Windows
> type ramp. Use Semibold instead of Bold for emphasis. Italic is excluded because
> it can reduce readability and legibility, particularly for people with dyslexia."

> **Minimum values: 14px Semibold, 12px Regular.** „Text smaller than these sizes
> and weights are illegible in some languages."

> **Casing: Sentence case** for all UI text, including titles.

> **Truncation: ellipses** in most cases.

> **Alignment: Left by default.**

> Keep **50–60 characters per line**; „don't use fewer than 20 characters or more
> than 60 characters per line as this is difficult to read."

→ `theme.py` TYPE ramp ustawiony dokładnie na tych wartościach (12/16, 14/20,
  18/24, 20/28, 28/36).
→ Tytuły używają **wagi 500–600 (semibold), nigdy 700 (bold)**.
→ Żadnego kursywy w interfejsie.
→ Nazwy plików skracane wielokropkiem (`QFontMetrics.elidedText`).
→ Panel szczegółów ma stałą szerokość 360 px → ~44 znaki na linię (≤60).
→ Interfejs polski = sentence case („Upuść zdjęcia”, nie „UPUŚĆ ZDJĘCIA”).
  Wyjątkiem są tylko krótkie plakietki danych (`LOKALIZACJA`), które są
  pojedynczym słowem i tak wyglądają w obu wersjach tak samo.

### 1.3 Font
> „You should use one font throughout your app's UI, and we recommend sticking with
> the default font for Windows apps, **Segoe UI Variable**."

Wagi Segoe UI Variable: Light 300, Semilight 350, Regular 400, **Semibold 600**, Bold 700.

→ `QSS` ustawia `'Segoe UI'` przed Inter na Windows (font systemowy), Inter na
  Linuksie. Jedna rodzina przez całą aplikację, zero mieszania krojów.

### 1.4 Breakpointy (`layout/screen-sizes-and-breakpoints-for-responsive-design`)
> Small: do 640 px · Medium: 641–1007 px · **Large: 1008 px i więcej**

> **Multiples of four.** „The sizes, margins, and positions of UI elements should
> always be in multiples of 4 epx… Using multiples of four aligns all UI elements
> with whole pixels and ensures crisp, sharp edges."

> Projektuj dla **okna**, nie dla ekranu.

→ `theme.py: SPACE = 4/8/12/16/24/32/40/48/64` — wszystko wielokrotność 4.
→ Próg przebudowy układu: 1008 px (`_BREAK_LARGE`). Poniżej panel boczny schodzi
  pod siatkę kart (GNOME: „a utility pane can be replaced with a bottom panel when
  a window is narrow").
→ Wszystkie marginesy i odstępy są wielokrotnością 4 — brak ułamków pikseli.

### 1.5 Kolor (`signature-experiences/color`)
> „**Use color meaningfully.** When color is used sparingly to highlight important
> elements, it can help create a user interface that is fluid and intuitive."

> „**Use color to indicate interactivity.** It's a good idea to choose one color to
> indicate elements of your application that are interactive."

> „…avoid using these combinations as the sole differentiator between application
> elements" (czerwień↔zieleń; **8% mężczyzn i 0,5% kobiet ma daltonizm R-G**).

→ Jeden kolor interaktywny: `--accent` (indigo 9). Używany tylko dla CTA, focus
  i stanu zaznaczenia. Nic innego nie jest niebieskie.
→ **Nigdy sam kolor jako jedyny nośnik informacji**: karty z ryzykiem mają etykietę
  tekstową (`LOKALIZACJA` / `TOŻSAMOŚĆ`), najgorszy plik ma napis `NAJGORSZY`,
  poziom ryzyka to liczba. Czerwień i zieleń nigdy nie porównują się ze sobą bez
  tekstu.
→ Red/green dla statusu są z rodu odstępów 9 (te same co akcent), nie losowe
  jasne kolory.

### 1.6 Commanding (`basics/commanding-basics`)
> „**Always try to let users manipulate content directly** rather than through
> commands that act on the content."

> „Be careful of how much your app uses confirmation dialogs; they can be helpful
> when a user makes a mistake, [but] a hindrance whenever the user is trying to
> perform an action intentionally."

> „For actions that **can be undone**, offering a simple undo command is usually
> enough."

> „Provide feedback only when necessary and only if it's not available elsewhere."

→ Główna czynność to **przeciągnij i upuść** (canvas), nie przycisk „skanuj”.
→ **Zero potwierdzeń przy czyszczeniu** — operacja jest odwracalna, bo oryginały
  zostają nietknięte. Dialog w oknie „Zapisz czyste kopie TUTAJ" to wybór miejsca,
  nie potwierdzenie.
→ Potwierdzenie tylko przy **nieodwracalnej** operacji: nadpisanie oryginału
  (które blokujemy) i wybór katalogu wyjściowego.
→ Sprzątanie danych to **informacja zwrotna w miejscu** (panel + toast), nie modal.

### 1.7 Dialogi
> „Dialog controls are modal UI overlays… can be disruptive and should only be used in
> certain situations."

→ Jeden dialog: aktywacja licencji (blokująca, bez wyjścia).
→ „Jak to działa" to nie dialog — przycisk otwiera panel, bo informacja jest
  niekrytyczna. To świadomy wybór: mniej przerwań.

---

## 2. GNOME HIG — Linux i adaptacyjność

### 2.1 Skalowanie (`guidelines/adaptive`)
> „**Resizing the window should be smooth and glitch-free.** For example widgets
> should not jump around or disappear without an animation."

> „Ensure that the width of each container always feels good, irrespective of the
> window size, without requiring manual resizing by the user. For example, sidebars
> should never look excessively wide or narrow in relation to the main window area."

> „Windows that are sub-divided into numerous small panes or panels are hard to make
> adaptive."

> „Using list patterns for content is encouraged because they scale well."

> „**The smallest recommended display size for GNOME on desktop is currently
> 1024×600px**, and this size should be supported by all apps."

> „…place content within containers that have a **maximum width**" (duże okna).

→ Minimalne okno ustawione na **1024×640** (`setMinimumSize`) — spełnia wymóg GNOME.
→ Panel szczegółów **stała szerokość 360 px** — nigdy nie jest „za szeroki w stosunku
  do okna" ani nie znika bez powodu.
→ Siatka kart: `CARD_W` stała szerokość, liczba kolumn zależy tylko od viewportu,
  nigdy od rozmiaru okna w pętli zwrotnej (petla resize→render→resize zawieszała
  aplikację — GNOME wprost tego zabrania).
→ Treść w kontenerze o maksymalnej szerokości: szczegóły nie rozciągają się w nieskończoność.

### 2.2 Klawiatura (`guidelines/keyboard`)
> „**Every action should also be possible with the keyboard.** Test how accessible
> your app is by trying to use it with just a keyboard."

Skróty, które **muszą** działać:

| Klawisz | Funkcja |
| --- | --- |
| `Tab` / `Shift+Tab` | następny / poprzedni element |
| `Return` | aktywuj zaznaczony element |
| `Space` | przełącz stan |
| `F10` | menu główne |
| `Esc` | zamknij kontener tymczasowy |

> „Shortcut keys should also be assigned to the **most commonly-used actions**…
> However, don't assign shortcuts for everything."

> „Do not use **Alt** for shortcut keys" i „Super" jest zarezerwowany przez system.

→ Skróty (Ctrl+O pliki, Ctrl+D folder, Ctrl+R skanuj ponownie, Esc) implementowane
  i przypisane do najczęstszych akcji; **bez Alt i Super**.
→ Cała siatka kart osiągalna klawiszem: `Return` aktywuje zaznaczoną kartę.
→ `Esc` zamyka dialog i czyści zaznaczenie.

### 2.3 Progress bars (`patterns/feedback/progress-bars`)
> „A progress bar should always be determinate when the duration is known."

→ Pasek postępu jest deterministyczny (`done/total`), nie animowany na ślepo.

---

## 3. Apple HIG — premium desktop

### 3.1 Hierarchia wizualna
Apple wymaga trzech czytelnych poziomów w oknie: **pasek tytułu / treść / pasek
narzędzi**, oraz odstępu minimum 20 px między sekcjami tekstowymi i 8 px wokół
elementów w grupie.

→ Okno ma: pasek nagłówkowy → nagłówek treści → zawartość → pasek akcji.
  Odstępy z `theme.SPACE` (24 px między sekcjami, 8–12 px wewnątrz grup).
→ Panel boczny nie „pływa" w siatce — ma własne tło, radius i padding 20 px.

### 3.2 Toolbar
Apple: ikony w pasku narzędzi mają **jedną funkcję, etykietę pod ikoną lub tooltip,
i stan zaznaczenia**. Pasek narzędzi nie jest polem na kolorowe plamy.

→ Nagłówek ma logo + nazwę + dwa przyciski ghost, bez ikon-dekoracji.
→ `QToolTip` pokazuje pełną ścieżkę pliku, gdy nazwa jest skrócona.

---

## 4. Wzorce dla danych

### 4.1 Radix Themes — skale (realne wartości, nie zgadywane)
- **Odstępy** (`space.css`): 4, 8, 12, 16, 24, 32, 40, 48, 64 px.
- **Radius** (`radius.css`): 3, 4, 6, 8, 12, 16 px × `radius-factor`.
- **Typografia** (`typography.css`): 12/16, 14/20, 16/24, 18/24, 20/28, 24/30,
  28/36, 35/40, 60/60 + ujemny letter-spacing od 18 px w górę.
- **Cienie** (`shadow.css`, dark): 6 poziomów, każdy z obręczą 1 px.

### 4.2 Radix Colors — palety dark
Realne hexy (`@radix-ui/colors`): slate (tło), indigo (akcent), red/amber/green
(status). Numery kroków 1–12 w ciemnym motywie są odwrócone — **krok 9 to najmocniejszy
kolor w tekście, kroki 1–2 to tła**. Używamy: slate 1 = tło aplikacji, slate 2–3 =
panele, slate 11–12 = tekst, indigo 9 = akcent, red/amber/green 9 = status.
Warianty `a3/a6/a10` → przezroczyste tła pod etykietami.

> **Uwaga techniczna:** Qt nie rozumie `#RRGGBBAA` — 8-cyfrowy hex jest cicho
> zastępowany innym kolorem (daje żółte obramowania w całym UI). `theme.rgba()`
> konwertuje jawnie.

### 4.3 shadcn — semantyka tokenów
Pary `background/foreground`, `card`, `popover`, `primary`, `secondary`, `muted`,
`accent`, `destructive`, `border`, `input`, `ring`. Skala radiusu liczona
z promienia bazowego 10 px: 6 / 8 / 10 / 14 / 18 / 22 / 26.

→ `theme.py` używa dokładnie tych nazw, więc każdy kolor w UI ma **jedno**
  źródło prawdy.

---

## 5. Laws of UX — psychologia w interfejsie

| Prawo | Wymóg (cytat z takeaways) | Gdzie |
| --- | --- | --- |
| **Doherty** (<400 ms) | „Provide system feedback within 400 ms" | szkielety kart + pasek postępu pojawiają się natychmiast |
| **Fitts** | cel zależy od odległości i rozmiaru | cała karta (228 px) jest klikalna, nie tylko tytuł |
| **Hick** | „Minimize choices when response times are critical" | jedna akcja główna (CTA), reszta ghost; „Jak to działa" nie zajmuje panelu |
| **Von Restorff** | „Make important information visually distinctive… use restraint" | jeden `NAJGORSZY` wyróżniony, reszta neutralna |
| **Miller** | „Organize content into smaller chunks" | findings pogrupowane: lokalizacja / tożsamość / sprzęt / czas |
| **Peak-End** | „Users judge an experience based on how they felt at its peak and at its end" | zakończenie: zielony „Gotowe" + dokładna ścieżka do kopii |
| **Postel** | „Be liberal in what you accept, conservative in what you send" | przyjmujemy dowolny plik (sniff bajtów), zapisujemy tylko znane formaty |
| **Aesthetic-Usability** | ładniejszy interfejs jest postrzegany jako działający lepiej | spójny token system zamiast kolorów „na oko" |

---

## 6. Checklista przed każdą zmianą UI

- [ ] Czy każda liczba to wielokrotność 4 px?
- [ ] Czy to pasuje do type rampu 12/14/18/20/28 (waga 500, nie 700)?
- [ ] Czy nowy kolor pochodzi z `theme.py` (nie wpisany z palca)?
- [ ] Czy informacja jest przekazywana **tekstem**, nie tylko kolorem?
- [ ] Czy akcja działa też z klawiatury (Tab + Return)?
- [ ] Czy okno 1024×640 wygląda dobrze?
- [ ] Czy resize jest gładki, bez przeskakiwania widgetów?
- [ ] Czy nie dodałem dialogu tam, gdzie wystarczy informacja zwrotna?
- [ ] Czy tekst mieści się w 20–60 znakach na linię?
- [ ] Czy to jest *n*iewyższe wyjaśnienie niż dotąd?
