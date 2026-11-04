# -*- coding: utf-8 -*-
"""Klient HTTP serwera gry (repo ap-gra: kontener Docker, port 8766).

API: github.com/jgrynczewski/ap-gra, docs/api.md. Serwer niczego nie
pamieta - stan gry ("state") trzyma klient: zapis w ~/.ap-gra/zapis.json
(po kazdym wyborze), razem z odkrytymi zakonczeniami; kazda gra osobno
(save_file). Gra wybierana parametrem game (domyslnie Tajemnica zegara).

Nagrania narratora (WAV) pobierane z serwera do ~/.ap-gra/nagrania/ -
nazwa pliku zalezy od tekstu i glosu, wiec raz pobrane nie starzeja sie.

Bledy: GraError(kind)
  'offline' - serwer gry nie odpowiada (kontener nie dziala)
  'state'   - zapis nie pasuje do scenariusza (np. po aktualizacji gry)
  'server'  - inny blad (szczegoly w gra.log)
"""

import os
import json
import logging
import urllib2

BASE_URL = 'http://localhost:8766'
TIMEOUT = 10

AP_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(AP_DIR, 'gra.log')
DATA_DIR = os.path.join(os.path.expanduser('~'), '.ap-gra')
SAVE_FILE = os.path.join(DATA_DIR, 'zapis.json')
AUDIO_DIR = os.path.join(DATA_DIR, 'nagrania')

_log = logging.getLogger('gra')
if not _log.handlers:
    _handler = logging.FileHandler(LOG_FILE)
    _handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s',
                                            '%Y-%m-%d %H:%M:%S'))
    _log.addHandler(_handler)
    _log.setLevel(logging.INFO)


class GraError(Exception):
    def __init__(self, kind, message=''):
        Exception.__init__(self, message)
        self.kind = kind
        self.message = message


def _request(method, path, body=None):
    url = BASE_URL + path
    data = json.dumps(body) if body is not None else None
    request = urllib2.Request(url, data, {'Content-Type': 'application/json'})
    request.get_method = lambda: method
    try:
        response = urllib2.urlopen(request, timeout=TIMEOUT)
        return json.loads(response.read())
    except urllib2.HTTPError as e:
        try:
            error = json.loads(e.read()).get('error', '')
        except Exception:
            error = ''
        _log.error('%s %s -> HTTP %s %s', method, url, e.code, error)
        if e.code == 400:
            raise GraError('state', error)
        raise GraError('server', 'HTTP %s' % e.code)
    except Exception as e:  # URLError, timeout, socket
        _log.error('%s %s -> %r', method, url, e)
        raise GraError('offline', str(e))


#-----------------------------------------------------------------------------
# Gry na serwerze: identyfikator = nazwa scenariusza (scenariusz/<id>.md w ap-gra)
DEFAULT_GAME = 'sala_pod_zegarem'   # Tajemnica zegara


def _path(path, game):
    return '%s?game=%s' % (path, game or DEFAULT_GAME)


def health(game=None):
    """{"ok", "title", "endings", "recordings", "interface"}"""
    return _request('GET', _path('/v1/health', game))


def start(game=None):
    return _request('POST', _path('/v1/start', game), {})


def view(state, game=None):
    """Widok sceny z zapisu (Kontynuuj)."""
    return _request('POST', _path('/v1/view', game), {'state': state})


def choose(state, number, game=None):
    return _request('POST', _path('/v1/choose', game), {'state': state, 'option': number})


#-----------------------------------------------------------------------------
def audio_file(audio):
    """Lokalna sciezka nagrania ({"url", "duration"} z widoku) albo None.
    Pobiera, jesli jeszcze go nie ma. Wywolywac poza watkiem GUI."""
    if not audio:
        return None
    name = str(audio['url'].rsplit('/', 1)[-1])  # <skrot>.wav - ASCII; str dla pygame
    path = os.path.join(AUDIO_DIR, name)
    if os.path.exists(path):
        return path
    try:
        if not os.path.isdir(AUDIO_DIR):
            os.makedirs(AUDIO_DIR)
        data = urllib2.urlopen(BASE_URL + audio['url'], timeout=TIMEOUT).read()
        partial = path + '.part'
        with open(partial, 'wb') as f:
            f.write(data)
        os.rename(partial, path)
        return path
    except Exception as e:
        _log.error('nagranie %s -> %r', audio['url'], e)
        return None


#-----------------------------------------------------------------------------
def save_file(game=None):
    """Zapis osobno dla kazdej gry; Tajemnica zegara - dawny zapis.json."""
    game = game or DEFAULT_GAME
    if game == DEFAULT_GAME:
        return SAVE_FILE
    return os.path.join(DATA_DIR, 'zapis_%s.json' % game)


def load_save(game=None):
    """{"state": {...} | None, "endings": [id, ...]} - pusty, gdy brak zapisu."""
    try:
        with open(save_file(game)) as f:
            save = json.load(f)
        return {'state': save.get('state'), 'endings': list(save.get('endings', []))}
    except (IOError, ValueError):
        return {'state': None, 'endings': []}


def write_save(save, game=None):
    path = save_file(game)
    try:
        if not os.path.isdir(DATA_DIR):
            os.makedirs(DATA_DIR)
        partial = path + '.part'
        with open(partial, 'w') as f:
            json.dump(save, f)
        os.rename(partial, path)
    except (IOError, OSError) as e:
        _log.error('zapis gry: %r', e)
