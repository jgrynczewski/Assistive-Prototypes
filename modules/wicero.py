#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""Modul Wicero - filmy od bliskich (ADR-0001: docs/adr/0001-modul-wicero.md).

Nawigacja:
    nowe.py [WICERO] -> SendersBoard (nadawcy) -> TypesBoard (FILMY)
        -> IntroScreen (komentarz, POWTORZ / START / POWROT) -> WiceroPlayer

Cala logika (kolejnosc filmow, teksty do przeczytania, przypomnienia) jest
w Cloud Functions Wicero - tutaj tylko wyswietlanie i sterowanie.
Komunikacja: wicero_client.py (katalog AP).

UWAGA: logika skanowania w Board (onPress / timerUpdate) jest skopiowana
z youtube_menu.py - nie zmieniac bez potrzeby (AT_YOUTUBE_PROGRESS.md).

STATUS: napisany bez mozliwosci uruchomienia (brak wx 2.8 / VLC / milena
na komputerze deweloperskim) - do przetestowania na komputerze uzytkownika,
patrz WICERO_PLAN.md.
"""

import os, sys, time, threading, subprocess, logging
from cStringIO import StringIO

import wx
import wx.lib.buttons as bt

from pymouse import PyMouse
from pygame import mixer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import wicero_client
from modules import youtube2

_log = logging.getLogger('wicero')

VIEWED_FRACTION = 0.85              # obejrzany = 85% dlugosci (jak _isRealEnd w youtube2)
NOTIFY_FIRST_DELAY = 15 * 1000      # pierwsze sprawdzenie po starcie AP [ms]
NOTIFY_INTERVAL = 60 * 1000         # kolejne co minute [ms]
MAX_SENDERS = 5                     # plansza 2x3: 5 nadawcow + POWROT (stronicowanie - pozniej)

# Modul Wicero otwarty (od planszy nadawcow do wyjscia z niej) - Notifier
# wtedy nie oglasza: ani w trakcie filmu, ani przy czytaniu komentarza (T10)
ACTIVE = False

NOTIFIER_LOCK = '/tmp/ap_wicero_notifier.lock'  # jeden Notifier na komputer (T10, BUG 2)


#=============================================================================
def say(text, wait=False):
    """Przeczytaj tekst przez milena_say. wait=True - czekaj na koniec (tylko poza watkiem GUI)."""
    if isinstance(text, unicode):
        text = text.encode('utf-8')
    words = text.split()
    if not words:
        return
    try:
        # Jak w iot.py / youtube2.py ('milena_say ' + tekst, shell=True): tekst jako
        # osobne slowa, ale bez powloki - komentarz nadawcy moze zawierac ; " $ itp.
        p = subprocess.Popen(['milena_say'] + words, stdin=subprocess.PIPE)
        if wait:
            p.wait()
    except OSError as e:
        _log.error('milena_say: %r', e)


def say_error(error):
    """Komunikat dla WiceroError."""
    if error.kind == 'offline':
        say(u'Brak połączenia z internetem.')
    elif error.kind == 'token':
        say(u'Wicero nie jest skonfigurowane. Brak lub nieprawidłowy token.')
    else:
        say(u'Wystąpił błąd. Spróbuj później.')


def run_in_thread(target, on_success, on_error):
    """target() w watku; wynik / WiceroError do GUI przez wx.CallAfter."""
    def worker():
        try:
            result = target()
        except wicero_client.WiceroError as e:
            wx.CallAfter(on_error, e)
            return
        wx.CallAfter(on_success, result)
    t = threading.Thread(target=worker)
    t.daemon = True
    t.start()


def open_wicero(parent):
    """Wejscie z nowe.py: pobierz nadawcow, potem pokaz plansze.
    parent.stoper jest zatrzymany przez wywolujacego."""

    def on_success(senders):
        if not senders:
            say(u'Nie masz jeszcze żadnych filmów.')
            _resume(parent)
            return
        SendersBoard(parent, senders).Show(True)
        parent.Hide()

    def on_error(e):
        say_error(e)
        _resume(parent)

    run_in_thread(wicero_client.get_senders, on_success, on_error)


def _resume(frame):
    if frame.control != 'tracker':
        frame.stoper.Start(frame.timeGap)


#=============================================================================
class Board(wx.Frame):
    """Plansza z przyciskami i skanowaniem wiersze -> kolumny.

    buttons: lista slownikow {'key', 'text' | 'bitmap', 'speech'}
      key    - przekazywany do onSelect; 'POWROT' i 'PUSTE' obslugiwane tutaj
      text   - napis na przycisku (imie nadawcy) albo
      bitmap - sciezka ikony wzgledem katalogu AP
      speech - co przeczytac przy skanowaniu (milena_say); None = brak
    """

    def __init__(self, parent, buttons, rows=2, columns=3):
        self.winWidth, self.winHeight = wx.DisplaySize()

        wx.Frame.__init__(self, parent, -1, 'AP Wicero')
        style = self.GetWindowStyle()
        self.SetWindowStyle(style | wx.STAY_ON_TOP)

        self.parent = parent
        self.buttons = buttons
        self.speech = dict((b['key'], b.get('speech')) for b in buttons)

        self.Maximize(True)
        self.Centre(True)
        self.MakeModal(True)

        self.initializeParameters(rows, columns)
        self.createGui()
        self.createBindings()
        self.initializeTimer()

    #-------------------------------------------------------------------------
    def initializeParameters(self, rows, columns):

        with open('./.pathToAP', 'r') as textFile:
            self.pathToAP = textFile.readline()

        sys.path.append(self.pathToAP)
        from reader import reader

        reader = reader()
        reader.readParameters()
        parameters = reader.getParameters()

        for item in parameters:
            try:
                setattr(self, item[:item.find('=')], int(item[item.find('=')+1:]))
            except ValueError:
                setattr(self, item[:item.find('=')], item[item.find('=')+1:])

        self.labels = [b['key'] for b in self.buttons]

        self.flag = 'row'
        self.pressFlag = False

        self.numberOfRows = [rows]
        self.numberOfColumns = [columns]
        self.maxRows = [3 * item for item in self.numberOfRows]
        self.maxColumns = [2 * item for item in self.numberOfColumns]

        self.rowIteration = 0
        self.colIteration = 0
        self.countRows = 0
        self.countColumns = 0

        self.numberOfPresses = 1

        if self.control != 'tracker':
            self.mouseCursor = PyMouse()
            self.mousePosition = self.winWidth - 4 - self.xBorder, self.winHeight - 4 - self.yBorder
            self.mouseCursor.move(*self.mousePosition)

        mixer.init()
        self.switchingSound = mixer.Sound(self.pathToAP + '/sounds/switchSound.ogg')
        self.pressingSound = mixer.Sound(self.pathToAP + '/sounds/pressSound.ogg')

        if self.switchSound.lower() == 'voice' or self.pressSound.lower() == 'voice':
            self.powrotSound = mixer.Sound(self.pathToAP + '/sounds/powrot.ogg')
            self.pusteSound = mixer.Sound(self.pathToAP + '/sounds/puste.ogg')
            self.usypiamSound = mixer.Sound(self.pathToAP + '/sounds/usypiam.ogg')
            self.oneSound = mixer.Sound(self.pathToAP + '/sounds/rows/1.ogg')
            self.twoSound = mixer.Sound(self.pathToAP + '/sounds/rows/2.ogg')
            self.threeSound = mixer.Sound(self.pathToAP + '/sounds/rows/3.ogg')

        self.SetBackgroundColour('black')

    #-------------------------------------------------------------------------
    def createTop(self, vbox):
        """Gorna czesc okna (IntroScreen). Domyslnie brak - same przyciski."""
        return False

    #-------------------------------------------------------------------------
    def createGui(self):

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        hasTop = self.createTop(self.vbox)
        self.sizer = wx.GridSizer(self.numberOfRows[0], self.numberOfColumns[0], self.xBorder, self.yBorder)

        if self.control != 'tracker':
            event = wx.EVT_LEFT_DOWN
        else:
            event = wx.EVT_BUTTON

        font = wx.Font(self.tableFontSize, wx.SWISS, wx.NORMAL, wx.BOLD)

        for button in self.buttons:
            if button.get('bitmap'):
                bitmap = wx.BitmapFromImage(
                    wx.ImageFromStream(open(self.pathToAP + button['bitmap'], 'rb')))
                b = bt.GenBitmapButton(self, -1, bitmap=bitmap, name=button['key'])
            else:
                b = bt.GenButton(self, -1, label=button.get('text', u''), name=button['key'])
                b.SetFont(font)
                b.SetForegroundColour(self.textColour)
            b.SetBackgroundColour(self.backgroundColour)
            b.Bind(event, self.onPress)
            self.sizer.Add(b, 0, wx.EXPAND)

        self.vbox.Add(self.sizer, proportion=1 if hasTop else 2,
                      flag=wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT | wx.RIGHT, border=self.xBorder)
        self.SetSizer(self.vbox)

    #-------------------------------------------------------------------------
    def initializeTimer(self):
        self.stoper = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.timerUpdate, self.stoper)

        if self.control != 'tracker':
            self.stoper.Start(self.timeGap)

    #-------------------------------------------------------------------------
    def createBindings(self):
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    #-------------------------------------------------------------------------
    def OnCloseWindow(self, event):
        # Zamkniecie okna (np. Alt+F4) = powrot, bez pytania
        self.onExit()

    #-------------------------------------------------------------------------
    def onExit(self):
        self.stoper.Stop()
        self.MakeModal(False)
        self.parent.Show(True)
        if self.control != 'tracker':
            self.parent.stoper.Start(self.parent.timeGap)
        self.Destroy()

    #-------------------------------------------------------------------------
    def onSelect(self, key):
        """Wybrano przycisk (poza POWROT / PUSTE) - do nadpisania."""
        pass

    #-------------------------------------------------------------------------
    def _select(self, label):
        if label == 'POWROT':
            if self.pressSound.lower() == 'voice':
                self.powrotSound.play()
            self.onExit()
        elif label == 'PUSTE':
            if self.pressSound.lower() == 'voice':
                self.pusteSound.play()
        else:
            self.onSelect(label)

    #-------------------------------------------------------------------------
    def _voice(self, name):
        """Dzwiek przycisku przy skanowaniu."""
        if name == 'POWROT':
            self.powrotSound.play()
        elif name == 'PUSTE':
            self.pusteSound.play()
        elif self.speech.get(name):
            say(self.speech[name])

    #-------------------------------------------------------------------------
    def onPress(self, event):

        if self.pressSound.lower() != 'off':
            self.pressingSound.play()

        if self.control == 'tracker':
            if self.pressFlag == False:
                self.button = event.GetEventObject()
                self.button.SetBackgroundColour(self.selectionColour)
                self.pressFlag = True
                self.Update()
                self.label = event.GetEventObject().GetName().encode('utf-8')
                self.stoper.Start(0.15 * self.timeGap)

                self._select(self.label)

        else:
            self.numberOfPresses += 1
            self.countRows = 0

            if self.numberOfPresses == 1:

                if self.flag == 'rest':
                    self.flag = 'row'
                    self.rowIteration = 0
                    self.colIteration = 0
                    self.countRows = 0

                elif self.flag == 'row':
                    if self.pressSound == 'voice':
                        if self.rowIteration == 1:
                            self.oneSound.play()
                        if self.rowIteration == 2:
                            self.twoSound.play()
                        if self.rowIteration == 3:
                            self.threeSound.play()

                    buttonsToHighlight = range(
                        (self.rowIteration - 1) * self.numberOfColumns[0],
                        (self.rowIteration - 1) * self.numberOfColumns[0] + self.numberOfColumns[0])
                    for button in buttonsToHighlight:
                        item = self.sizer.GetItem(button)
                        b = item.GetWindow()
                        b.SetBackgroundColour(self.selectionColour)
                        b.SetFocus()

                    self.Update()

                    self.stoper.Stop()
                    time.sleep(self.selectionTime / 1000.)
                    self.stoper.Start(self.timeGap)

                    self.flag = 'columns'
                    self.colIteration = 0

                elif self.flag == 'columns':

                    self.position = (self.rowIteration - 1) * self.numberOfColumns[0] + self.colIteration - 1

                    item = self.sizer.GetItem(self.position)
                    selectedButton = item.GetWindow()
                    selectedButton.SetBackgroundColour(self.selectionColour)
                    selectedButton.SetFocus()
                    self.Update()

                    label = self.labels[self.position]

                    self.flag = 'row'
                    self.rowIteration = 0
                    self.colIteration = 0
                    self.countColumns = 0
                    self.countRows = 0

                    # Po zresetowaniu stanu - _select moze zamknac okno
                    self._select(label)

            else:
                pass

    #-------------------------------------------------------------------------
    def timerUpdate(self, event):

        if self.control == 'tracker':

            if self.button.GetBackgroundColour() == self.backgroundColour:
                self.button.SetBackgroundColour(self.selectionColour)
            else:
                self.button.SetBackgroundColour(self.backgroundColour)

            self.stoper.Stop()
            self.pressFlag = False

        else:
            if self.control != 'tracker':
                self.mouseCursor.move(*self.mousePosition)
                self.numberOfPresses = 0

            if self.flag == 'rest':
                pass

            elif self.countRows < self.maxRows[0]:

                if self.flag == 'row':

                    self.rowIteration = self.rowIteration % self.numberOfRows[0]

                    if self.switchSound == 'voice':
                        if self.rowIteration == 0:
                            self.oneSound.play()
                        if self.rowIteration == 1:
                            self.twoSound.play()
                        if self.rowIteration == 2:
                            self.threeSound.play()

                    items = self.sizer.GetChildren()
                    for item in items:
                        b = item.GetWindow()
                        b.SetBackgroundColour(self.backgroundColour)
                        b.SetFocus()

                    buttonsToHighlight = range(
                        self.rowIteration * self.numberOfColumns[0],
                        self.rowIteration * self.numberOfColumns[0] + self.numberOfColumns[0])
                    for button in buttonsToHighlight:
                        item = self.sizer.GetItem(button)
                        b = item.GetWindow()
                        b.SetBackgroundColour(self.scanningColour)
                        b.SetFocus()

                    self.rowIteration += 1
                    self.countRows += 1

                elif self.flag == 'columns':
                    if self.countColumns == self.maxColumns[0]:
                        self.flag = 'row'
                        self.rowIteration = 0
                        self.colIteration = 0
                        self.countColumns = 0
                        self.countRows = 0
                    else:
                        self.colIteration = self.colIteration % self.numberOfColumns[0]

                        items = self.sizer.GetChildren()
                        for item in items:
                            b = item.GetWindow()
                            b.SetBackgroundColour(self.backgroundColour)
                            b.SetFocus()

                        item = self.sizer.GetItem(
                            (self.rowIteration - 1) * self.numberOfColumns[0] + self.colIteration)
                        b = item.GetWindow()
                        b.SetBackgroundColour(self.scanningColour)
                        b.SetFocus()

                        self.Update()

                        if self.switchSound == 'voice':
                            self._voice(b.Name)

                        self.colIteration += 1
                        self.countColumns += 1

                if self.switchSound.lower() == 'on':
                    self.switchingSound.play()

            elif self.countRows == self.maxRows[0]:
                if self.switchSound == 'voice':
                    self.usypiamSound.play()
                self.flag = 'rest'
                self.countRows += 1

                items = self.sizer.GetChildren()
                for item in items:
                    b = item.GetWindow()
                    b.SetBackgroundColour(self.backgroundColour)
                    b.SetFocus()

            else:
                pass


def _fill(buttons, total):
    """Uzupelnij plansze pustymi polami i przyciskiem POWROT na ostatnim miejscu."""
    buttons = list(buttons)
    while len(buttons) < total - 1:
        buttons.append({'key': 'PUSTE', 'bitmap': 'icons/modules/puste.png'})
    buttons.append({'key': 'POWROT', 'bitmap': 'icons/back.png'})
    return buttons


#=============================================================================
class SendersBoard(Board):
    """Nadawcy (imiona) + POWROT."""

    def __init__(self, parent, senders):
        global ACTIVE
        ACTIVE = True
        self.senders = dict(('S%d' % i, s) for i, s in enumerate(senders[:MAX_SENDERS]))
        buttons = [{'key': 'S%d' % i, 'text': s['name'], 'speech': s.get('say', s['name'])}
                   for i, s in enumerate(senders[:MAX_SENDERS])]
        Board.__init__(self, parent, _fill(buttons, 6))

    def onExit(self):
        # Wyjscie z modulu Wicero - Notifier znow oglasza (zalegle przy nastepnym takcie)
        global ACTIVE
        ACTIVE = False
        Board.onExit(self)

    def onSelect(self, key):
        self.stoper.Stop()
        TypesBoard(self, self.senders[key]).Show(True)
        self.Hide()


#=============================================================================
class TypesBoard(Board):
    """Typy materialow nadawcy - na razie tylko FILMY (od razu, zeby nawyk
    nawigacji nie zmienil sie, gdy dojda kolejne typy)."""

    def __init__(self, parent, sender):
        self.sender = sender
        self.types = dict((t['type'].upper(), t) for t in sender['types'])
        buttons = [{'key': t['type'].upper(), 'text': t['label'].upper(),
                    'speech': t.get('say', t['label'])}
                   for t in sender['types']]
        Board.__init__(self, parent, _fill(buttons, 6))

    def onSelect(self, key):
        self.stoper.Stop()
        material_type = self.types[key]['type']

        def on_success(items):
            if not items:
                say(u'Nie ma tu jeszcze filmów.')
                _resume(self)
                return
            IntroScreen(self, items).Show(True)
            self.Hide()

        def on_error(e):
            say_error(e)
            _resume(self)

        run_in_thread(lambda: wicero_client.get_messages(self.sender['senderId'], material_type),
                      on_success, on_error)


#=============================================================================
class IntroScreen(Board):
    """Ekran przed filmem: miniatura, tytul, komentarz; milena czyta 'say'.
    Przyciski: POWTORZ / START / POWROT."""

    def __init__(self, parent, items):
        self.items = items
        self.index = 0
        buttons = [
            {'key': 'POWTORZ', 'text': u'POWTÓRZ', 'speech': u'Powtórz'},
            {'key': 'START', 'text': u'START', 'speech': u'Start'},
            {'key': 'POWROT', 'bitmap': 'icons/back.png'},
        ]
        Board.__init__(self, parent, buttons, rows=1, columns=3)
        self.showCurrent()

    def createTop(self, vbox):
        self.topPanel = wx.Panel(self, -1)
        self.topPanel.SetBackgroundColour(self.backgroundColour)
        box = wx.BoxSizer(wx.VERTICAL)

        self.thumbnail = wx.StaticBitmap(self.topPanel, -1)
        self.title = wx.StaticText(self.topPanel, -1, u'', style=wx.ALIGN_CENTRE)
        self.title.SetFont(wx.Font(self.tableFontSize / 2, wx.SWISS, wx.NORMAL, wx.NORMAL))
        self.comment = wx.StaticText(self.topPanel, -1, u'', style=wx.ALIGN_CENTRE)
        self.comment.SetFont(wx.Font(self.tableFontSize * 2 / 3, wx.SWISS, wx.NORMAL, wx.BOLD))
        for text in (self.title, self.comment):
            text.SetForegroundColour(self.textColour)

        box.Add(self.thumbnail, 0, wx.ALIGN_CENTER | wx.TOP, self.yBorder)
        box.Add(self.title, 0, wx.ALIGN_CENTER | wx.TOP, self.yBorder)
        box.Add(self.comment, 0, wx.ALIGN_CENTER | wx.TOP, self.yBorder)
        self.topPanel.SetSizer(box)

        vbox.Add(self.topPanel, proportion=3, flag=wx.EXPAND | wx.ALL, border=self.xBorder)
        return True

    #-------------------------------------------------------------------------
    def current(self):
        return self.items[self.index]

    def showCurrent(self):
        """Pokaz film self.index, zglos 'otwarty', przeczytaj tekst, potem skanowanie."""
        self.stoper.Stop()
        item = self.current()

        self.title.SetLabel(item['title'])
        self.title.Wrap(self.winWidth - 4 * self.xBorder)
        self.comment.SetLabel(item.get('comment') or u'')
        self.comment.Wrap(self.winWidth - 4 * self.xBorder)
        self.thumbnail.SetBitmap(wx.NullBitmap)
        self.topPanel.Layout()
        self._loadThumbnail(item)

        if item.get('isNew'):
            item['isNew'] = False
            run_in_thread(lambda: wicero_client.mark_opened(item),
                          lambda result: None,
                          lambda e: _log.error('mark_opened: %s', e.message))

        self._sayThenScan(item['say'])

    def _sayThenScan(self, text):
        """Skanowanie startuje dopiero po przeczytaniu - inaczej glosy sie nakladaja."""
        def worker():
            say(text, wait=True)
            wx.CallAfter(self._startScanning)
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()

    def _startScanning(self):
        if not self:  # okno zamkniete w trakcie czytania
            return
        self.flag = 'row'
        self.rowIteration = 0
        self.colIteration = 0
        self.countRows = 0
        self.countColumns = 0
        _resume(self)

    def _loadThumbnail(self, item):
        height = int(self.winHeight * 0.35)

        def worker():
            try:
                data = wicero_client._request.urlopen(item['thumbnailUrl'], timeout=10).read()
            except Exception as e:
                _log.error('thumbnail %s: %r', item['thumbnailUrl'], e)
                return
            wx.CallAfter(show, data)

        def show(data):
            if not self or self.current() is not item:
                return
            image = wx.ImageFromStream(StringIO(data))
            width = image.GetWidth() * height / image.GetHeight()
            image.Rescale(width, height, wx.IMAGE_QUALITY_HIGH)
            self.thumbnail.SetBitmap(wx.BitmapFromImage(image))
            self.topPanel.Layout()

        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()

    #-------------------------------------------------------------------------
    def onSelect(self, key):
        if key == 'POWTORZ':
            self.stoper.Stop()
            self._sayThenScan(self.current()['say'])
        elif key == 'START':
            self.stoper.Stop()
            WiceroPlayer(self, self.current()).Show(True)
            self.Hide()

    def moveBy(self, step):
        """Wywolywane przez WiceroPlayer po NASTEPNY / POPRZEDNI / koncu filmu."""
        if not self:
            return
        index = self.index + step
        if index >= len(self.items):
            self.stoper.Stop()
            say(u'To już wszystkie filmy.')
            self.onExit()
            return
        self.index = max(index, 0)
        self.showCurrent()


#=============================================================================
class WiceroPlayer(youtube2.PlayerFrame):
    """Odtwarzacz jednego filmu Wicero (wzor: FavouritesPlayer).

    NASTEPNY / POPRZEDNI / koniec filmu -> powrot do IntroScreen
    z nastepnym / poprzednim filmem (kazdy film ma swoj ekran z komentarzem).
    Przy VIEWED_FRACTION dlugosci - zgloszenie 'obejrzany'.
    Nie zapisuje tabeli seen (stan obejrzenia jest w Wicero); ULUBIONE dziala
    jak w youtube2 (ulubione AP).
    """

    def __init__(self, parent, item):
        self.item = item
        self._viewedSent = item.get('status') == 'viewed'
        youtube2.PlayerFrame.__init__(self, parent, query='__wicero__')

        self.progress = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._checkProgress, self.progress)
        self.progress.Start(1000)

    def _cacheFile(self):
        return None

    def _loadPlaylist(self):
        url = self.item['url']
        self.playlist = [url]
        self.playlist_meta[url] = {'id': self.item['videoId'], 'title': self.item['title']}
        wx.CallAfter(self._playCurrent)

    def _startPlay(self, url, video_url):
        # Jak FavouritesPlayer: bez tabeli seen i bez doladowywania playlisty
        self.player.set_xwindow(self.vlcPanel.GetHandle())
        media = self.vlc_instance.media_new(video_url)
        self.player.set_media(media)
        self.player.play()

    def _checkProgress(self, event):
        if self._viewedSent or self._length_ms <= 0:
            return
        if self.player.get_time() >= VIEWED_FRACTION * self._length_ms:
            self._viewedSent = True
            self.item['status'] = 'viewed'
            run_in_thread(lambda: wicero_client.mark_viewed(self.item),
                          lambda result: None,
                          lambda e: _log.error('mark_viewed: %s', e.message))

    def _next(self):
        self._leave(1)

    def _prev(self):
        self._leave(-1)

    def _leave(self, step):
        parent = self.parent
        self._onExit()
        wx.CallAfter(parent.moveBy, step)

    def _onExit(self):
        self.progress.Stop()
        youtube2.PlayerFrame._onExit(self)


#=============================================================================
class Notifier(wx.EvtHandler):
    """Ogloszenia w tle - tworzony raz w ap.py (main_menu).

    Co minute pyta serwer, co przeczytac (nowe filmy - raz; przypomnienie
    o nieotwartych - przy starcie i co godzine; decyduje serwer).
    Nie dziala, gdy brak .wicero_token (AP bez Wicero). Bledy - tylko log.

    Gdy modul Wicero jest otwarty (ACTIVE) - nie pyta i nie czyta. Teksty
    pobrane tuz przed wejsciem do Wicero (zapytanie trwa) nie gina - serwer
    oznaczyl je juz jako ogloszone - tylko czekaja w self.pending na wyjscie.

    Tylko jeden Notifier na komputer (blokada NOTIFIER_LOCK): gdy dziala
    drugi proces AP, ten nie oglasza - inaczej kazde ogloszenie padloby
    w kazdym procesie (log pokazywal zapytania co ~37 s / ~23 s).
    """

    def __init__(self):
        wx.EvtHandler.__init__(self)
        self.startup = True
        self.busy = False
        self.pending = []
        if not os.path.exists(wicero_client.TOKEN_FILE):
            return
        if not self._lock():
            return
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._tick, self.timer)
        self.timer.Start(NOTIFY_FIRST_DELAY, oneShot=True)

    def _lock(self):
        """Blokada na czas zycia procesu (zwalniana przez system przy jego koncu)."""
        try:
            import fcntl
        except ImportError:  # nie-Linux (test na innym komputerze)
            return True
        self._lockFile = open(NOTIFIER_LOCK, 'a+')
        try:
            fcntl.flock(self._lockFile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            self._lockFile.seek(0)
            _log.warning('Notifier wylaczony - oglasza juz inny proces AP (PID %s). '
                         'Sprawdz: ps aux | grep ap.py', self._lockFile.read().strip() or '?')
            return False
        self._lockFile.seek(0)
        self._lockFile.truncate()
        self._lockFile.write(str(os.getpid()))
        self._lockFile.flush()
        return True

    def _tick(self, event):
        self.timer.Start(NOTIFY_INTERVAL)
        if self.busy or ACTIVE:
            return
        self.busy = True
        startup = self.startup

        def worker():
            try:
                texts = self.pending
                self.pending = []
                if not texts:
                    texts = wicero_client.get_notifications(startup=startup)
                    self.startup = False
                for i, text in enumerate(texts):
                    if ACTIVE:  # wejscie do Wicero w trakcie zapytania / czytania
                        self.pending = texts[i:]
                        break
                    say(text, wait=True)
            except wicero_client.WiceroError as e:
                _log.error('notifications: %s %s', e.kind, e.message)
            finally:
                self.busy = False

        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()


#=============================================================================
class _Standalone(wx.Frame):
    """Rodzic zastepujacy nowe.py przy samodzielnym uruchomieniu.
    Powrot do rodzica (Show / stoper.Start) konczy program."""

    control = 'switch'
    timeGap = 1000

    def __init__(self):
        wx.Frame.__init__(self, None, -1, 'AP Wicero (test)')
        self.stoper = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, lambda event: self.Destroy(), self.stoper)

    def Show(self, show=True):
        if show:
            wx.CallAfter(self.Destroy)
        return True


if __name__ == '__main__':
    # Test modulu bez ap.py / nowe.py - uruchamiac z katalogu AP:
    #     python2.7 modules/wicero.py
    app = wx.App(False)
    open_wicero(_Standalone())
    app.MainLoop()
