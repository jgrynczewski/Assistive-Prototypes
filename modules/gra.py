#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""Modul Gra - gra przygodowa czytana na glos (repo ap-gra).

Serwer gry dziala w kontenerze Docker na tym komputerze (port 8766) -
tutaj tylko wyswietlanie, czytanie i skanowanie. Komunikacja:
gra_client.py (katalog AP).

Ekran (GameBoard):
    tekst sceny - wypisywany w takt czytania (nagrania narratora z serwera)
    z prawej    - scenka: zegar z wahadlem i krzatajace sie ludziki (modules/scenka.py)
    opcje 2-4   - szerokie przyciski jeden pod drugim
    POWTORZ / WYJDZ - w rzedzie pod opcjami
Skanowanie - po przyciskach od gory (jak ekran przed filmem w Wicero),
dopiero po przeczytaniu tekstu; po dwoch pustych przejsciach - uspienie.
Opcje i przyciski czyta glos narratora (nie milena).

Zapis gry (gra_client): po kazdej scenie; przy wejsciu, gdy jest zapis -
KONTYNUUJ / NOWA GRA.

Uruchomienie bez ap.py (z katalogu AP): python2.7 modules/gra.py
"""

import os, sys, time, threading, logging

import wx
from pygame import mixer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gra_client
from modules import board, scenka
from modules.board import say, resume

_log = logging.getLogger('gra')

MAX_OPTIONS = 4
LINE_PAUSE = 600            # [ms] przerwa miedzy liniami tekstu (jak miedzy zdaniami w nagraniu)
PARAGRAPH_PAUSE = 1000      # [ms] przed nowym akapitem
TYPE_TICK = 40              # [ms] krok wypisywania tekstu
CHARS_PER_SECOND = 14.0     # tempo wypisywania linii bez nagrania


#=============================================================================
def run_in_thread(target, on_success, on_error):
    """target() w watku; wynik / GraError do GUI przez wx.CallAfter."""
    def worker():
        try:
            result = target()
        except gra_client.GraError as e:
            wx.CallAfter(on_error, e)
            return
        except Exception as e:  # blad w kodzie - nie zostawiac AP bez odpowiedzi
            _log.exception('gra')
            wx.CallAfter(on_error, gra_client.GraError('server', repr(e)))
            return
        wx.CallAfter(on_success, result)
    t = threading.Thread(target=worker)
    t.daemon = True
    t.start()


def error_text(error):
    if error.kind == 'offline':
        return u'Gra nie jest uruchomiona.'
    return u'Wystąpił błąd gry.'


def open_gra(parent):
    """Wejscie z nowe.py: sprawdz serwer, pobierz nagrania przyciskow, pokaz gre.
    parent.stoper jest zatrzymany przez wywolujacego."""

    def load():
        health = gra_client.health()
        for item in health.get('interface', {}).values():
            item['path'] = gra_client.audio_file(item.get('audio'))
        return health

    def on_success(health):
        GameBoard(parent, health, gra_client.load_save()).Show(True)
        parent.Hide()

    def on_error(e):
        say(error_text(e))
        resume(parent)

    run_in_thread(load, on_success, on_error)


def prepare(view):
    """W watku: pobierz nagrania widoku; dopisz 'path' do kazdego 'audio'."""
    for item in view['lines'] + view['options']:
        item['path'] = gra_client.audio_file(item.get('audio'))
    ending = view.get('ending')
    if ending:
        ending['path'] = gra_client.audio_file(ending.get('audio'))
        ending['label_path'] = gra_client.audio_file(ending.get('label_audio'))
    return view


#=============================================================================
def wrap(dc, text, width):
    """Zawijanie wierszy z gory (a nie w trakcie wypisywania - slowa nie
    przeskakuja do nastepnej linii). Spacje -> nowe linie; dlugosc tekstu
    bez zmian, wiec pozycja wypisywania jest ta sama."""
    result = list(text)
    lineStart, lastSpace = 0, -1
    for i, ch in enumerate(text):
        if ch == u'\n':
            lineStart, lastSpace = i + 1, -1
            continue
        if ch == u' ':
            lastSpace = i
        if lastSpace > lineStart and dc.GetTextExtent(text[lineStart:i + 1])[0] > width:
            result[lastSpace] = u'\n'
            lineStart, lastSpace = lastSpace + 1, -1
    return u''.join(result)


class TextPanel(wx.Panel):
    """Tekst sceny rysowany recznie: przerwa miedzy akapitami = pol linii,
    wypisywanie po znaku (show), a gdy tekst sie nie miesci - mniejsza
    czcionka (najwyzej o MIN_SCALE). Caly tekst ma byc widoczny - limit
    dlugosci sceny pilnuje ap-gra (engine/screen.py), to tylko zabezpieczenie."""

    PARAGRAPH_GAP = 0.5
    MIN_SCALE = 0.7

    def __init__(self, parent, size, colour, background, margin):
        wx.Panel.__init__(self, parent, -1)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.baseSize = size
        self.colour = colour
        self.background = background
        self.margin = margin
        self.text = u''
        self.wrapped = u''
        self.typed = 0
        self.font = self._font(size)
        self.lineHeight = size
        self.Bind(wx.EVT_PAINT, self.onPaint)
        self.Bind(wx.EVT_SIZE, self.onSize)

    def _font(self, size):
        return wx.Font(size, wx.SWISS, wx.NORMAL, wx.NORMAL)

    def setText(self, text):
        self.text = text
        self.typed = 0
        self._fit()
        self.Refresh(False)

    def show(self, typed):
        """Pokaz pierwsze `typed` znakow tekstu."""
        self.typed = typed
        self.Refresh(False)

    def _height(self, wrapped, lineHeight):
        return sum(lineHeight * self.PARAGRAPH_GAP if line == u'' else lineHeight
                   for line in wrapped.split(u'\n'))

    def _fit(self):
        width, height = self.GetClientSize()
        width -= 2 * self.margin
        height -= 2 * self.margin
        if width <= 0 or height <= 0:
            self.wrapped = self.text
            return
        dc = wx.ClientDC(self)
        size = self.baseSize
        while True:
            font = self._font(size)
            dc.SetFont(font)
            wrapped = wrap(dc, self.text, width)
            lineHeight = int(dc.GetTextExtent(u'ĄŻgj')[1] * 1.1)
            if (self._height(wrapped, lineHeight) <= height
                    or size <= self.baseSize * self.MIN_SCALE):
                break
            size -= 1
        if size < self.baseSize:
            _log.warning('tekst nie miescil sie - czcionka %d zamiast %d', size, self.baseSize)
        self.font, self.wrapped, self.lineHeight = font, wrapped, lineHeight

    def onSize(self, event):
        self._fit()
        self.Refresh(False)
        event.Skip()

    def onPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        dc.SetBackground(wx.Brush(self.background))
        dc.Clear()
        dc.SetFont(self.font)
        dc.SetTextForeground(self.colour)
        y = self.margin
        for line in self.wrapped[:self.typed].split(u'\n'):
            if line == u'':
                y += int(self.lineHeight * self.PARAGRAPH_GAP)
            else:
                dc.DrawText(line, self.margin, y)
                y += self.lineHeight


#=============================================================================
class GameBoard(board.Board):

    columnsOnly = True
    title = 'AP Gra'

    def __init__(self, parent, health, save):
        self.health = health
        self.interface = health.get('interface', {})
        self.save = save
        self.view = None
        self.segments = []       # (przed, tekst, sciezka nagrania, dlugosc [s])
        self.readId = 0          # rosnie przy kazdym czytaniu - stare wywolania sie koncza
        self.later = None
        self.channel = None
        self.sounds = {}
        self.voicePaths = {}     # klucz przycisku -> nagranie
        self.busy = False

        buttons = [{'key': 'OPCJA%d' % i, 'text': u''} for i in range(1, MAX_OPTIONS + 1)]
        buttons += [
            {'key': 'POWTORZ', 'bitmap': 'icons/pilots/musicPilot/10_repeat.png'},
            {'key': 'WYJDZ', 'bitmap': 'icons/back.png'},
        ]
        board.Board.__init__(self, parent, buttons, rows=1, columns=len(buttons))
        self.stoper.Stop()  # skanowanie - dopiero po przeczytaniu tekstu

        self.typer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._type, self.typer)

        for key, name in (('POWTORZ', 'powtorz'), ('WYJDZ', 'wyjdz'),
                          ('KONTYNUUJ', 'kontynuuj'), ('NOWA_GRA', 'nowa_gra')):
            item = self.interface.get(name, {})
            self.voicePaths[key] = item.get('path')
            self.speech[key] = item.get('text')

        self.setSegments([])
        self.setButtons([], repeat=False)  # do czasu pobrania pierwszej sceny
        if self.save.get('state'):
            self.showMenu()
        else:
            self.newGame()

    #-------------------------------------------------------------------------
    def createGui(self):
        self.vbox = wx.BoxSizer(wx.VERTICAL)

        self.topPanel = wx.Panel(self, -1)
        self.topPanel.SetBackgroundColour(self.backgroundColour)
        self.text = TextPanel(self.topPanel, self.tableFontSize * 3 / 5, self.textColour,
                              self.backgroundColour, 2 * self.xBorder)
        # Z prawej scenka (zegar, ludziki) - ok. 1/3 szerokosci, rusza sie caly czas
        self.scenka = scenka.Scenka(self.topPanel)
        self.scenka.SetMinSize((self.winWidth / 3, -1))
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.text, 1, wx.EXPAND)
        box.Add(self.scenka, 0, wx.EXPAND)
        self.topPanel.SetSizer(box)
        # Tekst wyzszy niz opcje razem (6 : 4 + 1) - limit dlugosci sceny w ap-gra
        # (engine/screen.py) jest liczony dla tego ukladu
        self.vbox.Add(self.topPanel, 6, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, self.xBorder)

        font = wx.Font(self.tableFontSize * 2 / 3, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.windows = {}
        self.optionWindows = []
        for button in self.buttons[:MAX_OPTIONS]:
            b = self.makeButton(self, button, font)
            self.windows[button['key']] = b
            self.optionWindows.append(b)
            self.vbox.Add(b, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, self.xBorder)

        # POWTORZ / WYJDZ na cala szerokosc, ostatni przycisk dochodzi do prawego
        # marginesu jak w innych planszach - przy sterowaniu przelacznikiem kursor
        # myszy stoi w prawym dolnym rogu i klikniecie musi trafic w przycisk
        bottom = wx.BoxSizer(wx.HORIZONTAL)
        last = self.buttons[-1]['key']
        for button in self.buttons[MAX_OPTIONS:]:
            b = self.makeButton(self, button, font)
            self.windows[button['key']] = b
            bottom.Add(b, 1, wx.EXPAND | (0 if button['key'] == last else wx.RIGHT), self.xBorder)
        self.vbox.Add(bottom, 1, wx.EXPAND | wx.ALL, self.xBorder)

        self.buttonWindows = []
        self.SetSizer(self.vbox)

    #-------------------------------------------------------------------------
    def setButtons(self, options, repeat=True):
        """options: [(klucz, napis, nagranie)] - na przyciskach opcji, od gory.
        Skanowanie: opcje, potem POWTORZ (gdy repeat) i WYJDZ."""
        keys, windows = [], []
        for i, b in enumerate(self.optionWindows):
            if i < len(options):
                key, label, path = options[i]
                b.SetName(key)  # Board czyta przycisk po nazwie (_voice)
                b.SetLabel(label)
                self.speech[key] = label
                self.voicePaths[key] = path
                self.vbox.Show(b, True)
                keys.append(key)
                windows.append(b)
            else:
                self.vbox.Show(b, False)
        self.windows['POWTORZ'].Show(repeat)
        for key in (['POWTORZ'] if repeat else []) + ['WYJDZ']:
            keys.append(key)
            windows.append(self.windows[key])

        self.labels = keys
        self.buttonWindows = windows
        self.numberOfColumns = [len(keys)]
        self.maxColumns = [2 * len(keys)]
        self._clearHighlight()
        self.Layout()

    #-------------------------------------------------------------------------
    # Ekrany

    def showMenu(self):
        """Jest zapis gry: KONTYNUUJ / NOWA GRA."""
        title = self.health.get('title') or u''
        # Najpierw przyciski (uklad), potem tekst - dopasowanie tekstu do pola
        self.setButtons([('KONTYNUUJ', u'Kontynuuj', self.voicePaths.get('KONTYNUUJ')),
                         ('NOWA_GRA', u'Nowa gra', self.voicePaths.get('NOWA_GRA'))],
                        repeat=False)
        self.setSegments([(u'', title, None, 0), (u'\n\n', u'Masz zapisaną grę.', None, 0)])
        self.startReading()

    def newGame(self):
        if not self:  # okno zamkniete w trakcie komunikatu
            return
        self.save['state'] = None
        self.load(gra_client.start)

    def load(self, request):
        """request() -> widok (w watku), potem pokaz scene."""
        if self.busy:
            return
        self.busy = True
        self.stopReading()

        def on_success(view):
            self.busy = False
            if self:
                self.showView(view)

        def on_error(e):
            self.busy = False
            if not self:
                return
            if e.kind == 'state':  # zapis nie pasuje do nowej wersji gry
                self.save['state'] = None
                gra_client.write_save(self.save)
                board.say_then(u'Zapis gry nie pasuje do nowej wersji. Zaczynamy od początku.',
                               self.newGame)
            else:
                board.say_then(error_text(e), self.onExit)

        run_in_thread(lambda: prepare(request()), on_success, on_error)

    def showView(self, view):
        self.view = view
        ending = view.get('ending')

        if ending:
            self.save['state'] = None
            if ending['id'] not in self.save['endings']:
                self.save['endings'].append(ending['id'])
        else:
            self.save['state'] = view['state']
        gra_client.write_save(self.save)

        segments = [(line['before'], line['text'], line.get('path'),
                     (line.get('audio') or {}).get('duration'))
                    for line in view['lines']]
        if ending:
            found = len(self.save['endings'])
            segments += [
                (u'\n\n', ending['title'], ending.get('path'),
                 (ending.get('audio') or {}).get('duration')),
                (u'\n', ending['label'], ending.get('label_path'),
                 (ending.get('label_audio') or {}).get('duration')),
                (u'\n', u'Odkryte zakończenia: %d z %d.' % (found, ending['total']), None, 0),
            ]
            options = [('NOWA_GRA', u'Nowa gra', self.voicePaths.get('NOWA_GRA'))]
        else:
            options = [('OPCJA%d' % o['number'], o['text'], o.get('path'))
                       for o in view['options']]
        self.setButtons(options)  # najpierw uklad, potem dopasowanie tekstu
        self.setSegments(segments)
        self.startReading()

    #-------------------------------------------------------------------------
    # Czytanie i wypisywanie tekstu

    def setSegments(self, segments):
        self.segments = segments
        self.text.setText(u''.join(before + text for before, text, path, duration in segments))

    def startReading(self):
        """Tekst od poczatku, w takt nagran; potem skanowanie."""
        self.stopReading()
        self.readId += 1
        self.segment = -1
        self.typed = 0        # ile znakow tekstu juz wypisane
        self.text.show(0)
        self._nextSegment(self.readId)

    def stopReading(self):
        self.readId += 1
        self.stoper.Stop()
        self.typer.Stop()
        if self.later:
            self.later.Stop()
            self.later = None
        self._stopVoice()
        self._clearHighlight()

    def _nextSegment(self, readId):
        if not self or readId != self.readId:
            return
        self.segment += 1
        if self.segment >= len(self.segments):
            self._doneReading()
            return
        before = self.segments[self.segment][0]
        pause = 0 if self.segment == 0 else (PARAGRAPH_PAUSE if before == u'\n\n' else LINE_PAUSE)
        if self.segments[self.segment][2] is None and not self.segments[self.segment][3]:
            pause = 0  # tekst bez czytania (np. "Masz zapisaną grę.") - od razu
        self.later = wx.CallLater(max(pause, 1), self._playSegment, readId)

    def _playSegment(self, readId):
        if not self or readId != self.readId:
            return
        self.later = None
        before, text, path, duration = self.segments[self.segment]
        if path:
            self._play(path)
        if not duration:
            duration = len(text) / CHARS_PER_SECOND if path else 0
        self.segmentStart = time.time()
        self.segmentDuration = duration
        self.segmentFrom = self.typed + len(before)
        self.segmentTo = self.segmentFrom + len(text)
        self.typer.Start(TYPE_TICK)
        self._type(None)

    def _type(self, event):
        if not self or self.segment < 0 or self.segment >= len(self.segments):
            self.typer.Stop()
            return
        elapsed = time.time() - self.segmentStart
        done = self.segmentDuration <= 0 or elapsed >= self.segmentDuration
        if done:
            position = self.segmentTo
        else:
            fraction = elapsed / self.segmentDuration
            position = self.segmentFrom + int((self.segmentTo - self.segmentFrom) * fraction)
        if position != self.typed or done:
            self.typed = position
            self.text.show(position)
        if done:
            self.typer.Stop()
            self._nextSegment(self.readId)

    def _doneReading(self):
        self.resetScanning()
        resume(self)

    #-------------------------------------------------------------------------
    # Dzwiek

    def _sound(self, path):
        if path not in self.sounds:
            try:
                self.sounds[path] = mixer.Sound(path)
            except Exception as e:
                _log.error('nagranie %s: %r', path, e)
                self.sounds[path] = None
        return self.sounds[path]

    def _play(self, path):
        self._stopVoice()
        sound = self._sound(path)
        if sound is None:
            return False
        self.channel = sound.play()
        return True

    def _stopVoice(self):
        if self.channel is not None:
            self.channel.stop()
            self.channel = None

    def _voice(self, name):
        """Przycisk przy skanowaniu - glosem narratora; bez nagrania - milena."""
        path = self.voicePaths.get(name)
        if path and self._play(path):
            return
        if self.speech.get(name):
            say(self.speech[name])

    #-------------------------------------------------------------------------
    def onSelect(self, key):
        if self.busy:
            return
        if key == 'POWTORZ':
            self.startReading()
        elif key == 'WYJDZ':
            self.onExit()
        elif key == 'KONTYNUUJ':
            state = self.save['state']
            self.load(lambda: gra_client.view(state))
        elif key == 'NOWA_GRA':
            self.newGame()
        elif key.startswith('OPCJA'):
            state = self.view['state']
            number = int(key[len('OPCJA'):])
            self.load(lambda: gra_client.choose(state, number))

    def onExit(self):
        if not self:
            return
        self.stopReading()
        self.scenka.stop()
        board.Board.onExit(self)


#=============================================================================
class _Standalone(wx.Frame):
    """Rodzic zastepujacy nowe.py przy samodzielnym uruchomieniu.
    Powrot do rodzica (Show / stoper.Start) konczy program."""

    control = 'switch'
    timeGap = 1000

    def __init__(self):
        wx.Frame.__init__(self, None, -1, 'AP Gra (test)')
        self.stoper = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, lambda event: self.Destroy(), self.stoper)

    def Show(self, show=True):
        if show:
            wx.CallAfter(self.Destroy)
        return True


if __name__ == '__main__':
    # Test modulu bez ap.py / nowe.py - uruchamiac z katalogu AP:
    #     python2.7 modules/gra.py
    app = wx.App(False)
    open_gra(_Standalone())
    app.MainLoop()
