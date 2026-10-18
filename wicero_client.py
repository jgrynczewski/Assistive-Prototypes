# -*- coding: utf-8 -*-
"""Klient HTTP API Wicero (Cloud Functions) - ADR-0001 (docs/adr/0001-modul-wicero.md).

Dziala w Pythonie 2.7 (AP) i 3 (testy poza AP). Cala logika (kolejnosc
filmow, teksty do przeczytania, przypomnienia) jest po stronie serwera -
tutaj tylko zapytania i bledy.

Token kontaktu: plik .wicero_token w katalogu AP (jedna linia, z panelu
admina Wicero).

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

BASE_URL = 'https://europe-central2-wicero-d9a70.cloudfunctions.net'
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
    """[{'senderId', 'name', 'newCount', 'types': [{'type', 'label', 'newCount'}]}]
    posortowani po imieniu."""
    return _call('GET', 'contact_senders')['senders']


def get_messages(sender_id, material_type='youtube'):
    """Filmy nadawcy w kolejnosci playlisty. Kazdy element:
    {'connectionId', 'messageId', 'videoId', 'url', 'title', 'thumbnailUrl',
     'comment', 'senderName', 'status', 'isNew', 'say'}
    'say' - gotowy tekst dla milena_say na ekranie przed filmem."""
    return _call('GET', 'contact_messages',
                 params={'senderId': sender_id, 'type': material_type})['items']


def mark_opened(item):
    """Kontakt wszedl na ekran przed filmem."""
    return _call('POST', 'contact_message_event', body={
        'connectionId': item['connectionId'],
        'messageId': item['messageId'],
        'event': 'opened',
    })


def mark_viewed(item):
    """Kontakt obejrzal 85% filmu."""
    return _call('POST', 'contact_message_event', body={
        'connectionId': item['connectionId'],
        'messageId': item['messageId'],
        'event': 'viewed',
    })


def get_notifications(startup=False):
    """Lista tekstow do przeczytania teraz (moze byc pusta).
    startup=True przy starcie AP - wymusza przypomnienie o nieotwartych."""
    return _call('POST', 'contact_notifications', body={'startup': startup})['say']
