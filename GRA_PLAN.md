# Moduł GRA - plan i testy

Gra przygodowa czytana na głos - **„Tajemnica zegara”** (przycisk na planszy gier, obok SKOCZKA i ŁAPACZA; nagranie nazwy: `sounds/tajemnica_zegara.ogg`). Pierwsza opowieść: „Sala pod zegarem”. Serwer gry (silnik, scenariusz, nagrania narratora) - osobne repo `github.com/jgrynczewski/ap-gra`, kontener Docker na tym komputerze (port 8766, obok huba IoT 8765). W AP: `gra_client.py`, `modules/gra.py` (ekran), `modules/scenka.py` (zegar i ludziki), `modules/board.py` (plansza ze skanowaniem - wspólna z Wicero).

Skanowanie przycisków gry czeka, aż narrator doczyta przycisk, plus przerwa na zastanowienie - **parametr `gameOptionPause` w pliku `parameters`** (ms, domyślnie 1000; bez tej linii - 1 s), nigdy szybciej niż `timeGap`. Po wyborze: „Wybrałeś: <opcja>” (przycisk podświetlony kolorem wyboru), potem następna scena.

Zapis gry: `~/.ap-gra/zapis.json`; nagrania pobrane z serwera: `~/.ap-gra/nagrania/`; log: `gra.log` w katalogu AP.

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

## Testy ręczne (komputer użytkownika, po kolei)

| # | Test | Oczekiwane | Wynik |
|---|---|---|---|
| G0 | Instalacja serwera (wyżej) | `curl` zwraca `"ok": true`, `"recordings": 99` | passed |
| G1 | `git pull` w AP, start AP, menu główne → przycisk gier (dawniej mówił „skoczek”) | przycisk mówi „gry” (`sounds/gry.ogg`; dopóki go nie ma - „gra”); na planszy gier jeden rząd: SKOCZEK, SKOCZEK2, ŁAPACZ, TAJEMNICA ZEGARA (książka ze znakiem zapytania), pod nimi POWRÓT; przy skanowaniu: „Tajemnica zegara” (`sounds/tajemnica_zegara.ogg`; dopóki go nie ma - milena) | passed (kafel w NOWE - przeniesiony) |
| G2 | Wejście w TAJEMNICĘ ZEGARA (pierwszy raz) - 1. próba: tekst się nie mieścił, WYJDŹ nie łapał kliknięcia (poprawione) | tekst sceny wypisuje się w takt czytania (głos narratora, nie milena); z prawej rusza się zegar i ludziki; 4 opcje jedna pod drugą + POWTÓRZ i WYJDŹ; skanowanie rusza dopiero po przeczytaniu; opcje czyta narrator | passed |
| G3 | Wybór opcji 1 (Kuba), potem 2 (żart) | kolejne sceny; w scenie radiowęzła zdanie „Klasa jeszcze chichocze…” | passed |
| G4 | POWTÓRZ | tekst sceny od nowa, znowu w takt czytania | passed |
| G5 | WYJDŹ, ponowne wejście w GRA | powrót do menu; po wejściu: „Masz zapisaną grę.”, KONTYNUUJ / NOWA GRA; KONTYNUUJ - ta sama scena co przy wyjściu | passed |
| G5a | Skanowanie opcji (po poprawce z G6) | narrator doczytuje każdą opcję do końca, potem ok. 1 s przerwy, dopiero wtedy następny przycisk; po wyborze „Wybrałeś: …” z podświetlonym wybranym przyciskiem | |
| G6 | Gra do końca (drzwi auli) - 1. próba: skanowanie ucinało czytanie opcji, brak potwierdzenia wyboru (poprawione) | zakończenie: tytuł „Ciąg dalszy nastąpi”, „Zakończenie pierwsze z jednego”, „Odkryte zakończenia: 1 z 1”; przycisk NOWA GRA | |
| G7 | Dwa przejścia skanowania bez naciśnięcia, potem naciśnięcie | „usypiam”, potem skanowanie od początku | |
| G8 | `cd ~/ap-gra && docker compose stop`, wejście w GRA; potem `docker compose start` | milena: „Gra nie jest uruchomiona.”, zostaje menu | |
| G9 | Wicero (plansza przeniesiona do `modules/board.py`): nadawcy → FILMY → ekran przed filmem → film → powrót | działa jak wcześniej | |
| G10 | `top` przy otwartej grze | AP nie zjada procesora przez animację (orientacyjnie < 30%) | |

Przy błędzie: traceback z terminala AP i `tail -n 20 gra.log`.
