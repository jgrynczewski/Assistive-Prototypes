# Plan modułu YouTube dla Assistive-Prototypes

## Kontekst

Moduł YouTube jako rozszerzenie `nowe.py` w projekcie Assistive-Prototypes.
Wszystko w jednym repo, bez osobnego serwisu.
Zasady AT obowiązują w całości: scanning interface, jeden przycisk/switch, Python 2.7, wxPython 2.8.

---

## Architektura

```
ap.py
  └── nowe.py
        ├── [IOT]      → modules/iot.py
        ├── [YOUTUBE]  → at_youtube.py
        ├── [SHORTS]   → at_youtube.py (tryb shorts, implementacja później)
        ├── [PUSTE]
        ├── [PUSTE]
        └── [EXIT]
```

### Przepływ danych

```
.youtube_api_key (plik konfiguracyjny)
        ↓
at_youtube.py pobiera listę 50 URL filmów przez YouTube Data API v3
        ↓
python-vlc otrzymuje URL-e jako playlist
        ↓
VLC streamuje filmy bezpośrednio z YouTube (embedded w oknie wxPython)
        ↓
pilot wxPython (dolna część okna) steruje VLC przez python-vlc API:
  next() / previous() / pause() / audio_set_volume()
```

### Jedno okno wxPython

```
┌─────────────────────────────────────────┐
│                                         │
│         VLC embedded (film)             │
│            (~80% okna)                  │
│                                         │
├─────────────────────────────────────────┤
│  ◀  │  ▶/⏸  │  ▶▶  │  🔊+  │  🔊-  │ ✕ │
│         scanning interface              │
└─────────────────────────────────────────┘
```

---

## Pliki do utworzenia

### `at_youtube.py`
Główny moduł YouTube. Klasa `youtube(wx.Frame)`.
Wzorzec: identyczny jak inne moduły AP (`initializeParameters`, `initializeBitmaps`, `createGui`, `createBindings`, `initializeTimer`, `onPress`, `timerUpdate`, `onExit`, `OnCloseWindow`).

Struktura okna:
- górna część: `wx.Panel` z VLC XEmbed (`vlc.MediaPlayer` + `set_xwindow(panel.GetHandle())`)
- dolna część: `wx.GridBagSizer` z 6 przyciskami (1 wiersz)

Stan wewnętrzny:
- `self.playlist` - lista URL filmów
- `self.current_index` - aktualny film
- `self.player` - instancja `vlc.MediaPlayer`
- `self.is_playing` - bool (do przełączania ikony play/pause)

### `.youtube_api_key`
Plik tekstowy w katalogu AP, jedna linia - klucz API Google.
Edytowany ręcznie przez opiekuna użytkownika.
Format: `AIza...`

### `icons/modules/youtube.png`
Ikona przycisku YOUTUBE w `nowe.py`. 200×200px, PNG RGBA.

### `icons/youtube/`
Ikony przycisków pilota (200×200px, PNG RGBA):
- `poprzedni.png` - strzałka w lewo z kreską
- `play.png` - trójkąt
- `pause.png` - dwie pionowe kreski
- `nastepny.png` - strzałka w prawo z kreską
- `glosniej.png` - głośnik z falami +
- `ciszej.png` - głośnik z falami -

### `sounds/youtube/`
Dźwięki przycisków pilota (.ogg, fallback milena_say):
- `youtube.ogg` - „YouTube"
- `poprzedni.ogg` - „poprzedni"
- `play.ogg` - „odtwarzaj"
- `pause.ogg` - „pauza"
- `nastepny.ogg` - „następny"
- `glosniej.ogg` - „głośniej"
- `ciszej.ogg` - „ciszej"

---

## Zmiany w istniejących plikach

### `modules/nowe.py`
- Dodać `import at_youtube` (lub wywołanie przez subprocess)
- Zmienić slot 2 z `PUSTE` na `YOUTUBE`
- Dodać ikonę `youtube.png` dla slotu YOUTUBE
- Dodać dźwięk `youtube.ogg`
- Dodać obsługę `label == 'YOUTUBE'` w `onPress` i `timerUpdate`

---

## Implementacja `at_youtube.py` - szczegóły

### `initializeParameters`
- Wczytuje klucz API z `.youtube_api_key`
- Inicjalizuje `vlc.Instance()` i `vlc.MediaPlayer()`
- Pobiera playlistę przez YouTube Data API v3
- Ładuje dźwięki przycisków

### Pobieranie playlisty (YouTube Data API v3)

Cel: maksymalna różnorodność, charakter zbliżony do scrollowania Shorts.

**Strategia startowa:**
- Pobierz 50 filmów popularnych w PL (`chart=mostPopular&regionCode=PL`)
- Pobierz po ~20 filmów z kilku kategorii (muzyka, sport, gaming, rozrywka, nauka)
- Łącznie ~150-200 filmów na start
- Shuffle całej listy przed odtwarzaniem

**Kategorie YouTube (categoryId):**
| ID | Kategoria |
|----|----------|
| 10 | Muzyka |
| 17 | Sport |
| 20 | Gaming |
| 24 | Entertainment |
| 28 | Nauka i technologia |

```
GET https://www.googleapis.com/youtube/v3/videos
  ?part=snippet,contentDetails
  &chart=mostPopular
  &regionCode=PL
  &maxResults=50
  &videoCategoryId=<id>   ← opcjonalnie
  &pageToken=<token>      ← paginacja
  &key=<klucz>
```
Zwraca listę video ID → konstruuje URL-e: `https://www.youtube.com/watch?v=<id>`

**Ładowanie kolejnych filmów (doładowywanie):**
- Gdy zostanie ~20 filmów na liście → pobierz kolejne 50 w tle (wątek/timer)
- Użyj `pageToken` do paginacji
- Nowe filmy dołącz (shuffle) do końca listy

**Historia (seen_ids):**
- Przechowywana w SQLite (`youtube.db`)
- Przy pobieraniu nowych filmów: pomiń ID już widziane
- Czyść historię starszą niż 30 dni (lub po obejrzeniu całej dostępnej puli)

### `createGui`
- Górna część: `wx.Panel` jako kontener VLC
- Dolna część: `wx.GridBagSizer` 1×6 z przyciskami
- VLC embedded: `self.player.set_xwindow(self.vlc_panel.GetHandle())`
- Uruchamia pierwszy film: `self.player.set_mrl(self.playlist[0])` + `self.player.play()`

### Przyciski pilota

| Nazwa | Akcja |
|-------|-------|
| `poprzedni` | `self.current_index -= 1` + `_play_current()` |
| `play_pause` | `self.player.pause()` + zmiana ikony play↔pause |
| `nastepny` | `self.current_index += 1` + `_play_current()` |
| `glosniej` | `self.player.audio_set_volume(vol + 10)` |
| `ciszej` | `self.player.audio_set_volume(vol - 10)` |
| `wyjście` | `self.player.stop()` + `self.onExit()` |

### `timerUpdate`
Identyczny wzorzec jak inne moduły AP:
- scanning wierszy → skanowanie kolumn → wybór
- Ostatni element (wyjście) obsługiwany jak back button w innych modułach
- Auto-wykrywanie końca filmu: `self.player.get_state() == vlc.State.Ended` → `_next()`

---

## Obsługa błędów

| Błąd | Zachowanie |
|------|-----------|
| Brak pliku `.youtube_api_key` | milena_say „Brak klucza API" → `onExit()` |
| Błąd połączenia z API | milena_say „Brak połączenia z internetem" → `onExit()` |
| Pusta lista filmów | milena_say „Nie pobrano filmów" → `onExit()` |
| Błąd streamowania filmu | automatycznie przejdź do następnego |
| VLC XEmbed nie działa | fallback: mpv jako osobny subprocess (plan B) |

---

## Zależności systemowe

Zainstalowane i działające:
- VLC: `sudo apt install vlc` ✅
- python-vlc dla Python 2.7: pobrane ręcznie `vlc.py` wersja 2.2 z github oaubert ✅
  - UWAGA: wersja 3.0 nie działa z Python 2.7 (używa `PyFile_FromFd` z Python 3)
  - Plik: `/home/radoslaw/.local/lib/python2.7/site-packages/vlc.py`
- yt-dlp: `python3.12 -m pip install -U yt-dlp` → `/home/radoslaw/.local/bin/yt-dlp` ✅
  - UWAGA: stara wersja 2021 nie działa z YouTube (błąd signature extraction)
  - UWAGA: yt-dlp wymaga Python 3.10+, nie działa przez Python 2.7
  - Wywołujemy jako subprocess z Python 2.7
- Klucz YouTube Data API v3: zapisany w `.youtube_api_key` ✅

---

## Ulubione (SQLite)

Przechowywanie w `youtube.db` (SQLite) - wbudowany w Python, nie wymaga instalacji.

```sql
CREATE TABLE favourites (
    id          TEXT PRIMARY KEY,  -- video ID z YouTube
    title       TEXT,
    thumbnail   TEXT,              -- URL miniaturki
    duration    TEXT,              -- np. '3:45'
    added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE seen (
    id       TEXT PRIMARY KEY,
    seen_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Przycisk „dodaj do ulubionych"** (w pilocie, obok wyjścia):
- Zapisuje aktualny film do tabeli `favourites`
- Odczytuje `snippet.title` i `snippet.thumbnails` z danych API (przechowywanych w pamięci razem z playlist)

**Widok ulubionych:**
- Osobny ekran / tryb w `at_youtube.py`
- Lista filmów z ulubionych - skanowanie + odtworzenie wybranego
- Przycisk „usuń z ulubionych" przy każdym filmie

---

## Pomysły na przyszłość (nie w MVP)

- **Galeria thumbnails** - kafelki z miniaturkami filmów, skanowanie po kafelkach (jak żarówki w iot.py)
- **Hasła/kategorie użytkownika** - np. „filozofia", „japonia" → wyszukiwanie na YouTube, wyniki jako galeria
- **Shorts** - slot PUSTE w nowe.py, osobny tryb

---

## Co NIE wchodzi w MVP

- Galeria thumbnails
- Hasła użytkownika / wyszukiwarka
- **Shorts** - implementacja później
- **Napisy**
- **Wybór jakości**

---

## Plan B - jeśli VLC XEmbed nie zadziała

Jeśli embedded VLC w wxPython 2.8 będzie niestabilny:
- mpv jako osobny subprocess (`--geometry` na górne 80% ekranu)
- pilot wxPython jako osobne okno (`STAY_ON_TOP`, dolne 20%)
- komunikacja przez IPC socket `/tmp/mpv-yt.sock` (JSON commands)
- `at_youtube.py` uruchamia oba i czeka na zamknięcie pilota

---

## Zasoby do ponownego użycia (już w repo)

### Logika skanowania
Kopiujemy z `modules/pilots/musicPilot.py` - przetestowany wzorzec:
- `numberOfEmptyIteration` + `suspend.py` do uśpienia
- `pactl set-sink-volume 0 ±20%` do głośności systemowej
- `STAY_ON_TOP` pilot w rogu ekranu
- Pełna obsługa tracker/switch

### Ikony przycisków pilota - gotowe z `icons/pilots/minitubePilot/`
| Przycisk | Plik |
|----------|------|
| volume down | `1_volume down.png` |
| volume up | `2_volume up.png` |
| previous | `3_previous.png` |
| next | `4_next.png` |
| pause | `6_pause.png` |
| play | `12_play.png` |
| cancel/wyjście | `9_cancel.png` |

### Dźwięki - gotowe w `sounds/`
- `poprzedni.ogg` ✅
- `następny.ogg` ✅ (z polskim znakiem)
- `ciszej.ogg` ✅
- `glosniej.ogg` ✅
- `zatrzymaj_graj.ogg` ✅ (play/pause)
- `powrot.ogg` ✅
- `youtube.ogg` ✅
- `usypiam.ogg` ✅

### Ikona modułu w nowe.py
Brakuje `icons/modules/youtube.png` - do wygenerowania (można przerobić `youtube1.png`).

---

## Uwaga - minitube

`minitubePilot.py` sterował programem Minitube przez `xdotool` (symulacja klawiszy).
Minitube może nadal działać - to osobna ścieżka, nie koliduje z `at_youtube.py`.
`at_youtube.py` używa VLC/python-vlc zamiast xdotool.

---

## Szybkie przywrócenie kontekstu

1. Przeczytaj ten plik
2. Wzorzec kodu: `modules/pilots/musicPilot.py` (skanowanie, głośność, uśpienie)
3. Ikony: `icons/pilots/minitubePilot/` - gotowe do użycia
4. Sprawdź `modules/nowe.py` - tam wpięcie przycisku YOUTUBE
5. Klucz API: `.youtube_api_key` w katalogu AP
6. Zależności: `python-vlc`, `vlc`, klucz Google API
