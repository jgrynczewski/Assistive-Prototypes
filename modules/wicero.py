#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""Modul Wicero - filmy od bliskich (ADR-0001: docs/adr/0001-modul-wicero.md).

Nawigacja:
    nowe.py [WICERO] -> SendersBoard (nadawcy) -> TypesBoard (FILMY)
        -> IntroScreen (komentarz, POWTORZ / START / NASTEPNY / POPRZEDNI / POWROT)
        -> WiceroPlayer

Cala logika (kolejnosc filmow, teksty do przeczytania, przypomnienia) jest
w Cloud Functions Wicero - tutaj tylko wyswietlanie i sterowanie.
Komunikacja: wicero_client.py (katalog AP).

Plansza ze skanowaniem (Board) - modules/board.py, wspolna z modulem Gra.

STATUS: napisany bez mozliwosci uruchomienia (brak wx 2.8 / VLC / milena
na komputerze deweloperskim) - do przetestowania na komputerze uzytkownika,
patrz WICERO_PLAN.md.
"""

import os, sys, time, threading, subprocess, logging
from cStringIO import StringIO

import wx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import wicero_client
from modules import youtube2, board, background
# Wspolne z modulem Gra (modules/board.py); nazwy zostaja - uzywaja ich
# nowe.py (wicero.say) i youtube2.py (PRZESLIJ)
from modules.board import say, say_then, resume as _resume, fill as _fill

_log = logging.getLogger('wicero')

VIEWED_FRACTION = 0.85              # obejrzany = 85% dlugosci (jak _isRealEnd w youtube2)
NOTIFY_FIRST_DELAY = 15 * 1000      # pierwsze sprawdzenie po starcie AP [ms]
NOTIFY_INTERVAL = 60 * 1000         # kolejne co minute [ms]
MAX_SENDERS = 5                     # plansza 2x3: 5 nadawcow + POWROT (stronicowanie - pozniej)

# Modul Wicero otwarty (od planszy nadawcow do wyjscia z niej) - Notifier
# wtedy nie oglasza: ani w trakcie filmu, ani przy czytaniu komentarza (T10)
ACTIVE = False

NOTIFIER_LOCK = '/tmp/ap_wicero_notifier.lock'  # jeden Notifier na komputer (T10, BUG 2)


def error_text(error):
    """Komunikat dla WiceroError."""
    if error.kind == 'offline':
        return u'Brak połączenia z internetem.'
    if error.kind == 'token':
        if os.path.exists(wicero_client.TOKEN_FILE):
            return u'Nieprawidłowy token Wicero.'  # serwer odrzucil (zly / uniewazniony)
        return u'Wicero nie jest skonfigurowane.'
    return u'Wystąpił błąd. Spróbuj później.'


def say_error(error):
    say(error_text(error))


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


#=============================================================================
class Board(board.Board):
    """Plansza Wicero - wspolna plansza ze skanowaniem (modules/board.py)."""

    title = 'AP Wicero'


#=============================================================================
class SendersBoard(Board):
    """Nadawcy (imiona) + POWROT."""

    def __init__(self, parent, senders):
        global ACTIVE
        ACTIVE = True
        background.pause('wicero')  # film YouTube w tle czeka (wznowienie w onExit)
        self.senders = dict(('S%d' % i, s) for i, s in enumerate(senders[:MAX_SENDERS]))
        buttons = [{'key': 'S%d' % i, 'text': s['name'], 'speech': s.get('say', s['name'])}
                   for i, s in enumerate(senders[:MAX_SENDERS])]
        Board.__init__(self, parent, _fill(buttons, 6))
        self.shown = False

    def Show(self, show=True):
        # Powrot z planszy typow / filmu (onExit dziecka): liczby nowych mogly
        # sie zmienic - pobierz je w tle (N3: kafel czytal stare "3 nowe filmy")
        if show and self.shown:
            run_in_thread(wicero_client.get_senders, self._refresh,
                          lambda e: None)  # blad juz w wicero.log; zostaja stare teksty
        self.shown = self.shown or show
        return Board.Show(self, show)

    def _refresh(self, senders):
        if not self:  # okno zamkniete w trakcie zapytania
            return
        fresh = dict((s['conversationId'], s) for s in senders)
        for key, sender in self.senders.items():
            sender = fresh.get(sender['conversationId'])
            if sender:
                self.senders[key] = sender
                self.speech[key] = sender.get('say', sender['name'])

    def onExit(self):
        # Wyjscie z modulu Wicero - Notifier znow oglasza (zalegle przy nastepnym takcie)
        global ACTIVE
        ACTIVE = False
        Board.onExit(self)
        background.resume('wicero')

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
        self.shown = False

    def Show(self, show=True):
        # Powrot z ekranu przed filmem - jak w SendersBoard.Show
        if show and self.shown:
            run_in_thread(wicero_client.get_senders, self._refresh, lambda e: None)
        self.shown = self.shown or show
        return Board.Show(self, show)

    def _refresh(self, senders):
        if not self:
            return
        for sender in senders:
            if sender['conversationId'] == self.sender['conversationId']:
                self.sender = sender
                for t in sender['types']:
                    key = t['type'].upper()
                    if key in self.types:
                        self.types[key] = t
                        self.speech[key] = t.get('say', t['label'])

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

        run_in_thread(lambda: wicero_client.get_messages(self.sender['conversationId'], material_type),
                      on_success, on_error)


#=============================================================================
class IntroScreen(Board):
    """Ekran przed filmem: miniatura, tytul, komentarz; milena czyta 'say'.
    Przyciski (jeden wiersz, skanowanie od razu po przyciskach - R6):
    POWTORZ / START / NASTEPNY / POPRZEDNI / POWROT."""

    columnsOnly = True

    def __init__(self, parent, items):
        self.items = items
        self.index = 0
        buttons = [
            {'key': 'POWTORZ', 'bitmap': 'icons/pilots/musicPilot/10_repeat.png', 'speech': u'Powtórz'},
            {'key': 'START', 'bitmap': 'icons/pilots/minitubePilot/12_play.png', 'speech': u'Start'},
            {'key': 'NASTEPNY', 'bitmap': 'icons/pilots/minitubePilot/4_next.png', 'speech': u'Następny'},
            {'key': 'POPRZEDNI', 'bitmap': 'icons/pilots/minitubePilot/3_previous.png', 'speech': u'Poprzedni'},
            {'key': 'POWROT', 'bitmap': 'icons/back.png'},
        ]
        Board.__init__(self, parent, buttons, rows=1, columns=5)
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
        self.resetScanning()
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
        elif key == 'NASTEPNY':
            self.moveBy(1)
        elif key == 'POPRZEDNI':
            self.moveBy(-1)

    def moveBy(self, step):
        """NASTEPNY / POPRZEDNI - tutaj albo w WiceroPlayer; koniec filmu."""
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
def share_film(player, film):
    """PRZESLIJ w odtwarzaczu (youtube2.PlayerFrame - YouTube i Wicero):
    pauza -> plansza kontaktow -> wyslanie -> powrot do filmu w tym samym miejscu.
    film: jak w wicero_client.send_film, plus 'exclude' - rozmowa, z ktorej
    film przyszedl (Wicero) - jej nie ma na planszy (odsylanie nie ma sensu)."""
    player.stoper.Stop()
    resume = bool(player.player.is_playing())
    if resume:
        player.player.pause()

    def back():
        if resume:
            player.player.play()
        _resume(player)

    def on_success(recipients):
        if not recipients:
            say_then(u'Nie masz komu przesłać tego filmu.', back)
            return
        SendBoard(player, recipients, film, resume).Show(True)

    def on_error(e):
        say_then(error_text(e), back)

    run_in_thread(lambda: wicero_client.get_recipients(film.get('exclude')),
                  on_success, on_error)


#=============================================================================
class SendBoard(Board):
    """Komu przeslac film: kontakty (nazwy) + POWROT. Wybor = wyslanie od razu,
    "Film przesłany: <nazwa>." i powrot do filmu. Odtwarzacz (rodzic) zostaje
    pod spodem - bez Hide (VLC rysuje w jego oknie)."""

    def __init__(self, parent, recipients, film, resume):
        self.film = film
        self.resume = resume
        self.sending = False
        self.closed = False
        recipients = recipients[:MAX_SENDERS]  # stronicowanie - pozniej
        self.recipients = dict(('C%d' % i, c) for i, c in enumerate(recipients))
        buttons = [{'key': 'C%d' % i, 'text': c['name'], 'speech': c['name']}
                   for i, c in enumerate(recipients)]
        Board.__init__(self, parent, _fill(buttons, 6))

    def onSelect(self, key):
        if self.sending:  # drugie nacisniecie w trakcie wysylania
            return
        self.sending = True
        self.stoper.Stop()
        recipient = self.recipients[key]

        def on_success(result):
            say_then(u'Film przesłany: %s.' % recipient['name'], self.onExit)

        def on_error(e):
            say_then(error_text(e), self.onExit)

        # Komentarz (comment=...) - gdy AP dostanie sposob jego wpisania
        run_in_thread(lambda: wicero_client.send_film(recipient['conversationId'], self.film),
                      on_success, on_error)

    def onExit(self):
        # Tylko raz: POWROT w trakcie wysylania, potem koniec komunikatu
        if self.closed:
            return
        self.closed = True
        if self.resume:
            self.parent.player.play()
        Board.onExit(self)


#=============================================================================
class WiceroPlayer(youtube2.PlayerFrame):
    """Odtwarzacz jednego filmu Wicero (wzor: FavouritesPlayer).

    NASTEPNY / POPRZEDNI / koniec filmu -> powrot do IntroScreen
    z nastepnym / poprzednim filmem (kazdy film ma swoj ekran z komentarzem).
    Przy VIEWED_FRACTION dlugosci - zgloszenie 'obejrzany'.
    Nie zapisuje tabeli seen (stan obejrzenia jest w Wicero); ULUBIONE dziala
    jak w youtube2 (ulubione AP).

    W TLE (jak w YouTube): Wicero sie zamyka, AP wraca do NOWE, film gra
    dalej; powrot - kafel ODTWARZACZ w NOWE (albo w menu YOUTUBE). Ekranu
    przed filmem juz wtedy nie ma - koniec filmu / NASTEPNY / POPRZEDNI
    konczy odtwarzanie (w tle - po cichu, bez wyskakujacych plansz).
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

    def _shareable(self):
        # Przekazanie dalej (u odbiorcy "przekazany", bez pochodzenia);
        # bez nadawcy tego filmu na planszy
        return {'forwardFrom': {'conversationId': self.item['conversationId'],
                                'messageId': self.item['messageId']},
                'exclude': self.item['conversationId']}

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
        inBackground = background.player() is self
        self._onExit()  # w tle: zamyka film po cichu (PlayerFrame._onExit)
        # Ekran przed filmem jest tylko wtedy, gdy film nie byl w tle (po
        # powrocie przez ODTWARZACZ rodzicem jest menu NOWE / YOUTUBE)
        if not inBackground and parent and hasattr(parent, 'moveBy'):
            wx.CallAfter(parent.moveBy, step)

    def _onExit(self):
        self.progress.Stop()
        youtube2.PlayerFrame._onExit(self)

    def closeBackground(self):
        self.progress.Stop()
        youtube2.PlayerFrame.closeBackground(self)


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
