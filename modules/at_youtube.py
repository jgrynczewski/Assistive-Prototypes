#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import wxversion

import wx, os, sys, time, subprocess, json, random, sqlite3, urllib2, threading
import wx.lib.buttons as bt

from pymouse import PyMouse
from pygame import mixer

import vlc

#=============================================================================
class youtube(wx.Frame):
    def __init__(self, parent, id):

        self.winWidth, self.winHeight = wx.DisplaySize()

        wx.Frame.__init__(self, parent, id, 'AP YouTube')
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
            self.powrotSound = mixer.Sound(self.pathToAP + '/sounds/powrot.ogg')
            self.usypiamSound = mixer.Sound(self.pathToAP + '/sounds/usypiam.ogg')
            self.pusteSound = mixer.Sound(self.pathToAP + '/sounds/puste.ogg')
            self.oneSound = mixer.Sound(self.pathToAP + '/sounds/rows/1.ogg')

        self.SetBackgroundColour('black')

        self._initDb()

    #-------------------------------------------------------------------------
    def _initDb(self):
        dbPath = os.path.join(self.pathToAP, 'youtube.db')
        self.db = sqlite3.connect(dbPath)
        self.db.execute('''CREATE TABLE IF NOT EXISTS favourites (
            id TEXT PRIMARY KEY,
            title TEXT,
            thumbnail TEXT,
            duration TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        self.db.execute('''CREATE TABLE IF NOT EXISTS seen (
            id TEXT PRIMARY KEY,
            seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        self.db.execute('''DELETE FROM seen WHERE seen_at < datetime('now', '-30 days')''')
        self.db.commit()

    #-------------------------------------------------------------------------
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
        em.event_attach(vlc.EventType.MediaPlayerEndReached,
            lambda e: wx.CallAfter(self._onEndReached))
        em.event_attach(vlc.EventType.MediaPlayerEncounteredError,
            lambda e: wx.CallAfter(self._onVlcError))
        em.event_attach(vlc.EventType.MediaPlayerStopped,
            lambda e: wx.CallAfter(self._onVlcStopped))
        em.event_attach(vlc.EventType.MediaPlayerPlaying,
            lambda e: wx.CallAfter(self._onVlcPlaying))
        self.is_playing = False
        self.current_index = 0
        self.playlist = []
        self.playlist_meta = {}
        self._loading_next = False
        self._play_start_time = None
        self._intentional_stop = False
        self._ffmpeg_proc = None
        self._length_ms = 0

    #-------------------------------------------------------------------------
    def _fetchVideos(self, categoryId=None, pageToken=None, maxResults=50):
        keyFile = os.path.join(self.pathToAP, '.youtube_api_key')
        if not os.path.exists(keyFile):
            return [], None
        with open(keyFile, 'r') as f:
            key = f.read().strip()
        url = ('https://www.googleapis.com/youtube/v3/videos'
               '?part=snippet,contentDetails'
               '&chart=mostPopular'
               '&regionCode=PL'
               '&maxResults=' + str(maxResults) +
               '&key=' + key)
        if categoryId:
            url += '&videoCategoryId=' + str(categoryId)
        if pageToken:
            url += '&pageToken=' + pageToken
        try:
            data = json.loads(urllib2.urlopen(url, timeout=30).read())
            items = data.get('items', [])
            nextToken = data.get('nextPageToken', None)
            result = []
            for item in items:
                vid_id = item['id']
                title = item['snippet'].get('title', '')
                thumbnail = item['snippet'].get('thumbnails', {}).get('default', {}).get('url', '')
                duration = item.get('contentDetails', {}).get('duration', '')
                result.append({'id': vid_id, 'title': title, 'thumbnail': thumbnail, 'duration': duration})
            return result, nextToken
        except Exception as e:
            print 'BLAD API:', e
            return [], None

    #-------------------------------------------------------------------------
    def _loadPlaylist(self):
        print '[%.3f][LOAD] start' % time.time()
        categories = [None, 10, 17, 20, 24, 28]
        allVideos = []
        for cat in categories:
            maxR = 50 if cat is None else 20
            videos, _ = self._fetchVideos(categoryId=cat, maxResults=maxR)
            allVideos.extend(videos)

        dbPath = os.path.join(self.pathToAP, 'youtube.db')
        db = sqlite3.connect(dbPath)
        seenIds = set(row[0] for row in db.execute('SELECT id FROM seen'))
        db.close()

        filtered = [v for v in allVideos if v['id'] not in seenIds]
        if len(filtered) < 10:
            filtered = allVideos

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
            os.system('milena_say Nie pobrano filmów')
            wx.CallAfter(self.onExit)
            return

        print '[%.3f][LOAD] done, playlist=%d' % (time.time(), len(self.playlist))
        wx.CallAfter(self._playCurrent)

    #-------------------------------------------------------------------------
    def _getStreamUrls(self, youtube_url):
        fmt = 'bestvideo[height<=480][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio'
        try:
            result = subprocess.check_output(
                ['/home/radoslaw/.local/bin/yt-dlp',
                 '--print', '%(duration)s', '-g', '-f', fmt, youtube_url],
                stderr=open(os.devnull, 'w')
            )
            lines = result.strip().split('\n')
            duration_s = float(lines[0]) if lines[0].replace('.', '').isdigit() else 0
            video_url = lines[1]
            audio_url = lines[2] if len(lines) > 2 else None
            return video_url, audio_url, duration_s
        except Exception as e:
            print 'BLAD yt-dlp:', e
            return None, None, 0

    #-------------------------------------------------------------------------
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
        print '[%.3f][RESOLVE] start %s' % (time.time(), url[-11:])
        video_url, audio_url, duration_s = self._getStreamUrls(url)
        if video_url is None:
            wx.CallAfter(self._next)
            return
        self._length_ms = int(duration_s * 1000)
        print '[%.3f][RESOLVE] got urls duration=%.1fs' % (time.time(), duration_s)
        if audio_url:
            self._ffmpeg_proc = subprocess.Popen(
                ['ffmpeg', '-loglevel', 'quiet',
                 '-i', video_url, '-i', audio_url,
                 '-c', 'copy', '-f', 'matroska', 'pipe:1'],
                stdout=subprocess.PIPE,
                stderr=open(os.devnull, 'w')
            )
            fd_path = '/proc/self/fd/%d' % self._ffmpeg_proc.stdout.fileno()
            print '[%.3f][RESOLVE] ffmpeg pid=%d fd=%s' % (time.time(), self._ffmpeg_proc.pid, fd_path)
            wx.CallAfter(self._startPlay, url, fd_path)
        else:
            wx.CallAfter(self._startPlay, url, video_url)

    def _startPlay(self, url, video_url):
        print '[%.3f][START] url=%s' % (time.time(), video_url[:60])
        self.player.set_xwindow(self.vlcPanel.GetHandle())
        media = self.vlc_instance.media_new(video_url)
        self.player.set_media(media)
        self.player.play()
        self.is_playing = True

        vid_id = self.playlist_meta.get(url, {}).get('id', '')
        if vid_id:
            try:
                self.db.execute('INSERT OR REPLACE INTO seen (id) VALUES (?)', (vid_id,))
                self.db.commit()
            except Exception:
                pass

        remaining = len(self.playlist) - self.current_index
        if remaining <= 20 and not self._loading_next:
            self._loading_next = True
            t = threading.Thread(target=self._loadMore)
            t.daemon = True
            t.start()

    #-------------------------------------------------------------------------
    def _loadMore(self):
        categories = [None, 10, 17, 20, 24, 28]
        allVideos = []
        for cat in categories:
            maxR = 50 if cat is None else 20
            videos, _ = self._fetchVideos(categoryId=cat, maxResults=maxR)
            allVideos.extend(videos)

        dbPath = os.path.join(self.pathToAP, 'youtube.db')
        db = sqlite3.connect(dbPath)
        seenIds = set(row[0] for row in db.execute('SELECT id FROM seen'))
        db.close()
        existingIds = set(self.playlist_meta[u]['id'] for u in self.playlist if u in self.playlist_meta)
        filtered = [v for v in allVideos if v['id'] not in seenIds and v['id'] not in existingIds]

        seen = {}
        unique = []
        for v in filtered:
            if v['id'] not in seen:
                seen[v['id']] = True
                unique.append(v)

        random.shuffle(unique)

        newUrls = ['https://www.youtube.com/watch?v=' + v['id'] for v in unique]
        for v in unique:
            self.playlist_meta['https://www.youtube.com/watch?v=' + v['id']] = v

        self.playlist.extend(newUrls)
        self._loading_next = False

    #-------------------------------------------------------------------------
    def _onVlcPlaying(self):
        self._play_start_time = time.time()
        print '[%.3f][VLC] PLAYING' % self._play_start_time

    #-------------------------------------------------------------------------
    def _isRealEnd(self, elapsed, length_ms):
        if length_ms <= 0 or elapsed < 0:
            return True
        return elapsed >= (length_ms / 1000.0) * 0.85

    def _onVlcStopped(self):
        elapsed = time.time() - self._play_start_time if self._play_start_time else -1
        print '[%.3f][VLC] STOPPED elapsed=%.1fs intentional=%s' % (time.time(), elapsed, self._intentional_stop)
        if self._intentional_stop:
            self._intentional_stop = False
            return
        if not self._isRealEnd(elapsed, self._length_ms):
            wx.CallLater(500, self.player.play)

    #-------------------------------------------------------------------------
    def _onVlcError(self):
        print '[%.3f][VLC] ERROR' % time.time()
        wx.CallAfter(self._next)

    #-------------------------------------------------------------------------
    def _onEndReached(self):
        elapsed = time.time() - self._play_start_time if self._play_start_time else -1
        print '[%.3f][VLC] END_REACHED elapsed=%.1fs length_ms=%d' % (time.time(), elapsed, self._length_ms)
        if not self._isRealEnd(elapsed, self._length_ms):
            return
        self._next()

    #-------------------------------------------------------------------------
    def _next(self):
        if self.current_index < len(self.playlist) - 1:
            self.current_index += 1
        else:
            self.current_index = 0
        self._playCurrent()

    #-------------------------------------------------------------------------
    def _prev(self):
        if self.current_index > 0:
            self.current_index -= 1
        else:
            self.current_index = 0
        self._playCurrent()

    #-------------------------------------------------------------------------
    def _addToFavourites(self):
        url = self.playlist[self.current_index] if self.playlist else None
        if not url:
            return
        meta = self.playlist_meta.get(url, {})
        vid_id = meta.get('id', '')
        if not vid_id:
            return
        try:
            self.db.execute(
                'INSERT OR REPLACE INTO favourites (id, title, thumbnail, duration) VALUES (?, ?, ?, ?)',
                (vid_id, meta.get('title', ''), meta.get('thumbnail', ''), meta.get('duration', ''))
            )
            self.db.commit()
        except Exception as e:
            print 'BLAD zapis ulubionych:', e

    #-------------------------------------------------------------------------
    def initializeBitmaps(self):

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
            self.labelbitmaps[self.labels[index]] = wx.BitmapFromImage(wx.ImageFromStream(open(labelFiles[index], 'rb')))

    #-------------------------------------------------------------------------
    def createGui(self):

        self.vbox = wx.BoxSizer(wx.VERTICAL)

        self.vlcPanel = wx.Panel(self, -1)
        self.vlcPanel.SetBackgroundColour('black')

        self.sizer = wx.GridSizer(self.numberOfRows[0], self.numberOfColumns[0], self.xBorder, self.yBorder)

        if self.control != 'tracker':
            event = eval('wx.EVT_LEFT_DOWN')
        else:
            event = eval('wx.EVT_BUTTON')

        for i in self.labels:
            b = bt.GenBitmapButton(self, -1, bitmap=self.labelbitmaps[i], name=i)
            b.Bind(event, self.onPress)
            self.sizer.Add(b, 0, wx.EXPAND)

        self.vbox.Add(self.vlcPanel, proportion=4, flag=wx.EXPAND)
        self.vbox.Add(self.sizer, proportion=1, flag=wx.EXPAND | wx.TOP | wx.LEFT, border=self.xBorder)
        self.SetSizer(self.vbox)

        self._initVlc()
        t = threading.Thread(target=self._loadPlaylist)
        t.daemon = True
        t.start()

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
                    self.mousePosition = self.winWidth/1.7, self.winHeight/1.7
                else:
                    self.mousePosition = self.winWidth/1.8, self.winHeight/1.7
            else:
                self.mousePosition = self.winWidth/1.9, self.winHeight/1.68

            self.mouseCursor.move(*self.mousePosition)

        dial = wx.MessageDialog(self, u'Czy napewno chcesz wyjść z programu?', u'Wyjście',
                                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION | wx.STAY_ON_TOP)

        ret = dial.ShowModal()

        if ret == wx.ID_YES:
            self._intentional_stop = True
            if self._ffmpeg_proc:
                self._ffmpeg_proc.kill()
            self.player.stop()
            self.db.close()
            self.Destroy()
        else:
            event.Veto()

            if self.control != 'tracker':
                self.mousePosition = self.winWidth - 4 - self.xBorder, self.winHeight - 4 - self.yBorder
                self.mouseCursor.move(*self.mousePosition)

    #-------------------------------------------------------------------------
    def onExit(self):
        self._intentional_stop = True
        if self._ffmpeg_proc:
            self._ffmpeg_proc.kill()
        self.player.stop()
        self.db.close()
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

                if self.label == 'POPRZEDNI':
                    self._prev()
                elif self.label == 'PLAY_PAUSE':
                    if self.player.get_state() == vlc.State.Playing:
                        self.player.pause()
                        self.is_playing = False
                    else:
                        self.player.play()
                        self.is_playing = True
                elif self.label == 'NASTEPNY':
                    self._next()
                elif self.label == 'GLOSNIEJ':
                    os.system('pactl set-sink-volume 0 +20%')
                elif self.label == 'CISZEJ':
                    os.system('pactl set-sink-volume 0 -20%')
                elif self.label == 'ULUBIONE':
                    self._addToFavourites()
                elif self.label == 'EXIT':
                    self.onExit()

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
                            self.is_playing = False
                        else:
                            self.player.play()
                            self.is_playing = True

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

                    elif label == 'EXIT':
                        if self.pressSound.lower() == 'voice':
                            self.powrotSound.play()
                        self.onExit()

                    self.flag = 'rest'
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

            else:
                pass

#=============================================================================
if __name__ == '__main__':

    app = wx.App(False)
    frame = youtube(parent=None, id=-1)
    frame.Show(True)
    app.MainLoop()