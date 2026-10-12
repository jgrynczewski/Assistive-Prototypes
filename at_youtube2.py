#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os, sys, time, subprocess, threading, random, json
import wx

import vlc

from oauth2client import client, file as oauth_file, tools
from googleapiclient.discovery import build
import httplib2

CLIENT_SECRETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secrets.json')
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'youtube_oauth_token.json')
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'youtube_playlist_cache.json')
CACHE_MAX_AGE = 6 * 3600
SCOPES = 'https://www.googleapis.com/auth/youtube.readonly'

YTDLP = '/home/radoslaw/.local/bin/yt-dlp'
FMT = 'bestvideo[height<=480][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio'


def get_authenticated_service():
    store = oauth_file.Storage(TOKEN_FILE)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRETS, SCOPES)
        flow.user_agent = 'AP YouTube'
        import argparse
        flags = argparse.Namespace(
            auth_host_name='localhost',
            auth_host_port=[8080, 8090],
            logging_level='ERROR',
            noauth_local_webserver=False
        )
        credentials = tools.run_flow(flow, store, flags)
    http = credentials.authorize(httplib2.Http())
    return build('youtube', 'v3', http=http)


def get_urls(youtube_url):
    try:
        result = subprocess.check_output(
            [YTDLP, '--print', '%(duration)s', '-g', '-f', FMT, youtube_url],
            stderr=open(os.devnull, 'w')
        )
        lines = result.strip().split('\n')
        duration_s = float(lines[0]) if lines[0].replace('.', '').isdigit() else 0
        video_url = lines[1]
        audio_url = lines[2] if len(lines) > 2 else None
        return video_url, audio_url, duration_s
    except Exception as e:
        print '[YTDLP] BLAD:', e
        return None, None, 0


class TestFrame(wx.Frame):
    def __init__(self, youtube_service):
        wx.Frame.__init__(self, None, -1, 'YouTube OAuth2 Test', size=(800, 600))

        self.youtube = youtube_service
        self.current_index = 0
        self._play_start_time = None
        self._intentional_stop = False
        self._length_ms = 0
        self._ffmpeg_proc = None
        self.playlist = []

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
            lambda e: wx.CallAfter(self._on_playing))
        em.event_attach(vlc.EventType.MediaPlayerEndReached,
            lambda e: wx.CallAfter(self._on_end))
        em.event_attach(vlc.EventType.MediaPlayerStopped,
            lambda e: wx.CallAfter(self._on_stopped))
        em.event_attach(vlc.EventType.MediaPlayerEncounteredError,
            lambda e: wx.CallAfter(self._on_error))

        self.vlc_panel = wx.Panel(self, -1)
        self.vlc_panel.SetBackgroundColour('black')

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for label in ['< POPRZEDNI', 'NASTEPNY >', 'WYJSCIE']:
            b = wx.Button(self, -1, label)
            b.Bind(wx.EVT_BUTTON, self._on_btn)
            btn_sizer.Add(b, 1, wx.EXPAND | wx.ALL, 4)

        self.status = wx.StaticText(self, -1, 'Ladowanie playlisty...')

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.vlc_panel, proportion=4, flag=wx.EXPAND)
        vbox.Add(self.status, 0, wx.ALL, 4)
        vbox.Add(btn_sizer, 0, wx.EXPAND)
        self.SetSizer(vbox)

        self.Bind(wx.EVT_CLOSE, self._on_close)

        self._progress_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_progress_timer, self._progress_timer)
        self._progress_timer.Start(200)

        t = threading.Thread(target=self._load_playlist)
        t.daemon = True
        t.start()

    def _load_playlist(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                age = time.time() - cache.get('timestamp', 0)
                if age < CACHE_MAX_AGE and cache.get('videos'):
                    print '[LOAD] cache OK (wiek: %ds)' % int(age)
                    videos = [tuple(v) for v in cache['videos']]
                    random.shuffle(videos)
                    self.playlist = videos
                    wx.CallAfter(self._play_current)
                    return
            except Exception as e:
                print '[LOAD] BLAD cache:', e

        print '[LOAD] pobieranie subskrypcji...'
        videos = []

        try:
            channel_ids = []
            next_page = None
            while True:
                kwargs = dict(part='snippet', mine=True, maxResults=50)
                if next_page:
                    kwargs['pageToken'] = next_page
                resp = self.youtube.subscriptions().list(**kwargs).execute()
                for item in resp.get('items', []):
                    channel_ids.append(item['snippet']['resourceId']['channelId'])
                next_page = resp.get('nextPageToken')
                if not next_page:
                    break
            print '[LOAD] subskrypcje: %d kanalow' % len(channel_ids)
        except Exception as e:
            print '[LOAD] BLAD subskrypcji:', e
            channel_ids = []

        for channel_id in channel_ids:
            try:
                uploads_playlist_id = 'UU' + channel_id[2:]
                next_page = None
                fetched = 0
                while fetched < 5:
                    kwargs = dict(
                        part='snippet',
                        playlistId=uploads_playlist_id,
                        maxResults=min(5 - fetched, 50)
                    )
                    if next_page:
                        kwargs['pageToken'] = next_page
                    resp = self.youtube.playlistItems().list(**kwargs).execute()
                    for item in resp.get('items', []):
                        vid_id = item['snippet']['resourceId'].get('videoId')
                        title = item['snippet'].get('title', '')
                        if vid_id:
                            videos.append(('https://www.youtube.com/watch?v=' + vid_id, title))
                            fetched += 1
                    next_page = resp.get('nextPageToken')
                    if not next_page or fetched >= 5:
                        break
            except Exception:
                pass

        print '[LOAD] filmow z subskrypcji: %d' % len(videos)

        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump({'timestamp': time.time(), 'videos': videos}, f)
        except Exception as e:
            print '[LOAD] BLAD zapisu cache:', e

        random.shuffle(videos)
        self.playlist = videos
        if self.playlist:
            wx.CallAfter(self._play_current)
        else:
            wx.CallAfter(self.status.SetLabel, 'Brak filmow')

    def _play_current(self):
        if not self.playlist:
            return
        url, title = self.playlist[self.current_index]
        self.status.SetLabel('[%d/%d] Ladowanie: %s' % (self.current_index+1, len(self.playlist), title[:50]))
        self._play_start_time = None
        self._intentional_stop = True
        if self._ffmpeg_proc:
            self._ffmpeg_proc.kill()
            self._ffmpeg_proc = None
        self.player.stop()
        t = threading.Thread(target=self._resolve_and_play, args=(url,))
        t.daemon = True
        t.start()

    def _resolve_and_play(self, url):
        video_url, audio_url, duration_s = get_urls(url)
        if video_url is None:
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
            wx.CallAfter(self._start_play, fd_path)
        else:
            wx.CallAfter(self._start_play, video_url)

    def _start_play(self, video_url):
        self.player.set_xwindow(self.vlc_panel.GetHandle())
        media = self.vlc_instance.media_new(video_url)
        self.player.set_media(media)
        self.player.play()

    def _on_playing(self):
        self._play_start_time = time.time()
        url, title = self.playlist[self.current_index]
        print '[VLC] PLAYING: %s' % title[:60]

    def _on_progress_timer(self, event):
        if self.player.get_state() not in (vlc.State.Playing, vlc.State.Paused):
            return
        elapsed = time.time() - self._play_start_time if self._play_start_time else 0.0
        length = self._length_ms / 1000.0
        if self.playlist:
            _, title = self.playlist[self.current_index]
            self.status.SetLabel('[%d/%d] %.1fs / %.1fs  %s' % (
                self.current_index+1, len(self.playlist),
                elapsed, length, title[:40]))

    def _is_real_end(self, elapsed, length_ms):
        if length_ms <= 0 or elapsed < 0:
            return True
        return elapsed >= (length_ms / 1000.0) * 0.85

    def _on_end(self):
        elapsed = time.time() - self._play_start_time if self._play_start_time else -1
        if not self._is_real_end(elapsed, self._length_ms):
            return
        self._next()

    def _on_stopped(self):
        elapsed = time.time() - self._play_start_time if self._play_start_time else -1
        if self._intentional_stop:
            self._intentional_stop = False
            return
        if not self._is_real_end(elapsed, self._length_ms):
            wx.CallLater(500, self.player.play)

    def _on_error(self):
        wx.CallAfter(self._next)

    def _next(self):
        if self.current_index < len(self.playlist) - 1:
            self.current_index += 1
        else:
            self.current_index = 0
        self._play_current()

    def _prev(self):
        if self.current_index > 0:
            self.current_index -= 1
        self._play_current()

    def _on_btn(self, event):
        label = event.GetEventObject().GetLabel()
        if 'POPRZEDNI' in label:
            self._prev()
        elif 'NASTEPNY' in label:
            self._next()
        elif 'WYJSCIE' in label:
            self.Close()

    def _on_close(self, event):
        self._intentional_stop = True
        if self._ffmpeg_proc:
            self._ffmpeg_proc.kill()
        self.player.stop()
        self.Destroy()


if __name__ == '__main__':
    print 'Autoryzacja OAuth2...'
    youtube_service = get_authenticated_service()
    print 'OK'

    app = wx.App(False)
    frame = TestFrame(youtube_service)
    frame.Show(True)
    app.MainLoop()
