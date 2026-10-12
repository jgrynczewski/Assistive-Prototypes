#!/bin/env python2.7
# -*- coding: utf-8 -*-

import os, sys, time, subprocess
import wx
import wx.lib.buttons as bt
from pymouse import PyMouse
from pygame import mixer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import iot_client

# Plansza urzadzen:   1 wiersz tresc  + 1 wiersz back = 2 wiersze, 3 kolumny
# Plansza capabilities: 3 wiersze tresc + 1 wiersz back = 4 wiersze, 3 kolumny
# Plansza wartosci:   3 wiersze tresc + 1 wiersz back = 4 wiersze, 4 kolumny
PANEL_DEVICES      = 'devices'
PANEL_CAPABILITIES = 'capabilities'
PANEL_VALUES       = 'values'

CAPABILITY_ORDER = ['power', 'brightness', 'color', 'temperature', 'effects', 'reset']

BRIGHTNESS_VALUES  = [25, 50, 75, 100]
COLOR_VALUES       = ['blue', 'green', 'orange', 'pink', 'purple', 'red', 'white', 'yellow']
TEMPERATURE_VALUES = ['warm', 'neutral', 'cold']
EFFECT_VALUES      = ['disco', 'ocean', 'police', 'pulse', 'rainbow', 'strobe', 'stop']

SOUND_MAP = {
    'power':       u'zasilanie',
    'brightness':  u'jasność',
    'color':       u'kolor',
    'temperature': u'temperatura',
    'effects':     u'efekt',
    'reset':       u'reset',
    25:            u'dwadzieścia pięć procent',
    50:            u'pięćdziesiąt procent',
    75:            u'siedemdziesiąt pięć procent',
    100:           u'sto procent',
    'blue':        u'niebieski',
    'green':       u'zielony',
    'orange':      u'pomarańczowy',
    'pink':        u'różowy',
    'purple':      u'fioletowy',
    'red':         u'czerwony',
    'white':       u'biały',
    'yellow':      u'żółty',
    'warm':        u'ciepła',
    'neutral':     u'neutralna',
    'cold':        u'zimna',
    'disco':       u'disco',
    'ocean':       u'ocean',
    'police':      u'policja',
    'pulse':       u'puls',
    'rainbow':     u'tęcza',
    'strobe':      u'stroboskop',
    'stop':        u'stop',
}

SOUND_FILE_MAP = {
    'power':       'zasilanie.ogg',
    'brightness':  'jasnosc.ogg',
    'color':       'kolor.ogg',
    'temperature': 'temperatura.ogg',
    'effects':     'efekty.ogg',
    'reset':       'reset.ogg',
    25:            'jasnosc_25.ogg',
    50:            'jasnosc_50.ogg',
    75:            'jasnosc_75.ogg',
    100:           'jasnosc_100.ogg',
    'blue':        'kolor_niebieski.ogg',
    'green':       'kolor_zielony.ogg',
    'orange':      'kolor_pomaranczowy.ogg',
    'pink':        'kolor_rozowy.ogg',
    'purple':      'kolor_fioletowy.ogg',
    'red':         'kolor_czerwony.ogg',
    'white':       'kolor_bialy.ogg',
    'yellow':      'kolor_zolty.ogg',
    'warm':        'temp_ciepla.ogg',
    'neutral':     'temp_neutralna.ogg',
    'cold':        'temp_zimna.ogg',
    'disco':       'efekt_disco.ogg',
    'ocean':       'efekt_ocean.ogg',
    'police':      'efekt_policja.ogg',
    'pulse':       'efekt_puls.ogg',
    'rainbow':     'efekt_teczy.ogg',
    'strobe':      'efekt_stroboskop.ogg',
    'stop':        'zatrzymaj.ogg',
}

ICON_FILE_MAP = {
    'zarowka':     'zarowka.png',
    'power':       'zasilanie.png',
    'brightness':  'jasnosc.png',
    'color':       'kolor.png',
    'temperature': 'temperatura.png',
    'effects':     'efekt.png',
    'reset':       'reset.png',
    25:            'jasnosc_25.png',
    50:            'jasnosc_50.png',
    75:            'jasnosc_75.png',
    100:           'jasnosc_100.png',
    'blue':        'kolor_niebieski.png',
    'green':       'kolor_zielony.png',
    'orange':      'kolor_pomaranczowy.png',
    'pink':        'kolor_rozowy.png',
    'purple':      'kolor_fioletowy.png',
    'red':         'kolor_czerwony.png',
    'white':       'kolor_bialy.png',
    'yellow':      'kolor_zolty.png',
    'warm':        'temp_ciepla.png',
    'neutral':     'temp_neutralna.png',
    'cold':        'temp_zimna.png',
    'disco':       'efekt_disco.png',
    'ocean':       'efekt_ocean.png',
    'police':      'efekt_policja.png',
    'pulse':       'efekt_puls.png',
    'rainbow':     'efekt_tecza.png',
    'strobe':      'efekt_stroboskop.png',
    'stop':        'efekt_stop.png',
}


#=============================================================================
class iot(wx.Frame):
    def __init__(self, parent, id):

        self.winWidth, self.winHeight = wx.DisplaySize()

        wx.Frame.__init__(self, parent, id, 'IoT')
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

        with open(os.path.join(os.path.dirname(__file__), '.pathToAP'), 'r') as f:
            self.pathToAP = f.readline().strip()

        sys.path.append(self.pathToAP)

        from reader import reader
        self.reader = reader()
        self.reader.readParameters()
        parameters = self.reader.getParameters()
        self.unpackParameters(parameters)

        self.iotPanel = PANEL_DEVICES
        self.selected_device     = None
        self.selected_capability = None
        self.devices     = []
        self.capabilities = {}

        self.flag = 'row'
        self.pressFlag = False
        self.numberOfPresses = 1

        self.numberOfRows    = [2]
        self.numberOfColumns = [3]

        self.columnIteration      = 0
        self.rowIteration         = 0
        self.emptyColumnIteration = 0
        self.emptyRowIteration    = 0
        self.maxEmptyColumnIteration = 2
        self.maxEmptyRowIteration    = 2

        if self.control != 'tracker':
            self.mouseCursor   = PyMouse()
            self.mousePosition = self.winWidth - 8 - self.xBorder, self.winHeight - 8 - self.yBorder
            self.mouseCursor.move(*self.mousePosition)

        mixer.init()
        self.switchingSound = mixer.Sound(self.pathToAP + '/sounds/switchSound.ogg')
        self.pressingSound  = mixer.Sound(self.pathToAP + '/sounds/pressSound.ogg')
        self.usypiamSound   = mixer.Sound(self.pathToAP + '/sounds/usypiam.ogg')
        self.powrotSound    = mixer.Sound(self.pathToAP + '/sounds/powrot.ogg')
        self.pusteSound     = mixer.Sound(self.pathToAP + '/sounds/puste.ogg')
        self.oneSound       = mixer.Sound(self.pathToAP + '/sounds/rows/1.ogg')
        self.twoSound       = mixer.Sound(self.pathToAP + '/sounds/rows/2.ogg')
        self.threeSound     = mixer.Sound(self.pathToAP + '/sounds/rows/3.ogg')
        self.fourSound      = mixer.Sound(self.pathToAP + '/sounds/rows/4.ogg')

        self.iotSounds = {}
        sounds_dir = self.pathToAP + '/sounds/iot/'
        for key, filename in SOUND_FILE_MAP.items():
            path = sounds_dir + filename
            if os.path.exists(path):
                self.iotSounds[key] = mixer.Sound(path)

        self.SetBackgroundColour('black')

    #-------------------------------------------------------------------------
    def unpackParameters(self, parameters):
        for item in parameters:
            try:
                setattr(self, item[:item.find('=')], int(item[item.find('=') + 1:]))
            except ValueError:
                setattr(self, item[:item.find('=')], item[item.find('=') + 1:])

    #-------------------------------------------------------------------------
    def initializeBitmaps(self):
        icons_dir = self.pathToAP + '/icons/iot/'
        self.bitmaps = {}
        for key, filename in ICON_FILE_MAP.items():
            path = icons_dir + filename
            if os.path.exists(path):
                self.bitmaps[key] = wx.BitmapFromImage(wx.ImageFromStream(open(path, 'rb')))
        self.backBitmap = wx.BitmapFromImage(wx.ImageFromStream(open(self.pathToAP + '/icons/back.png', 'rb')))

    #-------------------------------------------------------------------------
    def _speak(self, key):
        if isinstance(key, bytes):
            key = key.decode('utf-8')
        if key in self.iotSounds:
            self.iotSounds[key].play()
        else:
            text = SOUND_MAP.get(key, u'')
            if text:
                cmd = u'milena_say ' + text
                subprocess.Popen(cmd.encode('utf-8'), shell=True, stdin=subprocess.PIPE)

    #-------------------------------------------------------------------------
    def _speak_error(self, message):
        cmd = u'milena_say ' + message
        subprocess.Popen(cmd.encode('utf-8'), shell=True, stdin=subprocess.PIPE)
        time.sleep(2)

    #-------------------------------------------------------------------------
    def createGui(self):

        if self.control != 'tracker':
            event = wx.EVT_LEFT_DOWN
        else:
            event = wx.EVT_BUTTON

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)

        # --- plansza urzadzen: 2 wiersze x 3 kolumny ---
        result = None
        for attempt in range(3):
            result = iot_client.discover_devices()
            if result is not None:
                break
            time.sleep(2)
        if result is None:
            self._speak_error(u'Błąd połączenia z hubem')
            wx.CallAfter(self.onExit)
            return
        self.devices = result.get('devices', [])
        if not self.devices:
            for attempt in range(3):
                time.sleep(2)
                result = iot_client.discover_devices()
                if result:
                    self.devices = result.get('devices', [])
                if self.devices:
                    break
        if not self.devices:
            self._speak_error(u'Nie znaleziono urządzeń')
            wx.CallAfter(self.onExit)
            return

        for dev in self.devices:
            if dev['id'] not in self.bitmaps:
                self.bitmaps[dev['id']] = self.bitmaps.get('zarowka', wx.NullBitmap)
            SOUND_MAP[dev['id']] = u'światło'
            SOUND_FILE_MAP[dev['id']] = 'swiatlo.ogg'
            path = self.pathToAP + '/sounds/iot/swiatlo.ogg'
            if os.path.exists(path):
                self.iotSounds[dev['id']] = mixer.Sound(path)

        # slot_names dla planszy urzadzen: maks 3 urzadzenia + back
        dev_slots = [None, None, None]
        for i, dev in enumerate(self.devices[:3]):
            dev_slots[i] = dev['id']

        self.subSizer_devices = wx.GridBagSizer(self.xBorder, self.yBorder)
        cols = 3
        for idx, name in enumerate(dev_slots):
            if name is not None:
                bmp = self.bitmaps.get(name, wx.NullBitmap)
                b = bt.GenBitmapButton(self, -1, name=str(name), bitmap=bmp)
            else:
                b = bt.GenButton(self, -1, name='empty')
            b.SetBackgroundColour(self.backgroundColour)
            b.SetBezelWidth(3)
            b.Bind(event, self.onPress)
            self.subSizer_devices.Add(b, (idx / cols, idx % cols), wx.DefaultSpan, wx.EXPAND)
        # wiersz back - span przez wszystkie kolumny
        bBack = bt.GenBitmapButton(self, -1, name='back', bitmap=self.backBitmap)
        bBack.SetBackgroundColour(self.backgroundColour)
        bBack.SetBezelWidth(3)
        bBack.Bind(event, self.onPress)
        self.subSizer_devices.Add(bBack, (1, 0), (1, cols), wx.EXPAND)
        for r in range(2):
            self.subSizer_devices.AddGrowableRow(r)
        for c in range(cols):
            self.subSizer_devices.AddGrowableCol(c)

        # --- plansza capabilities: 3 wiersze x 4 kolumny ---
        self.subSizer_capabilities = wx.GridBagSizer(self.xBorder, self.yBorder)
        caps_cols = 4
        caps_slots = list(CAPABILITY_ORDER)
        while len(caps_slots) < 2 * caps_cols:
            caps_slots.append(None)
        for idx, name in enumerate(caps_slots):
            if name is not None:
                bmp = self.bitmaps.get(name, wx.NullBitmap)
                b = bt.GenBitmapButton(self, -1, name=str(name), bitmap=bmp)
            else:
                b = bt.GenButton(self, -1, name='empty')
            b.SetBackgroundColour(self.backgroundColour)
            b.SetBezelWidth(3)
            b.Bind(event, self.onPress)
            self.subSizer_capabilities.Add(b, (idx / caps_cols, idx % caps_cols), wx.DefaultSpan, wx.EXPAND)
        bBack2 = bt.GenBitmapButton(self, -1, name='back', bitmap=self.backBitmap)
        bBack2.SetBackgroundColour(self.backgroundColour)
        bBack2.SetBezelWidth(3)
        bBack2.Bind(event, self.onPress)
        self.subSizer_capabilities.Add(bBack2, (2, 0), (1, caps_cols), wx.EXPAND)
        for r in range(3):
            self.subSizer_capabilities.AddGrowableRow(r)
        for c in range(caps_cols):
            self.subSizer_capabilities.AddGrowableCol(c)

        # --- plansza wartosci: 3 wiersze x 4 kolumny ---
        self.subSizer_values = wx.GridBagSizer(self.xBorder, self.yBorder)
        val_cols = 4
        for idx in range(2 * val_cols):
            b = bt.GenButton(self, -1, name='empty')
            b.SetBackgroundColour(self.backgroundColour)
            b.SetBezelWidth(3)
            b.Bind(event, self.onPress)
            self.subSizer_values.Add(b, (idx / val_cols, idx % val_cols), wx.DefaultSpan, wx.EXPAND)
        bBack3 = bt.GenBitmapButton(self, -1, name='back', bitmap=self.backBitmap)
        bBack3.SetBackgroundColour(self.backgroundColour)
        bBack3.SetBezelWidth(3)
        bBack3.Bind(event, self.onPress)
        self.subSizer_values.Add(bBack3, (2, 0), (1, val_cols), wx.EXPAND)
        for r in range(3):
            self.subSizer_values.AddGrowableRow(r)
        for c in range(val_cols):
            self.subSizer_values.AddGrowableCol(c)

        # dodaj wszystkie plansze do mainSizer, pokazuj tylko devices
        self.mainSizer.Add(self.subSizer_devices,      proportion=1, flag=wx.EXPAND | wx.ALL, border=self.xBorder)
        self.mainSizer.Add(self.subSizer_capabilities, proportion=1, flag=wx.EXPAND | wx.ALL, border=self.xBorder)
        self.mainSizer.Add(self.subSizer_values,       proportion=1, flag=wx.EXPAND | wx.ALL, border=self.xBorder)

        self.mainSizer.Show(item=self.subSizer_capabilities, show=False, recursive=True)
        self.mainSizer.Show(item=self.subSizer_values,       show=False, recursive=True)

        self.SetSizer(self.mainSizer)
        self.Layout()

        self.numberOfRows    = [2]
        self.numberOfColumns = [3]

    #-------------------------------------------------------------------------
    def _show_panel(self, panel_name):
        self.iotPanel = panel_name
        self.mainSizer.Show(item=self.subSizer_devices,      show=(panel_name == PANEL_DEVICES),      recursive=True)
        self.mainSizer.Show(item=self.subSizer_capabilities, show=(panel_name == PANEL_CAPABILITIES), recursive=True)
        self.mainSizer.Show(item=self.subSizer_values,       show=(panel_name == PANEL_VALUES),       recursive=True)
        self.SetSizer(self.mainSizer)
        self.Layout()

        if panel_name == PANEL_DEVICES:
            self.numberOfRows    = [2]
            self.numberOfColumns = [3]
        elif panel_name == PANEL_CAPABILITIES:
            self.numberOfRows    = [3]
            self.numberOfColumns = [4]
        elif panel_name == PANEL_VALUES:
            self.numberOfRows    = [3]
            self.numberOfColumns = [4]

        self.flag             = 'row'
        self.rowIteration     = 0
        self.columnIteration  = 0
        self.emptyRowIteration    = 0
        self.emptyColumnIteration = 0

    #-------------------------------------------------------------------------
    def _current_sizer(self):
        if self.iotPanel == PANEL_DEVICES:
            return self.subSizer_devices
        elif self.iotPanel == PANEL_CAPABILITIES:
            return self.subSizer_capabilities
        else:
            return self.subSizer_values

    #-------------------------------------------------------------------------
    def _fill_values_panel(self, capability):
        if capability == 'brightness':
            values = BRIGHTNESS_VALUES
        elif capability == 'color':
            values = COLOR_VALUES
        elif capability == 'temperature':
            values = TEMPERATURE_VALUES
        elif capability == 'effects':
            values = EFFECT_VALUES
        else:
            return

        val_cols = 4
        slots = list(values)
        while len(slots) < 2 * val_cols:
            slots.append(None)

        if self.control != 'tracker':
            event = wx.EVT_LEFT_DOWN
        else:
            event = wx.EVT_BUTTON

        # zamień przyciski w subSizer_values (pierwsze 12 pozycji)
        while self.subSizer_values.GetChildren():
            item = self.subSizer_values.GetItem(0)
            old_b = item.GetWindow()
            self.subSizer_values.Detach(old_b)
            old_b.Destroy()

        for idx, name in enumerate(slots):
            if name is not None:
                bmp = self.bitmaps.get(name, wx.NullBitmap)
                b = bt.GenBitmapButton(self, -1, name=str(name), bitmap=bmp)
            else:
                b = bt.GenButton(self, -1, name='empty')
            b.SetBackgroundColour(self.backgroundColour)
            b.SetBezelWidth(3)
            b.Bind(event, self.onPress)
            self.subSizer_values.Add(b, (idx / val_cols, idx % val_cols), wx.DefaultSpan, wx.EXPAND)

        bBack = bt.GenBitmapButton(self, -1, name='back', bitmap=self.backBitmap)
        bBack.SetBackgroundColour(self.backgroundColour)
        bBack.SetBezelWidth(3)
        bBack.Bind(event, self.onPress)
        self.subSizer_values.Add(bBack, (2, 0), (1, val_cols), wx.EXPAND)

        self.Layout()

    #-------------------------------------------------------------------------
    def _fill_capabilities_panel(self):
        caps_cols = 4
        slots = []
        for cap in CAPABILITY_ORDER:
            if cap == 'reset' or cap in self.capabilities:
                slots.append(cap)
        while len(slots) < 2 * caps_cols:
            slots.append(None)

        if self.control != 'tracker':
            event = wx.EVT_LEFT_DOWN
        else:
            event = wx.EVT_BUTTON

        while self.subSizer_capabilities.GetChildren():
            item = self.subSizer_capabilities.GetItem(0)
            old_b = item.GetWindow()
            self.subSizer_capabilities.Detach(old_b)
            old_b.Destroy()

        for idx, name in enumerate(slots):
            if name is not None:
                bmp = self.bitmaps.get(name, wx.NullBitmap)
                b = bt.GenBitmapButton(self, -1, name=str(name), bitmap=bmp)
            else:
                b = bt.GenButton(self, -1, name='empty')
            b.SetBackgroundColour(self.backgroundColour)
            b.SetBezelWidth(3)
            b.Bind(event, self.onPress)
            self.subSizer_capabilities.Add(b, (idx / caps_cols, idx % caps_cols), wx.DefaultSpan, wx.EXPAND)

        bBack = bt.GenBitmapButton(self, -1, name='back', bitmap=self.backBitmap)
        bBack.SetBackgroundColour(self.backgroundColour)
        bBack.SetBezelWidth(3)
        bBack.Bind(event, self.onPress)
        self.subSizer_capabilities.Add(bBack, (2, 0), (1, caps_cols), wx.EXPAND)

        self.Layout()

    #-------------------------------------------------------------------------
    def createBindings(self):
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    #-------------------------------------------------------------------------
    def initializeTimer(self):
        self.stoper = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.timerUpdate, self.stoper)
        if self.control != 'tracker':
            self.stoper.Start(self.timeGap)

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
            if __name__ == '__main__':
                self.Destroy()
            else:
                self.parent.Destroy()
                self.Destroy()
        else:
            event.Veto()
            if self.control != 'tracker':
                self.mousePosition = self.winWidth - 8 - self.xBorder, self.winHeight - 8 - self.yBorder
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
                self.label = event.GetEventObject().GetName().encode('utf-8')
                self.stoper.Start(0.15 * self.timeGap)
            self._handleLabel(self.label)

        else:
            self.numberOfPresses += 1

            if self.numberOfPresses == 1:

                if self.flag == 'rest':
                    self.flag = 'row'

                elif self.flag == 'row':
                    row = self.rowIteration - 1
                    cols = self.numberOfColumns[0]
                    rows = self.numberOfRows[0]

                    # ostatni wiersz to BACK - dziala od razu na poziomie wiersza
                    if row == rows - 1:
                        if self.pressSound.lower() == 'voice':
                            self.powrotSound.play()
                        self._goBack()
                        return

                    buttonsToHighlight = range(row * cols, row * cols + cols)

                    if self.pressSound == 'voice':
                        if row == 0: self.oneSound.play()
                        elif row == 1: self.twoSound.play()
                        elif row == 2: self.threeSound.play()
                        elif row == 3: self.fourSound.play()

                    sizer = self._current_sizer()
                    for i in buttonsToHighlight:
                        item = sizer.GetItem(i)
                        b = item.GetWindow()
                        b.SetBackgroundColour(self.selectionColour)
                        b.SetFocus()

                    self.stoper.Stop()
                    time.sleep(self.selectionTime / 1000.)
                    self.stoper.Start(self.timeGap)

                    self.flag = 'columns'
                    self.columnIteration = 0

                elif self.flag == 'columns':
                    row  = self.rowIteration - 1
                    cols = self.numberOfColumns[0]
                    pos  = row * cols + self.columnIteration - 1

                    sizer = self._current_sizer()
                    item  = sizer.GetItem(pos)
                    selectedButton = item.GetWindow()
                    selectedButton.SetBackgroundColour(self.selectionColour)
                    selectedButton.SetFocus()
                    self.Update()

                    label = selectedButton.GetName().encode('utf-8')

                    if self.pressSound == 'voice':
                        self.stoper.Stop()
                        if label == 'empty':
                            self.pusteSound.play()
                        time.sleep((self.selectionTime + self.timeGap) / 1000.)
                        self.stoper.Start(self.timeGap)

                    self._handleLabel(label)

                    self.flag = 'row'
                    self.rowIteration = 0
                    self.columnIteration = 0
                    self.emptyRowIteration = 0
                    self.emptyColumnIteration = 0

            else:
                pass

    #-------------------------------------------------------------------------
    def _goBack(self):
        if self.iotPanel == PANEL_DEVICES:
            self.onExit()
        elif self.iotPanel == PANEL_CAPABILITIES:
            self._show_panel(PANEL_DEVICES)
        elif self.iotPanel == PANEL_VALUES:
            self._show_panel(PANEL_CAPABILITIES)

    #-------------------------------------------------------------------------
    def _handleLabel(self, label):

        if label == 'back':
            if self.switchSound.lower() == 'voice':
                self.powrotSound.play()
            self._goBack()
            return

        if label == 'empty':
            return

        if self.iotPanel == PANEL_DEVICES:
            result = iot_client.get_capabilities(label)
            if result is None:
                self._speak_error(u'Błąd pobierania danych urządzenia')
                return
            self.selected_device  = label
            self.capabilities     = result.get('capabilities', {})
            self._fill_capabilities_panel()
            self._show_panel(PANEL_CAPABILITIES)

        elif self.iotPanel == PANEL_CAPABILITIES:
            if label == 'power':
                if self.switchSound.lower() == 'voice':
                    self._speak('power')
                result = iot_client.control_device(self.selected_device, 'power', 'toggle')
                if result is None:
                    self._speak_error(u'Błąd sterowania urządzeniem')
            elif label == 'reset':
                if self.switchSound.lower() == 'voice':
                    self._speak('reset')
                result = iot_client.reset_device(self.selected_device)
                if result is None:
                    self._speak_error(u'Błąd sterowania urządzeniem')
            elif label in CAPABILITY_ORDER:
                self.selected_capability = label
                self._fill_values_panel(label)
                self._show_panel(PANEL_VALUES)

        elif self.iotPanel == PANEL_VALUES:
            cap = self.selected_capability
            if cap == 'effects':
                if label == 'stop':
                    result = iot_client.stop_effect(self.selected_device)
                else:
                    result = iot_client.device_effect(self.selected_device, label)
            else:
                try:
                    val = int(label)
                except (ValueError, TypeError):
                    val = label
                result = iot_client.control_device(self.selected_device, cap, val)

            if result is None:
                self._speak_error(u'Błąd sterowania urządzeniem')
            else:
                if self.switchSound.lower() == 'voice':
                    try:
                        self._speak(int(label))
                    except (ValueError, TypeError):
                        self._speak(label)

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

            sizer = self._current_sizer()
            rows  = self.numberOfRows[0]
            cols  = self.numberOfColumns[0]

            if self.flag == 'row':

                if self.emptyRowIteration == self.maxEmptyRowIteration:
                    if self.switchSound.lower() == 'voice':
                        self.usypiamSound.play()
                    self.flag = 'rest'
                    self.emptyRowIteration = 0
                    self.rowIteration = 0
                    items = sizer.GetChildren()
                    for item in items:
                        b = item.GetWindow()
                        b.SetBackgroundColour(self.backgroundColour)
                        b.SetFocus()

                else:
                    self.rowIteration = self.rowIteration % rows

                    items = sizer.GetChildren()
                    for item in items:
                        b = item.GetWindow()
                        b.SetBackgroundColour(self.backgroundColour)
                        b.SetFocus()

                    if self.rowIteration == rows - 1:
                        self.emptyRowIteration += 1
                        scope = self.rowIteration * cols,
                        if self.switchSound == 'voice':
                            self.powrotSound.play()
                    else:
                        scope = range(self.rowIteration * cols, self.rowIteration * cols + cols)
                        if self.switchSound == 'voice':
                            if self.rowIteration == 0: self.oneSound.play()
                            elif self.rowIteration == 1: self.twoSound.play()
                            elif self.rowIteration == 2: self.threeSound.play()
                            elif self.rowIteration == 3: self.fourSound.play()

                    for i in scope:
                        item = sizer.GetItem(i)
                        b = item.GetWindow()
                        b.SetBackgroundColour(self.scanningColour)
                        b.SetFocus()

                    self.rowIteration += 1

            elif self.flag == 'columns':

                if self.emptyColumnIteration == self.maxEmptyColumnIteration:
                    self.flag = 'row'
                    self.rowIteration = 0
                    self.columnIteration = 0
                    self.emptyColumnIteration = 0
                    self.emptyRowIteration = 0
                    items = sizer.GetChildren()
                    for item in items:
                        b = item.GetWindow()
                        b.SetBackgroundColour(self.backgroundColour)
                        b.SetFocus()

                else:
                    self.columnIteration = self.columnIteration % cols

                    if self.columnIteration == cols - 1:
                        self.emptyColumnIteration += 1

                    items = sizer.GetChildren()
                    for item in items:
                        b = item.GetWindow()
                        b.SetBackgroundColour(self.backgroundColour)
                        b.SetFocus()

                    pos = (self.rowIteration - 1) * cols + self.columnIteration
                    item = sizer.GetItem(pos)
                    b = item.GetWindow()
                    b.SetBackgroundColour(self.scanningColour)
                    b.SetFocus()

                    label = b.GetName().encode('utf-8')
                    if self.switchSound.lower() == 'voice':
                        if label == 'back':
                            self.powrotSound.play()
                        elif label == 'empty':
                            self.pusteSound.play()
                        else:
                            try:
                                self._speak(int(label))
                            except (ValueError, TypeError):
                                self._speak(label)

                    self.columnIteration += 1

            if self.flag != 'rest':
                if self.switchSound.lower() == 'on':
                    self.switchingSound.play()


#=============================================================================
if __name__ == '__main__':
    app = wx.App(False)
    frame = iot(parent=None, id=-1)
    frame.Show(True)
    app.MainLoop()