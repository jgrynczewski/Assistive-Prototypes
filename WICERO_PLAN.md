# Moduł Wicero w AP - plan i stan prac

## Szybkie przywrócenie kontekstu (dla Claude bez kontekstu Wicero)

1. Przeczytaj ten plik, potem decyzję: `docs/adr/0001-modul-wicero.md`.
2. Kod w AP: `wicero_client.py` (klient HTTP), `modules/wicero.py` (UI), wpięcie w `modules/nowe.py` i `ap.py` (szukaj `wicero`).
3. Wzorce, na których moduł jest oparty: `modules/youtube_menu.py` (skanowanie plansz), `modules/youtube2.py` → `PlayerFrame` / `FavouritesPlayer` (odtwarzacz), `iot_client.py` (klient HTTP).
4. Najpierw `python2.7 test_wicero_api.py` - sprawdza połączenie z API, zanim zaczniesz debugować UI.
5. Potem moduł samodzielnie: `python2.7 modules/wicero.py` (bez `ap.py`), na końcu całe AP (`./ap.py`).
6. Logi: `wicero.log` w katalogu AP (każde zapytanie i odpowiedź API, błędy).
7. Testy T1-T13 niżej - odhaczaj `[x]` w tym pliku i dopisuj obserwacje.

### ▶ Start następnej sesji (stan 2026-10-31 wieczorem)
- **PRZEŚLIJ w odtwarzaczu** (etap 2) - zaimplementowane i wypchnięte (`c44c54a`), sekcja "PRZEŚLIJ w odtwarzaczu" niżej. Część sieciowa sprawdzona z Pythona 3; **UI jeszcze nie działa poprawnie**: przy pierwszej próbie P1 na komputerze użytkownika pojawił się błąd - szczegóły nieznane (nie zebrane).
- **Pierwszy krok:** testy P1-P5 (sekcja niżej) na komputerze użytkownika. Przy każdym błędzie zebrać: ostatnie linie terminala, w którym działa AP (traceback Pythona), oraz `tail -n 20 wicero.log`; przy którym kroku i co było widać / słychać.
- Kod do sprawdzenia przy błędzie (pisany bez wx / VLC - nigdy nie uruchomiony): `wicero.share_film` i `SendBoard` (plansza nad odtwarzaczem bez `Hide`, pauza / wznowienie VLC, `say_then`), `youtube2.PlayerFrame._buttonLabels` / `ICONS` (pasek 8 przycisków), lazy import `from modules import wicero` w `PlayerFrame._wicero`.
- Niezależnie do sprawdzenia: przycisk ULUBIONE w odtwarzaczu Wicero (test U1 - nie wykonany; ma działać jak w YouTube).

### Stan na 2026-10-31 - nowy model Wicero (ADR-0011 w repo `wicero`)
- AP jest **urządzeniem konta Wicero**: token urządzenia z aplikacji Wicero (ekran "Urządzenia" albo panel admina → użytkownik → Urządzenia). Te same kontakty i historia co w aplikacji na telefonie.
- `wicero_client.py` przeszedł na wspólne API `/api/v1/...` (stare `contact_*` usunięte). Zwraca te same pola co wcześniej - w `modules/wicero.py` zmieniło się tylko `senderId` → `conversationId`. Sprawdzone z komputera deweloperskiego (Python 3, `test_wicero_api.py`, test T20 w repo `wicero`).
- Dane w Wicero są od zera - **stary token kontaktu przestał działać**, trzeba dodać urządzenie i wpisać nowy token (sekcja "Przygotowanie").
- Test na komputerze użytkownika (T21 w repo `wicero`, testy N1-N4 niżej) **przeszedł** 2026-10-31, razem z R7 / R9.

### Stan na 2026-10-18
- Testy na komputerze użytkownika (Ubuntu 20.04) przeszły: T3-T10, T12, T13. Wnioski z T7 / T10 / T13 poprawione (serwer + `modules/wicero.py`) - **do sprawdzenia: testy R1-R5** (sekcja "Poprawki 2026-10-18" niżej).
- T1 / T2 (test API z terminala) nie były potrzebne - AP od razu działało. T11 (tracker) - pominięty, tryb nieobsługiwany.

### Stan na 2026-10-13 (koniec pracy na komputerze deweloperskim)
- **Backend gotowy, wdrożony i przetestowany** z prawdziwym tokenem (Python 3 + `wicero_client.py`): nadawcy, filmy, kolejność, teksty, ogłoszenie (raz), przypomnienie (start / co godzinę), "otwarty", "obejrzany" → nadawca widzi w aplikacji Wicero status "Obejrzany". Po stronie serwera nie powinno być nic do zrobienia.
- **Kod AP (Python 2.7 / wx 2.8) nigdy nie był uruchomiony** - ani składnia, ani UI. To jest zadanie na komputerze użytkownika: uruchomić, poprawić błędy, przejść T1-T13.
- Nieprzetestowane po stronie serwera tylko: czy ogłoszenie nowego filmu przesuwa przypomnienie o godzinę (wychodzi przy T10).

**Terminologia:** w kodzie, UI i komunikatach nie używamy słów "opiekun" ani "niepełnosprawny". Osoba korzystająca z AP to **kontakt**, osoba wysyłająca filmy - **nadawca**.

---

## Czym jest Wicero (minimum potrzebne do pracy w AP)

- System, w którym bliscy (nadawcy) wysyłają kontaktowi linki do filmów YouTube z opcjonalnym komentarzem. Repo: `github.com/jgrynczewski/wicero` (Flutter + Firebase) - **nie trzeba go mieć na tym komputerze**.
- Nadawca w aplikacji Wicero (web / Android) widzi oś czasu wysłanych filmów ze statusem "Wysłany" / "Obejrzany + data". "Obejrzany" ustawia AP (85% filmu).
- Każdy ma zwykłe konto Wicero (zakłada je sam albo admin). AP to **urządzenie** tego konta: dostaje **token urządzenia** (w aplikacji Wicero: "Urządzenia" → "Dodaj urządzenie", albo admin w panelu) - to jego jedyne "logowanie". Zaproszenia przyjmuje się w aplikacji Wicero albo admin w imieniu użytkownika (w AP - na razie nie).
- Backend: Cloud Functions w Pythonie 3.13 w chmurze Google (region `europe-central2`). **Nie działają na tym komputerze** - AP tylko wysyła do nich zapytania HTTPS. Zmiany po stronie serwera robi się w repo Wicero (`functions/`), nie tutaj.

## API (kontrakt)

Bazowy URL: `https://europe-central2-wicero-d9a70.cloudfunctions.net/api`. Każde zapytanie: nagłówek `Authorization: Bearer <token urządzenia>`. Odpowiedzi JSON UTF-8; błąd → `{"error": "..."}` + kod 400/401/403/404. 401 = zły / brak / unieważniony token; 403 = konto nieaktywne. Pełna lista tras: `functions/README.md` w repo `wicero`; AP używa tych:

| Trasa | Wejście | Wyjście (`wicero_client.py`) |
|---|---|---|
| `GET v1/conversations` | `?voice=pl` | `get_senders()`: `[{"conversationId", "name", "newCount", "say", "types": [{"type": "youtube", "label": "Filmy", "newCount", "say"}]}]` - posortowane po nazwie, także dawne kontakty (historia zostaje) |
| `GET v1/conversations/{id}/messages` | `?type=youtube&direction=in&order=playlist&voice=pl` | `get_messages()`: `[{"conversationId", "messageId", "videoId", "url", "title", "thumbnailUrl", "comment", "senderName", "status", "isNew", "say", ...}]` - tylko otrzymane; kolejność playlisty: nowe (nieotwarte) od najnowszego, potem reszta od najnowszego (status "obejrzany" nie wpływa na kolejność); max 150. `say` = tytuł + komentarz, bez imienia nadawcy |
| `POST v1/conversations/{id}/messages/{mid}/events` | `{"event": "opened" \| "viewed"}` | `{"ok": true}` |
| `POST v1/notifications` | `{"startup": bool}` | `{"say": ["Anna przysyła nowy film.", ...]}` - może być pusta; osobno dla każdego urządzenia |

- `say` - gotowe teksty dla `milena_say` (odmiana po polsku robiona na serwerze). AP ich nie składa.
- `isNew` - film nigdy nieotwarty (nie było ekranu przed filmem).
- Nowy film jest ogłaszany **raz**; przypomnienie o nieotwartych - **przy starcie AP i co godzinę** (decyduje serwer, AP pyta co minutę).

## Pliki

| Plik | Stan | Opis |
|---|---|---|
| `wicero_client.py` | ✅ nowe API (ADR-0011) przetestowane na Pythonie 3 (2026-10-31: rozmowy, filmy, ogłoszenia, przypomnienia, opened → "Wyświetlono" u nadawcy); ⏳ Python 2.7 na nowym API | Funkcje: `get_senders`, `get_messages`, `mark_opened`, `mark_viewed`, `get_notifications`. Błędy: `WiceroError.kind` = `offline` / `token` / `server`. |
| `test_wicero_api.py` | ✅ Python 3; ⏳ Python 2.7 | Diagnostyka API (patrz T1). |
| `modules/wicero.py` | ✅ działa na Ubuntu 20.04 (testy 2026-10-18); ⏳ poprawki Notifiera (R4, R5) | `Board` (plansza ze skanowaniem), `SendersBoard`, `TypesBoard`, `IntroScreen`, `WiceroPlayer`, `Notifier`, `say()`. Samodzielnie: `python2.7 modules/wicero.py` (rodzic `_Standalone` zamiast `nowe.py`; powrót z planszy nadawców kończy program). |
| `modules/nowe.py` | ✅ | Slot 3: `PUSTE` → `WICERO` (import, etykieta, ikona, `onPress`, dźwięk przy skanowaniu przez `milena_say`). |
| `ap.py` | ✅ | Import `wicero` + `self.wiceroNotifier = wicero.Notifier( )` w `initializeTimer`. |
| `icons/modules/wicero.png` | ✅ | Logo Wicero (dwa "V" tworzące "W" - Vincentius / Wincenty) na białym zaokrąglonym kwadracie, 200×200 RGBA. Białe tło celowo: przy skanowaniu kafelek dostaje `scanningColour` (#0033FF), na którym niebieskie logo by znikło. Źródło: repo `wicero`, `assets/logo/wicero.svg` + `tools/generate_icons.py`. |
| `.wicero_token` | do utworzenia | Token urządzenia z aplikacji Wicero ("Urządzenia") albo z panelu admina, jedna linia. W `.gitignore`. |
| `wicero.log` | tworzony automatycznie | Własny handler loggera `wicero` (nie `basicConfig` - ten zajmuje już `iot_client.py`). Każda linia z PID procesu (`[1234]`) - widać, gdy działa kilka procesów AP. |
| `/tmp/ap_wicero_notifier.lock` | tworzony automatycznie | Blokada: tylko jeden proces AP ogłasza; w środku PID tego procesu. |

Kod UI powstał bez możliwości uruchomienia (Windows, bez wx 2.8 / VLC / milena), ale na Ubuntu zadziałał bez poprawek składni - błędy wyszły tylko w logice Notifiera (T10).

### Świadome odstępstwa od wzorców
- `Board.onPress` (kolumny): stan skanowania (`flag`, `rowIteration`, ...) jest resetowany **przed** wykonaniem akcji, nie po - akcja może zamknąć okno (`Destroy`). Poza tym logika identyczna z `youtube_menu.py`.
- `Board.OnCloseWindow`: zamknięcie okna = powrót, bez okna dialogowego "Czy na pewno...".
- `IntroScreen` ma 1 wiersz × 3 kolumny, ale używa skanowania wiersze → kolumny z `Board` (czyli najpierw podświetla cały wiersz). Jeśli to przeszkadza - przejść na wzorzec "tylko kolumny" z `PlayerFrame` (youtube2.py).
- `WiceroPlayer` odtwarza **jeden** film; NASTĘPNY / POPRZEDNI / koniec filmu zamykają odtwarzacz i `IntroScreen.moveBy(±1)` pokazuje ekran kolejnego filmu (każdy film ma swój komentarz).

## Jak działa kod UI (`modules/wicero.py`)

```
nowe.py onPress('WICERO') -> stoper.Stop() -> open_wicero(nowe)
  open_wicero: get_senders() w wątku -> SendersBoard (nowe.Hide())
                                    \-> błąd: say_error() + wznowienie skanowania nowe
SendersBoard.onSelect -> TypesBoard(sender)            (typy z odpowiedzi senders)
TypesBoard.onSelect   -> get_messages() w wątku -> IntroScreen(items)
IntroScreen.showCurrent: tytuł/komentarz/miniatura, mark_opened (jeśli isNew),
                         _sayThenScan: milena czyta 'say' (wątek, wait) -> dopiero potem skanowanie
  (columnsOnly: jeden wiersz, skanowanie od razu po przyciskach, po 2 przejściach uśpienie)
  POWTORZ -> czyta ponownie;  START -> WiceroPlayer(item);  NASTEPNY / POPRZEDNI -> moveBy(+1 / -1)
  POWROT -> TypesBoard
WiceroPlayer: timer 1 s, przy 85% mark_viewed (raz)
  NASTEPNY / koniec filmu -> _leave(+1): _onExit() + CallAfter(IntroScreen.moveBy(+1))
  POPRZEDNI -> _leave(-1);  EXIT pilota -> zwykłe _onExit() -> IntroScreen
  moveBy za ostatnim filmem -> "To już wszystkie filmy." -> IntroScreen.onExit() -> TypesBoard
Notifier (ap.py, cały czas, jeden na komputer - blokada w /tmp): 15 s po starcie
  (startup=True), potem co 60 s; pomija takt, gdy poprzednie czytanie trwa (busy)
  lub moduł Wicero jest otwarty (ACTIVE: od SendersBoard do wyjścia z niego).
  Teksty pobrane tuż przed wejściem do Wicero -> self.pending -> czytane po wyjściu.
```

- Każde okno: `Board.onExit()` = `parent.Show(True)` + wznowienie `parent.stoper` + `Destroy()` (jak w `youtube_menu.py`).
- Zapytania HTTP zawsze w wątku (`run_in_thread`), wynik do GUI przez `wx.CallAfter` - GUI nie zamarza przy wolnym internecie (timeout 20 s).
- `say(text, wait)` = `milena_say` z tekstem jako osobnymi słowami, bez powłoki (jak `iot.py`, ale bezpiecznie dla komentarzy z `;`, `"`, `$`).

### Zależności od wnętrza `youtube2.PlayerFrame`
`WiceroPlayer` nadpisuje / używa: `__init__(parent, query)`, `_cacheFile`, `_loadPlaylist`, `_startPlay(url, video_url)`, `_playCurrent`, `_next`, `_prev`, `_onExit`, pól `playlist`, `playlist_meta`, `_length_ms`, `player`, `vlc_instance`, `vlcPanel`. Zmiana tych nazw w `youtube2.py` psuje Wicero. Koniec filmu: `_onEndReached` → `_next` (przy błędzie VLC `_onVlcError` → `_next` - też przejście do następnego filmu).

### Znane ryzyka (sprawdź najpierw, jeśli coś nie działa)
| Ryzyko | Objaw | Co zrobić |
|---|---|---|
| SSL / certyfikaty Pythona 2.7 na Ubuntu 20.04 bez aktualizacji | `offline` + `SSL` / `CERTIFICATE_VERIFY_FAILED` w `wicero.log` | `python2.7 -c "import ssl; print ssl.OPENSSL_VERSION"`; YouTube Data API w AP działa przez HTTPS, więc raczej OK |
| `milena_say` z wieloma argumentami | cisza lub czyta tylko pierwsze słowo | sprawdzić `milena_say Ala ma kota` w terminalu; ew. zmienić `say()` na `' '.join` w jednym argumencie |
| `say(wait=True)` | skanowanie nie rusza po tekście (milena_say nie kończy się) | sprawdzić, czy `milena_say` wraca po przeczytaniu; `stdin=PIPE` jak w `iot.py` |
| wx 2.8: `StaticText.Wrap`, `ImageFromStream` (JPEG z YouTube), `Timer.Start(ms, oneShot=True)` | wyjątek przy IntroScreen / Notifier | odpowiedniki z wx 2.8 (`wx.Timer.Start(ms, True)`, `wx.ImageFromStream(stream, wx.BITMAP_TYPE_JPEG)`) |
| Układ IntroScreen | miniatura/tekst ucięte, przyciski za małe | proporcje w `createTop` (`proportion=3` góra / 1 przyciski), rozmiar miniatury 35% wysokości ekranu |
| `if not self` po `Destroy()` | `PyDeadObjectError` | w wx 2.8 martwy obiekt jest fałszywy - powinno działać; w razie czego flaga `self._closed` |
| Skanowanie 1x3 w IntroScreen (wiersz → kolumny) | jedno zbędne naciśnięcie | patrz "Świadome odstępstwa" |

## Backend (repo `wicero`) - gdyby trzeba było coś sprawdzić lub zmienić

- Kod: `github.com/jgrynczewski/wicero`, katalog `functions/` (`wicero_api.py` - trasy, `core.py` - reguły, `voice.py` - teksty do czytania, `tests/` - testy `python -m unittest discover -s tests`; w starszych notatkach niżej `contact_api.py` = dzisiejsze `core.py` + `voice.py`). Deploy: `firebase deploy --only functions` (Firebase CLI, konto właściciela projektu) - **zwykle robiony z komputera deweloperskiego**, nie z komputera użytkownika. Opisz potrzebną zmianę w notatce, jeśli nie masz tu repo / CLI.
- Firebase Console projektu `wicero-d9a70` → Firestore - podgląd i ręczna edycja danych.

### Model danych Firestore (to, czego dotyczy AP)
| Ścieżka | Pola istotne dla AP |
|---|---|
Szczegóły: ADR-0011 w repo `wicero`. Najważniejsze dla AP:

| Ścieżka | Pola istotne dla AP |
|---|---|
| `users/{uid}` | `displayName`, `status` (`active` / `inactive`) - profil konta; nazwa widoczna dla kontaktów |
| `users/{uid}/devices/{deviceId}` | `tokenHash` (w bazie tylko skrót tokenu z `.wicero_token`), `announcedUpTo` (do kiedy ogłoszono nowe filmy), `lastReminderAt`, `revokedAt` |
| `users/{uid}/inbox/{messageId}` | `conversationId`, `senderId`, `type`, `createdAt`, **`openedAt`** (null = nowy, nieotwarty), `viewedAt` |
| `connections/{uidA}_{uidB}` | `members`, `status` (`accepted` = kontakt) |
| `conversations/{id}/messages/{messageId}` | `senderId`, `type: "youtube"`, `content` (`videoId`, `url`, `title`), `comment`, `receipts.{uid}` (`openedAt`, `viewedAt`, `by`) |

### Reset stanu do ponownych testów
- Najprościej: nadawca wysyła nowy film w aplikacji Wicero (web / Android) - jest od razu nowy, nieotwarty i do ogłoszenia.
- Ogłoszenia są osobne dla każdego urządzenia: nowe urządzenie (nowy token) zaczyna od zera.

### Dane testowe (stan 2026-10-31)
Konta testowe Test Anna (admin), Test Bartek, Test Celina, Test Dorota, Test Ewa - z aplikacji Wicero (repo `wicero`, `docs/testy-adr-0011.md`). Test Bartek ma filmy od Test Anna. Tokeny urządzeń - od właściciela projektu (nie są w repo).

## Przygotowanie (na komputerze użytkownika)

1. `git pull` na gałęzi `user/radek/master`.
2. Token: aplikacja Wicero (konto osoby korzystającej z AP) → "Urządzenia" → "Dodaj urządzenie" (albo panel admina → użytkownik → Urządzenia) → skopiować token i zapisać jako jedyną linię `.wicero_token` w katalogu AP. Token jest pokazywany tylko raz.
3. W Wicero: konto musi mieć kontakt (przyjęte zaproszenie) z kontem nadawcy, a nadawca wysłać mu 1-2 filmy.
4. `milena_say` i `yt-dlp` - te same co dla YouTube (`AT_YOUTUBE_PLAN.md`). Zamiana milena_say na Piper TTS (lepszy głos): `SYNTEZATOR.md`.

## Testy (do przejścia po kolei)

- [ ] **T1 - API z Pythona 2.7:** `python2.7 test_wicero_api.py` → wersja Pythona/OpenSSL, nadawcy, filmy z `say`. Ryzyko: stare certyfikaty / OpenSSL Ubuntu 20.04 bez aktualizacji (wtedy błąd `offline` z `SSL` w `wicero.log`). API YouTube działa, więc raczej OK.
- [ ] **T2 - ogłoszenia z terminala:** `python2.7 test_wicero_api.py --notifications` → "X przysyła nowy film." (drugie uruchomienie: bez ogłoszenia, ale z przypomnieniem - `startup=True`).
- [x] **T3 - start AP:** `./ap.py` uruchamia się (import `wicero`, ikona). Po ~15 s - przypomnienie o nieotwartych filmach (`milena_say`).
- [x] **T4 - kafelek WICERO** w NOWE: czytany przy skanowaniu, wybór → plansza nadawców. Bez internetu → "Brak połączenia z internetem", powrót do skanowania NOWE.
- [x] **T5 - plansza nadawców:** imiona na kafelkach (czcionka `tableFontSize`), przy skanowaniu czytane z liczbą nowych ("Anna, 2 nowe filmy"), POWRÓT działa, uśpienie po 3 pustych cyklach.
- [x] **T6 - plansza typów:** FILMY + POWRÓT.
- [x] **T7 - ekran przed filmem:** miniatura, tytuł, komentarz; najpierw czytanie, potem skanowanie (głosy się nie nakładają); POWTÓRZ czyta ponownie. W aplikacji Wicero (oś czasu nadawcy) nic się nie zmienia - `openedAt` jest tylko w bazie; kolejne wejście w WICERO pokazuje mniejsze `newCount`.
  - **Obserwacja 1:** nowo wysłany film pojawia się jako ostatni wśród nieobejrzanych - poprawne (serwer sortuje nieotwarte od najstarszego), ale może zaskakiwać. Rozważyć zmianę kolejności po stronie serwera.
  - **Obserwacja 2:** na każdym ekranie przed filmem Piper czyta "jan kowalski przysyła film..." - po pierwszym razie zbędne, wystarczyłby sam tytuł + komentarz. Do zmiany w `contact_api.py` po stronie serwera (pole `say` dla kolejnych filmów bez imienia nadawcy).
  - **Obserwacja 3 / BUG UX:** gdy film ma komentarz, pole `say` zawiera tylko komentarz - tytuł nie jest czytany. Do sprawdzenia/zmiany w `contact_api.py` po stronie serwera.
  - **Obserwacja 4 / BUG UX - kolejność filmów:** filmy `sent` (w tym CLANNAD 3h) zawsze na początku kolejki, bo warunek `viewed` = 85% nigdy nie zostaje spełniony dla długich filmów. Propozycja: po `mark_opened` (pierwsze wejście na IntroScreen) film trafia do "zwykłej kolejki" (obejrzanych), niezależnie od 85%. Warunek 85% zostawić tylko do ustawienia statusu `viewed` u nadawcy. Zmiana po stronie serwera (`contact_messages` - kolejność i logika `isNew`).
  - **→ Poprawione 2026-10-18 po stronie serwera:** obserwacje 2 i 3 - `say` = "tytuł. komentarz" (bez imienia); obserwacje 1 i 4 - kolejność: nowe (nieotwarte) od najnowszego, potem reszta od najnowszego, 85% nie ma wpływu na kolejność. Sprawdzić: R1, R2.
- [x] **T8 - odtwarzanie:** START → film; pilot jak w YouTube; po 85% - w aplikacji Wicero status "Obejrzany" z datą (na żywo).
- [x] **T9 - nawigacja w filmach:** NASTĘPNY / koniec filmu → ekran następnego filmu; po ostatnim: "To już wszystkie filmy." i powrót do planszy typów; POPRZEDNI na pierwszym filmie - ten sam film.
- [x] **T10 - ogłoszenie w tle:**
  - **BUG 1:** ogłoszenie przychodzi podczas odtwarzania w WiceroPlayer mimo flagi `PLAYING`. Prawdopodobna przyczyna: race condition - wątek Notifiera startuje tuż przed ustawieniem `PLAYING=True`, sprawdzenie flagi jest na początku `_tick`, ale wątek już działa. Do naprawy w `wicero.py`: sprawdzać `PLAYING` też wewnątrz wątku workera przed każdym `say()`.
  - **BUG 2:** Notifier odpytuje dwa razy na ~60s (log pokazuje naprzemiennie ~37s i ~23s). Prawdopodobnie `wicero.Notifier()` tworzony dwa razy. Sprawdzić `ap.py`.
  - **Do obserwacji (z planu):** nakładanie głosów na IntroScreen (PLAYING obejmuje tylko WiceroPlayer) - potwierdzone jako problem w praktyce.
  - **→ Poprawione 2026-10-18 (`modules/wicero.py`):** BUG 1 + IntroScreen - flaga `PLAYING` zastąpiona `ACTIVE` (cały moduł Wicero, od planszy nadawców do wyjścia); worker sprawdza `ACTIVE` przed każdym tekstem, a niewypowiedziane teksty trzyma w `pending` (serwer już je oznaczył jako ogłoszone - bez tego by zginęły). BUG 2 - w kodzie `Notifier` jest tworzony raz; odstępy ~37 s / ~23 s = dwa procesy AP (np. proces pozostały po zamknięciu AP z ukrytym oknem). Teraz blokada `/tmp/ap_wicero_notifier.lock` (ogłasza tylko jeden proces) + PID w `wicero.log`. Sprawdzić: R4, R5.
  - **R4 NIE PRZESZŁO (2026-10-18) - prawdziwa przyczyna (z logów):** użytkownik miał dwa procesy AP. Notifier (PID 22265) ma własną zmienną `ACTIVE`; użytkownik wszedł do Wicero w PID 23145 - ale PID 22265 nic o tym nie wie, jego `ACTIVE` zostało False i ogłosił. `ACTIVE` jako zmienna per-proces nie wystarczy przy wielu procesach AP.
    **Poprawka:** zastąpić `ACTIVE` plikiem na dysku `/tmp/ap_wicero_active` (analogicznie do lock). `open_wicero()` tworzy plik (touch), `SendersBoard.onExit()` usuwa. Notifier sprawdza `os.path.exists(ACTIVE_FILE)`. Działa między procesami. Przy crashu plik zostaje - `open_wicero()` powinno go zawsze tworzyć na nowo, a przy starcie AP czyścić (lub sprawdzać przez lock czy jakiś proces go trzyma).
- [x] **T13 - wiele filmów przy wyłączonym komputerze:** AP wyłączone, nadawca wysyła kilka filmów → start AP → po ~15 s **jeden** komunikat na nadawcę ("X przysyła 5 nowych filmów."), nie osobny na każdy film. Jeśli u tego nadawcy były wcześniej ogłoszone, ale nieotwarte filmy, padnie też przypomnienie o nich ("Czekają nowe filmy. X: 2 nowe filmy.") - poprawne, ale może mylić; ewentualna zmiana po stronie serwera (`contact_notifications` w repo `wicero`): przy starcie jedno zdanie z łączną liczbą.
  - **→ Poprawione 2026-10-18 po stronie serwera:** gdy nadawca ma właśnie ogłoszony nowy film, w tym samym wywołaniu nie ma już przypomnienia o jego starszych nieotwartych filmach. Sprawdzić: R3.
- [~] **T11 - tryb tracker** (`control=tracker` w `parameters`) - wybór kafelków bez skanowania. **Pominięty - tryb nieobsługiwany.** Ostatnio używany ok. 10 lat temu, w znacznie starszych modułach; gałęzie `control == 'tracker'` w obecnych modułach (`youtube_menu.py`, `youtube2.py`, a za nimi `wicero.py`) to pozostałość po kopiowaniu kodu, nigdy z nimi nietestowana. Obecnie nie ma potrzeby go wspierać - nie testować, nie naprawiać, nie dopisywać do nowego kodu. Jeśli kiedyś wróci, to jako osobne zadanie dla całego AP. Jedyny test trybu tracker w tym planie.
- [x] **T12 - zły token** w `.wicero_token` → wejście w WICERO: "Wicero nie jest skonfigurowane..."; w tle cisza (tylko log).

## Poprawki 2026-10-18 - testy do powtórzenia

Serwer wdrożony 2026-10-18 (repo `wicero`, commit `d6063d9`; sprawdzone `test_wicero_api.py`: kolejność i teksty po nowemu) - R1-R3 działają od razu. AP (R4, R5): `git pull`. Przed testami zamknij AP i sprawdź `ps aux | grep ap.py` - nie powinien zostać żaden proces.

- [x] **R1 - tekst przed filmem:** film z komentarzem → czytane "Tytuł. Komentarz"; bez komentarza → sam tytuł; nigdzie "jan kowalski przysyła film".
  - **Do oceny przy R1:** tytuły z YouTube mają hashtagi, nazwy kanałów i emoji ("... #heroes3 #games #gaming #shorts", "@BEZRETUSZU-polska", "❤️🐶 #usa"). Posłuchać, jak syntezator je czyta. Jeśli przeszkadza - poprawka po stronie serwera (`contact_api.intro_text`: usuwać `#słowa`, `@nazwy` i emoji z tekstu do czytania; tytuł na ekranie bez zmian).
    **→ Decyzja: usuwamy.** Zrobione po stronie serwera (`contact_api.spoken`, repo `wicero`) - usuwane `#słowa`, `@nazwy` i emoji, także z komentarza; tytuł na ekranie bez zmian. Sprawdzić: R8.
  - **UX 1 - przyciski nawigacji w IntroScreen:** dodać NASTĘPNY i POPRZEDNI, żeby przejść do kolejnego/poprzedniego filmu bez uruchamiania aktualnego. Obecne 3 przyciski (POWTÓRZ, START, POWRÓT) → 5; proponowany układ 2×3: [POPRZEDNI | START | NASTĘPNY] / [POWTÓRZ | PUSTE | POWRÓT]. Zmiana tylko w `IntroScreen.__init__` i `onSelect` - bez wpływu na logikę kolejkowania.
    **→ Zrobione (decyzja: jeden wiersz, kolejność POWTÓRZ / START / NASTĘPNY / POPRZEDNI / POWRÓT** - układ 2×3 wykluczał UX 3). NASTĘPNY na ostatnim filmie → "To już wszystkie filmy." i powrót (jak w odtwarzaczu); POPRZEDNI na pierwszym → ten sam film od nowa. Uwaga: przeskoczony nowy film jest już "otwarty", więc przy kolejnym wejściu nie jest na początku listy. Sprawdzić: R6.
  - **UX 2 - ikony przycisków IntroScreen:** START → ikona play (jak w odtwarzaczu); POWTÓRZ → ikona powtórz (jeśli jest w zasobach AP). Sprawdzić `icons/pilots/`.
    **→ Zrobione:** POWTÓRZ `musicPilot/10_repeat.png` (`minitubePilot/10_undo.png` to strzałka jak POWRÓT - myliłaby się), START `minitubePilot/12_play.png`, NASTĘPNY / POPRZEDNI `minitubePilot/4_next.png` / `3_previous.png`. Przy skanowaniu głosowym czytane nazwy.
  - **UX 3 - skanowanie IntroScreen:** jeden wiersz, więc skanowanie od całego wiersza jest zbędne. Powinno startować bezpośrednio od kolumn (jak pilot odtwarzacza), ale automatycznie (nie na klik - film jeszcze nie gra). Zmiana w `IntroScreen` lub nowy wzorzec skanowania.
    **→ Zrobione:** `Board.columnsOnly` (w `IntroScreen` = True) - po przeczytaniu tekstu skanowanie od razu po przyciskach; po dwóch przejściach uśpienie, naciśnięcie budzi od pierwszego przycisku. Pozostałe plansze bez zmian. Sprawdzić: R6.
- [x] **R2 - kolejność:** nadawca wysyła nowy film → po wejściu w FILMY jest **pierwszy**. Film otwarty (ekran przed filmem), ale nieobejrzany do 85% (np. długi CLANNAD) → przy kolejnym wejściu **nie** jest już na początku, tylko wśród reszty (od najnowszego).
- [x] **R3 - jeden komunikat na nadawcę:** jak T13, ale gdy u nadawcy były wcześniej ogłoszone nieotwarte filmy → tylko "X przysyła N nowych filmów.", bez "Czekają nowe filmy. X: ...".
- [~] **R4 - cisza w Wicero:** wejść w WICERO (dowolna plansza, ekran przed filmem, film) → nadawca wysyła film → **brak** ogłoszenia, dopóki kontakt jest w Wicero. Po wyjściu z planszy nadawców → ogłoszenie w ciągu ~1 min. Wariant: nadawca wysyła film na kilka sekund przed wejściem w WICERO → ogłoszenie nie pada w środku modułu, tylko po wyjściu (`pending`).
  - **Wniosek z `ps aux` (2026-10-18):** AP przy normalnym zamknięciu sprząta po sobie (nowo otwarty PID znika po zamknięciu). Stare procesy w logu R4 to pozostałości z poprzednich sesji testowych (otwarte terminale). W produkcji (autostart, wyłączanie komputera) nigdy nie będą dwa procesy AP jednocześnie. Plik-based `ACTIVE_FILE` rozwiązałby krawędziowy przypadek - ale nie jest krytyczny. Osobna naprawa: zombie `[milena_say]` (patrz niżej).
  - **BUG 3 - zombie milena_say:** `say(wait=False)` tworzy subprocess ale nigdy nie woła `p.wait()`. Skończony proces basha czeka jako zombie do zamknięcia ap.py. Naprawa w `say()`: dodać wątek daemon `threading.Thread(target=p.wait)` dla `wait=False`. Trzy linijki.
    **→ Zrobione.** (Python 2.7 i tak sprząta zakończone procesy przy następnym `Popen`, więc zombie się nie mnożyły - to porządek, nie wyciek.) Sprawdzić: R7.
- [x] **R5 - jeden Notifier:** uruchomić AP dwa razy (dwa terminale) → w `wicero.log` zapytania `contact_notifications` tylko z jednego PID, co ~60 s; w logu drugiego procesu "Notifier wylaczony - oglasza juz inny proces AP (PID ...)". Jeśli w normalnym użyciu (jedno AP) ten wpis się pojawia - został proces po poprzednim uruchomieniu: `ps aux | grep ap.py`, ustalić, przy jakim zamknięciu AP zostaje.

## Poprawki 2026-10-18 (2) - testy do powtórzenia

Serwer (R8): do wdrożenia z repo `wicero` (`firebase deploy --only functions`). AP (R6, R7): `git pull`. Jak poprzednio: przed testami zamknąć AP i sprawdzić `ps aux | grep ap.py`.

- [x] **R6 - ekran przed filmem:** jeden wiersz z ikonami POWTÓRZ / START / NASTĘPNY / POPRZEDNI / POWRÓT. Po przeczytaniu tekstu skanowanie od razu po przyciskach (bez podświetlania całego wiersza). Po dwóch przejściach bez wyboru - uśpienie; naciśnięcie budzi od POWTÓRZ. NASTĘPNY → następny film (tekst, miniatura); na ostatnim → "To już wszystkie filmy." i powrót do FILMY. POPRZEDNI na pierwszym → ten sam film od nowa. Naciśnięcie zaraz po przeczytaniu tekstu, zanim coś się podświetli - nic się nie dzieje (bez błędu).
- [x] **R7 - R4 przy jednym AP:** jeden proces AP (`ps aux | grep ap.py` - jedna linia) → scenariusz R4 razem z wariantem `pending`. Przy okazji: po kilku komunikatach `ps aux | grep milena` - brak `<defunct>`. *(zrobiony 2026-10-31 jako N4)*
- [x] **R8 - tekst bez hashtagów:** film z tytułem z `#...`, `@...` i emoji → czytany sam tytuł, bez nich; na ekranie tytuł oryginalny. Tytuł złożony z samych hashtagów → czytany komentarz albo "Film".

## Testy na nowym API (2026-10-31, T21 w repo `wicero`)

Przygotowanie:
1. Zamknąć AP (`ps aux | grep ap.py` - pusto), `git pull` na `user/radek/master`.
2. Nadawca w aplikacji Wicero (web) zalogowany jako **Test Anna**. Panel admina (Test Anna) → Test Bartek → Urządzenia → "Dodaj urządzenie" `AP - komputer użytkownika` → token jako jedyna linia `.wicero_token` (stary token przestał działać).
3. Test Anna wysyła Test Bartkowi 2 filmy: jeden **z komentarzem**, jeden **bez**.

- [x] **N1 - API z Pythona 2.7:** `python2.7 test_wicero_api.py` → rozmowy Test Bartka (Test Anna z liczbą nowych, Test Celina), filmy od Test Anna z `say`. Błąd `offline` z `SSL` w `wicero.log` → zatrzymać się i zgłosić (stare OpenSSL w Pythonie 2.7).
- [x] **N2 - przegląd filmów (+R9):** uruchomić AP → WICERO → kafel czytany "Test Anna, N nowych filmów" (N - liczba nieotwartych) → FILMY → ekran przed filmem. Film z komentarzem czytany "Tytuł. Komentarz: treść." (obie części wyraźnie rozdzielone), bez komentarza - sam tytuł. W aplikacji u Test Anna oba filmy: "Wyświetlono".
- [x] **N3 - obejrzany:** START na jednym filmie, obejrzeć ponad 85% (krótki film) → u Test Anna "Obejrzano". Na planszy nadawców po powrocie - kafel bez "nowych".
- [x] **N4 - ogłoszenia (R7):** jeden proces AP (`ps aux | grep ap.py` - jedna linia), AP na ekranie głównym. Test Anna wysyła film → w ciągu ~1 min "Test Anna przysyła nowy film." - **raz**. Potem: wejść w WICERO i zostać na planszy, Test Anna wysyła kolejny film → **cisza**, dopóki jesteś w module; po wyjściu z planszy nadawców → ogłoszenie w ciągu ~1 min. Na koniec `ps aux | grep milena` - brak `<defunct>`.

**Wynik 2026-10-31: N1-N4 przeszły** (R7 i R9 w ramach N4 / N2). Przy N3: kafle po powrocie czytały stare liczby nowych filmów - poprawione (`5937e2a`, odświeżanie w tle przy powrocie na planszę nadawców / FILMY), sprawdzone.

Problem → zapisać obserwację tutaj + fragment `wicero.log`.

## PRZEŚLIJ w odtwarzaczu (2026-10-31, etap 2 ADR-0011)

Przycisk **PRZEŚLIJ** (niebieska strzałka, `icons/pilots/minitubePilot/13_share.png`) w odtwarzaczu `youtube2.PlayerFrame` - czyli w YouTube (WYSZUKAJ, ULUBIONE) i w Wicero. LOSOWE (`at_youtube.py`, osobny kod) - bez zmian.

- Miejsce: za ULUBIONE (w ulubionych za USUŃ). Tylko gdy jest plik `.wicero_token` - bez niego pasek jak dawniej (7 przycisków).
- Wybór → film pauzuje → plansza kontaktów (nazwy, max 5 + POWRÓT; stronicowanie później) → wybór kontaktu = wysłanie od razu → "Film przesłany: <nazwa>." → powrót do filmu, gra dalej. POWRÓT na planszy → film gra dalej, nic nie wysłane.
- Na planszy tylko aktualne kontakty z aktywnym kontem (`canSend`). W Wicero bez osoby, od której film przyszedł.
- Z YouTube - nowy film (link). Z Wicero - **przekazanie dalej** (u odbiorcy "przekazany", bez pochodzenia).
- Komunikaty: brak kontaktów → "Nie masz komu przesłać tego filmu."; brak pliku tokenu → "Wicero nie jest skonfigurowane."; token odrzucony → "Nieprawidłowy token Wicero." (także przy kafelku WICERO); brak sieci → "Brak połączenia z internetem."
- Komentarz: `wicero_client.send_film(..., comment=None)` - API go przyjmuje, AP na razie nie ma jak go wpisać.
- Kod: `wicero_client.get_recipients` / `send_film`, `wicero.share_film` + `SendBoard`, `youtube2.PlayerFrame._share` / `_shareable` (`WiceroPlayer._shareable` - przekazanie). Przyciski i ikony odtwarzacza: `PlayerFrame.LABELS` / `ICONS` (wcześniej listy po indeksie; `FavouritesPlayer` podmieniał przyciski po zbudowaniu paska).
- Sprawdzone z komputera deweloperskiego (Python 3): lista adresatów, przekazanie, wysłanie linku. UI - do sprawdzenia tutaj.

Przygotowanie: `git pull`, zamknąć AP. Test Bartek ma teraz w kontaktach tylko Test Anna - do P3 potrzebny drugi kontakt: Test Celina zaprasza Test Bartka w aplikacji, Test Bartek przyjmuje (w aplikacji albo admin w panelu).

- [ ] **U1 - ULUBIONE w Wicero:** WICERO → film → START → ULUBIONE (2. przycisk) → wyjść; YOUTUBE → ULUBIONE → film z Wicero na liście, da się odtworzyć.
- [ ] **P1 - YouTube:** *(2026-10-31: pierwsza próba - błąd, szczegóły nieznane)* YOUTUBE → WYSZUKAJ → dowolny film → na pasku 8 przycisków, PRZEŚLIJ za ULUBIONE, przy skanowaniu "Prześlij". Wybór → film staje, plansza z Test Anna (i Test Celina po przygotowaniu) → Test Anna → "Film przesłany: Test Anna." → film gra dalej od tego miejsca. W aplikacji u Test Anna nowy film od Test Bartek.
- [ ] **P2 - POWRÓT:** PRZEŚLIJ → na planszy POWRÓT → film gra dalej, nic nie wysłane.
- [ ] **P3 - Wicero:** WICERO → Test Anna → FILMY → START → PRZEŚLIJ → na planszy **tylko Test Celina** (bez Test Anna - to jej film) → wybór → "Film przesłany: Test Celina." U Test Celina film "przekazany". (Bez drugiego kontaktu: "Nie masz komu przesłać tego filmu." i film gra dalej.)
- [ ] **P4 - ulubione:** YOUTUBE → ULUBIONE → PRZEŚLIJ za USUŃ, działa jak w P1; USUŃ dalej usuwa z ulubionych.
- [ ] **P5 - bez Wicero:** zmienić nazwę `.wicero_token` (np. na `.wicero_token.off`) → YOUTUBE → film: pasek 7 przycisków jak dawniej; kafelek WICERO → "Wicero nie jest skonfigurowane.". Przywrócić nazwę, wpisać do pliku coś błędnego → PRZEŚLIJ → "Nieprawidłowy token Wicero." i film gra dalej. Na koniec przywrócić prawidłowy token.

## UX - do analizy i wdrożenia

### Rozdzielenie tytułu od komentarza przy czytaniu
Aktualnie pole `say` zawiera "Tytuł. Komentarz." - tytuł i komentarz się zlewają w mowie. Propozycja: wyraźne rozdzielenie przez zapowiedź słowną, np. "Tytuł: ... Komentarz od Jan Kowalski: ...". Zmiana po stronie serwera (`contact_api`, pole `say` / `spoken`).

Warianty do rozważenia:
- **Zapowiedź obu części:** "Tytuł: X. Komentarz od Jana: Y." - pełna informacja, dłuższe
- **Tylko zapowiedź komentarza:** "X. Komentarz: Y." - krótsze, tytuł bez etykiety (jest oczywisty)
- **Przerwa interpunkcyjna:** "X... Y." - wielokropek wydłuża pauzę w Piperze; bez dodatkowych słów

Decyzja wymaga posłuchania jak Piper czyta każdy wariant z prawdziwym tekstem.

**→ Decyzja 2026-10-19: tylko zapowiedź komentarza** - "Tytuł. Komentarz: treść." (`contact_api.intro_text`, repo `wicero`). Bez imienia nadawcy (wymagałoby odmiany - imiona są dowolne, teksty używają tylko mianownika; kontakt właśnie wybrał nadawcę). Bez wielokropka (pauza zależy od syntezatora). Sam komentarz bez tytułu - czytany bez etykiety. Sprawdzić: R9.

- [x] **R9 - tytuł i komentarz:** film z komentarzem → "Tytuł. Komentarz: treść." - obie części wyraźnie rozdzielone; film bez komentarza → sam tytuł. Serwer: `firebase deploy --only functions`; AP bez zmian.

## Do zrobienia później
- **Nowy model Wicero (repo `wicero`, ADR-0011 "Równoważni użytkownicy", 2026-10-19):** jedno konto dla każdego interfejsu, AP jako "urządzenie" konta (token z aplikacji Wicero), wspólne API `api` zamiast `contact_*`. Etap 1 zrobiony 2026-10-31: `wicero_client.py` na nowym API, ADR-0001 zaktualizowany. W etapie 2 wysyłanie z AP ("Prześlij" w odtwarzaczu).
- **Z tyłu głowy:** jeśli Wicero się przyjmie, część AP korzystająca z Wicero (`ap.py` i moduły) zostanie prawdopodobnie przepisana na nową bibliotekę, łatwą do zainstalowania na różnych systemach. Dlatego w obecnym AP nie inwestujemy w nic poza cienkim klientem API - logika zostaje w Wicero (ADR-0011, Notatki).
- Nagrania `.ogg` dla WICERO / FILMY / POWTÓRZ / START (teraz `milena_say`).
- Stronicowanie planszy nadawców (> 5).
- Zdjęcia nadawców na kafelkach - Wicero już je ma (`photoURL` w profilu, API zwraca je w `members`), w AP do zrobienia. Własne nazwy kontaktów ("Mama") już działają - AP dostaje je w `name`.
- Przyjmowanie zaproszeń w AP (teraz aplikacja Wicero na tym samym koncie albo admin w imieniu użytkownika).
- Kolejne typy materiałów: serwer zwróci je w `types`, w AP - nowe kafelki na planszy typów i własne ekrany.
