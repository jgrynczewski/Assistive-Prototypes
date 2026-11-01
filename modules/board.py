#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""Wspolna plansza ze skanowaniem - dla modulow Wicero i Gra.

Wydzielone z modules/wicero.py (bez zmiany dzialania). Logika skanowania
w Board (onPress / timerUpdate) jest skopiowana z youtube_menu.py - nie
zmieniac bez potrzeby (AT_YOUTUBE_PROGRESS.md).

Jedyna roznica wzgledem kopii w wicero.py: przyciski sa trzymane w liscie
self.buttonWindows (kolejnosc skanowania) zamiast pobierania z self.sizer -
dzieki temu podklasa moze ulozyc przyciski dowolnie (Gra: opcje w pionie,
POWTORZ / WYJDZ w rzedzie pod nimi) i skanowac je jak jeden rzad
(columnsOnly).
"""

import os, sys, time, threading, subprocess, logging

import wx
import wx.lib.buttons as bt

from pymouse import PyMouse
from pygame import mixer

_log = logging.getLogger('board')


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
        else:  # bez wait() skonczony proces zostaje jako zombie (R4, BUG 3)
            t = threading.Thread(target=p.wait)
            t.daemon = True
            t.start()
    except OSError as e:
        _log.error('milena_say: %r', e)


def say_then(text, callback):
    """Przeczytaj tekst, potem callback() w watku GUI - np. wznowienie filmu
    dopiero po komunikacie, zeby sie nie nakladaly."""
    def worker():
        say(text, wait=True)
        wx.CallAfter(callback)
    t = threading.Thread(target=worker)
    t.daemon = True
    t.start()


def resume(frame):
    """Wznow skanowanie okna (po zatrzymaniu stopera)."""
    if frame.control != 'tracker':
        frame.stoper.Start(frame.timeGap)


def fill(buttons, total):
    """Uzupelnij plansze pustymi polami i przyciskiem POWROT na ostatnim miejscu."""
    buttons = list(buttons)
    while len(buttons) < total - 1:
        buttons.append({'key': 'PUSTE', 'bitmap': 'icons/modules/puste.png'})
    buttons.append({'key': 'POWROT', 'bitmap': 'icons/back.png'})
    return buttons


#=============================================================================
class Board(wx.Frame):
    """Plansza z przyciskami i skanowaniem wiersze -> kolumny.

    buttons: lista slownikow {'key', 'text' | 'bitmap', 'speech'}
      key    - przekazywany do onSelect; 'POWROT' i 'PUSTE' obslugiwane tutaj
      text   - napis na przycisku (imie nadawcy) albo
      bitmap - sciezka ikony wzgledem katalogu AP
      speech - co przeczytac przy skanowaniu (milena_say); None = brak

    columnsOnly - jeden wiersz: skanowanie od razu po przyciskach, bez
      zaznaczania calego wiersza; po dwoch przejsciach - uspienie
    """

    columnsOnly = False
    title = 'AP'

    def __init__(self, parent, buttons, rows=2, columns=3):
        self.winWidth, self.winHeight = wx.DisplaySize()

        wx.Frame.__init__(self, parent, -1, self.title)
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

        self.pressFlag = False

        self.numberOfRows = [rows]
        self.numberOfColumns = [columns]
        self.maxRows = [3 * item for item in self.numberOfRows]
        self.maxColumns = [2 * item for item in self.numberOfColumns]

        self.resetScanning()

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
    def pressEvent(self):
        if self.control != 'tracker':
            return wx.EVT_LEFT_DOWN
        return wx.EVT_BUTTON

    def makeButton(self, parent, button, font):
        """Przycisk planszy (wx) dla slownika z self.buttons."""
        if button.get('bitmap'):
            bitmap = wx.BitmapFromImage(
                wx.ImageFromStream(open(self.pathToAP + button['bitmap'], 'rb')))
            b = bt.GenBitmapButton(parent, -1, bitmap=bitmap, name=button['key'])
        else:
            b = bt.GenButton(parent, -1, label=button.get('text', u''), name=button['key'])
            b.SetFont(font)
            b.SetForegroundColour(self.textColour)
        b.SetBackgroundColour(self.backgroundColour)
        b.Bind(self.pressEvent(), self.onPress)
        return b

    def createGui(self):

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        hasTop = self.createTop(self.vbox)
        self.sizer = wx.GridSizer(self.numberOfRows[0], self.numberOfColumns[0], self.xBorder, self.yBorder)

        font = wx.Font(self.tableFontSize, wx.SWISS, wx.NORMAL, wx.BOLD)

        self.buttonWindows = []
        for button in self.buttons:
            b = self.makeButton(self, button, font)
            self.buttonWindows.append(b)
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
    def resetScanning(self):
        """Skanowanie od poczatku: od wierszy, a przy columnsOnly od przyciskow."""
        if self.columnsOnly:
            self.flag = 'columns'
            self.rowIteration = 1
        else:
            self.flag = 'row'
            self.rowIteration = 0
        self.colIteration = 0
        self.countRows = 0
        self.countColumns = 0

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
    def _clearHighlight(self):
        for b in self.buttonWindows:
            b.SetBackgroundColour(self.backgroundColour)
            b.SetFocus()

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
                    self.resetScanning()

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
                        b = self.buttonWindows[button]
                        b.SetBackgroundColour(self.selectionColour)
                        b.SetFocus()

                    self.Update()

                    self.stoper.Stop()
                    time.sleep(self.selectionTime / 1000.)
                    self.stoper.Start(self.timeGap)

                    self.flag = 'columns'
                    self.colIteration = 0

                elif self.flag == 'columns' and self.colIteration == 0:
                    # Nic jeszcze nie podswietlone (columnsOnly: zaraz po przeczytaniu tekstu)
                    pass

                elif self.flag == 'columns':

                    self.position = (self.rowIteration - 1) * self.numberOfColumns[0] + self.colIteration - 1

                    selectedButton = self.buttonWindows[self.position]
                    selectedButton.SetBackgroundColour(self.selectionColour)
                    selectedButton.SetFocus()
                    self.Update()

                    label = self.labels[self.position]

                    self.resetScanning()

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

                    self._clearHighlight()

                    buttonsToHighlight = range(
                        self.rowIteration * self.numberOfColumns[0],
                        self.rowIteration * self.numberOfColumns[0] + self.numberOfColumns[0])
                    for button in buttonsToHighlight:
                        b = self.buttonWindows[button]
                        b.SetBackgroundColour(self.scanningColour)
                        b.SetFocus()

                    self.rowIteration += 1
                    self.countRows += 1

                elif self.flag == 'columns':
                    if self.countColumns == self.maxColumns[0] and self.columnsOnly:
                        self._sleep()
                    elif self.countColumns == self.maxColumns[0]:
                        self.flag = 'row'
                        self.rowIteration = 0
                        self.colIteration = 0
                        self.countColumns = 0
                        self.countRows = 0
                    else:
                        self.colIteration = self.colIteration % self.numberOfColumns[0]

                        self._clearHighlight()

                        b = self.buttonWindows[
                            (self.rowIteration - 1) * self.numberOfColumns[0] + self.colIteration]
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
                self._sleep()
                self.countRows += 1

            else:
                pass

    #-------------------------------------------------------------------------
    def _sleep(self):
        """Uspienie skanowania - budzi je nacisniecie (onPress, flag 'rest')."""
        if self.switchSound == 'voice':
            self.usypiamSound.play()
        self.flag = 'rest'
        self._clearHighlight()
