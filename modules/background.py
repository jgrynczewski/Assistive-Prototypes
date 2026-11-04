#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""Film YouTube w tle - jeden naraz.

W odtwarzaczu (youtube2.PlayerFrame) przycisk W TLE chowa okno, a film gra
dalej; uzytkownik korzysta z reszty AP (rysuje, gra). Dotyczy filmow
z YouTube (WYSZUKAJ, ULUBIONE) i z Wicero. Powrot: kafel ODTWARZACZ w menu
YOUTUBE i w NOWE (returnTo); zatrzymanie: EXIT w odtwarzaczu.

Odtwarzacze z W TLE: youtube2.PlayerFrame (WYSZUKAJ, ULUBIONE, Wicero)
i at_youtube.youtube (LOSOWE) - wspolny kod w BackgroundPlayer; nowy film
zamyka ten z tla (jeden naraz).

Moduly, ktore same graja albo mowia (Wicero, MUZYKA, RADIO, AUDIOBOOKI,
TV), na czas swojego dzialania pauzuja
film w tle i wznawiaja go po wyjsciu - pause(owner) / resume(owner) albo
guard(klasa, owner). Muzyka, radio i audiobooki graja dalej po wyjsciu
z modulu (smplayer w tle) - wtedy film w tle sie nie wznawia. W druga
strone: film YouTube, ktory zaczyna grac, zamyka smplayer (stopMusic).
"""

import logging
import os

_log = logging.getLogger('background')

_player = None          # PlayerFrame schowany w tle
_pausedBy = set()       # moduly, ktore wstrzymaly film (wznowienie, gdy wszystkie wyjda)
_wasPlaying = False     # czy film gral, zanim pierwszy modul go wstrzymal
_heldByUs = False       # film stoi przez nas (nie przez uzytkownika) - ODTWARZACZ go wznawia


def player():
    """Odtwarzacz w tle albo None (tez gdy okno juz zniszczone)."""
    global _player
    if _player is not None and not _player:  # wx: zniszczone okno jest "falsy"
        _player = None
    return _player


def has():
    return player() is not None


def put(frame):
    """frame (PlayerFrame) przechodzi w tlo - zastepuje poprzedni."""
    global _player, _wasPlaying, _heldByUs
    if player() is not None and _player is not frame:
        stop()
    _player = frame
    _pausedBy.clear()
    _wasPlaying = _heldByUs = False


def take():
    """Odtwarzacz wraca z tla na ekran - zwraca go (albo None). Film
    wstrzymany automatycznie (inny modul) wraca grajac - uzytkownik chce go
    ogladac; wstrzymany przez uzytkownika (PLAY_PAUSE) zostaje wstrzymany."""
    global _player, _heldByUs
    frame = player()
    _player = None
    if frame is not None and _heldByUs:
        _vlc(frame, 'play')
    _pausedBy.clear()
    _heldByUs = False
    return frame


def returnTo(menu):
    """Kafel ODTWARZACZ (menu YOUTUBE albo NOWE): film z tla wraca na ekran,
    po EXIT wroci do `menu`. False - nic nie gra w tle (kafel jak PUSTE)."""
    frame = take()
    if frame is None:
        return False
    frame.returnFromBackground(menu)
    return True


def stop():
    """Zatrzymaj i zamknij film w tle (np. przed otwarciem nowego odtwarzacza)."""
    global _player, _heldByUs
    frame = player()
    _player = None
    _pausedBy.clear()
    _heldByUs = False
    if frame is not None:
        frame.closeBackground()


def pause(owner):
    """Modul `owner` zaczyna grac / mowic - wstrzymaj film w tle."""
    global _wasPlaying, _heldByUs
    frame = player()
    if frame is None:
        return
    if not _pausedBy and not _heldByUs:
        _wasPlaying = bool(_vlc(frame, 'is_playing'))
        if _wasPlaying:
            _vlc(frame, 'pause')
            _heldByUs = True
    _pausedBy.add(owner)


def resume(owner):
    """Modul `owner` skonczyl - wznow film, gdy nikt go juz nie wstrzymuje
    i nie gra inny odtwarzacz (smplayer: muzyka, radio, audiobook)."""
    global _heldByUs
    frame = player()
    _pausedBy.discard(owner)
    if frame is None or _pausedBy or not _heldByUs:
        return
    if _smplayerRunning():
        _log.info('film w tle zostaje wstrzymany - gra smplayer')
        return
    _vlc(frame, 'play')
    _heldByUs = False


def stopMusic():
    """Film YouTube zaczyna grac (nowy albo powrot przez ODTWARZACZ) - zamknij
    smplayer (muzyka, radio, audiobook), jak robi to sama MUZYKA przy zmianie
    albumu. Gra to, co uzytkownik wybral ostatnio - nic sie nie naklada."""
    if _smplayerRunning():
        _log.info('film YouTube - zamykam smplayer')
        os.system('smplayer -send-action quit &')


def guard(cls, owner):
    """Klasa modulu (wx.Frame z onExit): przy otwarciu pauza filmu w tle,
    przy wyjsciu (onExit) wznowienie. Bez zmian w kodzie modulu."""
    init, onExit = cls.__init__, cls.onExit

    def __init__(self, *args, **kwargs):
        pause(owner)
        init(self, *args, **kwargs)

    def guardedExit(self, *args, **kwargs):
        result = onExit(self, *args, **kwargs)
        resume(owner)
        return result

    cls.__init__ = __init__
    cls.onExit = guardedExit
    return cls


class BackgroundPlayer(object):
    """Domieszka odtwarzacza z przyciskiem W TLE (youtube2.PlayerFrame,
    at_youtube.youtube - LOSOWE). Wymaga atrybutow odtwarzacza: player (VLC),
    stoper, parent, control, timeGap, mouseCursor / mousePosition,
    _ffmpeg_proc, _intentional_stop, db; opcjonalnie wTleSound."""

    def _sayBackground(self):
        sound = getattr(self, 'wTleSound', None)
        if sound:
            sound.play()
        else:
            from modules.board import say  # glos AP, dopoki nie ma sounds/do_tła.ogg
            say(u'Do tła')

    def _toBackground(self):
        """W TLE: okno znika, film gra dalej; AP wraca do najblizszego menu
        z kaflem ODTWARZACZ (YOUTUBE albo NOWE) - plansze po drodze (galeria
        fraz; w Wicero: ekran przed filmem, typy, nadawcy) zamykaja sie przez
        swoje onExit, ktore pokazuje rodzica."""
        self.stoper.Stop()
        self.MakeModal(False)
        self.Hide()
        put(self)
        frame = self.parent
        if hasattr(frame, 'refreshPlayerTile'):  # menu YOUTUBE (ULUBIONE, LOSOWE)
            frame.Show(True)
            if self.control != 'tracker':
                frame.stoper.Start(frame.timeGap)
            return
        while frame is not None and not hasattr(frame, 'refreshPlayerTile'):
            parent = getattr(frame, 'parent', None)
            if hasattr(frame, 'onExit'):
                frame.onExit()
            frame = parent

    def returnFromBackground(self, menu):
        """Kafel ODTWARZACZ: odtwarzacz wraca na ekran; EXIT wroci do `menu`."""
        stopMusic()  # film wraca - muzyka z MUZYKI / RADIA milknie (B5)
        self.parent = menu  # poprzedni rodzic mogl byc zamkniety
        menu.stoper.Stop()
        menu.Hide()
        self.flag = 'rest'
        self.colIteration = 0
        self.countColumns = 0
        self.countRows = 0
        # wx 2.8: MakeModal(True) kazdego okna otwartego w miedzyczasie
        # (menu YouTube, NOWE...) wylacza WSZYSTKIE inne okna, takze to
        # ukryte - bez Enable przyciski paska zostaja szare (test B3)
        self.Enable(True)
        self.Show(True)
        self.Raise()
        self.MakeModal(True)
        if self.control != 'tracker':
            self.mouseCursor.move(*self.mousePosition)
            self.stoper.Start(self.timeGap)

    def closeBackground(self):
        """Zatrzymaj film w tle i zamknij okno (bez pokazywania rodzica)."""
        self._intentional_stop = True
        if self._ffmpeg_proc:
            self._ffmpeg_proc.kill()
        self.player.stop()
        self.db.close()
        self.stoper.Stop()
        self.Destroy()

    def inBackground(self):
        return player() is self


def topWindow(window):
    """Najwyzsze okno nad `window` (glowne menu AP) - rodzic wx odtwarzacza,
    ktory moze isc w tlo: zamkniecie menu YouTube / galerii / Wicero go nie
    zamyka (gra do zamkniecia AP)."""
    while window is not None and window.GetParent() is not None:
        window = window.GetParent()
    return window


def _vlc(frame, method):
    try:
        return getattr(frame.player, method)()
    except Exception as e:
        _log.error('VLC %s: %r', method, e)
        return None


def _smplayerRunning():
    try:
        import psutil
        for pid in psutil.pids():
            try:
                name = psutil.Process(pid).name
                name = name() if callable(name) else name  # rozne wersje psutil
            except Exception:
                continue
            if name == 'smplayer':
                return True
    except Exception as e:
        _log.error('psutil: %r', e)
    return False
