#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""Plansza KOMPAN - rozmowa z AI na dowolny temat (repo ap-gra: usluga
ap-gra-kompan, docs/kompan.md). Wejscie: kafelek KOMPAN na planszy NOWE.

Ekran jak w grze (gra.NarratedBoard): u gory wypowiedz czytana glosem
narratora, pod nia 2-4 odpowiedzi od AI, na dole Blisko, Inne propozycje, Zmień
temat, WRÓĆ, ZAKOŃCZ. Pierwsze wejscie - od razu nowa rozmowa; potem najpierw
WRÓĆ DO ROZMOWY (z tematem) albo NOWA ROZMOWA.

Tak samo jak w rozmowie o grze (modules/kreator.py): AP nie czeka na AI, tylko
mowi "Myślę..." i co sekunde pyta o stan; WRÓĆ nie pyta AI. Inaczej niz tam:
rozmowa nie ma konca. ZAKOŃCZ znaczy "na razie wychodze", a rozmowa czeka na
serwerze, takze po restarcie. Calosc jest zapisana w logu na serwerze
(dane-kompan/rozmowy/<id>/log.jsonl w ap-gra).
"""

import os, sys, logging

import wx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kompan_client
from modules import board, gra
from modules.board import say, resume

_log = logging.getLogger('gra')

POLL = 1000            # [ms] co ile pytac o stan, gdy AI mysli
MAX_POLL_ERRORS = 10   # tyle nieudanych pytan pod rzad - Kompan przestal dzialac
MIN_FONT = 8

# Stany rozmowy (kompan/rozmowa.py w ap-gra)
MYSLI, PYTANIE, BLAD, LIMIT = 'mysli', 'pytanie', 'blad', 'limit'

# Stale odpowiedzi w dolnym rzedzie, w kolejnosci z serwera (pole "stale")
FIXED = ['BLISKO', 'INNE', 'ZMIEN']


def error_text(error):
    if error.kind == 'offline':
        return u'Kompan nie jest uruchomiony.'
    return u'Wystąpił błąd Kompana.'


def open_kompan(parent):
    """Kafelek KOMPAN: sprawdz serwer, pobierz nagrania przyciskow, pokaz
    plansze. parent.stoper jest zatrzymany przez wywolujacego."""

    def load():
        health = kompan_client.health()
        for item in health.get('interface', {}).values():
            item['path'] = kompan_client.audio_file(item.get('audio'))
        latest = health.get('ostatnia')
        if latest:
            latest['path'] = kompan_client.audio_file(latest.get('audio'))
        return health

    def on_success(health):
        if not health.get('ai'):
            # Brak klucza API w .env.kompan na tym komputerze (ap-gra, docs/kompan.md)
            say(u'Kompan nie jest jeszcze włączony.')
            resume(parent)
            return
        KompanBoard(parent, health).Show(True)
        parent.Hide()

    def on_error(e):
        say(error_text(e))
        resume(parent)

    gra.run_in_thread(load, on_success, on_error)


def prepare(view):
    """W watku: nagrania wypowiedzi i odpowiedzi (dopisuje 'path')."""
    view['path'] = kompan_client.audio_file(view.get('audio'))
    for option in view.get('opcje', []):
        option['path'] = kompan_client.audio_file(option.get('audio'))
    return view


#=============================================================================
class KompanBoard(gra.NarratedBoard):

    title = 'AP Kompan'

    def __init__(self, parent, health):
        self.latest = health.get('ostatnia')
        self.cid = None          # identyfikator rozmowy na serwerze
        self.shown = None        # (status, tekst) pokazane na ekranie
        self.numbers = {}        # klucz stalej odpowiedzi -> numer dla serwera
        self.seq = 0             # rosnie przy kazdym zapytaniu - stare odpowiedzi pomijane
        self.polling = False
        self.pollErrors = 0

        gra.NarratedBoard.__init__(self, parent, health.get('interface', {}),
                                   [('BLISKO', 'blisko'), ('INNE', 'inne_propozycje'),
                                    ('ZMIEN', 'zmien_temat'), ('WROC', 'wroc'),
                                    ('ZAKONCZ', 'zakoncz'), ('KOMPAN', 'kompan'),
                                    ('DO_ROZMOWY', 'wroc_do_rozmowy'), ('NOWA', 'nowa_rozmowa'),
                                    ('WYBRALES', 'wybrales'), ('MYSLE', 'mysle'),
                                    ('BLAD', 'blad'), ('LIMIT', 'limit')])
        self.poller = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._poll, self.poller)

        # Piec przyciskow w rzedzie: napisy musza sie zmiescic
        bottom = self.bottomButtons()
        width = (self.winWidth - (len(bottom) + 1) * self.xBorder) / len(bottom) - 2 * self.xBorder
        font = self._fittingFont([button['text'] for button in bottom], width)
        for button in bottom:
            self.windows[button['key']].SetFont(font)

        if self.latest:
            self.showEntry()
        else:
            self.setButtons([], ['ZAKONCZ'])
            self.request(kompan_client.start)

    def bottomButtons(self):
        return [{'key': 'BLISKO', 'text': u'Blisko'},
                {'key': 'INNE', 'text': u'Inne propozycje'},
                {'key': 'ZMIEN', 'text': u'Zmień temat'},
                {'key': 'WROC', 'text': u'WRÓĆ'},
                {'key': 'ZAKONCZ', 'text': u'ZAKOŃCZ'}]

    #-------------------------------------------------------------------------
    def _fittingFont(self, texts, width):
        """Najwieksza czcionka (do tej z gry), w ktorej wszystkie napisy maja
        najwyzej width pikseli: przycisk sam napisu nie zawinie."""
        dc = wx.ScreenDC()
        size = self.tableFontSize * 2 / 3
        while True:
            font = wx.Font(size, wx.SWISS, wx.NORMAL, wx.BOLD)
            dc.SetFont(font)
            if size <= MIN_FONT or max(dc.GetTextExtent(text)[0] for text in texts) <= width:
                return font
            size -= 1

    def setButtons(self, options, bottom):
        gra.NarratedBoard.setButtons(self, options, bottom)
        width = self.winWidth - 4 * self.xBorder
        for option, b in zip(options, self.optionWindows):
            b.SetFont(self._fittingFont([option[1]], width))
            b.Refresh()

    def _bottom(self, canGoBack):
        return (['WROC'] if canGoBack else []) + ['ZAKONCZ']

    def _line(self, key, fallback):
        """Segment tekstu ze stalego przycisku (nagranie albo milena)."""
        text = self.speech.get(key) or fallback
        return (u'', text, self.voicePaths.get(key), self.voiceDurations.get(key))

    def _showThinking(self, canGoBack):
        self.setButtons([], self._bottom(canGoBack))
        self.setSegments([self._line('MYSLE', u'Myślę...')])
        self.startReading()

    def showEntry(self):
        """Jest rozmowa, do ktorej mozna wrocic."""
        self.setButtons([('DO_ROZMOWY', self.latest['etykieta'], self.latest.get('path'),
                          (self.latest.get('audio') or {}).get('duration')),
                         self._interfaceOption('NOWA', u'Nowa rozmowa')],
                        ['ZAKONCZ'])
        self.setSegments([self._line('KOMPAN', u'Kompan')])
        self.startReading()

    def apply(self, view):
        """Pokaz stan rozmowy z serwera."""
        self.cid = view['id']
        status = view['status']
        canGoBack = view['mozna_wrocic']
        if status == MYSLI:
            if self.shown != (MYSLI, canGoBack):  # "Myślę..." czytane raz
                self.shown = (MYSLI, canGoBack)
                self._showThinking(canGoBack)
            if not self.poller.IsRunning():
                self.poller.Start(POLL)
            return
        self.poller.Stop()
        if (status, view['tekst']) == self.shown:
            return
        self.shown = (status, view['tekst'])
        if status == PYTANIE:
            # Rozmowa moze trwac godzinami, a kazde pytanie to nowe nagrania - w
            # pamieci tylko te z biezacego ekranu. Nic teraz nie gra (stopReading)
            self.sounds = {}
            self.numbers = dict((key, item['numer']) for key, item in zip(FIXED, view['stale']))
            options = [('OPCJA%d' % o['numer'], o['tekst'], o.get('path'),
                        (o.get('audio') or {}).get('duration'))
                       for o in view['opcje']]
            self.setButtons(options, FIXED + self._bottom(canGoBack))
            self.setSegments([(u'', view['tekst'], view.get('path'),
                               (view.get('audio') or {}).get('duration'))])
        elif status == LIMIT:
            self.setButtons([], ['ZAKONCZ'])
            self.setSegments([self._line('LIMIT', u'Na dziś muszę już kończyć. Wróćmy do tego jutro.')])
        else:  # BLAD
            self.setButtons([], self._bottom(canGoBack))
            self.setSegments([self._line('BLAD', u'Coś poszło nie tak. Wróć albo zakończ.')])
        self.startReading()

    #-------------------------------------------------------------------------
    def request(self, call):
        """call() -> stan rozmowy (w watku), potem apply."""
        if self.busy:
            return
        self.busy = True
        self.seq += 1
        seq = self.seq
        self.stopReading()

        def on_success(view):
            self.busy = False
            if self and seq == self.seq:
                self.apply(view)

        def on_error(e):
            self.busy = False
            if not self:
                return
            if e.kind == 'state' and self.cid:  # zapytanie nie pasowalo do stanu - pokaz aktualny
                self.shown = None
                self.request(lambda: kompan_client.state(self.cid))
            else:
                board.say_then(error_text(e), self.onExit)

        gra.run_in_thread(lambda: prepare(call()), on_success, on_error)

    def _poll(self, event):
        """AI mysli - czy jest juz odpowiedz?"""
        if self.polling or self.busy or not self.cid:
            return
        self.polling = True
        seq, cid = self.seq, self.cid

        def on_success(view):
            self.polling = False
            self.pollErrors = 0
            if self and seq == self.seq and view['status'] != MYSLI:
                self.stopReading()
                self.apply(view)

        def on_error(e):
            self.polling = False
            self.pollErrors += 1
            if self and self.pollErrors >= MAX_POLL_ERRORS:
                self.poller.Stop()
                board.say_then(error_text(e), self.onExit)

        gra.run_in_thread(lambda: prepare(kompan_client.state(cid)), on_success, on_error)

    #-------------------------------------------------------------------------
    def _answer(self, key, number):
        cid = self.cid
        self._confirm(key, lambda: self.request(lambda: kompan_client.answer(cid, number)))

    def onSelect(self, key):
        if self.busy:
            return
        cid = self.cid
        if key == 'ZAKONCZ':
            self.poller.Stop()
            if cid:
                # Zapis wyjscia w logu; blad (np. serwer nie dziala) nie zatrzymuje wyjscia
                gra.run_in_thread(lambda: kompan_client.leave(cid), lambda view: None, lambda e: None)
            self.onExit()
        elif key == 'DO_ROZMOWY':
            latest = self.latest['id']
            self._confirm(key, lambda: self.request(lambda: kompan_client.come_back(latest)))
        elif key == 'NOWA':
            self._confirm(key, lambda: self.request(kompan_client.start))
        elif key == 'WROC' and cid:
            self.shown = None
            self.request(lambda: kompan_client.back(cid))
        elif key in self.numbers and cid:
            self._answer(key, self.numbers[key])
        elif key.startswith('OPCJA') and cid:
            self._answer(key, int(key[len('OPCJA'):]))

    def onExit(self):
        """Powrot na plansze NOWE."""
        if not self:
            return
        self.poller.Stop()
        gra.NarratedBoard.onExit(self)
