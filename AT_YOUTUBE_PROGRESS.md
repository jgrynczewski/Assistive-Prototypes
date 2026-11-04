# Postęp prac - moduł YouTube

## Status: at_youtube.py działa w AP, youtube2.py działa, youtube_menu.py łączy wszystko

---

## Co zostało zrobione

### Infrastruktura
- ✅ Klucz YouTube Data API v3 zapisany w `.youtube_api_key`
- ✅ VLC zainstalowany (`sudo apt install vlc`)
- ✅ python-vlc 2.2 w `/home/radoslaw/.local/lib/python2.7/site-packages/vlc.py`
- ✅ yt-dlp zaktualizowany do 2026.x przez `python3.12 -m pip install -U yt-dlp`
- ✅ oauth2client + google-api-python-client==1.7.11 zainstalowane (dla at_youtube2.py)
- ✅ sqlite3 - baza `youtube.db` w pathToAP z tabelami `seen` i `favourites`

### Skrypty testowe
- ✅ `test_yt_api.py` - pobiera 50 filmów trending PL z YouTube Data API v3
- ✅ `test_vlc_stream.py` - VLC embedded w wxPython
- ✅ `test_vlc_control.py` - sterowanie next/prev/pause/volume
- ✅ `test_vlc_playback.py` - finalny test z ffmpeg pipe, paskiem postępu, 5 krótkich filmów
- ✅ `test_yt_search.py` - test wyszukiwania po frazie (lista fraz, cache 24h, ffmpeg pipe)

### Moduł at_youtube.py (modules/at_youtube.py)
- ✅ Zaimplementowany jako moduł AP (wx.Frame z skanowaniem)
- ✅ ffmpeg pipe (stdout=PIPE + /proc/self/fd/N) - audio sync działa
- ✅ Skanowanie: start w uśpieniu ('rest'), tylko kolumny (bez wiersza)
- ✅ Po wyborze przycisku → wraca do uśpienia
- ✅ Kolejność przycisków: NASTEPNY ULUBIONE PLAY_PAUSE CISZEJ GLOSNIEJ POPRZEDNI EXIT
- ✅ Dźwięki z `/sounds/youtube/`
- ✅ Losowe filmy z mostPopular (API key)

### Moduł youtube2.py (modules/youtube2.py)
- ✅ Galeria fraz - skanowanie panel→row→columns (skopiowane z youtube2_backup.py bez zmian)
- ✅ Wyszukiwanie po frazie przez YouTube Data API v3 (API key)
- ✅ Cache per fraza w `youtube_search_<fraza>.json` - ważny 24h
- ✅ Seen per fraza w SQLite (tabela `seen` z kolumną `query`) - nie powtarza obejrzanych
- ✅ Ulubione w SQLite (tabela `favourites`)
- ✅ Doładowywanie playlisty w tle gdy zostaje ≤10 filmów
- ✅ Pusty panel górny usunięty - galeria wypełnia cały ekran
- ✅ SQLite z `check_same_thread=False` (obiekt tworzony w głównym wątku, używany w wątku)

### Moduł youtube_menu.py (modules/youtube_menu.py)
- ✅ Menu wyboru trybu YouTube - topologia jak nowe.py (2 wiersze × 3 kolumny)
- ✅ WYSZUKAJ → youtube2.py (galeria fraz)
- ✅ LOSOWE → at_youtube.py (losowe filmy)
- ✅ EXIT → powrót do nowe.py

### Moduł at_youtube2.py (standalone OAuth2)
- ✅ OAuth2 z google-api-python-client (Desktop app, client_secrets.json)
- ✅ Pobiera subskrypcje przez `subscriptions().list()`
- ✅ `playlistItems().list()` zamiast `search().list()` - 1 jednostka/kanał zamiast 100
  - uploads playlist ID = 'UU' + channel_id[2:]
  - pobiera 5 ostatnich filmów z każdego kanału
- ✅ Cache w `youtube_playlist_cache.json` - ważny 6 godzin

### Integracja z AP
- ✅ `nowe.py` - YOUTUBE otwiera `youtube_menu` (zamiast bezpośrednio at_youtube)
- ✅ `migrate_youtube_db.py` - jednorazowy skrypt migracji bazy (dodaje kolumnę query do seen)

---

## Kluczowe wnioski techniczne

### ffmpeg pipe - jedyna działająca metoda audio+video
```python
self._ffmpeg_proc = subprocess.Popen(
    ['ffmpeg', '-loglevel', 'quiet',
     '-i', video_url, '-i', audio_url,
     '-c', 'copy', '-f', 'matroska', 'pipe:1'],
    stdout=subprocess.PIPE,
    stderr=open(os.devnull, 'w')
)
fd_path = '/proc/self/fd/%d' % self._ffmpeg_proc.stdout.fileno()
wx.CallAfter(self._start_play, fd_path)
```

### NIE UŻYWAĆ:
- `mkfifo` (named pipe) - ffmpeg blokuje się przy open(), deadlock
- `:input-slave=` - audio ucinane ~2s przed końcem
- `fd://N` lub `/proc/self/fd/N` jako stały URL - FD zmienia się między filmami (UWAGA: ale w obecnym kodzie /proc/self/fd/N **działa** bo jest odczytywane natychmiast po Popen)
- `vlc.Instance(..., '--no-plugins-cache')` - segfault
- `media.slaves_add()` - nie istnieje w vlc.py 2.2

### Format selector
```python
FMT = 'bestvideo[height<=480][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio'
```

### Pasek postępu - time.time() nie get_time()
`player.get_time()` przy DASH zwraca 0 przez pierwsze 2s i skacze.
`time.time() - _play_start_time` rośnie płynnie od zdarzenia PLAYING.

### Skanowanie AP - at_youtube.py (odtwarzacz)
```python
self.flag = 'rest'  # start w uśpieniu
# tylko kolumny, bez osobnego skanowania wiersza
```
**UWAGA:** Skanowanie jest bardzo wrażliwe na zmiany - nie modyfikować bez potrzeby.

### Skanowanie AP - youtube2.py (galeria)
Skopiowane dosłownie z `youtube2_backup.py`. Logika: panel→row→columns.
**UWAGA:** Nie zmieniać - każda zmiana może zepsuć działanie na wiele godzin debugowania.

### SQLite w wątkach
```python
self.db = sqlite3.connect(dbPath, check_same_thread=False)
```
Jeśli połączenie otwarte w głównym wątku ale używane w wątku roboczym → `ProgrammingError`.
Rozwiązanie: `check_same_thread=False`.

### SQLite - migracja schematu
Stara baza `youtube.db` (z at_youtube.py) miała tabelę `seen` bez kolumny `query`.
youtube2.py potrzebuje kolumny `query`. Rozwiązanie: jednorazowy skrypt `migrate_youtube_db.py`.
**NIE robić migracji w __init__ każdego uruchomienia.**

### Pusty panel w galerii
W youtube2_backup.py górny panel (22% wysokości) służył do wyświetlania obrazka komunikacyjnego.
W youtube2.py nie jest potrzebny - usunięto `displaySizer` i zmieniono `SetMinSize` na pełną wysokość.

### Głośność filmów
Filmy YouTube mają zróżnicowaną głośność nagraną w źródle.
Możliwe rozwiązania:
- VLC: dodać `'--gain=2.0'` do `vlc.Instance()`
- ffmpeg: zmienić `-c copy` na `-filter:a "volume=2.0"` (wymaga re-enkodowania audio, wolniejsze)

### YouTube API - quota i kiedy używać czego

| Metoda | Koszt | Kiedy używać |
|--------|-------|--------------|
| `search.list` | 100 jednostek | Szukanie po frazie - używaj rzadko, cache'uj wyniki |
| `playlistItems.list` | 1 jednostka | Ostatnie filmy z kanału - tanie, używamy w at_youtube2.py |
| `subscriptions.list` | 1 jednostka | Lista subskrybowanych kanałów |
| Limit dzienny | 10000 jednostek | Przy 123 kanałach × 1 = 123 jednostki na odświeżenie |

**Kiedy OAuth2, kiedy API key:**
- **API key** - wystarczy do `search.list` (wyszukiwanie po frazie), publiczne dane, bez logowania
- **OAuth2** - potrzebne do danych prywatnych: subskrypcje, historia, ulubione

**OAuth2 token - logowanie jednorazowe:**
- Token zapisany w `youtube_oauth_token.json`
- Zawiera refresh token - odnawiany automatycznie w tle
- NIE trzeba ponownie potwierdzać w przeglądarce po restarcie
- Jedyny wyjątek: usunięcie pliku tokenu lub cofnięcie uprawnień w Google Account

**Strategia search po frazie:**
- Jedno wyszukiwanie = 100 jednostek
- Cache wyniki w JSON per fraza (`youtube_search_<fraza>.json`), ważny 24h
- Odświeżaj gdy cache wygasł lub na żądanie użytkownika
- Używać API key (nie OAuth2) - prostsze, wystarczające

**Cache wiek w logach:**
`[LOAD] cache OK wiek=126s` - wiek pliku cache w sekundach od ostatniego pobrania. Normalny komunikat.

---

## Napotkane trudności i rozwiązania

| Problem | Przyczyna | Rozwiązanie |
|---------|-----------|-------------|
| Audio ucinane 2s przed końcem | `:input-slave=` nie synchronizuje zakończenia | ffmpeg remux do MKV pipe |
| Deadlock przy mkfifo | ffmpeg blokuje przy open(), VLC czeka na dane | `stdout=PIPE` + `/proc/self/fd/N` |
| `get_time()` skacze | DASH stream - VLC nie zna długości od razu | `time.time() - _play_start_time` |
| `ProgrammingError` SQLite w wątku | Połączenie z głównego wątku używane w worker thread | `check_same_thread=False` |
| `OperationalError: no such column: query` | Stara tabela `seen` bez kolumny `query` | Jednorazowy `migrate_youtube_db.py` |
| Czarny pasek 15% na górze galerii | Pusty `displaySizer` z oryginalnego youtube2_backup.py | Usunięcie panelu, pełna wysokość |
| Skanowanie przestaje działać | Drobna zmiana w logice timerUpdate/onPress | Kopiować dosłownie, nie modyfikować |
| `wx.CallLater` z wątku | wxPython 2.8 nie obsługuje CallLater z innego wątku | `wx.CallAfter(wx.CallLater, 500, ...)` |

---

## Co dalej

### Priorytet
- [ ] Głośność filmów - dodać `--gain` do VLC lub wzmocnienie w ffmpeg
- [ ] Ikona dla WYSZUKAJ w youtube_menu (na razie mockowana przez youtube2.png)
- [ ] Dźwięki dla WYSZUKAJ i LOSOWE w youtube_menu (na razie używa youtube.ogg dla obu)

### Zgłoszone przez użytkownika (2026-11-01)
- [x] **Odtwarzacz w tle** - zrobione i przetestowane 2026-11-01 (B1-B10 niżej); LOSOWE - B11-B12 do testu.
  - Decyzje użytkownika: przycisk **W TLE** na pasku odtwarzacza (za PRZEŚLIJ / ULUBIONE / USUŃ) - okno znika, film gra dalej, AP wraca do menu YOUTUBE; powrót: kafel **ODTWARZACZ** w menu YOUTUBE (na miejscu pustego; bez filmu w tle wygląda i działa jak PUSTE); zatrzymanie: EXIT w odtwarzaczu. Moduły, które grają / mówią, **pauzują film w tle i wznawiają po wyjściu**: Wicero, MUZYKA, RADIO, AUDIOBOOKI, TV. PISAK, SKOCZEK, ŁAPACZ i **Tajemnica zegara** - film gra dalej (gra: decyzja 2026-11-04 - użytkownik chce słuchać YouTube w trakcie gry; wcześniej gra pauzowała).
  - Ustalenia: jeden film w tle naraz (nowy odtwarzacz - WYSZUKAJ, ULUBIONE, LOSOWE, Wicero - zamyka ten z tła); muzyka / radio / audiobook grają dalej po wyjściu z modułu (smplayer) - wtedy film się nie wznawia, wraca grając dopiero przez ODTWARZACZ. **W drugą stronę (z testu B5):** film YouTube, który zaczyna grać (nowy, LOSOWE, Wicero, powrót przez ODTWARZACZ), zamyka smplayer (`background.stopMusic`) - gra to, co wybrane ostatnio, nic się nie nakłada.
  - Kod: `modules/background.py` (jeden odtwarzacz, `pause` / `resume` / `guard` / `stopMusic` / `returnTo`; domieszka `BackgroundPlayer` - `_toBackground`, `returnFromBackground`, `closeBackground` - wspólna dla `youtube2.PlayerFrame` i `at_youtube.youtube`; okno odtwarzacza należy do głównego menu AP (`topWindow`), więc zamknięcie menu YouTube / galerii / Wicero go nie zamyka), `nowe.py` (kafel ODTWARZACZ), `youtube_menu.py` (kafel ODTWARZACZ, `Show` → `refreshPlayerTile`), `ap.py` (`background.guard` dla muzyki, radia, audiobooków, TV), `wicero.py` / `gra.py` (pause / resume). Ikony: `icons/pilots/minitubePilot/14_background.png`, `icons/modules/youtube_odtwarzacz.png`.
  - Testy (AP z terminala: `python ap.py 2>&1 | tee /tmp/ap.log`):
    - B1-B7 passed 2026-11-01 (B7: ok. 1% CPU) (B6: poprzedni film przepada - decyzja: tak zostaje) (B3 po poprawce: szary pasek - `Enable` przy powrocie).
    - [x] **B1** YOUTUBE → WYSZUKAJ → film: na pasku W TLE (nuta ze strzałką) za PRZEŚLIJ, przy skanowaniu „do tła” (`sounds/do_tła.ogg`; bez pliku - głos AP). Wybór → menu YOUTUBE, film słychać dalej; kafel ODTWARZACZ z ikoną, przy skanowaniu „Odtwarzacz”.
    - [x] **B2** Z menu YOUTUBE wyjść do głównego menu, wejść w PISAK albo SKOCZEK - film słychać cały czas, wszystko działa normalnie.
    - [x] **B3** YOUTUBE → ODTWARZACZ - odtwarzacz wraca **z obrazem**, skanowanie paska działa; EXIT → film staje, w menu YOUTUBE kafel znów pusty.
    - [x] **B4** Film w tle → NOWE → WICERO - film milknie; wyjście z Wicero - gra dalej od tego miejsca. (Gra Tajemnica zegara pauzowała do 2026-11-04 - teraz film gra dalej, test G11 w `GRA_PLAN.md`.)
    - [x] **B5** Film w tle → MUZYKA → włączyć album → wyjść - gra muzyka, film stoi; YOUTUBE → ODTWARZACZ - film wraca grając, **muzyka milknie**; W TLE - gra tylko film. Też: muzyka gra → YOUTUBE → WYSZUKAJ → film - muzyka milknie.
    - [x] **B6** Film w tle → YOUTUBE → ULUBIONE (albo WYSZUKAJ) → inny film - tamten z tła zamilkł (jeden naraz); W TLE działa też z ULUBIONYCH.
    - [x] **B7** `top` z filmem w tle - AP nie zjada procesora (wideo dekodowane w ukrytym oknie).
  - **W TLE w Wicero** (prośba użytkownika 2026-11-01: długi film od kontaktu też w tle; B8-B10 passed 2026-11-01): W TLE w odtwarzaczu Wicero zamyka Wicero (ekran przed filmem, typy, nadawcy) i wraca do **NOWE**; film gra dalej. Kafel **ODTWARZACZ także w NOWE** (miejsce po przeniesionej grze) - wraca do każdego filmu w tle, z YouTube albo z Wicero. Film z Wicero w tle: koniec / NASTĘPNY / POPRZEDNI kończy odtwarzanie (ekranu przed filmem już nie ma - nic nie wyskakuje); „obejrzany” zgłasza się jak zwykle.
    - [x] **B8** WICERO → nadawca → FILMY → START → na pasku W TLE za PRZEŚLIJ → wybór: AP w NOWE, film słychać, kafel ODTWARZACZ (ekran z nutą). Wyjść do głównego menu, coś porobić - film gra.
    - [x] **B9** NOWE → ODTWARZACZ - film z Wicero wraca z obrazem, przyciski aktywne; EXIT → NOWE, kafel pusty. Też: film z YouTube w tle → NOWE → ODTWARZACZ - wraca film z YouTube.
    - [x] **B10** Film z Wicero w tle do końca (krótki film) - po końcu cisza, nic nie wyskakuje; w aplikacji Wicero u nadawcy film „obejrzany”.
  - **LOSOWE** (`at_youtube.py`, 2026-11-01): **PRZEŚLIJ i W TLE** jak w pozostałych odtwarzaczach - pasek `NASTĘPNY ULUBIONE PRZEŚLIJ W_TLE PLAY_PAUSE CISZEJ GŁOŚNIEJ POPRZEDNI EXIT` (PRZEŚLIJ tylko z plikiem `.wicero_token`). LOSOWE nie pauzuje już filmu w tle - zastępuje go (jeden naraz).
    - [ ] **B11** YOUTUBE → LOSOWE → na pasku PRZEŚLIJ i W TLE za ULUBIONE; PRZEŚLIJ → Test Anna → „Film przesłany: Test Anna.”, film gra dalej.
    - [ ] **B12** LOSOWE → W TLE → menu YOUTUBE, film słychać; ODTWARZACZ (w YOUTUBE albo NOWE) → wraca z obrazem, przyciski aktywne; po NASTĘPNY lecą kolejne losowe filmy; EXIT → kafel pusty. Film z WYSZUKAJ w tle → LOSOWE → tamten milknie.
- [x] **PRZEŚLIJ w LOSOWE** - zrobione 2026-11-01 razem z W TLE (wyżej, B11).

### at_youtube2.py - integracja do AP
- [ ] Przenieść logikę OAuth2+subskrypcje do osobnego modułu AP
- [ ] Dodać jako trzecia opcja w youtube_menu: SUBSKRYPCJE

### Opcjonalne ulepszenia
- [ ] Przycisk ODŚWIEŻ w odtwarzaczu - wymusza nowe zapytanie API (ignoruje cache)
- [ ] Licznik seen - "obejrzano X z Y dostępnych filmów dla tej frazy"
- [ ] Podgląd tytułu aktualnie odtwarzanego filmu (pasek statusu)

---

## Pliki kluczowe

| Plik | Opis |
|------|------|
| `modules/at_youtube.py` | ✅ Odtwarzacz losowych filmów (mostPopular) |
| `modules/youtube2.py` | ✅ Galeria fraz + odtwarzacz z wyszukiwaniem |
| `modules/youtube_menu.py` | ✅ Menu wyboru trybu YouTube |
| `modules/nowe.py` | Punkt wejścia - YOUTUBE → youtube_menu |
| `at_youtube2.py` | ✅ Standalone OAuth2 + subskrypcje |
| `modules/youtube2_backup.py` | Backup oryginalnej galerii (NIE modyfikować) |
| `client_secrets.json` | OAuth2 credentials (Desktop app) |
| `youtube_oauth_token.json` | Token OAuth2 (generowany automatycznie) |
| `youtube_playlist_cache.json` | Cache subskrypcji OAuth2 (generowany automatycznie) |
| `youtube_search_<fraza>.json` | Cache wyszukiwania per fraza (generowany automatycznie) |
| `.youtube_api_key` | Klucz API Google |
| `youtube.db` | Baza SQLite: tabele `seen` i `favourites` |
| `migrate_youtube_db.py` | Jednorazowa migracja DB (dodaje kolumnę query) |
| `test_vlc_playback.py` | Skrypt testowy ffmpeg pipe |
| `test_yt_search.py` | Skrypt testowy wyszukiwania po frazie |