# Moduł KOMPAN - plan i testy

Rozmowa z AI na dowolny temat: Kompan z czasem coraz lepiej zna użytkownika, może dowiedzieć się czegoś na prośbę innej osoby i przekazać to, co ważne, za zgodą użytkownika.

**Stan (2026-11-14):** kod etapów 1-3 gotowy, działa na komputerze z AP z prawdziwym AI; testy K1-K6 zaliczone. Po testach poprawiony prompt (najpierw podstawy, potem szczegóły; jeden wpis na sprawę; osoby pomagające) i koszt (notatki za pamięcią podręczną). Kod etapu 4 (wiadomości mailem) gotowy 2026-11-14, czeka na konto Gmail i `osoby.json`.

**Następna sesja:** `git pull` i `docker compose build && docker compose up -d` w `~/ap-gra` (jeśli jeszcze nie), czysty stan (sekcja niżej), notatki startowe, potem rozmowa sprawdzająca poprawki - zwłaszcza czy przy nowym temacie Kompan najpierw ustala podstawy i daje wybór kierunku. Potem przygotowanie wiadomości (sekcja niżej) i testy K7-K8.

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
- [ ] Przed etapem 5: dostęp SSH do komputera z AP

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
2. Dopisz do `~/ap-gra/.env.kompan` (hasło tylko tutaj, nigdzie indziej):
   ```
   AP_KOMPAN_GMAIL=adres.kompana@gmail.com
   AP_KOMPAN_GMAIL_HASLO=hasło aplikacji
   ```
3. Lista osób: `nano ~/ap-gra/dane-kompan/osoby.json` (wzór w `docs/kompan.md` w `ap-gra`, sekcja „Wiadomości”). Na pierwszy test wystarczy jedna osoba z Twoim adresem.
4. `docker compose up -d`, potem sprawdź: `curl -s localhost:8768/v1/kompan/health | python3 -m json.tool | grep -A3 poczta` - `"poczta": true`, imiona w `"osoby"`, pusty `"osoby_blad"`.

Bez konta albo bez osób Kompan po prostu nic nie proponuje.

## Czysty stan przed oddaniem użytkownikowi

Wszystko, co Kompan wie i zapisuje (notatki, rozmowy, streszczenie, koszty, nagrania), jest w `~/ap-gra/dane-kompan/`. AP po swojej stronie nic o rozmowach nie przechowuje. Katalog z testów odkładamy na bok zamiast kasować - przyda się przy poprawianiu promptu:

```
cd ~/ap-gra
docker compose stop ap-gra-kompan
mv dane-kompan dane-kompan-testy-RRRR-MM-DD
mkdir dane-kompan
cp dane-kompan-testy-RRRR-MM-DD/notatki_startowe.txt dane-kompan/   # tylko jeśli są już prawdziwe notatki startowe
cp dane-kompan-testy-RRRR-MM-DD/osoby.json dane-kompan/              # lista osób (etap 4), jeśli jest
docker compose start ap-gra-kompan
```

Potem Kompan nic nie wie, nie ma żadnej rozmowy (pierwsze wejście - od razu nowa), dzienny licznik kosztów startuje od zera.

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
| K7 | 4 | Porozmawiaj o czymś ważnym (np. jak z lekami): Kompan pyta „… Przekazać to komuś?”, osoby z listy i Nikomu. Jedna osoba i kilka (Komuś jeszcze?, To wszystko); potwierdzenie „Wiadomość dla: …” mieści się na ekranie; Popraw (Kompan dopytuje, potem nowa treść dla tych samych osób), Nie wysyłaj, Wyślij. Mail dochodzi: temat „Radek przekazuje przez Kompana”, treść, dopisek o AI i formułka. Kompan nie proponuje drobiazgów i nie wraca do sprawy po „Nikomu” | |
| K8 | 4 | Odłącz internet, Wyślij: Kompan przy następnym pytaniu mówi, że nie wyszło; po podłączeniu (do 5 minut) mail dochodzi, a Kompan wspomina, że w końcu wysłał | |
| K9 | 5 | Prośba od osoby z listy: Tak, zwrotka do autora tylko po zatwierdzeniu | |
| K10 | 5 | Prośba: Później (trzy razy) i Nie chcę | |
| K11 | 6 | Pytanie o bieżące sprawy: Kompan sprawdza w internecie | |
| K12 | 7 | Prośba i wiadomość przez Wicero, odpowiedź odbiorcy | |
