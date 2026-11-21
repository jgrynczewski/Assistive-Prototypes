# Telewizor - parowanie przy każdym starcie

**Utworzono:** 2026-11-21 · **Aktualizacja:** 2026-11-21 · **Kolejka:** `../ablelab-plany/README.md`
**Podsumowanie:** Moduł TV (`modules/tv.py` → `python3 controllers/tv/base.py <operacja>`, Samsung przez `samsungtvws`, port 8002) działa, ale po każdym włączeniu komputera pierwsza komenda wymaga zatwierdzenia parowania na telewizorze, a rodzice tego nie robią - więc dla użytkownika obsługa jest zablokowana. Użytkownik chce sam przełączać kanały (raport Kompana 2026-11-21).
**Gdzie jesteśmy:** przyczyna nieznana, trzy podejrzenia.
**Następny krok:** sprawdzenie 1 na komputerze z AP.

## Podejrzenia (od najbardziej prawdopodobnego)

1. **Ustawienie telewizora:** Ustawienia → Ogólne → Menedżer połączeń urządzeń zewnętrznych → Powiadomienie o dostępie - powinno być „Tylko za pierwszym razem” (nie „Za każdym razem”); na „Liście urządzeń” komputer z AP - „Zezwól”.
2. **Token w gicie:** `controllers/tv/tv-token.txt` jest w repo. Telewizor wydaje token, biblioteka go zapisuje, a `git pull` / `checkout` / `stash` może przywrócić stary. Poprawka: `git rm --cached controllers/tv/tv-token.txt`, wpis w `.gitignore`.
3. **Zmienny adres IP komputera** (DHCP) - telewizor może go brać za nowe urządzenie. Poprawka: stałe adresy w routerze dla komputera i telewizora (adres telewizora `192.168.100.134` jest wpisany w `base.py`).

## Sprawdzenie

1. `cd ~/Assistive-Prototypes && git status --short controllers/tv && ls -l --time-style=full-iso controllers/tv/` - czy token zmieniony / kiedy zapisany; plus ustawienie z punktu 1 w telewizorze
2. Po poprawce: restart komputera, komenda z planszy TV - bez pytania na telewizorze

## Później

- Telewizor jako umiejętność Kompana (ap-gra `docs/kompan-umiejetnosci.md`)
