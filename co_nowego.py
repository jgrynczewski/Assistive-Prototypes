# -*- coding: utf-8 -*-
"""Co nowego - ktore nowosci pokazac przy starcie AP (ekran powitalny,
modules/powitanie.py). Sama logika, bez okien - testy: test_co_nowego.py.

Plan i decyzje: ../ablelab-plany/watki/co-nowego.md.

- Nowosci: co_nowego.json w repo (wpis: id, data RRRR-MM-DD, tekst,
  opcjonalnie wymaga - funkcja, ktorej dotyczy, np. "wicero").
- Uslyszane: ~/.ap/co_nowego_uslyszane.json na komputerze uzytkownika - lista
  id (nie numer wersji: po dlugiej przerwie przychodza wszystkie zalegle).
  Wpis jest uslyszany, gdy zostal przeczytany do konca.
- Pierwsze uruchomienie (brak pliku): wszystko starsze niz FRESH_DAYS dni
  oznaczone jako uslyszane - nowy uzytkownik nie dostaje historii projektu.
- Zaleglych TOO_MANY i wiecej (ktos bardzo dlugo nie korzystal): pokazujemy
  SHOW_WHEN_TOO_MANY najnowszych, a wszystkie zalegle oznaczamy jako uslyszane.
"""

import io, os, json, datetime, logging

_log = logging.getLogger('co_nowego')

AP_DIR = os.path.dirname(os.path.abspath(__file__))
ENTRIES_FILE = os.path.join(AP_DIR, 'co_nowego.json')
HEARD_FILE = os.path.join(os.path.expanduser('~'), '.ap', 'co_nowego_uslyszane.json')

FRESH_DAYS = 7
TOO_MANY = 25
SHOW_WHEN_TOO_MANY = 10


def _date(text):
    return datetime.datetime.strptime(text, '%Y-%m-%d').date()


def load_entries(path=ENTRIES_FILE):
    """Nowosci od najnowszej (przy tej samej dacie - pozniejsza w pliku pierwsza)."""
    with io.open(path, encoding='utf-8') as f:
        entries = json.load(f)
    numbered = list(enumerate(entries))
    numbered.sort(key=lambda item: (item[1]['data'], item[0]), reverse=True)
    return [entry for _, entry in numbered]


def load_heard(path=HEARD_FILE):
    """Zbior id uslyszanych albo None, gdy pliku nie ma (pierwsze uruchomienie)."""
    if not os.path.exists(path):
        return None
    with io.open(path, encoding='utf-8') as f:
        return set(json.load(f).get('uslyszane', []))


def save_heard(heard, path=HEARD_FILE):
    folder = os.path.dirname(path)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    temp = path + '.tmp'
    text = json.dumps({'uslyszane': sorted(heard)}, ensure_ascii=False, indent=1)
    if isinstance(text, bytes):  # Python 2: samo ASCII - str, a io.open chce unicode
        text = text.decode('utf-8')
    with io.open(temp, 'w', encoding='utf-8') as f:
        f.write(text)
    try:
        os.rename(temp, path)  # podmiana w calosci - wylaczenie w polowie nie psuje pliku
    except OSError:  # Windows (testy) - rename nie nadpisuje
        os.remove(path)
        os.rename(temp, path)


def available(entry, features):
    """Czy nowosc dotyczy tego komputera. features: {funkcja: bool};
    nieznana funkcja - pokazujemy."""
    need = entry.get('wymaga')
    return not need or features.get(need, True)


def select(entries, heard, features, today):
    """(do pokazania, uslyszane) - nowosci od najnowszej i zbior id
    uslyszanych do zapisania (pierwsze uruchomienie, 25+), albo None, gdy
    nic nie trzeba zapisywac."""
    entries = [e for e in entries if available(e, features)]
    save = None
    if heard is None:
        oldest = today - datetime.timedelta(days=FRESH_DAYS)
        heard = set(e['id'] for e in entries if _date(e['data']) < oldest)
        save = heard
    waiting = [e for e in entries if e['id'] not in heard]
    if len(waiting) >= TOO_MANY:
        save = heard | set(e['id'] for e in waiting)
        waiting = waiting[:SHOW_WHEN_TOO_MANY]
    return waiting, save


def pending(features, today=None, entries_file=ENTRIES_FILE, heard_file=HEARD_FILE):
    """Nowosci do pokazania przy starcie (zapisuje uslyszane, gdy trzeba).
    Blad czegokolwiek - pusta lista: AP ma wystartowac zawsze."""
    try:
        today = today or datetime.date.today()
        entries = load_entries(entries_file)
        waiting, save = select(entries, load_heard(heard_file), features, today)
        if save is not None:
            save_heard(save, heard_file)
        return waiting
    except Exception as e:
        _log.error('co nowego: %r', e)
        return []


def mark_heard(entry_id, heard_file=HEARD_FILE):
    """Nowosc przeczytana do konca."""
    try:
        heard = load_heard(heard_file) or set()
        if entry_id not in heard:
            heard.add(entry_id)
            save_heard(heard, heard_file)
    except Exception as e:
        _log.error('co nowego - zapis %s: %r', entry_id, e)


#-----------------------------------------------------------------------------
# Teksty ekranu powitalnego

ORDINALS = [u'Pierwsza', u'Druga', u'Trzecia', u'Czwarta', u'Piąta', u'Szósta', u'Siódma',
            u'Ósma', u'Dziewiąta', u'Dziesiąta', u'Jedenasta', u'Dwunasta', u'Trzynasta',
            u'Czternasta', u'Piętnasta', u'Szesnasta', u'Siedemnasta', u'Osiemnasta',
            u'Dziewiętnasta', u'Dwudziesta']
# Dopelniacz liczebnika: "z trzech", "z pięciu"
OF = [None, None, u'dwóch', u'trzech', u'czterech', u'pięciu', u'sześciu', u'siedmiu',
      u'ośmiu', u'dziewięciu', u'dziesięciu', u'jedenastu', u'dwunastu', u'trzynastu',
      u'czternastu', u'piętnastu', u'szesnastu', u'siedemnastu', u'osiemnastu',
      u'dziewiętnastu', u'dwudziestu']
UNITS_OF = [u'', u'jeden', u'dwóch', u'trzech', u'czterech']

GREETING_ONE = u'Cześć! Jest nowość w AP.'
GREETING_MANY = u'Cześć! Są nowości w AP.'
THE_END = u'To już wszystkie nowości.'


def _ordinal(n):
    if n <= 20:
        return ORDINALS[n - 1]
    return u'Dwudziesta ' + ORDINALS[n - 21].lower()


def _of(n):
    if n <= 20:
        return OF[n]
    return u'dwudziestu ' + UNITS_OF[n - 20]


def heading(index, total):
    """Tekst przed nowoscia: index od 0. Przy jednej nowosci - bez numeru."""
    if total == 1:
        return GREETING_ONE
    line = u'%s z %s:' % (_ordinal(index + 1), _of(total))
    if index == 0:
        return GREETING_MANY + u' ' + line
    return line
