# ADR-0001: Moduł Wicero w AP - odbiór filmów od bliskich

**Status:** Accepted (pytania otwarte - patrz koniec dokumentu)

**Data:** 2026-10-12

---

## Kontekst

[Wicero](https://github.com/jgrynczewski/wicero) to system, w którym bliscy (dalej: **nadawcy**) wysyłają osobie korzystającej z AP (dalej: **kontakt**) materiały - na start linki do filmów YouTube z opcjonalnym komentarzem. Nadawcy korzystają z aplikacji Flutter (web / Android); dane są w Firebase (Firestore, Cloud Functions w Pythonie 3.13, region `europe-central2`). Nadawca widzi, czy film został obejrzany.

Do zrobienia: odbiór tych materiałów po stronie kontaktu.

Ograniczenia:
- AP: Python 2.7, wxPython 2.8, Ubuntu 20.04 **bez aktualizacji systemu**; interfejs skanujący (jeden przełącznik / eyetracker), komunikaty głosowe (`.ogg`, `milena_say`).
- Logika skanowania jest krucha (`AT_YOUTUBE_PROGRESS.md`) - nie modyfikujemy jej, tylko kopiujemy / dziedziczymy.
- Odtwarzanie YouTube już działa i jest przetestowane: `modules/youtube2.py` → `PlayerFrame` (yt-dlp + ffmpeg + VLC, wykrywanie końca 85%). `FavouritesPlayer` pokazuje, że wystarczy podmienić źródło playlisty (`_loadPlaylist`).
- Python 2.7 nie ma klienckiego SDK Firebase; zwykłe HTTPS (`urllib2`) działa - AP już tak woła YouTube Data API.

W tekstach, UI i komunikatach nie używamy słów "opiekun" ani "niepełnosprawny".

## Decyzja

### 1. Forma: moduł w AP, cała logika w chmurze
- Odbiór materiałów to **moduł AP** (Python 2.7, wx) - kontakt dostaje ten sam interfejs skanujący co w reszcie AP. Nie budujemy osobnej aplikacji.
- Podział wzorowany na IoT (`iot_client.py` + zewnętrzne API), ale **bez lokalnego kontenera**: API to **Cloud Functions Wicero** (repo `wicero`, katalog `functions/`, Python 3.13). Lokalny kontener IoT jest potrzebny, bo hub musi być w sieci z żarówkami; dane Wicero są w chmurze, więc serwis też.
- **AP nie zawiera logiki biznesowej** - nie zna Firebase, nie liczy kolejności, nie decyduje o przypomnieniach. Pyta API i wyświetla. Zmiana reguł = deploy funkcji, bez aktualizacji komputerów użytkowników.

| Chmura (Cloud Functions, Python 3.13) | AP (Python 2.7) |
|---|---|
| Weryfikacja tokenu kontaktu, sprawdzenie, że kontakt jest aktywny | `.wicero_token` + `wicero_client.py` (styl `iot_client.py`: `urllib2`, timeout, retry, log `wicero.log`) |
| Lista nadawców z liczbą nowych filmów | Kafelek **WICERO** w `nowe.py` → plansza nadawców |
| Filmy nadawcy w gotowej kolejności | Ekran pośredni + `WiceroPlayer` |
| Zapis "otwarty" / "obejrzany" | Wywołanie przy wejściu na ekran pośredni / przy 85% filmu |
| Decyzja: co ogłosić, czy przypomnieć | Timer w tle → `milena_say` |

### 2. Autoryzacja: token w każdym zapytaniu
- Token kontaktu (UUID z panelu admina Wicero) w pliku `.wicero_token` w katalogu AP (jak `.youtube_api_key`), wpisywany ręcznie przy instalacji.
- Każde zapytanie wysyła go w nagłówku `Authorization: Bearer <token>`; funkcja szuka kontaktu po tokenie (Admin SDK po stronie serwera).
- **Zmiana względem ADR-0009 w repo Wicero**, który planował wymianę tokenu na Firebase custom token (`desktop_login`) i bezpośredni dostęp do Firestore. Bez SDK w Pythonie 2.7 custom token wymagałby ręcznej obsługi ID tokenów i odświeżania - token w zapytaniu jest prostszy i wystarcza, bo AP nie nasłuchuje na żywo.

### 3. API (repo `wicero/functions/`, wdrożone 2026-10-12)
| Endpoint | Zwraca / robi |
|---|---|
| `GET contact_senders` | nadawcy z połączeniem `accepted`, z liczbą nowych (`newCount`) i typami materiałów |
| `GET contact_messages?senderId=&type=youtube` | filmy w kolejności playlisty: nowe (nieotwarte) od najnowszego, potem reszta od najnowszego - 85% nie wpływa na kolejność (zmiana 2026-10-18 po testach: długie filmy blokowały początek listy) |
| `POST contact_message_event` `{connectionId, messageId, event: "opened" \| "viewed"}` | ustawia `openedAt` (pierwsze wejście) / `status: viewed`, `viewedAt`, `statusChangedBy: "contact"` |
| `POST contact_notifications` `{startup: bool}` | `{say: [...]}` - ogłoszenia nowych (i oznacza je `announcedAt`) oraz przypomnienie o nieotwartych, jeśli `startup` lub minęła godzina od ostatniego |

Gotowe teksty do przeczytania (`say`) składa serwer - odmiana po polsku w jednym miejscu. Dokładny kontrakt pól: `WICERO_PLAN.md`.

Odpowiedzi: JSON w UTF-8, błąd → `{"error": "..."}`. Brak / zły token → HTTP 401. Kontakt nieaktywny jest wpuszczany - otrzymane materiały zostają dostępne (ADR-0010 w repo Wicero).

### 4. Model danych (rozszerzenie modelu z ADR-0010 w repo Wicero)
- `messages`: nowe pola `openedAt` (pierwsze wejście na ekran pośredni - "kliknięty") i `announcedAt` (ogłoszony głosowo). Statusy bez zmian: `sent` → `viewed`.
- Czas ostatniego przypomnienia - w dokumencie per kontakt (np. `contacts/{id}/private/inbox.lastReminderAt`), żeby zachowanie nie zależało od komputera.

### 5. Nawigacja i UI w AP
```
nowe.py:  IOT  YOUTUBE  WICERO  PUSTE  PUSTE  EXIT
                          │
                          ▼
          Plansza nadawców (imię = displayName nadawcy; czytane przy skanowaniu przez milena_say) + POWRÓT
                          ▼
          Plansza typów materiałów: FILMY + POWRÓT
              (od razu, choć typ jest jeden - nawyk nawigacji nie zmieni się, gdy dojdą zdjęcia, słowa, quizy)
                          │
                          ▼
          Ekran pośredni filmu: tytuł, komentarz, miniatura
              milena_say: "<tytuł>. <komentarz>" (bez imienia - kontakt właśnie wybrał nadawcę;
                          bez #hashtagów, @kanałów i emoji)
              przyciski (jeden wiersz, skanowanie od razu po przyciskach):
                POWTÓRZ (czyta jeszcze raz)  START  NASTĘPNY  POPRZEDNI  POWRÓT
                          │ START
                          ▼
          WiceroPlayer (podklasa PlayerFrame) - pilot jak w youtube2
              NASTĘPNY / POPRZEDNI → ekran pośredni kolejnego / poprzedniego filmu
              koniec filmu → ekran pośredni następnego; po ostatnim → "To już wszystkie filmy." → plansza typów
```
- **Playlista zamiast galerii miniatur** - przy jednym przełączniku każdy wybór to kilka cykli skanowania; playlista daje pierwszy film po dwóch wyborach. Galeria ("przeglądaj wszystkie") ewentualnie później.
- **Obejrzany = 85% długości** (ta sama miara co `_isRealEnd`), zgłaszany raz w trakcie odtwarzania.
- Skanowanie plansz kopiowane z istniejących modułów bez zmian logiki (`youtube_menu.py` / `iot.py`).
- `WiceroPlayer` nie zapisuje tabeli `seen` w `youtube.db` (stan obejrzenia jest w Wicero). Przycisk ULUBIONE zostaje - dodaje film do ulubionych AP.

### 6. Powiadomienia
- Timer w głównym oknie AP (`ap.py`, istnieje przez cały czas działania) co **60 s** woła `contact_notifications` w osobnym wątku.
- Nowy film → **jedno** ogłoszenie: "<imię> przysyła nowy film." (imię zawsze w mianowniku - bez odmiany).
- Nieotwarte filmy (nigdy nie kliknięte) → przypomnienie **przy starcie AP i co godzinę**.
- Gdy kontakt jest w module Wicero (plansze, ekran przed filmem, film), nie ogłaszamy - ogłoszenie po wyjściu, w ciągu minuty. Ogłasza tylko jeden proces AP na komputerze. W pozostałych modułach (radio, muzyka, audiobook...) ogłaszamy normalnie - `milena_say` mówi przez dźwięk modułu.
- Brak internetu w tle → cisza (wpis w logu). Brak internetu po wejściu w WICERO → `milena_say` "Brak połączenia z internetem" → powrót.

### 7. Zaproszenia
Akceptowane na razie w panelu admina Wicero. W AP - później.

### 8. Środowisko pracy
Development i testy bezpośrednio na komputerze użytkownika (Ubuntu 20.04) - odtwarzanie, skanowanie i `milena_say` nie dają się sensownie testować gdzie indziej. Backend (Cloud Functions) rozwijany w repo `wicero`.

## Konsekwencje

### Pozytywne
- Kontakt korzysta z tego samego interfejsu co w reszcie AP; przetestowany odtwarzacz bez zmian.
- Brak nowych zależności na komputerach użytkowników (tylko `urllib2`, `json`, `threading`).
- Logika w jednym miejscu (chmura) - poprawki bez dostępu do komputerów, które nie są aktualizowane.
- Kolejne typy materiałów: nowy endpoint / parametr `type` + nowa plansza w AP.

### Negatywne
- Brak natychmiastowości - nowy film ogłaszany z opóźnieniem do 60 s (akceptowalne dla filmów; przy przyszłym czacie do rewizji).
- Każda zmiana UI w AP wymaga ręcznego wgrania kodu na komputery użytkowników (brak aktualizacji).
- Token w pliku na dysku - kto ma dostęp do komputera, może czytać materiały kontaktu (ten sam poziom co `.youtube_api_key`); wyciek → nowy token w panelu admina.
- Odstępstwo od ADR-0009 (custom token) - do odnotowania w repo Wicero.

## Rozważane alternatywy

### Nowa, osobna aplikacja (np. Flutter web) uruchamiana z AP
**Przeciw:** od nowa skanowanie, dźwięki, parametry, uśpienie - najdroższa i najbardziej ryzykowna część AP. **Odrzucona.**

### Lokalny kontener / serwis w Pythonie 3 (jak IoT hub)
**Za:** nowoczesny Python, możliwy nasłuch Firestore na żywo.
**Przeciw:** Docker i dodatkowy proces na każdym komputerze; zysk (natychmiastowość) zbędny dla filmów. **Odrzucona** - rolę serwisu pełnią Cloud Functions.

### Firebase custom token + Firestore REST z AP (ADR-0009)
**Przeciw:** ręczna obsługa ID tokenów i ich odświeżania w Pythonie 2.7, logika (kolejność, przypomnienia) rozproszona między AP a regułami. **Odrzucona** na rzecz tokenu w zapytaniu.

### Galeria miniatur zamiast playlisty
**Przeciw:** dużo cykli skanowania przy wielu filmach. **Odłożona.**

## Ustalenia szczegółowe i pytania otwarte
- Imię nadawcy: na razie `displayName` z rejestracji Wicero. Nazwa nadawana per połączenie ("Mama", "Ciocia Ania") - TODO w repo Wicero (`PROGRESS.md`, Faza 3).
- Plansza typów materiałów: od razu, z jednym kafelkiem FILMY.
- Ogłoszenia w trakcie innych modułów: mówimy przez nie.
- Więcej niż 5 nadawców: na razie nie występuje - stronicowanie planszy później.
- [ ] Ikona i nagranie `.ogg` dla WICERO i FILMY (na start fallback `milena_say`).

## Odnośniki
- **`WICERO_PLAN.md`** - stan implementacji, kontrakt API, lista testów
- Repo Wicero: `docs/adr/0009-*` (tokeny, Cloud Functions), `docs/adr/0010-*` (model materiałów), `docs/analiza-wysylanie-materialow.md`
- `AT_YOUTUBE_PROGRESS.md`, `modules/youtube2.py` (`PlayerFrame`, `FavouritesPlayer`)
- `IOT_INTEGRATION_PLAN.md`, `iot_client.py` (wzorzec klienta HTTP)
