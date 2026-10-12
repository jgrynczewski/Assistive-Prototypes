#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import vlc
import urllib2
import json
import os
import sys
import subprocess

KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.youtube_api_key')

def load_playlist():
    if not os.path.exists(KEY_FILE):
        print 'Brak klucza API - uzyje testowych URL-i'
        return [
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://www.youtube.com/watch?v=9bZkp7q19f0',
            'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
        ]
    with open(KEY_FILE, 'r') as f:
        key = f.read().strip()
    url = (
        'https://www.googleapis.com/youtube/v3/videos'
        '?part=snippet&chart=mostPopular&regionCode=PL&maxResults=10&key=' + key
    )
    try:
        data = json.loads(urllib2.urlopen(url, timeout=10).read())
        urls = ['https://www.youtube.com/watch?v=' + item['id'] for item in data.get('items', [])]
        print 'Pobrano', len(urls), 'filmow z API'
        return urls
    except Exception as e:
        print 'Blad API:', e
        sys.exit(1)

class TestControlFrame(wx.Frame):
    def __init__(self, playlist):
        wx.Frame.__init__(self, None, -1, 'Test sterowania VLC', size=(1280, 800))
        self.SetBackgroundColour('black')

        self.playlist = playlist
        self.current = 0

        self.vlc_instance = vlc.Instance('--no-xlib')
        self.player = self.vlc_instance.media_player_new()

        self.vlc_panel = wx.Panel(self, -1)
        self.vlc_panel.SetBackgroundColour('black')

        btn_style = wx.DefaultSize
        self.btn_prev     = wx.Button(self, -1, u'◀ POPRZEDNI')
        self.btn_playpause = wx.Button(self, -1, u'⏸ PAUZA/PLAY')
        self.btn_next     = wx.Button(self, -1, u'▶ NASTEPNY')
        self.btn_volup    = wx.Button(self, -1, u'🔊+ GLOSNIEJ')
        self.btn_voldown  = wx.Button(self, -1, u'🔊- CISZEJ')
        self.btn_quit     = wx.Button(self, -1, u'✕ WYJSCIE')

        for btn in [self.btn_prev, self.btn_playpause, self.btn_next,
                    self.btn_volup, self.btn_voldown, self.btn_quit]:
            btn.SetBackgroundColour('#333333')
            btn.SetForegroundColour('white')

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for btn in [self.btn_prev, self.btn_playpause, self.btn_next,
                    self.btn_volup, self.btn_voldown, self.btn_quit]:
            btn_sizer.Add(btn, proportion=1, flag=wx.EXPAND | wx.ALL, border=4)

        self.status = wx.StaticText(self, -1, '')
        self.status.SetForegroundColour('white')
        self.status.SetBackgroundColour('black')

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.vlc_panel, proportion=1, flag=wx.EXPAND)
        sizer.Add(btn_sizer, proportion=0, flag=wx.EXPAND)
        sizer.Add(self.status, proportion=0, flag=wx.EXPAND)
        self.SetSizer(sizer)

        self.btn_prev.Bind(wx.EVT_BUTTON, self.on_prev)
        self.btn_playpause.Bind(wx.EVT_BUTTON, self.on_playpause)
        self.btn_next.Bind(wx.EVT_BUTTON, self.on_next)
        self.btn_volup.Bind(wx.EVT_BUTTON, self.on_volup)
        self.btn_voldown.Bind(wx.EVT_BUTTON, self.on_voldown)
        self.btn_quit.Bind(wx.EVT_BUTTON, self.on_quit)
        self.Bind(wx.EVT_CLOSE, self.on_quit)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(1000)

        self.Bind(wx.EVT_SHOW, self.on_show)

    def on_show(self, event):
        if event.IsShown():
            self.play_current()

    def _get_stream_urls(self, youtube_url):
        self.status.SetLabel('Pobieram URL streamu... ' + youtube_url[:60])
        self.Update()
        fmt = 'bestvideo[height<=720][vcodec^=avc]+bestaudio[ext=m4a]/best[height<=720][vcodec^=avc]/best[height<=720]/best'
        try:
            result = subprocess.check_output(
                ['/home/radoslaw/.local/bin/yt-dlp', '-g', '-f', fmt, youtube_url],
                stderr=open(os.devnull, 'w')
            )
            urls = result.strip().split('\n')
            video_url = urls[0]
            audio_url = urls[1] if len(urls) > 1 else None
            return video_url, audio_url
        except Exception as e:
            print 'BLAD yt-dlp:', e
            return None, None

    def play_current(self):
        url = self.playlist[self.current]
        self.player.stop()
        video_url, audio_url = self._get_stream_urls(url)
        if video_url is None:
            self.status.SetLabel('BLAD: nie mozna pobrac URL dla ' + url[:60])
            return
        self.player.set_xwindow(self.vlc_panel.GetHandle())
        if audio_url:
            media = self.vlc_instance.media_new(video_url, ':input-slave=' + audio_url)
        else:
            media = self.vlc_instance.media_new(video_url)
        self.player.set_media(media)
        self.player.play()
        self.update_status()

    def on_prev(self, event):
        self.current = max(0, self.current - 1)
        self.play_current()
        print 'POPRZEDNI -> film', self.current

    def on_next(self, event):
        self.current = min(len(self.playlist) - 1, self.current + 1)
        self.play_current()
        print 'NASTEPNY -> film', self.current

    def on_playpause(self, event):
        state = self.player.get_state()
        if state == vlc.State.Playing:
            self.player.pause()
            print 'PAUZA'
        else:
            self.player.play()
            print 'PLAY'
        self.update_status()

    def on_volup(self, event):
        vol = min(100, self.player.audio_get_volume() + 10)
        self.player.audio_set_volume(vol)
        print 'GLOSNOSC:', vol
        self.update_status()

    def on_voldown(self, event):
        vol = max(0, self.player.audio_get_volume() - 10)
        self.player.audio_set_volume(vol)
        print 'GLOSNOSC:', vol
        self.update_status()

    def on_quit(self, event):
        self.timer.Stop()
        self.player.stop()
        self.Destroy()

    def on_timer(self, event):
        if self.player.get_state() == vlc.State.Ended:
            print 'Film zakonczony - przechodze do nastepnego'
            self.on_next(None)
        self.update_status()

    def update_status(self):
        state = self.player.get_state()
        state_names = {
            vlc.State.NothingSpecial: 'brak',
            vlc.State.Opening:        'otwieranie',
            vlc.State.Buffering:      'buforowanie',
            vlc.State.Playing:        'ODTWARZA',
            vlc.State.Paused:         'PAUZA',
            vlc.State.Stopped:        'zatrzymany',
            vlc.State.Ended:          'zakonczony',
            vlc.State.Error:          'BLAD',
        }
        label = state_names.get(state, str(state))
        vol = self.player.audio_get_volume()
        url = self.playlist[self.current]
        self.status.SetLabel(
            'Film %d/%d | Stan: %s | Glosnosc: %d%% | %s' % (
                self.current + 1, len(self.playlist), label, vol, url[:70]
            )
        )

if __name__ == '__main__':
    print '=== Test sterowania VLC (next/prev/pause/volume) ==='
    print ''
    playlist = load_playlist()
    print 'Playlista:', len(playlist), 'filmow'
    print ''

    app = wx.App(False)
    frame = TestControlFrame(playlist)
    frame.Show()
    app.MainLoop()

    print ''
    print 'WYNIK: jesli film sie wyswietlal i przyciski dzialaly - wszystko OK'