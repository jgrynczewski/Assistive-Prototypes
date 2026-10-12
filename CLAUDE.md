# AP - Assistive Prototypes

Aplikacja dla osób komunikujących się jednym przełącznikiem lub eyetrackerem (interfejs skanujący, komunikaty głosowe). Działa na komputerach użytkowników: **Ubuntu 20.04 bez aktualizacji systemu, Python 2.7, wxPython 2.8**. Kod musi działać w Pythonie 2.7 - bez f-stringów, `print` jako instrukcja lub `from __future__ import print_function`, `unicode` vs `str`.

## Bieżące zadanie: moduł Wicero
Odbiór filmów YouTube przesyłanych przez bliskich w systemie Wicero. **Zacznij od `WICERO_PLAN.md`** (stan, kontrakt API, testy T1-T12, ryzyka), decyzja: `docs/adr/0001-modul-wicero.md`. Backend jest gotowy w chmurze; kod w AP czeka na pierwsze uruchomienie i poprawki na tym komputerze.

## Zasady
- **Terminologia:** nigdy nie używaj słów "opiekun" ani "niepełnosprawny" (kod, UI, komunikaty, dokumentacja). Osoba korzystająca z AP to **kontakt**, osoba wysyłająca materiały - **nadawca**.
- **Komendy:** pytaj o zgodę przed każdą komendą zmieniającą stan (instalacja, zapis poza edycją kodu, git commit/push, restart usług). Odczyt (pliki, logi, `git status`, uruchomienie testów tylko do odczytu) - bez pytania.
- **Logika skanowania** (`onPress` / `timerUpdate` w modułach) jest krucha - kopiuj z istniejących modułów, nie przerabiaj (`AT_YOUTUBE_PROGRESS.md`).
- Nie aktualizuj pakietów systemowych ani Pythona - komputery użytkowników nie są aktualizowane, kod ma działać na tym, co jest.
- Rozmowa i dokumentacja po polsku; komentarze w kodzie jak w otaczającym kodzie.

## Inne dokumenty
- `AT_YOUTUBE_PLAN.md`, `AT_YOUTUBE_PROGRESS.md` - moduł YouTube (`modules/youtube_menu.py`, `modules/youtube2.py`)
- `IOT_INTEGRATION_PLAN.md` - moduł IoT (`iot_client.py`, `modules/iot.py`)
- `parameters` (przez `reader.py`) - ustawienia użytkownika: `control` (`switch` / `tracker`), `timeGap`, kolory, dźwięki
