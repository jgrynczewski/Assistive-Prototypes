# Moduł KOMPAN - plan i testy

Rozmowa z AI na dowolny temat: Kompan z czasem coraz lepiej zna użytkownika, może dowiedzieć się czegoś na prośbę innej osoby i przekazać to, co ważne, za zgodą użytkownika.

**Stan (2026-11-14):** kod etapów 1-3 gotowy, działa na komputerze z AP z prawdziwym AI; testy K1-K6 zaliczone. Po testach poprawiony prompt (najpierw podstawy, potem szczegóły; jeden wpis na sprawę; osoby pomagające) i koszt (notatki za pamięcią podręczną). Kod etapu 4 (wiadomości mailem) gotowy 2026-11-14, etapu 5 (poczta przychodząca: WIADOMOŚCI, odpowiedzi w wątku, ogłoszenia w całym AP) 2026-11-15; czekają na konto Gmail i `osoby.json`. Od 2026-11-15 wiadomości są pisane w pierwszej osobie, z widoczną stopką o AI. **Od 2026-11-15 Radek używa Kompana na co dzień - `~/ap-gra/dane-kompan/` to prawdziwe dane: kopia przed każdą aktualizacją, testy tylko na instancji testowej (sekcje niżej).** **Uwaga:** etap 5 zmienił `Notifier` w `modules/wicero.py` (jeden zwiastun dla Wicero i Kompana) - przy K9 sprawdzić też, że ogłoszenia Wicero o filmach działają jak dotąd.

**Następna sesja:** aktualizacja z kopią danych (sekcja „Aktualizacja bez utraty danych”), potem instancja testowa (sekcja „Testy na instancji testowej”) z kontem Gmail i testy K7-K10.

- Wszystkie ustalenia, architektura i plan etapów do odhaczania: `docs/kompan.md` w repo `ap-gra`
- Serwer: usługa `ap-gra-kompan` w `ap-gra`, port 8768
- W tym repozytorium: `kompan_client.py`, `modules/kompan.py`, kafelek KOMPAN na planszy NOWE (zamiast pustego pola), ikona. Brakuje nagrania `sounds/kompan.ogg` (do tego czasu głos AP)
- Plansza jak rozmowa o grze (`modules/kreator.py`, `gra.NarratedBoard`)

## Do zrobienia przez Ciebie

Po kolei, każde wtedy, gdy będzie potrzebne:
- [x] Klucz API `ap-kompan` i uruchomienie, testy K1-K6 (2026-11-14)
- [ ] Najlepiej przed kolejną rozmową: notatki startowe w `~/ap-gra/dane-kompan/notatki_startowe.txt` (zwykły tekst; czytane przy każdym pytaniu, bez restartu)
- [ ] Kiedy chcesz: nagranie `sounds/kompan.ogg` (nazwa kafelka; do tego czasu głos AP)
- [ ] Przed testami K7-K8: konto Gmail dla Kompana, hasło aplikacji i lista osób (sekcja „Wiadomości” niżej)
- [ ] Kiedyś: dostęp SSH do komputera z AP (do zdalnej pomocy; prośby przyjdą mailem, decyzja 2026-11-15)

## Uruchomienie na komputerze z AP

Raz, przed pierwszym testem:

1. Na https://platform.claude.com utwórz klucz API o nazwie `ap-kompan`.
2. Pobierz kod i wpisz klucz (klucz tylko w tym pliku, nigdzie indziej):
   ```
   cd ~/ap-gra && git pull
   cp .env.kompan.example .env.kompan
   nano .env.kompan
   ```
3. Notatki startowe (opcjonalnie, można później): `mkdir -p dane-kompan && nano dane-kompan/notatki_startowe.txt`. Zwykły tekst: kim jest użytkownik, bliskie osoby, zainteresowania, jak lubi rozmawiać.
4. Zbuduj i uruchom, potem sprawdź (`"ai": true` = klucz działa):
   ```
   docker compose build && docker compose up -d
   curl -s localhost:8768/v1/kompan/health | python3 -m json.tool | head -5
   ```
5. `cd ~/Assistive-Prototypes && git pull`, uruchom AP od nowa.

Podgląd rozmowy, kosztów i logów: `docs/podglad.md` w repo `ap-gra`, sekcja „Kompan”.

## Wiadomości (etap 4) - przygotowanie

1. Załóż osobne konto Gmail dla Kompana. Włącz weryfikację dwuetapową (bez niej Google nie da hasła aplikacji), potem: Konto Google → Bezpieczeństwo → Hasła aplikacji → utwórz hasło (np. „kompan”).
2. Na czas testów dopisz do `~/ap-gra/.env.kompan-test`, po testach przenieś do `~/ap-gra/.env.kompan` (hasło tylko w tych plikach, nigdzie indziej):
   ```
   AP_KOMPAN_GMAIL=adres.kompana@gmail.com
   AP_KOMPAN_GMAIL_HASLO=hasło aplikacji
   ```
3. Lista osób: `nano ~/ap-gra/dane-kompan-test/osoby.json` (po testach `dane-kompan/osoby.json` z prawdziwymi osobami) (wzór w `docs/kompan.md` w `ap-gra`, sekcja „Wiadomości”). Na pierwszy test wystarczy jedna osoba z Twoim adresem. Pole `"opis"` (kim jest dla Radka i jak do niej pisać) jest nieobowiązkowe, ale poprawia ton wiadomości i propozycje odpowiedzi.
4. `docker compose --profile test up -d ap-gra-kompan-test`, potem sprawdź: `curl -s localhost:8769/v1/kompan/health | python3 -m json.tool | grep -A3 poczta` - `"poczta": true`, imiona w `"osoby"`, pusty `"osoby_blad"` (prawdziwa instancja: port 8768 i `docker compose up -d`).

Bez konta albo bez osób Kompan po prostu nic nie proponuje.

## Aktualizacja bez utraty danych

Wszystko, co Kompan wie o Radku (notatki, rozmowy, streszczenie, koszty), jest w `~/ap-gra/dane-kompan/`. AP po swojej stronie nic o rozmowach nie przechowuje. **Tego katalogu nie przenosimy, nie kasujemy i nie testujemy na nim** („czysty stan” był jednorazowy, przed oddaniem Kompana).

Przy każdej aktualizacji, gdy Radek nie rozmawia z Kompanem:

```
cd ~/ap-gra
curl -s localhost:8768/v1/kompan/health | python3 -m json.tool | grep -E '"notatki"|"tytul"'   # zapisz liczbę notatek i tytuł ostatniej rozmowy
docker compose stop ap-gra-kompan
mkdir -p ~/kopie-kompan
sudo tar czf ~/kopie-kompan/dane-kompan-$(date +%F-%H%M).tgz dane-kompan
ls -lh ~/kopie-kompan                                    # kopia jest i nie ma 0 bajtów
git pull
docker compose build && docker compose up -d
curl -s localhost:8768/v1/kompan/health | python3 -m json.tool | grep -E '"test"|"notatki"|"tytul"'   # "test": false, ta sama liczba notatek, ten sam tytuł
cd ~/Assistive-Prototypes && git pull                    # potem AP od nowa
```

Na koniec w AP: KOMPAN - na ekranie wejścia WRÓĆ DO ROZMOWY z ostatnim tematem Radka. Nowa wersja czyta dane starszych (sprawdza to test automatyczny), a kopia jest na wszelki wypadek. Przywrócenie kopii (tylko gdyby coś poszło źle):
```
cd ~/ap-gra && docker compose stop ap-gra-kompan
sudo mv dane-kompan dane-kompan-zepsute-$(date +%F)
sudo tar xzf ~/kopie-kompan/<plik>.tgz
docker compose start ap-gra-kompan
```

## Testy na instancji testowej

Testy nie mogą zmieniać danych, logów ani kosztów Radka. Dlatego testujemy na osobnej instancji Kompana: ten sam kod, ale własne dane (`~/ap-gra/dane-kompan-test/`), własny klucz API, własny limit i port 8769. Prawdziwy Kompan w tym czasie stoi nietknięty.

Raz, przed pierwszymi testami:
1. Na https://platform.claude.com utwórz klucz API `ap-kompan-test` (koszty testów będą osobno także w konsoli).
2. Ustawienia i dane testowej instancji:
   ```
   cd ~/ap-gra
   cp .env.kompan.example .env.kompan-test
   nano .env.kompan-test      # ANTHROPIC_API_KEY=klucz ap-kompan-test, AP_KOMPAN_LIMIT_USD=1, Gmail (sekcja „Wiadomości” niżej)
   mkdir -p dane-kompan-test
   cp dane-kompan/notatki_startowe.txt dane-kompan-test/     # kopia - rozmowy testowe podobne do prawdziwych
   nano dane-kompan-test/osoby.json                          # tylko Twoje adresy, nikogo prawdziwego
   ```

Każde testy:
```
cd ~/ap-gra && docker compose --profile test up -d ap-gra-kompan-test
curl -s localhost:8769/v1/kompan/health | python3 -m json.tool | grep -E '"test"|"ai"|"poczta"'   # "test": true
```
Zamknij zwykłe AP i uruchom AP testowe:
```
cd ~/Assistive-Prototypes && AP_KOMPAN_URL=http://localhost:8769 python ap.py 2>&1 | tee /tmp/ap.log
```
W KOMPANIE ekran wejścia mówi „Kompan, wersja testowa”. Jeśli mówi tylko „Kompan”, to prawdziwy - przerwij. Po testach: zamknij AP, `docker compose stop ap-gra-kompan-test`, uruchom AP zwykle. Ogłoszenia Wicero o filmach, które przyjdą w czasie testów, usłyszysz Ty, nie Radek (filmy zostają w Wicero).

Poczta: na testy K7-K10 konto Gmail Kompana wpisz tylko do `.env.kompan-test`. Dwie instancje nie mogą czytać tej samej skrzynki - jedna zabierałaby maile drugiej. Do prawdziwego `.env.kompan` Gmail trafia dopiero po testach (wtedy usuń go z `.env.kompan-test`, a do kolejnych testów poczty załóż osobne konto testowe).

## Testy na komputerze z AP

Po jednym, z oczekiwanym wynikiem. Szczegóły dopiszemy przy każdym etapie.

| # | Etap | Test | Wynik |
|---|---|---|---|
| K1 | 2 | Kafelek KOMPAN na planszy NOWE; pierwsze wejście - od razu nowa rozmowa | OK 2026-11-14 (pierwsze prawdziwe zapytanie do AI) |
| K2 | 2 | Przyciski (Blisko, Inne propozycje, Zmień temat, WRÓĆ, ZAKOŃCZ) mieszczą się, skanowanie nie jest za długie | OK 2026-11-14 |
| K3 | 2 | ZAKOŃCZ, wejście ponownie: WRÓĆ DO ROZMOWY z tematem, NOWA ROZMOWA | OK 2026-11-14 (pamięć między rozmowami - w K6) |
| K4 | 2 | **Czy dobrze się rozmawia:** jedno pytanie naraz, bez ślepych uliczek, Kompan sam proponuje tematy | OK 2026-11-14 (sprawnie doszedł do „leki za późno”; poprawki: notatki za pamięcią podręczną - taniej, jeden wpis zamiast kilku wersji, nazywanie osób pomagających) |
| K5 | 2 | Dzienny limit kosztów: komunikat, rozmowa zostaje zapisana | OK 2026-11-14 (limit 0,1 USD na próbę) |
| K6 | 3 | Kompan zapisuje informacje (`curl -s localhost:8768/v1/kompan/notatki`); po ok. 5 wpisach, w spokojnej chwili, przegląd: Wszystko dobrze / Coś jest źle (po kolei, usuwanie) / Nie teraz; tekst przeglądu mieści się na ekranie; CO O MNIE WIESZ na ekranie wejścia: Dalej, To nieprawda, usuń, Wystarczy | OK 2026-11-14; uwaga: przed szczegółami nowego tematu AI ma najpierw ustalić podstawy (dopisane do promptu) |
| K7 | 4 | Porozmawiaj o czymś ważnym (np. jak z lekami): Kompan pyta „… Przekazać to komuś?”, osoby z listy i Nikomu. Jedna osoba i kilka (Komuś jeszcze?, To wszystko); potwierdzenie „Wiadomość dla: …” mieści się na ekranie; Popraw (Kompan dopytuje, potem nowa treść dla tych samych osób), Nie wysyłaj, Wyślij. Mail dochodzi: nadawca „Radek (przez Kompana)”, temat - tytuł rozmowy, powitanie w tonie z opisu osoby (dla kilku osób bez imienia), treść w pierwszej osobie („Leki dostaję…”), podpis „Radek”, pod spodem krótka stopka o AI widoczna jak reszta tekstu. Kompan nie proponuje drobiazgów i nie wraca do sprawy po „Nikomu” | |
| K8 | 4 | Odłącz internet, Wyślij: Kompan przy następnym pytaniu mówi, że nie wyszło; po podłączeniu (do 5 minut) mail dochodzi, a Kompan wspomina, że w końcu wysłał | |
| K9 | 5 | Mail od osoby z listy (z `"pisze": true` w `osoby.json`): AP ogłasza go poza Kompanem, a ogłoszenia Wicero o filmach działają jak dotąd; przy wejściu „Masz nową wiadomość od …”, PRZECZYTAJ (nagłówek, części z Dalej), ODPOWIEDZ - odpowiedź dochodzi w tym samym wątku (pierwsza z powitaniem, kolejna w tym wątku bez); mail spoza listy albo z podrobionym nadawcą - nic się nie pojawia | |
| K10 | 5 | PÓŹNIEJ, NIE ODPOWIADAM i powrót przez WIADOMOŚCI (osoba → tematy → wiadomość), ODPISZ Z KOMPANEM przy starej wiadomości; nowa wiadomość w trakcie rozmowy - „Przeczytać teraz?” w spokojnej chwili | |
| K11 | 6 | Pytanie o bieżące sprawy: Kompan sprawdza w internecie | |
| K12 | 7 | Prośba i wiadomość przez Wicero, odpowiedź odbiorcy | |
