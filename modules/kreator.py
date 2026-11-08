#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""Plansza rozmowy z AI o nowej grze (kreator gier, repo ap-gra:
docs/kreator-gier.md). Wejscie: STWÓRZ GRĘ na planszy GRY PRZYGODOWE.

Ekran jak w grze (gra.NarratedBoard): u gory pytanie AI czytane glosem
narratora, pod nim odpowiedzi (2-3 od AI i "Inne propozycje"), na dole
WRÓĆ i PRZERWIJ. Na koncu AI czyta streszczenie pomyslu: ROZPOCZNIJ (gra
tworzy sie w tle - kilkanascie minut) albo INNY POMYSŁ.

AP nie czeka na AI: odpowiedz wraca od razu ze stanem "mysli", plansza mowi
"Myślę..." i co sekunde pyta kreator o stan (kreator_client). WRÓĆ nie pyta
AI - kreator pokazuje poprzednie pytanie od razu. Cala rozmowa jest zapisana
w logu kreatora (dane/rozmowy/<id>/log.jsonl w ap-gra).
"""

import os, sys, logging

import wx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kreator_client
from modules import board, gra
from modules.board import say, resume

_log = logging.getLogger('gra')

POLL = 1000            # [ms] co ile pytac kreator o stan, gdy AI mysli
MAX_POLL_ERRORS = 10   # tyle nieudanych pytan pod rzad - kreator przestal dzialac

# Stany rozmowy (kreator/rozmowa.py w ap-gra)
MYSLI, PYTANIE, PODSUMOWANIE, BLAD = 'mysli', 'pytanie', 'podsumowanie', 'blad'
PRZERWANA, ZATWIERDZONA = 'przerwana', 'zatwierdzona'


def error_text(error):
    if error.kind == 'offline':
        return u'Tworzenie gier nie jest uruchomione.'
    return u'Wystąpił błąd tworzenia gry.'


def open_kreator(parent):
    """STWÓRZ GRĘ: sprawdz kreator, pobierz nagrania przyciskow, pokaz plansze
    rozmowy. parent.stoper jest zatrzymany przez wywolujacego."""

    def load():
        health = kreator_client.health()
        for item in health.get('interface', {}).values():
            item['path'] = kreator_client.audio_file(item.get('audio'))
        return health

    def on_success(health):
        if not health.get('ai'):
            # Brak klucza API w .env na tym komputerze (ap-gra, docs/kreator-gier.md)
            say(u'Tworzenie gier nie jest jeszcze włączone.')
            resume(parent)
            return
        ConversationBoard(parent, health).Show(True)
        parent.Hide()

    def on_error(e):
        say(error_text(e))
        resume(parent)

    gra.run_in_thread(load, on_success, on_error)


def prepare(view):
    """W watku: nagrania pytania i odpowiedzi (dopisuje 'path')."""
    view['path'] = kreator_client.audio_file(view.get('audio'))
    for option in view.get('opcje', []):
        option['path'] = kreator_client.audio_file(option.get('audio'))
    return view


#=============================================================================
class ConversationBoard(gra.NarratedBoard):

    title = 'AP Nowa gra'

    def __init__(self, parent, health):
        self.cid = None          # identyfikator rozmowy w kreatorze
        self.view = None
        self.shown = None        # (status, tekst) pokazane na ekranie
        self.seq = 0             # rosnie przy kazdym zapytaniu - stare odpowiedzi pomijane
        self.polling = False
        self.pollErrors = 0

        gra.NarratedBoard.__init__(self, parent, health.get('interface', {}),
                                   [('WROC', 'wroc'), ('PRZERWIJ', 'przerwij'),
                                    ('WYBRALES', 'wybrales'), ('MYSLE', 'mysle'),
                                    ('BLAD', 'blad'), ('TWORZE', 'tworze')])
        self.poller = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._poll, self.poller)

        self.setButtons([], ['PRZERWIJ'])
        self._showThinking(False)
        self.request(kreator_client.start)

    def bottomButtons(self):
        return [{'key': 'WROC', 'text': u'WRÓĆ'}, {'key': 'PRZERWIJ', 'text': u'PRZERWIJ'}]

    #-------------------------------------------------------------------------
    def _bottom(self, canGoBack):
        return (['WROC'] if canGoBack else []) + ['PRZERWIJ']

    def _line(self, key, fallback):
        """Segment tekstu ze stalego przycisku kreatora (nagranie albo milena)."""
        text = self.speech.get(key) or fallback
        return (u'', text, self.voicePaths.get(key), self.voiceDurations.get(key))

    def _showThinking(self, canGoBack):
        self.setButtons([], self._bottom(canGoBack))
        self.setSegments([self._line('MYSLE', u'Myślę...')])
        self.startReading()

    def apply(self, view):
        """Pokaz stan rozmowy z kreatora."""
        self.view = view
        self.cid = view['id']
        status = view['status']
        if status == MYSLI:
            if self.shown != (MYSLI, view['mozna_wrocic']):  # "Myślę..." czytane raz
                self.shown = (MYSLI, view['mozna_wrocic'])
                self._showThinking(view['mozna_wrocic'])
            if not self.poller.IsRunning():
                self.poller.Start(POLL)
            return
        self.poller.Stop()
        if (status, view['tekst']) == self.shown:
            return
        self.shown = (status, view['tekst'])
        if status in (PYTANIE, PODSUMOWANIE):
            options = [('OPCJA%d' % o['numer'], o['tekst'], o.get('path'),
                        (o.get('audio') or {}).get('duration'))
                       for o in view['opcje']]
            self.setButtons(options, self._bottom(view['mozna_wrocic']))
            self.setSegments([(u'', view['tekst'], view.get('path'),
                               (view.get('audio') or {}).get('duration'))])
            self.startReading()
        elif status == BLAD:
            self.setButtons([], self._bottom(view['mozna_wrocic']))
            self.setSegments([self._line('BLAD', u'Coś poszło nie tak. Wróć albo przerwij.')])
            self.startReading()
        elif status == ZATWIERDZONA:
            # Gra tworzy sie w tle - komunikat, potem powrot do planszy gier
            self.stopReading()
            self.setButtons([], [])
            self.setSegments([self._line('TWORZE', u'Tworzę grę.')])
            delay = self._speak('TWORZE')
            self.text.show(len(self.text.text))
            self.busy = True
            self.later = wx.CallLater(int(delay * 1000) + 500, self.onExit)
        else:  # PRZERWANA
            self.onExit()

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
                self.request(lambda: kreator_client.state(self.cid))
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

        gra.run_in_thread(lambda: prepare(kreator_client.state(cid)), on_success, on_error)

    #-------------------------------------------------------------------------
    def onSelect(self, key):
        if self.busy:
            return
        cid = self.cid
        if key == 'PRZERWIJ':
            self.poller.Stop()
            if cid:
                # Zapis przerwania w logu kreatora; blad (np. kreator nie dziala) nie zatrzymuje wyjscia
                gra.run_in_thread(lambda: kreator_client.stop(cid), lambda view: None, lambda e: None)
            self.onExit()
        elif key == 'WROC' and cid:
            self.shown = None
            self.request(lambda: kreator_client.back(cid))
        elif key.startswith('OPCJA') and cid:
            number = int(key[len('OPCJA'):])
            self._confirm(key, lambda: self.request(lambda: kreator_client.answer(cid, number)))

    def onExit(self):
        """Powrot na plansze GRY PRZYGODOWE - odswiezy liste (nowa gra w
        trakcie tworzenia) przy pokazaniu (przygody.AdventuresBoard.Show)."""
        if not self:
            return
        self.poller.Stop()
        gra.NarratedBoard.onExit(self)
