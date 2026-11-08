# Moduł GRA - plan i testy

**Od 2026-11-08: plansza GRY PRZYGODOWE** (kafelek na planszy gier zamiast TAJEMNICY i ZWROTKI) - obie gry i gry tworzone przez użytkownika z AI (kreator gier, ap-gra `docs/kreator-gier.md`). Testy: sekcja „Gry przygodowe i kreator” niżej.

Gry przygodowe czytane na głos (do 2026-11-08 na planszy GRY obok SKOCZKA i ŁAPACZA):
- **„Tajemnica zegara”** (przycisk TAJEMNICA, nagranie nazwy `sounds/tajemnica_zegara.ogg`) - opowieść „Sala pod zegarem” (na serwerze `sala_pod_zegarem`);
- **„Ostatnia zwrotka”** (przycisk ZWROTKA, od 2026-11-04; nagranie nazwy `sounds/ostatnia_zwrotka.ogg` - **do nagrania**, do tego czasu głos AP) - romans w willi z klubem muzycznym, 9 zakończeń (na serwerze `ostatnia_zwrotka`).

Obie gry działają na jednym serwerze (`?game=` w API), każda ma osobny zapis i licznik zakończeń.

**Stan (2026-11-01):** ekran gry przetestowany (G0-G10 passed). Opowieść kompletna jako PoC: 27 scen, 7 zakończeń, 8-12 minut na rozgrywkę (ap-gra, `docs/fabula.md` → „Wersja PoC”). Nagrania `sounds/gry.ogg` i `sounds/tajemnica_zegara.ogg` zrobione na komputerze użytkownika - **jeszcze nie w repo** (dodać: `git add sounds/gry.ogg sounds/tajemnica_zegara.ogg`). Dalej: granie różnymi ścieżkami i uwagi do fabuły; rozbudowa tylko, jeśli gra się spodoba. Serwer gry (silnik, scenariusz, nagrania narratora) - osobne repo `github.com/jgrynczewski/ap-gra`, kontener Docker na tym komputerze (port 8766, obok huba IoT 8765). W AP: `gra_client.py`, `modules/gra.py` (ekran), `modules/scenka.py` (zegar i ludziki), `modules/board.py` (plansza ze skanowaniem - wspólna z Wicero).

Skanowanie przycisków gry czeka, aż narrator doczyta przycisk, plus przerwa na zastanowienie - **parametr `gameOptionPause` w pliku `parameters`** (ms, domyślnie 1000; bez tej linii - 1 s), nigdy szybciej niż `timeGap`. Po wyborze: „Wybrałeś: <opcja>” (przycisk podświetlony kolorem wyboru), potem następna scena.

Zapis gry: `~/.ap-gra/zapis.json` (Tajemnica zegara), `~/.ap-gra/zapis_ostatnia_zwrotka.json` (Ostatnia zwrotka); nagrania pobrane z serwera: `~/.ap-gra/nagrania/`; log: `gra.log` w katalogu AP.

## Instalacja serwera gry (raz)

```bash
docker --version                       # musi być 23 lub nowszy (BuildKit - pamięć nagrań między budowaniami)
cd ~
git clone https://github.com/jgrynczewski/ap-gra.git
cd ap-gra
docker compose up -d --build           # pierwszy raz kilka minut: model głosu (~60 MB) i wszystkie nagrania
curl -s localhost:8766/v1/health       # "ok": true, "recordings": 99
```

Aktualizacja gry: `cd ~/ap-gra && git pull && docker compose up -d --build` (nagrywa tylko nowe teksty).

**Start z systemem:** AP niczego nie uruchamia. Kontener `ap-gra` ma `restart: unless-stopped` - podnosi go Docker przy starcie komputera (jak `aac-iot-hub` i `unipress-game-server-1`; sprawdzone 2026-11-01). Wyjątek: kontener zatrzymany ręcznie (`docker compose stop`) zostaje zatrzymany także po restarcie - wtedy `cd ~/ap-gra && docker compose up -d`. Wicero nie ma nic lokalnie (Cloud Functions w chmurze, wystarczy internet).

Sprawdzenie wszystkich kontenerów:

```bash
docker ps -a --format '{{.Names}}\t{{.Status}}' | while IFS=$'\t' read n s; do echo "$n | $s | restart: $(docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' "$n")"; done
```

## Testy ręczne (komputer użytkownika, po kolei)

| # | Test | Oczekiwane | Wynik |
|---|---|---|---|
| G0 | Instalacja serwera (wyżej) | `curl` zwraca `"ok": true`, `"recordings": 99` | passed |
| G1 | `git pull` w AP, start AP, menu główne → przycisk gier (dawniej mówił „skoczek”) | przycisk mówi „gry” (`sounds/gry.ogg`; dopóki go nie ma - „gra”); na planszy gier jeden rząd: SKOCZEK, SKOCZEK2, ŁAPACZ, TAJEMNICA ZEGARA (książka ze znakiem zapytania), pod nimi POWRÓT; przy skanowaniu: „Tajemnica zegara” (`sounds/tajemnica_zegara.ogg`; dopóki go nie ma - milena) | passed (kafel w NOWE - przeniesiony) |
| G2 | Wejście w TAJEMNICĘ ZEGARA (pierwszy raz) - 1. próba: tekst się nie mieścił, WYJDŹ nie łapał kliknięcia (poprawione) | tekst sceny wypisuje się w takt czytania (głos narratora, nie milena); z prawej rusza się zegar i ludziki; 4 opcje jedna pod drugą + POWTÓRZ i WYJDŹ; skanowanie rusza dopiero po przeczytaniu; opcje czyta narrator | passed |
| G3 | Wybór opcji 1 (Kuba), potem 2 (żart) | kolejne sceny; w scenie radiowęzła zdanie „Klasa jeszcze chichocze…” | passed |
| G4 | POWTÓRZ | tekst sceny od nowa, znowu w takt czytania | passed |
| G5 | WYJDŹ, ponowne wejście w GRA | powrót do menu; po wejściu: „Masz zapisaną grę.”, KONTYNUUJ / NOWA GRA; KONTYNUUJ - ta sama scena co przy wyjściu | passed |
| G5a | Skanowanie opcji (po poprawce z G6) | narrator doczytuje każdą opcję do końca, potem ok. 1 s przerwy, dopiero wtedy następny przycisk; po wyborze „Wybrałeś: …” z podświetlonym wybranym przyciskiem | passed (najpierw „Wybrałeś” głosem AP - kontener nie był przebudowany) |
| G6 | Gra do końca (drzwi auli) - 1. próba: skanowanie ucinało czytanie opcji, brak potwierdzenia wyboru (poprawione) | zakończenie: tytuł „Ciąg dalszy nastąpi”, „Zakończenie pierwsze z jednego”, „Odkryte zakończenia: 1 z 1”; przycisk NOWA GRA | passed |
| G7 | Dwa przejścia skanowania bez naciśnięcia, potem naciśnięcie | „usypiam”, potem skanowanie od początku | passed |
| G8 | `cd ~/ap-gra && docker compose stop`, wejście w GRA; potem `docker compose start` | milena: „Gra nie jest uruchomiona.”, zostaje menu | passed |
| G9 | Wicero (plansza przeniesiona do `modules/board.py`): nadawcy → FILMY → ekran przed filmem → film → powrót | działa jak wcześniej | passed |
| G11 | Film YouTube albo Wicero w tle (W TLE), potem gry → TAJEMNICA ZEGARA, chwilę grać, WYJDŹ (od 2026-11-04) | film gra cały czas - razem z narratorem gry (nie milknie przy wejściu do gry) | |
| G10 | `top` przy otwartej grze | AP nie zjada procesora przez animację (orientacyjnie < 30%) | passed (7-15% CPU, Latitude 7490) |

### Ostatnia zwrotka (2026-11-04)

Przed testami: `cd ~/ap-gra && git pull && docker compose up -d --build` (nagra wszystkie teksty nowej gry - kilka minut), w AP `git pull`.

| # | Test | Oczekiwane | Wynik |
|---|---|---|---|
| Z1 | gry → plansza | jeden rząd: SKOCZEK, SKOCZEK2, ŁAPACZ, TAJEMNICA ZEGARA, OSTATNIA ZWROTKA (serce z nutą); przy skanowaniu „Ostatnia zwrotka” (głos AP, dopóki nie ma nagrania) | |
| Z2 | ZWROTKA (pierwszy raz) | scena na tarasie willi, taksówka, Nina i Bigos; 4 opcje; czyta narrator; cały tekst widoczny; **z prawej nowa scenka**: nocny ogród willi - migoczące gwiazdy, okna zapalają się i gasną, lampiony się kołyszą, para nad basenem, unoszące się serduszko, Bigos na brzegu | |
| Z3 | Kilka scen, WYJDŹ, ponownie ZWROTKA → KONTYNUUJ; potem TAJEMNICA | „Ostatnia zwrotka” wraca w tym samym miejscu; Tajemnica zegara ma **swój** zapis (bez zmian) | |
| Z4 | Gra do końca, przy pisaniu piosenki wybierać wersy | na festiwalu Nina śpiewa **wybrane** wersy (3 linie); zakończenie „… z dziewięciu.”, „Odkryte zakończenia: 1 z 9.” | |
| Z5 | Druga partia inną ścieżką (np. „Niech Bartas zapowie nową piosenkę”) | inne zakończenie, licznik „2 z 9” | |

### Gry przygodowe i kreator (2026-11-08)

Pliki: `modules/przygody.py` (plansza GRY PRZYGODOWE), `modules/kreator.py` (rozmowa z AI), `kreator_client.py` (usługa `ap-gra-kreator`, port 8767), `modules/gra.py` (wspólna część planszy gry i rozmowy - `NarratedBoard`), `modules/scenka.py` (`FramesScene` - animacja gier z kreatora), ikona `icons/new_games/gry_przygodowe.png`. Nagranie nazwy `sounds/gry_przygodowe.ogg` - **do nagrania**, do tego czasu głos AP. Kafelki i klatki gier z kreatora: `~/.ap-gra/gry/<id>/`.

Przed testami (komputer z AP):

```bash
cd ~/ap-gra && git pull
docker compose version                 # co najmniej 2.24 (opcjonalny plik .env)
cp .env.example .env && nano .env      # ANTHROPIC_API_KEY=... (klucz z konsoli Anthropic; limit kosztów ustawiony na koncie)
docker compose up -d --build           # trzy kontenery: ap-gra, ap-gra-kreator, ap-gra-rysownik
curl -s localhost:8767/v1/kreator/health   # "ai": true, "nagrania": true
```

W AP: `git pull`.

| # | Test | Oczekiwane | Wynik |
|---|---|---|---|
| P1 | gry → plansza | SKOCZEK, SKOCZEK2, ŁAPACZ, GRY PRZYGODOWE (książka z górami), puste pole; POWRÓT pod nimi; przy skanowaniu „Gry przygodowe” (głos AP) | |
| P2 | GRY PRZYGODOWE | plansza 3 x 5: NOWA GRA, TAJEMNICA ZEGARA, OSTATNIA ZWROTKA (ich ikony), puste pola, POWRÓT w prawym dolnym rogu; skanowanie wierszami, potem przyciskami; tytuły czyta narrator | |
| P3 | TAJEMNICA ZEGARA, kilka scen, WYJDŹ; to samo z ZWROTKĄ | gry jak wcześniej (zegar z ludzikami, ogród), zapisy zachowane - KONTYNUUJ wraca tam, gdzie przed aktualizacją; WYJDŹ wraca na planszę GRY PRZYGODOWE | |
| P4 | `cd ~/ap-gra && docker compose stop ap-gra-kreator`, potem NOWA GRA; potem `docker compose start ap-gra-kreator` | „Tworzenie gier nie jest uruchomione.”, zostaje plansza | |
| P5 | NOWA GRA | „Myślę...”, po kilku sekundach pierwsze pytanie AI czytane przez narratora; pod nim 2-3 odpowiedzi i „Inne propozycje”, na dole WRÓĆ (od drugiego pytania) i PRZERWIJ | |
| P6 | Odpowiedź, potem „Inne propozycje”, potem WRÓĆ | „Wybrałeś: …”, „Myślę...”, następne pytanie; „Inne propozycje” - to samo pytanie z innymi odpowiedziami; WRÓĆ - od razu poprzednie odpowiedzi (bez „Myślę...”) | |
| P7 | Odpowiadać do końca rozmowy | tytuł i streszczenie pomysłu; ROZPOCZNIJ / INNY POMYSŁ; INNY POMYSŁ - nowe streszczenie | |
| P8 | ROZPOCZNIJ | „Tworzę grę. To potrwa kilkanaście minut…”, powrót na planszę; nowy kafelek z tytułem i „(tworzy się)”; po wybraniu: „Ta gra jeszcze się tworzy.” | |
| P9 | Po kilkunastu minutach: POWRÓT i ponownie GRY PRZYGODOWE (zanotować, ile trwało tworzenie: `curl -s localhost:8767/v1/kreator/gry`) | kafelek z obrazkiem i tytułem; tytuł czyta narrator | |
| P10 | Nowa gra: kilka scen, WYJDŹ, ponownie → KONTYNUUJ, gra do końca | z prawej animacja gry (płynna, w pętli); tekst czyta narrator; zapis i zakończenia jak w innych grach | |
| P11 | `top` przy otwartej nowej grze | AP < 30% CPU (jak G10); pamięć AP nie rośnie z czasem | |
| P12 | NOWA GRA, kilka odpowiedzi, PRZERWIJ | powrót na planszę, bez nowego kafelka | |
| P13 | Gier więcej niż 12 (tworzyć kolejne albo skopiować katalog gry w `~/ap-gra/dane/gry/` pod inną nazwą) | DALEJ w dolnym rzędzie; DALEJ - następna strona; z ostatniej - pierwsza | |

Historia rozmów i tworzenia: `~/ap-gra/dane/rozmowy/<id>/log.jsonl`; rozgrywki: `docker exec ap-gra python -m tools.statystyki`.

Przy błędzie: traceback z terminala AP i `tail -n 20 gra.log`.
