# Moduł Wicero w AP - plan i stan prac

## Szybkie przywrócenie kontekstu (dla Claude bez kontekstu Wicero)

1. Przeczytaj ten plik, potem decyzję: `docs/adr/0001-modul-wicero.md`.
2. Kod w AP: `wicero_client.py` (klient HTTP), `modules/wicero.py` (UI), wpięcie w `modules/nowe.py` i `ap.py` (szukaj `wicero`).
3. Wzorce, na których moduł jest oparty: `modules/youtube_menu.py` (skanowanie plansz), `modules/youtube2.py` → `PlayerFrame` / `FavouritesPlayer` (odtwarzacz), `iot_client.py` (klient HTTP).
4. Najpierw `python2.7 test_wicero_api.py` - sprawdza połączenie z API, zanim zaczniesz debugować UI.
5. Potem moduł samodzielnie: `python2.7 modules/wicero.py` (bez `ap.py`), na końcu całe AP (`./ap.py`).
6. Logi: `wicero.log` w katalogu AP (każde zapytanie i odpowiedź API, błędy).
7. Testy T1-T13 niżej - odhaczaj `[x]` w tym pliku i dopisuj obserwacje.

### Stan na 2026-10-13 (koniec pracy na komputerze deweloperskim)
- **Backend gotowy, wdrożony i przetestowany** z prawdziwym tokenem (Python 3 + `wicero_client.py`): nadawcy, filmy, kolejność, teksty, ogłoszenie (raz), przypomnienie (start / co godzinę), "otwarty", "obejrzany" → nadawca widzi w aplikacji Wicero status "Obejrzany". Po stronie serwera nie powinno być nic do zrobienia.
- **Kod AP (Python 2.7 / wx 2.8) nigdy nie był uruchomiony** - ani składnia, ani UI. To jest zadanie na komputerze użytkownika: uruchomić, poprawić błędy, przejść T1-T13.
- Nieprzetestowane po stronie serwera tylko: czy ogłoszenie nowego filmu przesuwa przypomnienie o godzinę (wychodzi przy T10).

**Terminologia:** w kodzie, UI i komunikatach nie używamy słów "opiekun" ani "niepełnosprawny". Osoba korzystająca z AP to **kontakt**, osoba wysyłająca filmy - **nadawca**.

---

## Czym jest Wicero (minimum potrzebne do pracy w AP)

- System, w którym bliscy (nadawcy) wysyłają kontaktowi linki do filmów YouTube z opcjonalnym komentarzem. Repo: `github.com/jgrynczewski/wicero` (Flutter + Firebase) - **nie trzeba go mieć na tym komputerze**.
- Nadawca w aplikacji Wicero (web / Android) widzi oś czasu wysłanych filmów ze statusem "Wysłany" / "Obejrzany + data". "Obejrzany" ustawia AP (85% filmu).
- Kontakt jest dodawany w panelu admina Wicero; dostaje **token** (UUID) - to jego jedyne "logowanie". Admin akceptuje też zaproszenia nadawców (w AP - na razie nie).
- Backend: Cloud Functions w Pythonie 3.13 w chmurze Google (region `europe-central2`). **Nie działają na tym komputerze** - AP tylko wysyła do nich zapytania HTTPS. Zmiany po stronie serwera robi się w repo Wicero (`functions/`), nie tutaj.

## API (kontrakt)

Bazowy URL: `https://europe-central2-wicero-d9a70.cloudfunctions.net`. Każde zapytanie: nagłówek `Authorization: Bearer <token>`. Odpowiedzi JSON UTF-8; błąd → `{"error": "..."}` + kod 400/401/404/405. 401 = zły / brak tokenu.

| Endpoint | Wejście | Wyjście |
|---|---|---|
| `GET contact_senders` | - | `{"senders": [{"senderId", "name", "newCount", "say", "types": [{"type": "youtube", "label": "Filmy", "newCount", "say"}]}]}` - posortowani po imieniu |
| `GET contact_messages` | `?senderId=&type=youtube` | `{"senderName", "items": [{"connectionId", "messageId", "type", "videoId", "url", "title", "thumbnailUrl", "comment", "senderName", "status", "isNew", "say"}]}` - kolejność playlisty: nieobejrzane od najstarszego, potem obejrzane od najnowszego |
| `POST contact_message_event` | `{"connectionId", "messageId", "event": "opened" \| "viewed"}` | `{"ok": true}` |
| `POST contact_notifications` | `{"startup": bool}` | `{"say": ["Anna przysyła nowy film.", ...]}` - może być pusta |

- `say` - gotowe teksty dla `milena_say` (odmiana po polsku robiona na serwerze). AP ich nie składa.
- `isNew` - film nigdy nieotwarty (nie było ekranu przed filmem).
- Nowy film jest ogłaszany **raz**; przypomnienie o nieotwartych - **przy starcie AP i co godzinę** (decyduje serwer, AP pyta co minutę).

## Pliki

| Plik | Stan | Opis |
|---|---|---|
| `wicero_client.py` | ✅ przetestowany na Pythonie 3 z wdrożonym API (2026-10-13: nadawcy, filmy, ogłoszenia, przypomnienia, opened, viewed → "Obejrzany" u nadawcy); ⏳ Python 2.7 | Funkcje: `get_senders`, `get_messages`, `mark_opened`, `mark_viewed`, `get_notifications`. Błędy: `WiceroError.kind` = `offline` / `token` / `server`. |
| `test_wicero_api.py` | ✅ Python 3; ⏳ Python 2.7 | Diagnostyka API (patrz T1). |
| `modules/wicero.py` | ⏳ **nieuruchomiony** | `Board` (plansza ze skanowaniem), `SendersBoard`, `TypesBoard`, `IntroScreen`, `WiceroPlayer`, `Notifier`, `say()`. Samodzielnie: `python2.7 modules/wicero.py` (rodzic `_Standalone` zamiast `nowe.py`; powrót z planszy nadawców kończy program). |
| `modules/nowe.py` | ⏳ | Slot 3: `PUSTE` → `WICERO` (import, etykieta, ikona, `onPress`, dźwięk przy skanowaniu przez `milena_say`). |
| `ap.py` | ⏳ | Import `wicero` + `self.wiceroNotifier = wicero.Notifier( )` w `initializeTimer`. |
| `icons/modules/wicero.png` | ✅ | Logo Wicero (dwa "V" tworzące "W" - Vincentius / Wincenty) na białym zaokrąglonym kwadracie, 200×200 RGBA. Białe tło celowo: przy skanowaniu kafelek dostaje `scanningColour` (#0033FF), na którym niebieskie logo by znikło. Źródło: repo `wicero`, `assets/logo/wicero.svg` + `tools/generate_icons.py`. |
| `.wicero_token` | do utworzenia | Token kontaktu z panelu admina Wicero, jedna linia. W `.gitignore`. |
| `wicero.log` | tworzony automatycznie | Własny handler loggera `wicero` (nie `basicConfig` - ten zajmuje już `iot_client.py`). |

**Kod UI powstał bez możliwości uruchomienia** (komputer deweloperski: Windows, bez wx 2.8 / VLC / milena). Pisany przez kopiowanie istniejących wzorców, ale trzeba się spodziewać drobnych błędów.

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
  POWTORZ -> czyta ponownie;  START -> WiceroPlayer(item);  POWROT -> TypesBoard
WiceroPlayer: timer 1 s, przy 85% mark_viewed (raz)
  NASTEPNY / koniec filmu -> _leave(+1): _onExit() + CallAfter(IntroScreen.moveBy(+1))
  POPRZEDNI -> _leave(-1);  EXIT pilota -> zwykłe _onExit() -> IntroScreen
  moveBy za ostatnim filmem -> "To już wszystkie filmy." -> IntroScreen.onExit() -> TypesBoard
Notifier (ap.py, cały czas): 15 s po starcie (startup=True), potem co 60 s;
  pomija, gdy poprzednie czytanie trwa (busy) lub gra WiceroPlayer (PLAYING)
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

- Kod: `github.com/jgrynczewski/wicero`, katalog `functions/` (`main.py` - endpointy, `contact_api.py` - teksty i reguły, `tests/` - testy `python -m unittest discover -s tests`). Deploy: `firebase deploy --only functions` (Firebase CLI, konto właściciela projektu) - **zwykle robiony z komputera deweloperskiego**, nie z komputera użytkownika. Opisz potrzebną zmianę w notatce, jeśli nie masz tu repo / CLI.
- Firebase Console projektu `wicero-d9a70` → Firestore - podgląd i ręczna edycja danych.

### Model danych Firestore (to, czego dotyczy AP)
| Ścieżka | Pola istotne dla AP |
|---|---|
| `contacts/{contactId}/private/admin` | `desktopToken` - token z `.wicero_token` |
| `contacts/{contactId}/private/inbox` | `lastReminderAt` - czas ostatniego przypomnienia / ogłoszenia |
| `connections/{senderId}_{contactId}` | `senderId`, `contactId`, `status` (`accepted` = nadawca widoczny w AP) |
| `connections/{connectionId}/messages/{messageId}` | `senderId`, `contactId`, `type: "youtube"`, `videoId`, `url`, `title`, `comment`, `status` (`sent` → `viewed`), `createdAt`, `viewedAt`, `statusChangedBy`, **`openedAt`** (null = nowy, nieotwarty), **`announcedAt`** (null = jeszcze nie ogłoszony) |
| `users/{senderId}` | `displayName` - imię nadawcy w AP |

### Reset stanu do ponownych testów (Firebase Console → Firestore, edycja pola)
- Ponowne ogłoszenie filmu: `announcedAt` → `null` (typ null) i `status` = `sent`.
- Film znów "nowy" (przypomnienia, `newCount`): `openedAt` → `null`.
- Ponowne "obejrzany": `status` → `sent`, usunąć `viewedAt`.
- Przypomnienie od razu (bez startu AP): usunąć `lastReminderAt` w `contacts/{id}/private/inbox`.
- Najprościej: nadawca wysyła nowy film w aplikacji Wicero (web / Android).
- Filmy wysłane **przed 2026-10-12** nie mają pól `openedAt` / `announcedAt` - nigdy nie są "nowe" ani ogłaszane (zapytanie `== null` pomija brakujące pola). To celowe.

### Dane testowe (stan 2026-10-13)
Testowy kontakt ma jednego nadawcę: **"jan kowalski"** (displayName, małe litery - tak jest w danych) i 4 filmy: 2 stare (sprzed pól), "Wojciech Cejrowski..." (nowy, nieotwarty), "Piotr Szumowski..." (obejrzany przez test API). Token testowego kontaktu - od właściciela projektu (nie jest w repo).

## Przygotowanie (na komputerze użytkownika)

1. `git pull` na gałęzi `user/radek/master`.
2. Token: panel admina Wicero → kontakt → token → zapisać do `.wicero_token` w katalogu AP.
3. W Wicero: kontakt musi mieć **zaakceptowane** połączenie z kontem nadawcy, a nadawca wysłać mu 1-2 filmy **po 2026-10-12** (starsze nie mają pól `openedAt` / `announcedAt` - nie będą ogłaszane ani liczone jako nowe).
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
- [x] **T8 - odtwarzanie:** START → film; pilot jak w YouTube; po 85% - w aplikacji Wicero status "Obejrzany" z datą (na żywo).
- [x] **T9 - nawigacja w filmach:** NASTĘPNY / koniec filmu → ekran następnego filmu; po ostatnim: "To już wszystkie filmy." i powrót do planszy typów; POPRZEDNI na pierwszym filmie - ten sam film.
- [x] **T10 - ogłoszenie w tle:**
  - **BUG 1:** ogłoszenie przychodzi podczas odtwarzania w WiceroPlayer mimo flagi `PLAYING`. Prawdopodobna przyczyna: race condition - wątek Notifiera startuje tuż przed ustawieniem `PLAYING=True`, sprawdzenie flagi jest na początku `_tick`, ale wątek już działa. Do naprawy w `wicero.py`: sprawdzać `PLAYING` też wewnątrz wątku workera przed każdym `say()`.
  - **BUG 2:** Notifier odpytuje dwa razy na ~60s (log pokazuje naprzemiennie ~37s i ~23s). Prawdopodobnie `wicero.Notifier()` tworzony dwa razy. Sprawdzić `ap.py`.
  - **Do obserwacji (z planu):** nakładanie głosów na IntroScreen (PLAYING obejmuje tylko WiceroPlayer) - potwierdzone jako problem w praktyce.
- [ ] **T10 - ogłoszenie w tle:** nadawca wysyła film, AP w menu (lub radio / muzyka) → w ciągu ~1 min "X przysyła nowy film."; w trakcie filmu Wicero - ogłoszenie dopiero po wyjściu z odtwarzacza (Notifier pyta co 60 s, ale pomija takty, gdy `PLAYING`).
  - **Do obserwacji - nakładanie głosów na ekranie przed filmem:** `PLAYING` obejmuje tylko `WiceroPlayer`, więc ogłoszenie może paść w trakcie czytania komentarza w `IntroScreen` (lub na planszach Wicero). Test: wejść na ekran filmu, w tym czasie nadawca wysyła nowy film. Jeśli głosy się nakładają i przeszkadza to - ustawiać `PLAYING = True` (lub osobną flagę) od `open_wicero` do wyjścia z planszy nadawców.
- [x] **T13 - wiele filmów przy wyłączonym komputerze:** AP wyłączone, nadawca wysyła kilka filmów → start AP → po ~15 s **jeden** komunikat na nadawcę ("X przysyła 5 nowych filmów."), nie osobny na każdy film. Jeśli u tego nadawcy były wcześniej ogłoszone, ale nieotwarte filmy, padnie też przypomnienie o nich ("Czekają nowe filmy. X: 2 nowe filmy.") - poprawne, ale może mylić; ewentualna zmiana po stronie serwera (`contact_notifications` w repo `wicero`): przy starcie jedno zdanie z łączną liczbą.
- [~] **T11 - tryb tracker** (`control=tracker` w `parameters`) - wybór kafelków bez skanowania.
- [x] **T12 - zły token** w `.wicero_token` → wejście w WICERO: "Wicero nie jest skonfigurowane..."; w tle cisza (tylko log).

## Do zrobienia później
- Nagrania `.ogg` dla WICERO / FILMY / POWTÓRZ / START (teraz `milena_say`).
- Stronicowanie planszy nadawców (> 5).
- Ikony / zdjęcia nadawców (gdy Wicero je doda) i nazwy nadawane per połączenie ("Mama") - TODO w repo Wicero.
- Akceptacja zaproszeń w AP (teraz panel admina Wicero).
- Kolejne typy materiałów: serwer zwróci je w `types`, w AP - nowe kafelki na planszy typów i własne ekrany.
