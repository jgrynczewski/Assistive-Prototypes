#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""Plansza GRY PRZYGODOWE (kafelek na planszy gier, new_games.py): gry
czytane na glos z serwera ap-gra - wbudowane (Tajemnica zegara, Ostatnia
zwrotka) i stworzone przez uzytkownika z AI (kreator gier,
docs/kreator-gier.md w ap-gra).

Uklad 3 x 5, skanowanie jak na innych planszach (wiersze -> przyciski):
    NOWA GRA | gra | gra | gra | gra
    gra      | gra | gra | gra | gra
    gra      | gra | gra | DALEJ | POWRÓT
NOWA GRA - rozmowa z AI o nowej grze (modules/kreator.py). Gier na strone
jest PER_PAGE; wiecej - DALEJ przechodzi na nastepna strone (z ostatniej na
pierwsza). Lista jest budowana z serwera przy kazdym powrocie na plansze -
nowa gra pojawia sie bez zmiany kodu AP.

Kafelki: gry wbudowane - ich ikony; gry z kreatora - obrazek z serwera
(pierwsza klatka animacji) z tytulem; gra w trakcie tworzenia i nieudana -
napis, a po wybraniu komunikat glosowy. Tytuly czyta glos narratora.
"""

import os, sys, logging, datetime

import wx
import wx.lib.buttons as bt
from pygame import mixer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gra_client
import kreator_client
from modules import board, gra, kreator
from modules.board import say, resume

_log = logging.getLogger('gra')

ROWS, COLUMNS = 3, 5
PER_PAGE = ROWS * COLUMNS - 3   # bez NOWA GRA, DALEJ i POWRÓT
FAILED_DAYS = 3                 # nieudana gra widoczna (z komunikatem) tyle dni

# Ikony gier wbudowanych, w tej kolejnosci na poczatku listy
BUILTIN = [('sala_pod_zegarem', 'icons/new_games/tajemnica_zegara.png'),
           ('ostatnia_zwrotka', 'icons/new_games/ostatnia_zwrotka.png')]


#=============================================================================
def _voice(interface, name, fallback):
    """(tekst, nagranie, dlugosc) stalego przycisku z serwera."""
    item = interface.get(name) or {}
    return (item.get('text') or fallback, item.get('path'), (item.get('audio') or {}).get('duration'))


def _recent(created):
    """Czy nieudana gra jest z ostatnich FAILED_DAYS dni ("2026-11-08T12:00:00")."""
    try:
        when = datetime.datetime.strptime(created[:19], '%Y-%m-%dT%H:%M:%S')
    except (TypeError, ValueError):
        return False
    return datetime.datetime.now() - when < datetime.timedelta(days=FAILED_DAYS)


def load_tiles():
    """W watku: kafelki z serwera gry i kreatora, z nagraniami tytulow i
    obrazkami. Serwer gry nie dziala - GraError; kreator nie dziala - bez
    gier w trakcie tworzenia i bez NOWA GRA (komunikat po wybraniu)."""
    health = gra_client.health()
    interface = health.get('interface', {})
    for item in interface.values():
        item['path'] = gra_client.audio_file(item.get('audio'))
    try:
        made = kreator_client.games()
        creator = kreator_client.health().get('interface', {})
        for item in creator.values():
            item['path'] = kreator_client.audio_file(item.get('audio'))
    except gra_client.GraError:
        made, creator = [], {}

    games = gra_client.games()
    order = [gid for gid, icon in BUILTIN]
    games.sort(key=lambda g: (order.index(g['id']) if g['id'] in order else len(order),
                              not g.get('builtin'), g['id']))
    icons = dict(BUILTIN)
    tiles = []
    for game in games:
        title_audio = game.get('title_audio')
        tiles.append({'key': 'GRA:%s' % game['id'], 'kind': 'gra', 'title': game['title'], 'info': game,
                      'icon': icons.get(game['id']),
                      'image': None if game.get('builtin') else gra_client.tile_file(game),
                      'path': gra_client.audio_file(title_audio),
                      'duration': (title_audio or {}).get('duration')})
    ready = set(g['id'] for g in games)
    for task in made:
        if task['status'] == 'w_toku' or (task['status'] == 'nieudana' and _recent(task.get('utworzona'))):
            tiles.append({'key': 'TWORZONA:%s' % task['id'], 'kind': task['status'], 'title': task['tytul'],
                          'path': None, 'duration': None})
        elif task['status'] == 'gotowa' and task['gra'] not in ready:
            _log.warning('gra %s gotowa w kreatorze, a nie ma jej na serwerze gry', task['gra'])
    return {'tiles': tiles, 'interface': interface, 'creator': creator}


def open_przygody(parent):
    """Wejscie z planszy gier. parent.stoper jest zatrzymany przez wywolujacego."""

    def on_success(data):
        AdventuresBoard(parent, data).Show(True)
        parent.Hide()

    def on_error(e):
        say(gra.error_text(e))
        resume(parent)

    gra.run_in_thread(load_tiles, on_success, on_error)


#=============================================================================
class AdventuresBoard(board.Board):

    title = 'AP Gry przygodowe'

    def __init__(self, parent, data):
        self.data = data
        self.page = 0
        self.bitmaps = {}        # klucz kafelka -> bitmapa (rozmiar staly)
        self.voicePaths = {}
        self.channel = None
        self.sounds = {}
        self.shownOnce = False
        self.loading = False
        buttons = [{'key': 'POLE%d' % i, 'text': u''} for i in range(ROWS * COLUMNS)]
        board.Board.__init__(self, parent, buttons, rows=ROWS, columns=COLUMNS)
        self.showPage(0)

    #-------------------------------------------------------------------------
    def _tileSize(self):
        """Rozmiar obrazka na przycisku: komorka siatki minus marginesy."""
        width = (self.winWidth - (COLUMNS + 1) * self.xBorder) / COLUMNS
        height = (self.winHeight - (ROWS + 1) * self.xBorder - 2 * self.yBorder) / ROWS
        return max(32, int(width * 0.9)), max(32, int(height * 0.85))

    def makeButton(self, parent, button, font):
        b = bt.GenBitmapButton(parent, -1, bitmap=wx.EmptyBitmap(*self._tileSize()), name=button['key'])
        b.SetBackgroundColour(self.backgroundColour)
        b.SetBezelWidth(3)
        b.Bind(self.pressEvent(), self.onPress)
        return b

    def _canvas(self):
        width, height = self._tileSize()
        bitmap = wx.EmptyBitmap(width, height)
        dc = wx.MemoryDC()  # wx 2.8: bez bitmapy w konstruktorze
        dc.SelectObject(bitmap)
        dc.SetBackground(wx.Brush(self.backgroundColour))
        dc.Clear()
        return bitmap, dc, width, height

    def _text(self, dc, text, top, bottom, width, size):
        """Wysrodkowany, zawijany tekst miedzy top a bottom."""
        while True:
            dc.SetFont(wx.Font(size, wx.SWISS, wx.NORMAL, wx.BOLD))
            lines = gra.wrap(dc, text, width * 0.92).split(u'\n')
            lineHeight = dc.GetTextExtent(u'ĄŻgj')[1]
            if lineHeight * len(lines) <= bottom - top or size <= 8:
                break
            size -= 2
        dc.SetTextForeground(self.textColour)
        y = top + (bottom - top - lineHeight * len(lines)) / 2.0
        for line in lines:  # wx 2.8: wspolrzedne calkowite
            dc.DrawText(line, int((width - dc.GetTextExtent(line)[0]) / 2), int(y))
            y += lineHeight

    def _scaled(self, path, width, height):
        image = wx.Image(path)
        if not image.IsOk():
            return None
        scale = min(width / float(image.GetWidth()), height / float(image.GetHeight()))
        return image.Scale(max(1, int(image.GetWidth() * scale)), max(1, int(image.GetHeight() * scale)),
                           wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()

    def _bitmap(self, tile):
        """Bitmapa kafelka (raz na kafelek)."""
        if tile['key'] in self.bitmaps:
            return self.bitmaps[tile['key']]
        bitmap, dc, width, height = self._canvas()
        size = self.tableFontSize * 2 / 3
        picture = None
        if tile.get('icon'):
            picture = self._scaled(self.pathToAP + tile['icon'], width, height)
            if picture:
                dc.DrawBitmap(picture, (width - picture.GetWidth()) // 2, (height - picture.GetHeight()) // 2, True)
        elif tile.get('image'):
            # Gra z kreatora: obrazek nad tytulem
            band = int(height * 0.28)
            picture = self._scaled(tile['image'], width, height - band)
            if picture:
                dc.DrawBitmap(picture, (width - picture.GetWidth()) // 2, 0, True)
                self._text(dc, tile['title'], height - band, height, width, size)
        if picture is None:
            note = {'w_toku': u'(tworzy się)', 'nieudana': u'(nie udało się)'}.get(tile['kind'])
            text = tile['title'] + (u'\n' + note if note else u'')
            self._text(dc, text, 0, height, width, size)
        dc.SelectObject(wx.NullBitmap)
        self.bitmaps[tile['key']] = bitmap
        return bitmap

    #-------------------------------------------------------------------------
    def pages(self):
        return max(1, (len(self.data['tiles']) + PER_PAGE - 1) // PER_PAGE)

    def showPage(self, page):
        """Kafelki strony: NOWA GRA, gry strony, puste pola, DALEJ (gdy jest
        wiecej stron), POWRÓT."""
        self.page = page % self.pages()
        interface = self.data['interface']
        text, path, duration = _voice(interface, 'nowa_gra', u'Nowa gra')
        slots = [{'key': 'NOWA', 'kind': 'przycisk', 'title': text.upper(), 'path': path, 'duration': duration}]
        slots += self.data['tiles'][self.page * PER_PAGE:(self.page + 1) * PER_PAGE]
        while len(slots) < ROWS * COLUMNS - 2:
            slots.append({'key': 'PUSTE'})
        if self.pages() > 1:
            text, path, duration = _voice(interface, 'dalej', u'Dalej')
            slots.append({'key': 'DALEJ', 'kind': 'przycisk', 'title': text.upper(), 'path': path,
                          'duration': duration})
        else:
            slots.append({'key': 'PUSTE'})
        slots.append({'key': 'POWROT'})

        self.slots = dict((slot['key'], slot) for slot in slots)
        self.labels = []
        for slot, b in zip(slots, self.buttonWindows):
            key = slot['key']
            if key == 'PUSTE':
                b.SetBitmapLabel(self._file('icons/modules/puste.png'))
            elif key == 'POWROT':
                b.SetBitmapLabel(self._file('icons/back.png'))
            else:
                b.SetBitmapLabel(self._bitmap(slot))
                self.speech[key] = slot['title']
                self.voicePaths[key] = slot.get('path')
            b.SetName(key)
            b.Refresh()
            self.labels.append(key)
        self.resetScanning()
        self._clearHighlight()
        self.Layout()

    def _file(self, path):
        if path not in self.bitmaps:
            self.bitmaps[path] = wx.BitmapFromImage(wx.Image(self.pathToAP + path))
        return self.bitmaps[path]

    #-------------------------------------------------------------------------
    def refresh(self):
        """Lista gier od nowa (powrot z gry albo z rozmowy) - w tle."""
        if self.loading:
            return
        self.loading = True

        def on_success(data):
            self.loading = False
            if not self:
                return
            self.data = data
            self.bitmaps = dict((k, v) for k, v in self.bitmaps.items() if k.startswith('icons/'))
            self.showPage(self.page)

        def on_error(e):
            self.loading = False  # zostaje stara lista; gra sama powie, gdy serwer nie dziala

        gra.run_in_thread(load_tiles, on_success, on_error)

    def Show(self, show=True):
        result = board.Board.Show(self, show)
        if show and self.shownOnce:
            self.refresh()
        self.shownOnce = self.shownOnce or show
        return result

    #-------------------------------------------------------------------------
    def _voice(self, name):
        """Kafelek przy skanowaniu: nagranie tytulu glosem narratora; bez
        nagrania - milena (Board)."""
        path = self.voicePaths.get(name)
        if path:
            if path not in self.sounds:
                try:
                    self.sounds[path] = mixer.Sound(path)
                except Exception as e:
                    _log.error('nagranie %s: %r', path, e)
                    self.sounds[path] = None
            if self.sounds[path] is not None:
                if self.channel is not None:
                    self.channel.stop()
                self.channel = self.sounds[path].play()
                return
        board.Board._voice(self, name)

    def _say(self, interface, name, fallback):
        """Komunikat glosem narratora (nagranie kreatora) albo milena."""
        text, path, duration = _voice(interface, name, fallback)
        sound = None
        if path:
            try:
                sound = mixer.Sound(path)
            except Exception as e:
                _log.error('nagranie %s: %r', path, e)
        if sound is not None:
            sound.play()
        else:
            say(text)

    def onSelect(self, key):
        slot = self.slots.get(key) or {}
        if key == 'NOWA':
            self.stoper.Stop()
            kreator.open_kreator(self)
        elif key == 'DALEJ':
            self.showPage(self.page + 1)
        elif key.startswith('GRA:'):
            info = slot['info']
            self.stoper.Stop()
            gra.open_gra(self, info['id'], None if info.get('builtin') else info)
        elif key.startswith('TWORZONA:'):
            if slot.get('kind') == 'nieudana':
                self._say(self.data['creator'], 'nieudana', u'Nie udało się stworzyć tej gry.')
            else:
                self._say(self.data['creator'], 'w_trakcie', u'Ta gra jeszcze się tworzy.')
