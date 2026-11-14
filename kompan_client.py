# -*- coding: utf-8 -*-
"""Klient HTTP Kompana (repo ap-gra: usluga ap-gra-kompan, port 8768;
docs/api.md -> "Kompan", docs/kompan.md).

Jak kreator_client: kazde zapytanie wraca od razu - AI pracuje w tle, a plansza
pyta co sekunde o stan (status "mysli" -> "pytanie" / "blad" / "limit").

Bledy: gra_client.GraError(kind) - 'offline' (Kompan nie dziala), 'state'
(zapytanie nie pasuje do stanu rozmowy, HTTP 409), 'server'.
"""

import gra_client
import kreator_client

BASE_URL = 'http://localhost:8768'


def _request(method, path, body=None):
    return kreator_client._request(method, path, body, BASE_URL)


def health():
    """{"ok", "ai", "nagrania", "interface", "ostatnia"} - ai: czy jest klucz
    API; ostatnia: {"id", "tytul", "etykieta", "audio"} albo None."""
    return _request('GET', '/v1/kompan/health')


def start():
    """Nowa rozmowa - stan (zwykle status "mysli")."""
    return _request('POST', '/v1/kompan/rozmowy')


def state(cid):
    return _request('GET', '/v1/kompan/rozmowy/%s' % cid)


def answer(cid, number):
    return _request('POST', '/v1/kompan/rozmowy/%s/odpowiedz' % cid, {'opcja': number})


def back(cid):
    return _request('POST', '/v1/kompan/rozmowy/%s/wroc' % cid)


def come_back(cid):
    """WRÓĆ DO ROZMOWY."""
    return _request('POST', '/v1/kompan/rozmowy/%s/powrot' % cid)


def leave(cid):
    """ZAKOŃCZ - tylko zapis w logu, rozmowa zostaje."""
    return _request('POST', '/v1/kompan/rozmowy/%s/wyjscie' % cid)


def notes():
    """CO O MNIE WIESZ: {"wpisy": [{"id", "tekst", "przypuszczenie", "audio"}]}."""
    return _request('GET', '/v1/kompan/notatki')


def remove_note(nid):
    """To nieprawda, usuń - zwraca liste jak notes()."""
    return _request('POST', '/v1/kompan/notatki/%s/usun' % nid)


def audio_file(audio):
    return gra_client.audio_file(audio, BASE_URL)
