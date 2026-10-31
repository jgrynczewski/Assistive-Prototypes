# -*- coding: utf-8 -*-
"""Klient HTTP API Wicero (Cloud Functions) - ADR-0001 (docs/adr/0001-modul-wicero.md),
model z ADR-0011 w repo wicero (docs/adr/0011-rownowazni-uzytkownicy.md).

Dziala w Pythonie 2.7 (AP) i 3 (testy poza AP). Cala logika (kolejnosc
filmow, teksty do przeczytania, przypomnienia) jest po stronie serwera -
tutaj tylko zapytania i bledy.

AP to urzadzenie konta Wicero - te same kontakty i historia co w aplikacji.
Token urzadzenia: plik .wicero_token w katalogu AP (jedna linia, z ekranu
"Urzadzenia" w aplikacji Wicero albo z panelu admina).

Bledy zglaszane jako WiceroError z polem kind:
  'offline' - brak internetu / serwer nie odpowiada
  'token'   - brak pliku tokenu albo serwer go nie uznal
  'server'  - inny blad serwera (szczegoly w wicero.log)
"""

import json
import logging
import os

try:  # Python 2.7 (AP)
    import urllib2 as _request
    from urllib import urlencode
except ImportError:  # Python 3 (testy)
    import urllib.request as _request
    from urllib.parse import urlencode

BASE_URL = 'https://europe-central2-wicero-d9a70.cloudfunctions.net/api'
# Pierwsze zapytanie po przerwie budzi funkcje (cold start, 2-5 s)
TIMEOUT = 20

AP_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(AP_DIR, '.wicero_token')
LOG_FILE = os.path.join(AP_DIR, 'wicero.log')

# Wlasny handler zamiast logging.basicConfig - basicConfig dziala tylko raz
# na proces, a iot_client.py juz go wywoluje (logi trafialyby do iot.log).
_log = logging.getLogger('wicero')
if not _log.handlers:
    _handler = logging.FileHandler(LOG_FILE)
    _handler.setFormatter(logging.Formatter(
        # PID - kilka procesow AP pisze do tego samego pliku (T10, BUG 2)
        '%(asctime)s [%(process)d] %(levelname)s %(message)s', '%Y-%m-%d %H:%M:%S'))
    _log.addHandler(_handler)
    _log.setLevel(logging.INFO)
    _log.propagate = False


class WiceroError(Exception):
    def __init__(self, kind, message):
        Exception.__init__(self, message)
        self.kind = kind
        self.message = message


def _token():
    try:
        with open(TOKEN_FILE, 'r') as f:
            token = f.read().strip()
    except IOError:
        token = ''
    if not token:
        raise WiceroError('token', 'Brak pliku .wicero_token')
    return token


def _call(method, endpoint, params=None, body=None):
    url = BASE_URL + '/' + endpoint
    if params:
        url += '?' + urlencode(params)
    data = json.dumps(body).encode('utf-8') if body is not None else None
    headers = {'Authorization': 'Bearer ' + _token()}
    if data is not None:
        headers['Content-Type'] = 'application/json'

    _log.info('REQUEST %s %s body=%s', method, url, json.dumps(body))
    req = _request.Request(url, data, headers)
    req.get_method = lambda: method
    try:
        response = _request.urlopen(req, timeout=TIMEOUT)
        result = json.loads(response.read().decode('utf-8'))
        _log.info('RESPONSE %s %s -> %s', method, endpoint, json.dumps(result))
        return result
    except _request.HTTPError as e:
        try:
            error = json.loads(e.read().decode('utf-8')).get('error', '')
        except Exception:
            error = ''
        _log.error('ERROR %s %s -> HTTP %d %s', method, endpoint, e.code, json.dumps(error))
        if e.code == 401:
            raise WiceroError('token', 'Nieprawidlowy token')
        raise WiceroError('server', 'HTTP %d' % e.code)
    except Exception as e:
        # URLError, timeout, SSL - z punktu widzenia uzytkownika: brak polaczenia
        _log.error('ERROR %s %s -> %r', method, endpoint, e)
        raise WiceroError('offline', 'Brak polaczenia')


def get_senders():
    """Rozmowy (kafle na planszy nadawcow), posortowane po nazwie:
    [{'conversationId', 'name', 'newCount', 'say',
      'types': [{'type', 'label', 'newCount', 'say'}]}]
    Takze dawne kontakty - historia zostaje (ADR-0011)."""
    return _call('GET', 'v1/conversations', params={'voice': 'pl'})['conversations']


def get_messages(conversation_id, material_type='youtube'):
    """Otrzymane filmy rozmowy w kolejnosci playlisty. Kazdy element:
    {'conversationId', 'messageId', 'videoId', 'url', 'title', 'thumbnailUrl',
     'comment', 'senderName', 'status', 'isNew', 'say'}
    'say' - gotowy tekst dla milena_say na ekranie przed filmem."""
    messages = _call('GET', 'v1/conversations/%s/messages' % conversation_id, params={
        'type': material_type, 'direction': 'in', 'order': 'playlist', 'voice': 'pl',
    })['messages']
    items = []
    for m in messages:
        item = dict(m)
        item.update(m['content'])  # videoId, url, title, thumbnailUrl
        items.append(item)
    return items


def _event(item, event):
    return _call('POST', 'v1/conversations/%s/messages/%s/events'
                 % (item['conversationId'], item['messageId']), body={'event': event})


def mark_opened(item):
    """Wejscie na ekran przed filmem."""
    return _event(item, 'opened')


def mark_viewed(item):
    """Obejrzane 85% filmu."""
    return _event(item, 'viewed')


def get_notifications(startup=False):
    """Lista tekstow do przeczytania teraz (moze byc pusta) - osobno dla
    kazdego urzadzenia. startup=True przy starcie AP - wymusza przypomnienie
    o nieotwartych."""
    return _call('POST', 'v1/notifications', body={'startup': startup})['say']
