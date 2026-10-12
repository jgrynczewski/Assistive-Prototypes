#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import wx, os, sys, time
import wx.lib.buttons as bt

from pymouse import PyMouse
from pygame import mixer

from modules import at_youtube, youtube2


#=============================================================================
class youtube_menu(wx.Frame):
    def __init__(self, parent, id):

        self.winWidth, self.winHeight = wx.DisplaySize()

        wx.Frame.__init__(self, parent, id, 'AP YouTube Menu')
        style = self.GetWindowStyle()
        self.SetWindowStyle(style | wx.STAY_ON_TOP)

        self.parent = parent

        self.Maximize(True)
        self.Centre(True)
        self.MakeModal(True)

        self.initializeParameters()
        self.initializeBitmaps()
        self.createGui()
        self.createBindings()
        self.initializeTimer()

    #-------------------------------------------------------------------------
    def initializeParameters(self):

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

        self.labels = 'WYSZUKAJ LOSOWE ULUBIONE PUSTE PUSTE EXIT'.split()

        self.flag = 'row'
        self.pressFlag = False

        self.numberOfRows = [2]
        self.numberOfColumns = [3]
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
            self.wyszukajSound = mixer.Sound(self.pathToAP + '/sounds/youtube/youtube.ogg')
            self.losoweSound = mixer.Sound(self.pathToAP + '/sounds/youtube/youtube.ogg')
            self.ulubioneSound = mixer.Sound(self.pathToAP + '/sounds/youtube/youtube ulubione.ogg')
            self.powrotSound = mixer.Sound(self.pathToAP + '/sounds/powrot.ogg')
            self.pusteSound = mixer.Sound(self.pathToAP + '/sounds/puste.ogg')
            self.usypiamSound = mixer.Sound(self.pathToAP + '/sounds/usypiam.ogg')
            self.oneSound = mixer.Sound(self.pathToAP + '/sounds/rows/1.ogg')
            self.twoSound = mixer.Sound(self.pathToAP + '/sounds/rows/2.ogg')
            self.threeSound = mixer.Sound(self.pathToAP + '/sounds/rows/3.ogg')

        self.SetBackgroundColour('black')

    #-------------------------------------------------------------------------
    def initializeBitmaps(self):

        labelFiles = [self.pathToAP + item for item in [
            'icons/modules/youtube2.png',
            'icons/modules/youtube1.png',
            'icons/modules/youtube_ulubione.png',
            'icons/modules/puste.png',
            'icons/modules/puste.png',
            'icons/back.png',
        ]]

        self.labelbitmaps = {}
        for index in xrange(len(self.labels)):
            self.labelbitmaps[self.labels[index]] = wx.BitmapFromImage(
                wx.ImageFromStream(open(labelFiles[index], 'rb')))

    #-------------------------------------------------------------------------
    def createGui(self):

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.sizer = wx.GridSizer(self.numberOfRows[0], self.numberOfColumns[0], self.xBorder, self.yBorder)

        if self.control != 'tracker':
            event = wx.EVT_LEFT_DOWN
        else:
            event = wx.EVT_BUTTON

        for i in self.labels:
            b = bt.GenBitmapButton(self, -1, bitmap=self.labelbitmaps[i], name=i)
            b.Bind(event, self.onPress)
            self.sizer.Add(b, 0, wx.EXPAND)

        self.vbox.Add(self.sizer, proportion=2, flag=wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT | wx.RIGHT, border=self.xBorder)
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

        if self.control != 'tracker':
            if True in ['debian' in item for item in os.uname()]:
                if os.environ.get('KDE_FULL_SESSION'):
                    self.mousePosition = self.winWidth / 1.7, self.winHeight / 1.7
                else:
                    self.mousePosition = self.winWidth / 1.8, self.winHeight / 1.7
            else:
                self.mousePosition = self.winWidth / 1.9, self.winHeight / 1.68

            self.mouseCursor.move(*self.mousePosition)

        dial = wx.MessageDialog(self, u'Czy napewno chcesz wyjść z programu?', u'Wyjście',
                                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION | wx.STAY_ON_TOP)

        ret = dial.ShowModal()

        if ret == wx.ID_YES:
            self.Destroy()
        else:
            event.Veto()
            if self.control != 'tracker':
                self.mousePosition = self.winWidth - 4 - self.xBorder, self.winHeight - 4 - self.yBorder
                self.mouseCursor.move(*self.mousePosition)

    #-------------------------------------------------------------------------
    def onExit(self):
        if __name__ == '__main__':
            self.stoper.Stop()
            self.Destroy()
        else:
            self.stoper.Stop()
            self.MakeModal(False)
            self.parent.Show(True)
            if self.control != 'tracker':
                self.parent.stoper.Start(self.parent.timeGap)
            self.Destroy()

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

                if self.label == 'WYSZUKAJ':
                    self.stoper.Stop()
                    youtube2.youtube2(self, id=-1).Show(True)
                    self.Hide()
                elif self.label == 'LOSOWE':
                    self.stoper.Stop()
                    at_youtube.youtube(self, id=-1).Show(True)
                    self.Hide()
                elif self.label == 'ULUBIONE':
                    self.stoper.Stop()
                    youtube2.FavouritesPlayer(self).Show(True)
                    self.Hide()
                elif self.label == 'EXIT':
                    self.onExit()

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

                    if label == 'WYSZUKAJ':
                        if self.pressSound.lower() == 'voice':
                            self.wyszukajSound.play()
                        self.stoper.Stop()
                        youtube2.youtube2(self, id=-1).Show(True)
                        self.Hide()

                    elif label == 'LOSOWE':
                        if self.pressSound.lower() == 'voice':
                            self.losoweSound.play()
                        self.stoper.Stop()
                        at_youtube.youtube(self, id=-1).Show(True)
                        self.Hide()

                    elif label == 'ULUBIONE':
                        if self.pressSound.lower() == 'voice':
                            self.ulubioneSound.play()
                        self.stoper.Stop()
                        youtube2.FavouritesPlayer(self).Show(True)
                        self.Hide()

                    elif label == 'EXIT':
                        if self.pressSound.lower() == 'voice':
                            self.powrotSound.play()
                        self.onExit()

                    elif label == 'PUSTE':
                        if self.pressSound.lower() == 'voice':
                            self.pusteSound.play()

                    self.flag = 'row'
                    self.rowIteration = 0
                    self.colIteration = 0
                    self.countColumns = 0
                    self.countRows = 0

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
                            if b.Name == 'WYSZUKAJ':
                                self.wyszukajSound.play()
                            elif b.Name == 'LOSOWE':
                                self.losoweSound.play()
                            elif b.Name == 'ULUBIONE':
                                self.ulubioneSound.play()
                            elif b.Name == 'EXIT':
                                self.powrotSound.play()
                            elif b.Name == 'PUSTE':
                                self.pusteSound.play()

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


#=============================================================================
if __name__ == '__main__':
    app = wx.App(False)
    frame = youtube_menu(parent=None, id=-1)
    frame.Show(True)
    app.MainLoop()