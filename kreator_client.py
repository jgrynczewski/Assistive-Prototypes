# -*- coding: utf-8 -*-
"""Klient HTTP kreatora gier (repo ap-gra: usluga ap-gra-kreator, port 8767;
docs/api.md -> "Kreator gier", docs/kreator-gier.md).

Kazde zapytanie wraca od razu - AI pracuje w tle, a plansza rozmowy pyta
co sekunde o stan (status "mysli" -> "pytanie" / "podsumowanie" / ...).
Nagrania pytan pobiera gra_client.audio_file(audio, BASE_URL).

Bledy: gra_client.GraError(kind) - 'offline' (kreator nie dziala),
'state' (zapytanie nie pasuje do stanu rozmowy, HTTP 409), 'server'.
"""

import json
import logging
import urllib2

import gra_client

BASE_URL = 'http://localhost:8767'
TIMEOUT = 10

_log = logging.getLogger('gra')


def _request(method, path, body=None, base=BASE_URL):
    """base - inny serwer o tych samych zasadach (kompan_client)."""
    url = base + path
    data = json.dumps(body) if body is not None else ('{}' if method == 'POST' else None)
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
        if e.code == 409:
            raise gra_client.GraError('state', error)
        raise gra_client.GraError('server', 'HTTP %s' % e.code)
    except Exception as e:  # URLError, timeout, socket
        _log.error('%s %s -> %r', method, url, e)
        raise gra_client.GraError('offline', str(e))


def health():
    """{"ok", "ai", "nagrania", "interface"} - ai: czy jest klucz API."""
    return _request('GET', '/v1/kreator/health')


def start():
    """Nowa rozmowa - stan (zwykle status "mysli")."""
    return _request('POST', '/v1/kreator/rozmowy')


def state(cid):
    return _request('GET', '/v1/kreator/rozmowy/%s' % cid)


def answer(cid, number):
    return _request('POST', '/v1/kreator/rozmowy/%s/odpowiedz' % cid, {'opcja': number})


def back(cid):
    return _request('POST', '/v1/kreator/rozmowy/%s/wroc' % cid)


def stop(cid):
    return _request('POST', '/v1/kreator/rozmowy/%s/przerwij' % cid)


def games():
    """Gry z kreatora: [{"id", "gra", "tytul", "status", "krok", ...}] -
    status w_toku / gotowa / nieudana."""
    return _request('GET', '/v1/kreator/gry')['gry']


def audio_file(audio):
    return gra_client.audio_file(audio, BASE_URL)
