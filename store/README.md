# Materialy do sklepow

Zrzuty z prawdziwego programu, nie mockupy.

| plik | co pokazuje |
|---|---|
| `02-wyniki-dark.png` | ciemny motyw, 8 plikow z danymi, GPS w panelu bocznym |
| `02-wyniki-light.png` | jasny motyw, to samo |
| `01-start-dark.png` | stan poczatkowy (sto) |
| `01-start-light.png` | stan poczatkowy, jasny |

## Skad zdjecia na zrzutach

`picsum.photos` (seedy p1-p12). Licencja pozwala na uzytk komercyjny
bez podawania autora.

Nie uzywam plikow testowych uzytkownika (`~/zdjecia-testowe/hard`) - zawieraja
jego dane osobowe (imie, nazwisko w Copyright/Artist, pelna sciezka
`/home/arch/...`). Pierwsza wersja zrzutu to pokazywala; do sklepu nie poszla.

## Skad metadane na zrzutach

Fikcyjne, generowane w `tools/make_store_shots.py`: GPS na tropie polskich
miast, wymysleni autorzy, `Copyright (c) 2026 Hartwell Labs`. Program naprawde
je znajduje - zrzut pokazuje dzialanie, nie atrapze.

## Brakuje

`03-telefon-*.png` - dialog "Wyslij zdjecia z telefonu". `Window._from_phone()`
konczy sie `d.exec()`, ktore blokuje petle (serwer HTTP trzyma watek), wiec
offscreen nie moze go zrobic. Zrob to recznie: kliknij "Z telefonu" i zrob
zrzut ekranu.

## Rozmiary dla sklepow

- Microsoft Store: 1366x768 lub 1920x1080, PNG lub JPEG
- Uptodown / Softpedia: 800x600 w gore
- Miniatury w sklepach: 256x256 i 512x512 (uzyj `packaging/msix/assets/logo.png`)
