# Plan integracji modułu IoT z Assistive-Prototypes

## Kontekst projektu

### Assistive-Prototypes (AP)
- Lokalizacja: `/home/radoslaw/Assistive-Prototypes/`
- Python 2.7, wxPython 2.8, pygame.mixer
- GUI typu scanning interface dla osób niepełnosprawnych
- Jeden przycisk/przełącznik jako wejście (tryb `switch`) lub eyetracker (tryb `tracker`)
- Plik konfiguracyjny: `parameters` (klucz=wartość)
- Główny plik: `ap.py` – klasa `main_menu`

### AAC IoT Hub
- Lokalizacja: `/home/radoslaw/aac-iot-hub/`
- Python 3.12, FastAPI, port **8765**
- Uruchomiony jako kontener Docker
- Kluczowe endpointy (poprawiony format):
  - `POST /api/v1/devices/discover` – wykryj urządzenia w sieci (timeout 30s)
  - `GET /api/v1/devices` – lista urządzeń
  - `GET /api/v1/devices/{id}/capabilities` – możliwości urządzenia
  - `PUT /api/v1/devices/{id}/control` – sterowanie (body: `{"properties": {"power": "toggle"}}`)
  - `POST /api/v1/devices/{id}/effect` – efekty świetlne (body: `{"effect_name": "disco"}`)
  - `POST /api/v1/devices/{id}/effect/stop` – zatrzymanie efektu

---

## Zasady implementacji

1. **Minimalna ingerencja w istniejący kod** – zmiany w `ap.py` tylko w miejscach gdzie są analogiczne wpisy dla innych modułów
2. **Styl identyczny z istniejącymi modułami** – klasa wxFrame, `initializeParameters`, `initializeBitmaps`, `createGui`, `createBindings`, `initializeTimer`, `onPress`, `timerUpdate`, `onExit`, `OnCloseWindow`
3. **GridBagSizer** – identycznie jak `radio.py` i `exercise.py`, trzy osobne sizery przełączane przez `mainSizer.Show()`
4. **Wzorzec dźwięku**: nagrania `.ogg` z `mixer.Sound`; `milena_say` przez `subprocess.Popen` jako fallback
5. **Język polski** – wszystkie etykiety, komunikaty, dźwięki po polsku
6. **Ikony 200×200px**, PNG z przezroczystością, czarne symbole na białym tle
7. **Logi do pliku** `iot.log` w katalogu projektu (moduł `logging`)

---

## Nawigacja w module IoT

```
Menu główne AP
    └── [IOT] → Plansza urządzeń (discovery z API)
                    ├── [żarówka / urządzenie X] → Plansza capabilities
                    │       ├── [zasilanie]   → bezpośredni toggle (bez kolejnej planszy)
                    │       ├── [jasność]     → Plansza: 25% / 50% / 75% / 100% / powrót
                    │       ├── [kolor]       → Plansza: niebieski / zielony / pomarańczowy /
                    │       │                            różowy / fioletowy / czerwony /
                    │       │                            biały / żółty / powrót
                    │       ├── [temperatura] → Plansza: ciepła / neutralna / zimna / powrót
                    │       ├── [efekt]       → Plansza: disco / puls / stroboskop /
                    │       │                            tęcza / policja / ocean / stop / powrót
                    │       ├── [reset]       → przywróć domyślne (power=on, brightness=100, temperature=warm)
                    │       └── [powrót]      → Plansza urządzeń
                    └── [powrót]              → Menu główne AP
```

**Zasady nawigacji:**
- Każda plansza ma przycisk `powrót` (ikona `back.png`) jako ostatni wiersz
- Skanowanie: wiersze → kolumny (identycznie jak wszystkie inne moduły)
- Po X pustych przejściach przez wiersze → uśpienie
- `power` = toggle bezpośrednio na planszy capabilities, bez wchodzenia głębiej
- `reset` = przywraca domyślny stan żarówki (power=on, brightness=100, temperature=warm)
- Puste sloty czytane jako „puste" przy skanowaniu i po wyborze
- Back button jako ostatni wiersz – obsługiwany na poziomie skanowania wiersza (bez wchodzenia w kolumny)

---

## Układ plansz (GridBagSizer)

| Plansza | Wiersze | Kolumny | Ostatni wiersz |
|---------|---------|---------|----------------|
| devices | 2 | 3 | back |
| capabilities | 3 | 4 | back |
| values | 3 | 4 | back |

---

## Pliki

### `modules/iot.py` ✅ GOTOWY
Główny moduł IoT – klasa `iot(wx.Frame)`.
- Trzy `wx.GridBagSizer`: `subSizer_devices`, `subSizer_capabilities`, `subSizer_values`
- `_show_panel()` przełącza widoczność sizerów i resetuje stan skanowania
- `_fill_capabilities_panel()` i `_fill_values_panel()` podmienia przyciski dynamicznie
- `_handleLabel()` obsługuje logikę nawigacji i API calls
- `_speak()` – odtwarzanie dźwięków z automatycznym decode bytes→unicode i fallback milena_say
- `_goBack()` – nawigacja wstecz przez plansze

### `iot_client.py` ✅ GOTOWY
Klient HTTP do AAC IoT Hub API (Python 2.7, `urllib2`).
- TIMEOUT = 10s
- Logi do `iot.log` przez moduł `logging`
- `_put()` – retry 3x przy HTTP 500 z 1s przerwą
- `discover_devices()` – timeout 30s, retry 3x w `createGui`
- Funkcje: `discover_devices`, `get_devices`, `get_capabilities`, `control_device`, `device_effect`, `stop_effect`, `reset_device`

**Poprawny format API (odkryty podczas implementacji):**
- control: `{"properties": {"power": "toggle"}}` (nie `{"property":..., "value":...}`)
- effect: `{"effect_name": "disco"}` (nie `{"effect":...}`)
- stop effect: `POST /effect/stop` (osobny endpoint)
- reset: `{"properties": {"power": "on", "brightness": 100, "temperature": "warm"}}`

### `generate_icons.py` ✅ GOTOWY
Skrypt Python 3 generujący ikony PIL/Pillow. Generować pojedyncze ikony przez inline script, nie przez uruchomienie całego pliku (by nie nadpisać ręcznych poprawek).

### `icons/iot/` ✅ GOTOWY
28 ikon 200×200 RGBA. Dodana `reset.png` (okrągła strzałka).

### `sounds/iot/` ✅ GOTOWY (częściowo)
Nagrane pliki .ogg. Mapowanie nazwa_klucza → nazwa_pliku (uwaga na rozbieżności):

| Klucz w kodzie | Plik na dysku |
|----------------|---------------|
| `effects` | `efekty.ogg` |
| `rainbow` | `efekt_teczy.ogg` |
| `stop` | `zatrzymaj.ogg` |
| device_id żarówki | `swiatlo.ogg` |
| pozostałe | zgodne z nazwą klucza |

### `ap.py` ✅ ZMODYFIKOWANY (6 miejsc)
1. Import: `from modules import iot`
2. Etykieta: `PUSTE` → `IOT`
3. Ładowanie `iotSound` (try/except, fallback milena)
4. Ikona: `puste.png` → `iot.png`
5. `onPress`: obsługa `label == 'IOT'`
6. `timerUpdate`: odczyt `iotSound` przy skanowaniu

### `iot.log` ✅ TWORZONY AUTOMATYCZNIE
Plik logów w `/home/radoslaw/Assistive-Prototypes/iot.log`.
Format: `YYYY-MM-DD HH:MM:SS LEVEL REQUEST/RESPONSE/ERROR/RETRY ...`

---

## Obsługa błędów

### Zasada ogólna
Każdy błąd komunikacji z API:
1. `_speak_error()` – odczytaj komunikat głosowy przez milena_say
2. Przy błędzie sterowania: zostań na aktualnej planszy (user może spróbować ponownie)
3. Przy błędzie krytycznym (hub niedostępny): `onExit()` z powrotem do menu AP

### Retry
- Discovery przy starcie: 3 próby z 2s przerwą (błąd połączenia) + 3 próby z 2s (brak urządzeń)
- `_put()`: 3 próby z 1s przerwą przy HTTP 500

### Scenariusze
| Błąd | Zachowanie |
|------|-----------|
| Hub niedostępny przy starcie | 3 retry → milena_say błąd → onExit() |
| Brak urządzeń | 3 retry discovery → milena_say brak urządzeń → onExit() |
| Błąd capabilities | milena_say błąd → zostań na planszy urządzeń |
| Błąd sterowania | milena_say błąd → zostań na aktualnej planszy |
| HTTP 500 (żarówka chwilowo niedostępna) | auto-retry 3x → jeśli nadal błąd → milena_say |

---

## Status implementacji

### ✅ Ukończone
- Faza 1: Ikony (28 ikon + reset.png)
- Faza 2: Klient API z logowaniem i retry
- Faza 3: Moduł iot.py (plansze, skanowanie, dźwięki, nawigacja)
- Faza 4: Integracja z ap.py
- Faza 5: Katalog sounds/iot/ z nagraniami

### ✅ Naprawione błędy podczas implementacji
- Błędny format API: `property/value` → `properties: {prop: value}`
- Błędny format effect: `effect` → `effect_name`
- Brak endpointu stop: `control power=on` → `POST /effect/stop`
- Timeout za krótki: 3s → 10s
- Brak retry przy HTTP 500
- Rozbieżności nazw plików .ogg (efekty.ogg, efekt_teczy.ogg, zatrzymaj.ogg, swiatlo.ogg)
- `label` jako bytes w Python 2.7 – decode przed użyciem w SOUND_MAP
- `reset` nie pojawiał się – dodany warunek `cap == 'reset' or cap in capabilities`
- Dźwięk `puste` po wyborze pustego slotu

### 🔲 Do przetestowania (Faza 6)
- T6.1 Pełna ścieżka: Menu → IOT → żarówka → zasilanie → powrót → kolor → czerwony → powrót → Menu
- T6.2 Pełna ścieżka z efektem: Menu → IOT → żarówka → efekt → disco → stop → powrót → Menu
- T6.3 Uśpienie na każdej planszy
- T6.4 Wyłączenie huba w trakcie działania → obsługa błędu → powrót do menu
- T6.5 Reset żarówki do domyślnych
- T6.6 Temperatura po ustawieniu koloru

---

## Szybkie przywrócenie kontekstu

1. Przeczytaj ten plik
2. Sprawdź działający hub: `curl http://localhost:8765/api/v1/devices`
3. Przeczytaj `modules/iot.py` i `iot_client.py`
4. Wzorce kodu: `modules/radio.py` (GridBagSizer, plansze), `modules/exercise.py` (back button jako ostatni wiersz, scope jako tuple)
5. Logi bieżące: `tail -f iot.log`
