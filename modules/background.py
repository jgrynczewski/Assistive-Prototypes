#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""Film YouTube w tle - jeden naraz.

W odtwarzaczu (youtube2.PlayerFrame) przycisk W TLE chowa okno, a film gra
dalej; uzytkownik korzysta z reszty AP (rysuje, gra). Dotyczy filmow
z YouTube (WYSZUKAJ, ULUBIONE) i z Wicero. Powrot: kafel ODTWARZACZ w menu
YOUTUBE i w NOWE (returnTo); zatrzymanie: EXIT w odtwarzaczu.

Moduly, ktore same graja albo mowia (Wicero, gra "Tajemnica zegara",
LOSOWE, MUZYKA, RADIO, AUDIOBOOKI, TV), na czas swojego dzialania pauzuja
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
