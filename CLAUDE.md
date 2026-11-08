# AP - Assistive Prototypes

Aplikacja dla osób komunikujących się jednym przełącznikiem lub eyetrackerem (interfejs skanujący, komunikaty głosowe). Działa na komputerach użytkowników: **Ubuntu 20.04 bez aktualizacji systemu, Python 2.7, wxPython 2.8**. Kod musi działać w Pythonie 2.7 - bez f-stringów, `print` jako instrukcja lub `from __future__ import print_function`, `unicode` vs `str`.

## Stan i gdzie zacząć (2026-11-04)
Mapa wszystkich trzech repozytoriów (AP, Wicero, ap-gra), komputery, zasady pracy i pułapki: **`docs/mapa-projektow.md` w repo `wicero`** (`C:\Users\User\PycharmProjects\wicero` na komputerze deweloperskim).
- **Wicero** (filmy od kontaktów, PRZEŚLIJ): działa i jest przetestowane na komputerze użytkownika. Stan i następne zadanie („nieaktywny kontakt”): `WICERO_PLAN.md` → „▶ Start następnej sesji”; decyzja: `docs/adr/0001-modul-wicero.md`.
- **Film w tle** (W TLE, kafel ODTWARZACZ w YOUTUBE i NOWE): `AT_YOUTUBE_PROGRESS.md` → „Zgłoszone przez użytkownika”; do testu B11-B12 (LOSOWE).
- **Gry przygodowe** (plansza GAMES → GRY PRZYGODOWE: Tajemnica zegara, Ostatnia zwrotka i gry tworzone przez użytkownika z AI): `GRA_PLAN.md` (testy P1-P11 zaliczone 2026-11-08, zostały P12 i P13); serwer gry i kreator - repo `ap-gra` (`docs/kreator-gier.md`).
- Kod UI pisany na komputerze deweloperskim nie da się tam uruchomić (brak wx 2.8 / VLC) - kompilacja w Pythonie 2.7 w Dockerze, testy ręczne u użytkownika, po jednym; AP z terminala: `python ap.py 2>&1 | tee /tmp/ap.log`.

## Zasady
- **Terminologia:** nigdy nie używaj słów "opiekun" ani "niepełnosprawny" (kod, UI, komunikaty, dokumentacja). Osoba korzystająca z AP to **kontakt**, osoba wysyłająca materiały - **nadawca**.
- **Komendy:** pytaj o zgodę przed każdą komendą zmieniającą stan (instalacja, zapis poza edycją kodu, git commit/push, restart usług). Odczyt (pliki, logi, `git status`, uruchomienie testów tylko do odczytu) - bez pytania.
- **Logika skanowania** (`onPress` / `timerUpdate` w modułach) jest krucha - kopiuj z istniejących modułów, nie przerabiaj (`AT_YOUTUBE_PROGRESS.md`).
- Nie aktualizuj pakietów systemowych ani Pythona - komputery użytkowników nie są aktualizowane, kod ma działać na tym, co jest.
- Rozmowa i dokumentacja po polsku; komentarze w kodzie jak w otaczającym kodzie.

## Inne dokumenty
- `AT_YOUTUBE_PLAN.md`, `AT_YOUTUBE_PROGRESS.md` - moduł YouTube (`modules/youtube_menu.py`, `modules/youtube2.py`, `modules/at_youtube.py`; film w tle - `modules/background.py`)
- `GRA_PLAN.md` - gry (`gra_client.py`, `modules/gra.py`, `modules/scenka.py`, `modules/przygody.py` - plansza GRY PRZYGODOWE; `kreator_client.py`, `modules/kreator.py` - rozmowa z AI o nowej grze); `modules/board.py` - wspólna plansza ze skanowaniem (Wicero, gra)
- `SYNTEZATOR.md` - głos AP (`milena_say` → Piper mc_speech)
- `IOT_INTEGRATION_PLAN.md` - moduł IoT (`iot_client.py`, `modules/iot.py`)
- `parameters` (przez `reader.py`) - ustawienia użytkownika: `control`, `timeGap`, kolory, dźwięki. Obsługiwany jest tylko `control=switch` (skanowanie). `tracker` jest nieużywany od ok. 10 lat; gałęzie `control == 'tracker'` w modułach to martwa pozostałość - nie testować ani nie rozwijać (szczegóły: T11 w `WICERO_PLAN.md`).
