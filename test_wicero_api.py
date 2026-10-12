#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""Test polaczenia z API Wicero - uruchomic jako pierwszy na komputerze uzytkownika.

    python2.7 test_wicero_api.py                 # tylko odczyt: nadawcy i filmy
    python2.7 test_wicero_api.py --notifications # + ogloszenia (oznacza filmy jako ogloszone!)
    python2.7 test_wicero_api.py --open          # + oznacza pierwszy film jako otwarty

Wymaga pliku .wicero_token w katalogu AP. Logi: wicero.log.
Dziala tez w Pythonie 3.
"""

from __future__ import print_function

import ssl
import sys

import wicero_client


def show(text):
    # Python 2: unicode do terminala UTF-8
    if sys.version_info[0] == 2 and isinstance(text, unicode):  # noqa: F821
        text = text.encode('utf-8')
    print(text)


def main():
    show('Python %s, %s' % (sys.version.split()[0], ssl.OPENSSL_VERSION))
    show('API: %s' % wicero_client.BASE_URL)

    try:
        senders = wicero_client.get_senders()
    except wicero_client.WiceroError as e:
        show('BLAD (%s): %s - szczegoly w wicero.log' % (e.kind, e.message))
        return 1

    show('\nNadawcy: %d' % len(senders))
    for s in senders:
        show(u'  %s - nowe: %d (%s)' % (s['name'], s['newCount'], s['senderId']))

    if not senders:
        show('Brak nadawcow - kontakt nie ma zaakceptowanych polaczen.')
        return 0

    first = senders[0]
    items = wicero_client.get_messages(first['senderId'])
    show(u'\nFilmy od %s: %d' % (first['name'], len(items)))
    for item in items:
        show(u'  [%s%s] %s' % (item['status'], ', nowy' if item['isNew'] else '', item['title']))
        show(u'      say: %s' % item['say'])

    if '--open' in sys.argv and items:
        wicero_client.mark_opened(items[0])
        show(u'\nOznaczono jako otwarty: %s' % items[0]['title'])

    if '--notifications' in sys.argv:
        say = wicero_client.get_notifications(startup=True)
        show('\nDo ogloszenia: %d' % len(say))
        for text in say:
            show(u'  %s' % text)

    show('\nOK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
