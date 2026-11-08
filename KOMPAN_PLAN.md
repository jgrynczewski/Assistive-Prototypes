# Moduł KOMPAN - plan i testy

Rozmowa z AI na dowolny temat: Kompan z czasem coraz lepiej zna użytkownika, może dowiedzieć się czegoś na prośbę innej osoby i przekazać to, co ważne, za zgodą użytkownika.

**Stan (2026-11-08):** kod serwera (etap 1) i modułu w AP (etap 2) gotowy, jeszcze bez prawdziwego AI i bez testów na komputerze z AP. Następny krok: uruchomienie i test K1.

- Wszystkie ustalenia, architektura i plan etapów do odhaczania: `docs/kompan.md` w repo `ap-gra`
- Serwer: usługa `ap-gra-kompan` w `ap-gra`, port 8768
- W tym repozytorium: `kompan_client.py`, `modules/kompan.py`, kafelek KOMPAN na planszy NOWE (zamiast pustego pola), ikona. Brakuje nagrania `sounds/kompan.ogg` (do tego czasu głos AP)
- Plansza jak rozmowa o grze (`modules/kreator.py`, `gra.NarratedBoard`)

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

## Testy na komputerze z AP

Po jednym, z oczekiwanym wynikiem. Szczegóły dopiszemy przy każdym etapie.

| # | Etap | Test | Wynik |
|---|---|---|---|
| K1 | 2 | Kafelek KOMPAN na planszy NOWE; pierwsze wejście - od razu nowa rozmowa | |
| K2 | 2 | Przyciski (Blisko, Inne propozycje, Zmień temat, WRÓĆ, ZAKOŃCZ) mieszczą się, skanowanie nie jest za długie | |
| K3 | 2 | ZAKOŃCZ, wejście ponownie: WRÓĆ DO ROZMOWY z tematem, NOWA ROZMOWA | |
| K4 | 2 | **Czy dobrze się rozmawia:** jedno pytanie naraz, bez ślepych uliczek, Kompan sam proponuje tematy | |
| K5 | 2 | Dzienny limit kosztów: komunikat, rozmowa zostaje zapisana | |
| K6 | 3 | Kompan zapisuje informacje, okresowy przegląd, CO O MNIE WIESZ, usuwanie błędnego wpisu | |
| K7 | 4 | Wybór jednej i kilku osób, Wyślij, Popraw, Nie wysyłaj; mail dochodzi, podpis i formułka | |
| K8 | 4 | Brak internetu: wiadomość czeka i wychodzi później | |
| K9 | 5 | Prośba od osoby z listy: Tak, zwrotka do autora tylko po zatwierdzeniu | |
| K10 | 5 | Prośba: Później (trzy razy) i Nie chcę | |
| K11 | 6 | Pytanie o bieżące sprawy: Kompan sprawdza w internecie | |
| K12 | 7 | Prośba i wiadomość przez Wicero, odpowiedź odbiorcy | |
