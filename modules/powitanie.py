#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""Ekran powitalny "Co nowego" - przy starcie AP, zanim ruszy wlasciwe AP.

Plan i decyzje: ../ablelab-plany/watki/co-nowego.md. Ktore nowosci -
co_nowego.py (katalog AP), lista nowosci - co_nowego.json.

Prawdziwy preload: ap.py tworzy menu glowne, skanowanie i zwiastun
(Notifier - maile Kompana, filmy Wicero i co dojdzie) dopiero po START /
POMIŃ, wiec w trakcie nowosci nic sie nie naklada. Gdy nowosci nie ma -
AP startuje jak dawniej.

Ekran (uklad jak w grze i Kompanie - gra.NarratedBoard):
    tekst nowosci  - duzymi literami, wypisywany w takt czytania
                     ("Cześć! Są nowości w AP. Pierwsza z trzech:" + tekst)
    NASTĘPNA, POPRZEDNIA (nie przy pierwszej), POWTÓRZ, POMIŃ
    na koniec: "To już wszystkie nowości." - START, POPRZEDNIA
Czyta milena_say (na komputerze z AP: Piper, glos narratora gier -
../ablelab-plany/README.md -> "Glos AP"), bez serwera i internetu.
Nowosc jest uslyszana, gdy zostala przeczytana do konca; POMIŃ albo
wylaczenie AP - nieprzeczytane wracaja przy nastepnym starcie.

Test bez ap.py (z katalogu AP; pokazuje wszystkie nowosci z co_nowego.json,
nic nie zapisuje): python2.7 modules/powitanie.py
"""

import os, sys, time, threading, logging

import wx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import co_nowego
import wicero_client
from modules import gra
from modules.board import say

_log = logging.getLogger('powitanie')

MIN_FONT = 8


def features():
    """Funkcje tego komputera dla pola "wymaga" (nieznane - pokazujemy)."""
    return {'wicero': os.path.exists(wicero_client.TOKEN_FILE)}


def open_welcome(start, entries=None, mark=True):
    """Pokaz nowosci, potem start() - tworzy wlasciwe AP. Zwraca False, gdy
    ekranu nie ma (brak nowosci, blad) - wtedy wywolujacy sam robi start().
    entries / mark - do testu bez ap.py."""
    try:
        if entries is None:
            entries = co_nowego.pending(features())
        if not entries:
            return False
        if not os.path.exists('./.pathToAP'):  # Board czyta sciezke AP (ap.py ja zapisuje)
            return False
        WelcomeBoard(entries, start, mark).Show(True)
        return True
    except Exception as e:
        _log.exception('ekran powitalny: %r', e)
        return False


#=============================================================================
class WelcomeBoard(gra.NarratedBoard):

    title = 'AP Co nowego'

    def __init__(self, entries, start, mark=True):
        self.entries = entries
        self.start = start
        self.mark = mark
        self.index = 0
        self.speaking = False   # milena_say jeszcze mowi
        self.waitingDone = False  # tekst wypisany, czekamy na koniec mowy
        self.started = False
        gra.NarratedBoard.__init__(self, None, {}, [])

        bottom = self.bottomButtons()
        width = (self.winWidth - (len(bottom) + 1) * self.xBorder) / len(bottom) - 2 * self.xBorder
        font = self._fittingFont([button['text'] for button in bottom], width)
        for button in bottom:
            self.windows[button['key']].SetFont(font)

        self.showEntry()

    def bottomButtons(self):
        # speech - czytane przy skanowaniu (milena) i po "Twój wybór:"
        return [{'key': 'NASTEPNA', 'text': u'NASTĘPNA', 'speech': u'Następna'},
                {'key': 'POPRZEDNIA', 'text': u'POPRZEDNIA', 'speech': u'Poprzednia'},
                {'key': 'POWTORZ', 'text': u'POWTÓRZ', 'speech': u'Powtórz'},
                {'key': 'POMIN', 'text': u'POMIŃ', 'speech': u'Pomiń'},
                {'key': 'START', 'text': u'START', 'speech': u'Start'}]

    def createGui(self):
        gra.NarratedBoard.createGui(self)
        # Tekst nowosci wiekszy niz w grze (tam miesci sie dluga scena)
        self.text.baseSize = self.tableFontSize * 4 / 5
        self.text.font = self.text._font(self.text.baseSize)

    def _fittingFont(self, texts, width):
        """Jak w Kompanie: najwieksza czcionka, w ktorej napisy sie mieszcza."""
        dc = wx.ScreenDC()
        size = self.tableFontSize * 2 / 3
        while True:
            font = wx.Font(size, wx.SWISS, wx.NORMAL, wx.BOLD)
            dc.SetFont(font)
            if size <= MIN_FONT or max(dc.GetTextExtent(text)[0] for text in texts) <= width:
                return font
            size -= 1

    #-------------------------------------------------------------------------
    def atEnd(self):
        return self.index >= len(self.entries)

    def showEntry(self):
        if self.atEnd():
            self.setButtons([], ['START', 'POPRZEDNIA'])
            segments = [(u'', co_nowego.THE_END, None, None)]
        else:
            self.setButtons([], (['NASTEPNA'] + (['POPRZEDNIA'] if self.index else [])
                                 + ['POWTORZ', 'POMIN']))
            entry = self.entries[self.index]
            segments = [(u'', co_nowego.heading(self.index, len(self.entries)), None, None),
                        (u'\n\n', entry['tekst'], None, None)]
        self.setSegments(segments)
        self.startReading()

    #-------------------------------------------------------------------------
    # Czytanie mileną: NarratedBoard czyta tylko nagrania - tu tekst czyta
    # milena_say, a skanowanie rusza dopiero, gdy skonczy mowic

    def _playSegment(self, readId):
        if not self or readId != self.readId:
            return
        self.later = None
        before, text, path, duration = self.segments[self.segment]
        self.speaking = True

        def worker():
            say(text, wait=True)
            wx.CallAfter(self._spoken, readId)
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()

        self.segmentStart = time.time()
        self.segmentDuration = len(text) / gra.CHARS_PER_SECOND
        self.segmentFrom = self.typed + len(before)
        self.segmentTo = self.segmentFrom + len(text)
        self.typer.Start(gra.TYPE_TICK)
        self._type(None)

    def _type(self, event):
        # Nastepny segment dopiero po wypisaniu i po koncu mowy
        if self.speaking and self.segment >= 0 and self.segment < len(self.segments):
            elapsed = time.time() - self.segmentStart
            if elapsed >= self.segmentDuration:
                self.typer.Stop()
                self.typed = self.segmentTo
                self.text.show(self.typed)
                self.waitingDone = True
                return
        gra.NarratedBoard._type(self, event)

    def _spoken(self, readId):
        if not self or readId != self.readId:
            return
        self.speaking = False
        if self.waitingDone:
            self.waitingDone = False
            self._nextSegment(readId)

    def startReading(self):
        self.speaking = False
        self.waitingDone = False
        gra.NarratedBoard.startReading(self)

    def _doneReading(self):
        if not self.atEnd() and self.mark:
            co_nowego.mark_heard(self.entries[self.index]['id'])
        gra.NarratedBoard._doneReading(self)

    #-------------------------------------------------------------------------
    def onSelect(self, key):
        if self.busy:
            return
        if key == 'NASTEPNA':
            self._confirm(key, self._move(1))
        elif key == 'POPRZEDNIA':
            self._confirm(key, self._move(-1))
        elif key == 'POWTORZ':
            self._confirm(key, self.showEntry)
        elif key in ('POMIN', 'START'):
            self._confirm(key, self.onExit)

    def _move(self, step):
        def go():
            self.index = max(0, self.index + step)
            self.showEntry()
        return go

    def onExit(self):
        """Wlasciwe AP: najpierw nowe okno, potem zamkniecie tego - inaczej
        wx konczy program, gdy zniknie ostatnie okno."""
        if not self or self.started:
            return
        self.started = True
        self.stopReading()
        self.MakeModal(False)
        try:
            self.start()
        finally:
            self.Destroy()


if __name__ == '__main__':
    # Test bez ap.py - uruchamiac z katalogu AP: python2.7 modules/powitanie.py
    logging.basicConfig()
    app = wx.App(False)
    if not open_welcome(lambda: None, co_nowego.load_entries(), mark=False):
        print('Brak nowosci albo pliku .pathToAP (uruchom raz ap.py)')
    else:
        app.MainLoop()
