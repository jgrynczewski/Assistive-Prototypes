#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import glob, os, time, sys, threading, subprocess, random, json, sqlite3, urllib, urllib2

import wx
import wx.lib.buttons as bt

from pymouse import PyMouse
from pygame import mixer

import vlc

YTDLP = '/home/radoslaw/.local/bin/yt-dlp'
FMT = 'bestvideo[height<=480][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio'
RESULTS_PER_QUERY = 25
CACHE_MAX_AGE = 24 * 3600


#=============================================================================
class GenSymbolTextButton(bt.GenBitmapTextButton):

    def _GetLabelSize(self):
        w, h = self.GetTextExtent(self.GetLabel())
        if not self.bmpLabel:
            return w, h, True
        w_bmp = self.bmpLabel.GetWidth() + 2
        h_bmp = self.bmpLabel.GetHeight() + 2
        height = h + h_bmp
        if w_bmp > w:
            width = w_bmp
        else:
            width = w
        return width, height, True

    def DrawLabel(self, dc, width, height, dx=0, dy=0):
        bmp = self.bmpLabel
        if bmp is not None:
            if self.bmpDisabled and not self.IsEnabled():
                bmp = self.bmpDisabled
            if self.bmpFocus and self.hasFocus:
                bmp = self.bmpFocus
            if self.bmpSelected and not self.up:
                bmp = self.bmpSelected
            bw, bh = bmp.GetWidth(), bmp.GetHeight()
            if not self.up:
                dx = dy = self.labelDelta
            hasMask = bmp.GetMask() is not None
        else:
            bw = bh = 0

        if self.IsEnabled():
            dc.SetTextForeground(self.GetForegroundColour())
        else:
            dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))

        label = self.GetLabel()
        tw, th = dc.GetTextExtent(label)
        if not self.up:
            dx = dy = 4

        if bmp is not None:
            dc.DrawBitmap(bmp, (width - bw) / 2, (height - 4*bh / 3) / 2, hasMask)

        dc.DrawText(label, (width - tw) / 2, (height + 2*bh / 3) / 2)


#=============================================================================
class PlayerFrame(wx.Frame):
    """Odtwarzacz filmow dla wybranej frazy."""

    def __init__(self, parent, query):
        wx.Frame.__init__(self, parent, -1, 'AP YouTube2')
        style = self.GetWindowStyle()
        self.SetWindowStyle(style | wx.STAY_ON_TOP)
        self.parent = parent
        self.query = query

        self.winWidth, self.winHeight = wx.DisplaySize()
        self.Maximize(True)
        self.Centre(True)
        self.MakeModal(True)

        self._readParameters()

        self.labels = 'NASTEPNY ULUBIONE PLAY_PAUSE CISZEJ GLOSNIEJ POPRZEDNI EXIT'.split()

        self.flag = 'rest'
        self.pressFlag = False
        self.numberOfRows = [1]
        self.numberOfColumns = [7]
        self.maxRows = [3 * item for item in self.numberOfRows]
        self.maxColumns = [2 * item for item in self.numberOfColumns]
        self.rowIteration = 1
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
            self.poprzedniSound = mixer.Sound(self.pathToAP + '/sounds/youtube/poprzedni.ogg')
            self.nastepnySound = mixer.Sound(self.pathToAP + '/sounds/youtube/nastepny.ogg')
            self.glosniejSound = mixer.Sound(self.pathToAP + '/sounds/youtube/glosniej.ogg')
            self.ciszejSound = mixer.Sound(self.pathToAP + '/sounds/youtube/ciszej.ogg')
            self.zatrzymajGrajSound = mixer.Sound(self.pathToAP + '/sounds/youtube/zatrzymaj,graj.ogg')
            self.ulubioneSound = mixer.Sound(self.pathToAP + '/sounds/youtube/ulubione.ogg')
            self.usunSound = mixer.Sound(self.pathToAP + '/sounds/youtube/usun z ulubiuonych.ogg')
            self.powrotSound = mixer.Sound(self.pathToAP + '/sounds/powrot.ogg')
            self.usypiamSound = mixer.Sound(self.pathToAP + '/sounds/usypiam.ogg')
            self.pusteSound = mixer.Sound(self.pathToAP + '/sounds/puste.ogg')
            self.oneSound = mixer.Sound(self.pathToAP + '/sounds/rows/1.ogg')

        self.SetBackgroundColour('black')

        self._initDb()
        self._initVlc()
        self._initGui()
        self._initTimer()

        self.Bind(wx.EVT_CLOSE, self._onCloseWindow)

        t = threading.Thread(target=self._loadPlaylist)
        t.daemon = True
        t.start()

    def _readParameters(self):
        with open('./.pathToAP', 'r') as f:
            self.pathToAP = f.readline()
        sys.path.append(self.pathToAP)
        from reader import reader as Reader
        r = Reader()
        r.readParameters()
        for item in r.getParameters():
            try:
                setattr(self, item[:item.find('=')], int(item[item.find('=')+1:]))
            except ValueError:
                setattr(self, item[:item.find('=')], item[item.find('=')+1:])

    def _initDb(self):
        dbPath = os.path.join(self.pathToAP, 'youtube.db')
        self.db = sqlite3.connect(dbPath, check_same_thread=False)
        self.db.execute('''CREATE TABLE IF NOT EXISTS favourites (
            id TEXT PRIMARY KEY,
            title TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'active'
        )''')
        self.db.execute('''CREATE TABLE IF NOT EXISTS seen (
            id TEXT,
            query TEXT,
            seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id, query)
        )''')
        self.db.execute('''DELETE FROM seen WHERE seen_at < datetime('now', '-30 days')''')
        self.db.commit()

    def _initVlc(self):
        self.vlc_instance = vlc.Instance(
            '--no-xlib',
            '--network-caching=10000',
            '--live-caching=10000',
            '--file-caching=10000',
            '--avcodec-hw=none',
            '--no-video-title-show',
            '--codec=avcodec',
        )
        self.player = self.vlc_instance.media_player_new()
        em = self.player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerPlaying,
            lambda e: wx.CallAfter(self._onVlcPlaying))
        em.event_attach(vlc.EventType.MediaPlayerEndReached,
            lambda e: wx.CallAfter(self._onEndReached))
        em.event_attach(vlc.EventType.MediaPlayerStopped,
            lambda e: wx.CallAfter(self._onVlcStopped))
        em.event_attach(vlc.EventType.MediaPlayerEncounteredError,
            lambda e: wx.CallAfter(self._onVlcError))
        self.current_index = 0
        self.playlist = []
        self.playlist_meta = {}
        self._play_start_time = None
        self._intentional_stop = False
        self._ffmpeg_proc = None
        self._length_ms = 0
        self._loading_next = False

    def _initGui(self):
        labelFiles = [
            self.pathToAP + 'icons/pilots/minitubePilot/4_next.png',
            self.pathToAP + 'icons/pilots/minitubePilot/7_download.png',
            self.pathToAP + 'icons/pilots/minitubePilot/6_pause.png',
            self.pathToAP + 'icons/pilots/minitubePilot/1_volume down.png',
            self.pathToAP + 'icons/pilots/minitubePilot/2_volume up.png',
            self.pathToAP + 'icons/pilots/minitubePilot/3_previous.png',
            self.pathToAP + 'icons/pilots/minitubePilot/9_cancel.png',
        ]
        self.labelbitmaps = {}
        for index in xrange(len(self.labels)):
            self.labelbitmaps[self.labels[index]] = wx.BitmapFromImage(
                wx.ImageFromStream(open(labelFiles[index], 'rb')))

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vlcPanel = wx.Panel(self, -1)
        self.vlcPanel.SetBackgroundColour('black')
        self.sizer = wx.GridSizer(self.numberOfRows[0], self.numberOfColumns[0], self.xBorder, self.yBorder)

        if self.control != 'tracker':
            event = wx.EVT_LEFT_DOWN
        else:
            event = wx.EVT_BUTTON

        for i in self.labels:
            b = bt.GenBitmapButton(self, -1, bitmap=self.labelbitmaps[i], name=i)
            b.Bind(event, self.onPress)
            self.sizer.Add(b, 0, wx.EXPAND)

        self.vbox.Add(self.vlcPanel, proportion=4, flag=wx.EXPAND)
        self.vbox.Add(self.sizer, proportion=1, flag=wx.EXPAND | wx.TOP | wx.LEFT, border=self.xBorder)
        self.SetSizer(self.vbox)

    def _initTimer(self):
        self.stoper = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.timerUpdate, self.stoper)
        if self.control != 'tracker':
            self.stoper.Start(self.timeGap)

    def _cacheFile(self):
        safe = self.query.encode('utf-8').replace('/', '_').replace(' ', '_')
        return os.path.join(self.pathToAP, 'youtube_search_%s.json' % safe)

    def _loadPlaylist(self):
        cacheFile = self._cacheFile()
        if os.path.exists(cacheFile):
            try:
                with open(cacheFile, 'r') as f:
                    cache = json.load(f)
                age = time.time() - cache.get('timestamp', 0)
                if age < CACHE_MAX_AGE and cache.get('videos'):
                    print '[LOAD] cache OK wiek=%ds query=%s' % (int(age), self.query.encode('utf-8'))
                    self._startFromVideos(cache['videos'])
                    return
            except Exception as e:
                print '[LOAD] BLAD cache:', e

        keyFile = os.path.join(self.pathToAP, '.youtube_api_key')
        if not os.path.exists(keyFile):
            wx.CallAfter(self._onExit)
            return
        with open(keyFile, 'r') as f:
            api_key = f.read().strip()

        videos = []
        print '[LOAD] szukam: "%s"' % self.query.encode('utf-8')
        try:
            url = 'https://www.googleapis.com/youtube/v3/search?' + urllib.urlencode({
                'part': 'snippet',
                'q': self.query.encode('utf-8'),
                'type': 'video',
                'maxResults': RESULTS_PER_QUERY,
                'key': api_key,
            })
            data = json.loads(urllib2.urlopen(url, timeout=15).read())
            for item in data.get('items', []):
                vid_id = item['id'].get('videoId')
                title = item['snippet'].get('title', '')
                if vid_id:
                    videos.append({'id': vid_id, 'title': title})
            print '[LOAD] znaleziono: %d' % len(videos)
        except Exception as e:
            print '[LOAD] BLAD search:', e

        try:
            with open(cacheFile, 'w') as f:
                json.dump({'timestamp': time.time(), 'query': self.query, 'videos': videos}, f)
        except Exception as e:
            print '[LOAD] BLAD zapisu cache:', e

        self._startFromVideos(videos)

    def _startFromVideos(self, videos):
        seenIds = set(row[0] for row in self.db.execute(
            'SELECT id FROM seen WHERE query=?', (self.query,)))

        filtered = [v for v in videos if v['id'] not in seenIds]
        if len(filtered) < 5:
            filtered = list(videos)

        seen = {}
        unique = []
        for v in filtered:
            if v['id'] not in seen:
                seen[v['id']] = True
                unique.append(v)

        random.shuffle(unique)

        self.playlist = ['https://www.youtube.com/watch?v=' + v['id'] for v in unique]
        for v in unique:
            self.playlist_meta['https://www.youtube.com/watch?v=' + v['id']] = v

        if not self.playlist:
            wx.CallAfter(self._onExit)
            return

        wx.CallAfter(self._playCurrent)

    def _playCurrent(self):
        if not self.playlist:
            return
        url = self.playlist[self.current_index]
        self._play_start_time = None
        self._intentional_stop = True
        if self._ffmpeg_proc:
            self._ffmpeg_proc.kill()
            self._ffmpeg_proc = None
        self.player.stop()
        t = threading.Thread(target=self._resolveAndPlay, args=(url,))
        t.daemon = True
        t.start()

    def _resolveAndPlay(self, url):
        try:
            result = subprocess.check_output(
                [YTDLP, '--print', '%(duration)s', '-g', '-f', FMT, url],
                stderr=open(os.devnull, 'w')
            )
            lines = result.strip().split('\n')
            duration_s = float(lines[0]) if lines[0].replace('.', '').isdigit() else 0
            video_url = lines[1]
            audio_url = lines[2] if len(lines) > 2 else None
        except Exception as e:
            print '[YTDLP] BLAD:', e
            wx.CallAfter(self._next)
            return

        self._length_ms = int(duration_s * 1000)

        if audio_url:
            self._ffmpeg_proc = subprocess.Popen(
                ['ffmpeg', '-loglevel', 'quiet',
                 '-i', video_url, '-i', audio_url,
                 '-c', 'copy', '-f', 'matroska', 'pipe:1'],
                stdout=subprocess.PIPE,
                stderr=open(os.devnull, 'w')
            )
            fd_path = '/proc/self/fd/%d' % self._ffmpeg_proc.stdout.fileno()
            wx.CallAfter(self._startPlay, url, fd_path)
        else:
            wx.CallAfter(self._startPlay, url, video_url)

    def _startPlay(self, url, video_url):
        self.player.set_xwindow(self.vlcPanel.GetHandle())
        media = self.vlc_instance.media_new(video_url)
        self.player.set_media(media)
        self.player.play()

        meta = self.playlist_meta.get(url, {})
        vid_id = meta.get('id', '')
        if vid_id:
            try:
                self.db.execute('INSERT OR REPLACE INTO seen (id, query) VALUES (?, ?)',
                                (vid_id, self.query))
                self.db.commit()
            except Exception:
                pass

        remaining = len(self.playlist) - self.current_index
        if remaining <= 10 and not self._loading_next:
            self._loading_next = True
            t = threading.Thread(target=self._loadMore)
            t.daemon = True
            t.start()

    def _loadMore(self):
        cacheFile = self._cacheFile()
        try:
            with open(cacheFile, 'r') as f:
                cache = json.load(f)
            allVideos = cache.get('videos', [])
        except Exception:
            allVideos = []

        seenIds = set(row[0] for row in self.db.execute(
            'SELECT id FROM seen WHERE query=?', (self.query,)))
        existingIds = set(self.playlist_meta[u]['id'] for u in self.playlist if u in self.playlist_meta)

        filtered = [v for v in allVideos if v['id'] not in seenIds and v['id'] not in existingIds]
        if not filtered:
            self.db.execute('DELETE FROM seen WHERE query=?', (self.query,))
            self.db.commit()
            filtered = [v for v in allVideos if v['id'] not in existingIds]

        random.shuffle(filtered)
        for v in filtered:
            url = 'https://www.youtube.com/watch?v=' + v['id']
            self.playlist.append(url)
            self.playlist_meta[url] = v

        self._loading_next = False

    def _onVlcPlaying(self):
        self._play_start_time = time.time()

    def _isRealEnd(self, elapsed, length_ms):
        if length_ms <= 0 or elapsed < 0:
            return True
        return elapsed >= (length_ms / 1000.0) * 0.85

    def _onVlcStopped(self):
        elapsed = time.time() - self._play_start_time if self._play_start_time else -1
        if self._intentional_stop:
            self._intentional_stop = False
            return
        if not self._isRealEnd(elapsed, self._length_ms):
            wx.CallLater(500, self.player.play)

    def _onVlcError(self):
        wx.CallAfter(self._next)

    def _onEndReached(self):
        elapsed = time.time() - self._play_start_time if self._play_start_time else -1
        if not self._isRealEnd(elapsed, self._length_ms):
            return
        self._next()

    def _next(self):
        if self.current_index < len(self.playlist) - 1:
            self.current_index += 1
        else:
            self.current_index = 0
        self._playCurrent()

    def _prev(self):
        if self.current_index > 0:
            self.current_index -= 1
        self._playCurrent()

    def _addToFavourites(self):
        if not self.playlist:
            return
        url = self.playlist[self.current_index]
        meta = self.playlist_meta.get(url, {})
        vid_id = meta.get('id', '')
        if not vid_id:
            return
        try:
            self.db.execute(
                'INSERT OR REPLACE INTO favourites (id, title) VALUES (?, ?)',
                (vid_id, meta.get('title', ''))
            )
            self.db.commit()
        except Exception as e:
            print '[ULUBIONE] BLAD:', e

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

                if self.label == 'POPRZEDNI':
                    self._prev()
                elif self.label == 'PLAY_PAUSE':
                    if self.player.get_state() == vlc.State.Playing:
                        self.player.pause()
                    else:
                        self.player.play()
                elif self.label == 'NASTEPNY':
                    self._next()
                elif self.label == 'GLOSNIEJ':
                    os.system('pactl set-sink-volume 0 +20%')
                elif self.label == 'CISZEJ':
                    os.system('pactl set-sink-volume 0 -20%')
                elif self.label == 'ULUBIONE':
                    self._addToFavourites()
                elif self.label == 'USUN':
                    self._addToFavourites()
                elif self.label == 'EXIT':
                    self._onExit()

        else:
            self.numberOfPresses += 1

            if self.numberOfPresses == 1:

                if self.flag == 'rest':
                    self.flag = 'columns'
                    self.colIteration = 0
                    self.countColumns = 0
                    self.countRows = 0

                elif self.flag == 'columns':

                    self.position = self.colIteration - 1

                    item = self.sizer.GetItem(self.position)
                    selectedButton = item.GetWindow()
                    selectedButton.SetBackgroundColour(self.selectionColour)
                    selectedButton.SetFocus()
                    self.Update()

                    label = self.labels[self.position]

                    if label == 'POPRZEDNI':
                        if self.pressSound.lower() == 'voice':
                            self.poprzedniSound.play()
                        self._prev()

                    elif label == 'PLAY_PAUSE':
                        if self.pressSound.lower() == 'voice':
                            self.zatrzymajGrajSound.play()
                        if self.player.get_state() == vlc.State.Playing:
                            self.player.pause()
                        else:
                            self.player.play()

                    elif label == 'NASTEPNY':
                        if self.pressSound.lower() == 'voice':
                            self.nastepnySound.play()
                        self._next()

                    elif label == 'GLOSNIEJ':
                        if self.pressSound.lower() == 'voice':
                            self.glosniejSound.play()
                        os.system('pactl set-sink-volume 0 +20%')

                    elif label == 'CISZEJ':
                        if self.pressSound.lower() == 'voice':
                            self.ciszejSound.play()
                        os.system('pactl set-sink-volume 0 -20%')

                    elif label == 'ULUBIONE':
                        if self.pressSound.lower() == 'voice':
                            self.ulubioneSound.play()
                        self._addToFavourites()

                    elif label == 'USUN':
                        if self.pressSound.lower() == 'voice':
                            self.usunSound.play()
                        self._addToFavourites()

                    elif label == 'EXIT':
                        if self.pressSound.lower() == 'voice':
                            self.powrotSound.play()
                        self._onExit()

                    self.flag = 'rest'
                    self.colIteration = 0
                    self.countColumns = 0
                    self.countRows = 0

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
                items = self.sizer.GetChildren()
                for item in items:
                    b = item.GetWindow()
                    b.SetBackgroundColour(self.backgroundColour)
                self.Update()

            elif self.countColumns < self.maxColumns[0]:

                if self.flag == 'columns':
                    self.colIteration = self.colIteration % self.numberOfColumns[0]

                    items = self.sizer.GetChildren()
                    for item in items:
                        b = item.GetWindow()
                        b.SetBackgroundColour(self.backgroundColour)
                        b.SetFocus()

                    item = self.sizer.GetItem(self.colIteration)
                    b = item.GetWindow()
                    b.SetBackgroundColour(self.scanningColour)
                    b.SetFocus()

                    self.Update()

                    if self.switchSound == 'voice':
                        if b.Name == 'POPRZEDNI':
                            self.poprzedniSound.play()
                        elif b.Name == 'PLAY_PAUSE':
                            self.zatrzymajGrajSound.play()
                        elif b.Name == 'NASTEPNY':
                            self.nastepnySound.play()
                        elif b.Name == 'GLOSNIEJ':
                            self.glosniejSound.play()
                        elif b.Name == 'CISZEJ':
                            self.ciszejSound.play()
                        elif b.Name == 'ULUBIONE':
                            self.ulubioneSound.play()
                        elif b.Name == 'USUN':
                            self.usunSound.play()
                        elif b.Name == 'EXIT':
                            self.powrotSound.play()

                    self.colIteration += 1
                    self.countColumns += 1

                if self.switchSound.lower() == 'on':
                    self.switchingSound.play()

            elif self.countColumns == self.maxColumns[0]:
                if self.switchSound == 'voice':
                    self.usypiamSound.play()
                self.flag = 'rest'
                self.countRows += 1

                items = self.sizer.GetChildren()
                for item in items:
                    b = item.GetWindow()
                    b.SetBackgroundColour(self.backgroundColour)
                    b.SetFocus()

    def _onCloseWindow(self, event):
        if self.control != 'tracker':
            self.mousePosition = self.winWidth / 1.8, self.winHeight / 1.7
            self.mouseCursor.move(*self.mousePosition)

        dial = wx.MessageDialog(self, u'Czy napewno chcesz wyjść?', u'Wyjście',
                                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION | wx.STAY_ON_TOP)
        ret = dial.ShowModal()

        if ret == wx.ID_YES:
            self._intentional_stop = True
            if self._ffmpeg_proc:
                self._ffmpeg_proc.kill()
            self.player.stop()
            self.db.close()
            self.stoper.Stop()
            self.MakeModal(False)
            self.parent.Show(True)
            self.parent.stoper.Start(self.parent.timeGap)
            self.Destroy()
        else:
            event.Veto()
            if self.control != 'tracker':
                self.mousePosition = self.winWidth - 4 - self.xBorder, self.winHeight - 4 - self.yBorder
                self.mouseCursor.move(*self.mousePosition)

    def _onExit(self):
        self._intentional_stop = True
        if self._ffmpeg_proc:
            self._ffmpeg_proc.kill()
        self.player.stop()
        self.db.close()
        self.stoper.Stop()
        self.MakeModal(False)
        self.parent.Show(True)
        self.parent.stoper.Start(self.parent.timeGap)
        self.Destroy()


#=============================================================================
class FavouritesPlayer(PlayerFrame):
    """Odtwarzacz ulubionych - laduje filmy z tabeli favourites WHERE status=active."""

    def __init__(self, parent):
        PlayerFrame.__init__(self, parent, query='__favourites__')
        self.labels = 'NASTEPNY POPRZEDNI PLAY_PAUSE CISZEJ GLOSNIEJ USUN EXIT'.split()
        labelFiles = [
            self.pathToAP + 'icons/pilots/minitubePilot/4_next.png',
            self.pathToAP + 'icons/pilots/minitubePilot/3_previous.png',
            self.pathToAP + 'icons/pilots/minitubePilot/6_pause.png',
            self.pathToAP + 'icons/pilots/minitubePilot/1_volume down.png',
            self.pathToAP + 'icons/pilots/minitubePilot/2_volume up.png',
            self.pathToAP + 'icons/delete2.png',
            self.pathToAP + 'icons/pilots/minitubePilot/9_cancel.png',
        ]
        for index in xrange(len(self.labels)):
            self.labelbitmaps[self.labels[index]] = wx.BitmapFromImage(
                wx.ImageFromStream(open(labelFiles[index], 'rb')))
        items = list(self.sizer.GetChildren())
        for i, item in enumerate(items):
            b = item.GetWindow()
            b.SetName(self.labels[i])
            b.SetBitmapLabel(self.labelbitmaps[self.labels[i]])

    def _removeFromFavourites(self):
        if not self.playlist:
            return
        url = self.playlist[self.current_index]
        meta = self.playlist_meta.get(url, {})
        vid_id = meta.get('id', '')
        if not vid_id:
            return
        try:
            self.db.execute("UPDATE favourites SET status='removed' WHERE id=?", (vid_id,))
            self.db.commit()
            self.playlist.pop(self.current_index)
            if not self.playlist:
                self._onExit()
                return
            if self.current_index >= len(self.playlist):
                self.current_index = len(self.playlist) - 1
            self._playCurrent()
        except Exception as e:
            print '[USUN] BLAD:', e

    def _addToFavourites(self):
        self._removeFromFavourites()

    def _cacheFile(self):
        return None

    def _loadPlaylist(self):
        rows = list(self.db.execute("SELECT id, title FROM favourites WHERE status='active' ORDER BY added_at DESC"))
        if not rows:
            wx.CallAfter(self._onExit)
            return
        videos = [{'id': row[0], 'title': row[1]} for row in rows]
        self._startFromVideos(videos)

    def _startFromVideos(self, videos):
        unique = []
        seen = {}
        for v in videos:
            if v['id'] not in seen:
                seen[v['id']] = True
                unique.append(v)

        self.playlist = ['https://www.youtube.com/watch?v=' + v['id'] for v in unique]
        for v in unique:
            self.playlist_meta['https://www.youtube.com/watch?v=' + v['id']] = v

        if not self.playlist:
            wx.CallAfter(self._onExit)
            return

        wx.CallAfter(self._playCurrent)

    def _startPlay(self, url, video_url):
        self.player.set_xwindow(self.vlcPanel.GetHandle())
        media = self.vlc_instance.media_new(video_url)
        self.player.set_media(media)
        self.player.play()


#=============================================================================
class youtube2(wx.Frame):
    """Galeria fraz - wybor tematu do wyszukania."""

    def __init__(self, parent, id):
        self.winWidth, self.winHeight = wx.DisplaySize()
        self.winHeight -= 20

        wx.Frame.__init__(self, parent, id, 'APYoutube2')
        style = self.GetWindowStyle()
        self.SetWindowStyle(style | wx.STAY_ON_TOP)
        self.parent = parent

        self.Maximize(True)
        self.Centre(True)
        self.MakeModal(True)

        self.initializeParameters()
        self.initializeBitmaps()
        self.createGui()
        self.initializeTimer()
        self.createBindings()

    def initializeParameters(self):
        with open('./.pathToAP', 'r') as textFile:
            self.pathToAP = textFile.readline()

        sys.path.append(self.pathToAP)
        from reader import reader as Reader

        r = Reader()
        r.readParameters()
        parameters = r.getParameters()

        for item in parameters:
            try:
                setattr(self, item[:item.find('=')], int(item[item.find('=')+1:]))
            except ValueError:
                setattr(self, item[:item.find('=')], item[item.find('=')+1:])

        self.panelIteration = 0
        self.rowIteration = 0
        self.columnIteration = 0

        self.defaultNumberOfColumns = 6
        self.defaultNumberOfRows = 4

        self.countRows = 0
        self.countColumns = 0
        self.button = 1
        self.countMaxRows = 2
        self.countMaxColumns = 2
        self.numberOfPresses = 0

        self.numberOfSymbol = 0
        self.flag = 'panel'

        if self.control != 'tracker':
            self.mouseCursor = PyMouse()
            self.mousePosition = self.winWidth - 8 - self.xBorder, self.winHeight - 8 - self.yBorder
            self.mouseCursor.move(*self.mousePosition)

        if self.switchSound.lower() != 'off' or self.pressSound.lower() != 'off':
            mixer.init()
            self.switchingSound = mixer.Sound(self.pathToAP + '/sounds/switchSound.ogg')
            self.pressingSound = mixer.Sound(self.pathToAP + '/sounds/pressSound.ogg')

            self.oneSound = mixer.Sound(self.pathToAP + '/sounds/rows/1.ogg')
            self.twoSound = mixer.Sound(self.pathToAP + '/sounds/rows/2.ogg')
            self.threeSound = mixer.Sound(self.pathToAP + '/sounds/rows/3.ogg')
            self.powrotSound = mixer.Sound(self.pathToAP + '/sounds/powrot.ogg')
            self.pusteSound = mixer.Sound(self.pathToAP + '/sounds/puste.ogg')

            self.pageFlipSounds = glob.glob(self.pathToAP + 'sounds/page_flip/*')
            self.pageFlipSound = mixer.Sound(self.pageFlipSounds[1])
            self.lastPageFlipSound = mixer.Sound(self.pathToAP + 'sounds/page-flip-13.ogg')
            self.pageFlipSounds = [mixer.Sound(s) for s in self.pageFlipSounds]

        self.SetBackgroundColour('black')

    def initializeBitmaps(self):
        dictPath = self.pathToAP + 'multimedia/youtube/*'
        pages = sorted([item for item in glob.glob(dictPath) if item[item.rfind('/')+1:].isdigit()])
        self.numberOfpages = len(pages)

        self.blissBook = {}
        self.numberOfRows, self.numberOfColumns, self.numberOfCells = [], [], []

        for page in pages:
            try:
                pageNumber = int(page[page.rfind('/')+1:])
            except ValueError:
                print 'Folderowi %s nadano nieprawidłową nazwę.' % page[page.rfind('/')+1:]
                continue

            sizerTopology = open(page + '/sizer')
            for line in sizerTopology:
                if line[:12] == 'numberOfRows':
                    self.numberOfRows.append(int(line[-2]))
                elif line[:15] == 'numberOfColumns':
                    self.numberOfColumns.append(int(line[-2]))
                else:
                    self.numberOfColumns.append(self.defaultNumberOfColumns)
                    self.numberOfRows.append(self.defaultNumberOfRows)

            symbols = (glob.glob(page + '/*.jpg') + glob.glob(page + '/*.png') +
                       glob.glob(page + '/*.JPG') + glob.glob(page + '/*.jpeg'))
            symbols = [item.decode('utf-8') for item in symbols]

            symbolInfo = []
            self.newHeight = 0.6 * self.winHeight / self.numberOfRows[-1]

            for symbol in symbols:
                image = wx.ImageFromStream(open(symbol, 'rb'))
                self.newWidth = image.GetSize()[0] * (self.newHeight / float(image.GetSize()[1]))
                image.Rescale(self.newWidth, self.newHeight, wx.IMAGE_QUALITY_HIGH)
                bitmapSymbol = wx.BitmapFromImage(image)

                symbolName = symbol[symbol.rfind('/')+1:symbol.rfind('.')]
                try:
                    symbolPosition = int(symbolName.split('_')[0])
                    symbolTranslate = symbolName[symbolName.find('_')+1:].replace('_', ' ')
                    symbolInfo.append([bitmapSymbol, symbolPosition, symbolTranslate])
                except ValueError:
                    print 'Symbol %s ma nieprawidłową nazwę.' % symbolName

            symbolInfo.sort(key=lambda x: x[1])
            self.blissBook[pageNumber] = symbolInfo

    def createGui(self):
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.subSizers = []

        for item in range(len(self.numberOfRows)):
            subSizer = wx.GridSizer(self.numberOfRows[item], self.numberOfColumns[item], 1, 1)
            subSizer.SetMinSize((self.winWidth, self.winHeight))
            self.subSizers.append(subSizer)

            i, j = 0, 1
            self.numberOfCells = self.numberOfRows[item] * self.numberOfColumns[item]

            while j <= self.numberOfCells:
                try:
                    if i < len(self.blissBook[item]):
                        while j != self.blissBook[item][i][1]:
                            b = bt.GenButton(self, -1, name='puste')
                            b.Bind(wx.EVT_LEFT_DOWN, self.onPress)
                            b.SetBackgroundColour(self.backgroundColour)
                            self.subSizers[item].Add(b, 0, wx.EXPAND | wx.ALIGN_CENTER)
                            j += 1

                        b = bt.GenBitmapButton(self, -1, bitmap=self.blissBook[item][i][0],
                                               name=self.blissBook[item][i][2])
                        b.Bind(wx.EVT_LEFT_DOWN, self.onPress)
                        b.SetBackgroundColour(self.backgroundColour)
                        self.subSizers[item].Add(b, 0, wx.EXPAND | wx.ALIGN_CENTER)
                        i += 1
                        j += 1
                    else:
                        b = bt.GenButton(self, -1, name='puste')
                        b.Bind(wx.EVT_LEFT_DOWN, self.onPress)
                        b.SetBackgroundColour(self.backgroundColour)
                        self.subSizers[item].Add(b, 0, wx.EXPAND | wx.ALIGN_CENTER)
                        j += 1
                except IndexError:
                    print 'IndexError', i, j

            self.Layout()
            self.mainSizer.Add(self.subSizers[item], proportion=0,
                               flag=wx.EXPAND | wx.LEFT, border=3)

            if item != 0:
                self.mainSizer.Show(item=self.subSizers[item], show=False, recursive=True)

        self.SetSizer(self.mainSizer)

    def initializeTimer(self):
        self.stoper = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.timerUpdate, self.stoper)
        self.stoper.Start(self.timeGap)

    def createBindings(self):
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def OnCloseWindow(self, event):
        self.mousePosition = self.winWidth / 1.85, (self.winHeight + 20) / 1.85
        self.mouseCursor.move(*self.mousePosition)

        dial = wx.MessageDialog(None, u'Czy napewno chcesz wyjść z programu?', u'Wyjście',
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
            self.mousePosition = self.winWidth - 8, self.winHeight + 20 - 8
            self.mouseCursor.move(*self.mousePosition)

    def onExit(self):
        if __name__ == '__main__':
            self.stoper.Stop()
            self.Destroy()
        else:
            self.stoper.Stop()
            self.MakeModal(False)
            self.parent.Show(True)
            self.parent.stoper.Start(self.parent.timeGap)
            self.Destroy()

    def onPress(self, event):
        if self.pressSound.lower() != 'off':
            self.pressingSound.play()

        if self.numberOfPresses == 0:

            if self.flag == 'panel':
                items = self.subSizers[self.panelIteration].GetChildren()

                for item in items:
                    b = item.GetWindow()
                    b.SetBackgroundColour(self.scanningColour)
                    b.SetFocus()

                if self.blissBook[self.panelIteration][0][2] == 'EXIT' and self.panelIteration == len(self.subSizers) - 1:
                    if self.pressSound.lower() == 'voice':
                        self.stoper.Stop()
                        time.sleep((self.selectionTime + self.timeGap) / (1000. * 2))
                        self.powrotSound.play()
                        time.sleep((self.selectionTime + self.timeGap) / (1000. * 2))
                        self.stoper.Start(self.timeGap)
                    self.onExit()
                else:
                    self.flag = 'row'
                    self.rowIteration = 0

            elif self.flag == 'row':
                self.rowIteration -= 1

                if self.pressSound == 'voice':
                    if self.rowIteration == 0:
                        self.oneSound.play()
                    if self.rowIteration == 1:
                        self.twoSound.play()

                buttonsToHighlight = range(
                    self.rowIteration * self.numberOfColumns[self.panelIteration],
                    self.rowIteration * self.numberOfColumns[self.panelIteration] + self.numberOfColumns[self.panelIteration])

                for button in buttonsToHighlight:
                    item = self.subSizers[self.panelIteration].GetItem(button)
                    b = item.GetWindow()
                    b.SetBackgroundColour(self.selectionColour)
                    b.SetFocus()

                self.flag = 'columns'
                self.columnIteration = 0

            elif self.flag == 'columns':
                self.columnIteration -= 1

                item = self.subSizers[self.panelIteration].GetItem(
                    self.rowIteration * self.numberOfColumns[self.panelIteration] + self.columnIteration)
                selectedButton = item.GetWindow()

                self.Update()

                if self.pressSound == 'voice':
                    if selectedButton.GetName() == 'puste':
                        selectedButton.SetBackgroundColour('red')
                        selectedButton.SetFocus()
                        self.Update()
                        self.pusteSound.play()
                    else:
                        selectedButton.SetBackgroundColour(self.selectionColour)
                        selectedButton.SetFocus()

                        query = selectedButton.GetName()

                        if query != 'EXIT':
                            self._openPlayer(query)
                        else:
                            self.onExit()

                self.flag = 'panel'
                self.panelIteration = 0
                self.rowIteration = 0
                self.columnIteration = 0
                self.count = 0
                self.countRows = 0

        self.numberOfPresses += 1

    def _openPlayer(self, query):
        self.stoper.Stop()
        self.Hide()
        player = PlayerFrame(self, query)
        player.Show(True)

    def timerUpdate(self, event):
        self.mouseCursor.move(*self.mousePosition)
        self.numberOfPresses = 0

        if self.flag == 'panel':
            self.panelIteration += 1

            if self.panelIteration == len(self.blissBook):
                self.panelIteration = 0

            if self.switchSound == 'voice':
                if self.panelIteration == len(self.blissBook) - 1:
                    self.powrotSound.play()
                elif self.panelIteration == len(self.blissBook) - 2:
                    self.lastPageFlipSound.play()
                else:
                    self.pageFlipSounds[self.panelIteration % len(self.pageFlipSounds)].play()

            for item in range(len(self.blissBook)):
                if item != self.panelIteration:
                    self.mainSizer.Show(item=self.subSizers[item], show=False, recursive=True)

            self.mainSizer.Show(item=self.subSizers[self.panelIteration], show=True, recursive=True)
            self.SetSizer(self.mainSizer)
            self.Layout()

        if self.flag == 'row':

            if self.countRows == self.countMaxRows:
                self.flag = 'panel'
                self.countRows = 0

                items = self.subSizers[self.panelIteration].GetChildren()
                for item in items:
                    b = item.GetWindow()
                    b.SetBackgroundColour(self.backgroundColour)
                    b.SetFocus()

            else:
                if self.rowIteration == self.numberOfRows[self.panelIteration]:
                    self.rowIteration = 0

                if self.rowIteration == self.numberOfRows[self.panelIteration] - 1:
                    self.countRows += 1

                items = self.subSizers[self.panelIteration].GetChildren()
                for item in items:
                    b = item.GetWindow()
                    b.SetBackgroundColour(self.backgroundColour)
                    b.SetFocus()

                zakres = range(
                    self.rowIteration * self.numberOfColumns[self.panelIteration],
                    self.rowIteration * self.numberOfColumns[self.panelIteration] + self.numberOfColumns[self.panelIteration])

                for i in zakres:
                    item = self.subSizers[self.panelIteration].GetItem(i)
                    b = item.GetWindow()
                    b.SetBackgroundColour(self.scanningColour)
                    b.SetFocus()
                self.rowIteration += 1

                if self.switchSound == 'voice':
                    if self.rowIteration == 1:
                        self.oneSound.play()
                    if self.rowIteration == 2:
                        self.twoSound.play()
                    if self.rowIteration == 3:
                        self.threeSound.play()

        elif self.flag == 'columns':

            if self.countColumns == self.countMaxColumns:
                self.flag = 'row'
                self.rowIteration = 0
                self.columnIteration = 0
                self.countColumns = 0
                self.countRows = 0

                items = self.subSizers[self.panelIteration].GetChildren()
                for item in items:
                    b = item.GetWindow()
                    b.SetBackgroundColour(self.backgroundColour)
                    b.SetFocus()

            else:
                if self.columnIteration == self.numberOfColumns[self.panelIteration]:
                    self.columnIteration = 0

                if self.columnIteration == self.numberOfColumns[self.panelIteration] - 1:
                    self.countColumns += 1

                items = self.subSizers[self.panelIteration].GetChildren()
                for item in items:
                    b = item.GetWindow()
                    b.SetBackgroundColour(self.backgroundColour)
                    b.SetFocus()

                item = self.subSizers[self.panelIteration].GetItem(
                    self.rowIteration * self.numberOfColumns[self.panelIteration] + self.columnIteration)
                b = item.GetWindow()
                b.SetBackgroundColour(self.scanningColour)
                b.SetFocus()

                self.columnIteration += 1

                if self.switchSound.lower() == 'voice':
                    if b.Name == 'puste':
                        self.pusteSound.play()
                    else:
                        cmd = 'milena_say %s' % b.Name
                        subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)

                elif self.switchSound.lower() != 'off':
                    self.switchingSound.play()


#=============================================================================
if __name__ == '__main__':
    app = wx.App(False)
    frame = youtube2(parent=None, id=-1)
    frame.Show(True)
    app.MainLoop()