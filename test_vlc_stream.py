#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import vlc
import subprocess
import os
import sys

TEST_URL = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, 'Test VLC embedded', size=(1280, 800))

        self.vlc_instance = vlc.Instance('--no-xlib')
        self.player = self.vlc_instance.media_player_new()

        self.vlc_panel = wx.Panel(self, -1)
        self.vlc_panel.SetBackgroundColour('black')

        self.status = wx.StaticText(self, -1, 'Ladowanie...', size=(1280, 40))
        self.status.SetForegroundColour('white')
        self.status.SetBackgroundColour('black')

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.vlc_panel, proportion=1, flag=wx.EXPAND)
        sizer.Add(self.status, proportion=0, flag=wx.EXPAND)
        self.SetSizer(sizer)
        self.SetBackgroundColour('black')

        self.Bind(wx.EVT_SHOW, self.on_show)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(1000)

    def on_show(self, event):
        if event.IsShown():
            self.start_playback()

    def start_playback(self):
        self.status.SetLabel('Pobieram URL streamu przez yt-dlp...')
        self.Update()

        import subprocess
        try:
            result = subprocess.check_output(
                ['yt-dlp', '-g', TEST_URL],
                stderr=open(os.devnull, 'w')
            )
            urls = result.strip().split('\n')
            video_url = urls[0]
            audio_url = urls[1] if len(urls) > 1 else None
            print 'Video URL:', video_url[:80]
            if audio_url:
                print 'Audio URL:', audio_url[:80]
        except Exception as e:
            self.status.SetLabel('BLAD yt-dlp: ' + str(e))
            print 'BLAD yt-dlp:', e
            return

        self.player.set_xwindow(self.vlc_panel.GetHandle())
        if audio_url:
            media = self.vlc_instance.media_new(video_url, ':input-slave=' + audio_url)
        else:
            media = self.vlc_instance.media_new(video_url)
        self.player.set_media(media)
        self.player.play()

        self.status.SetLabel('Odtwarzam: ' + TEST_URL)

    def on_timer(self, event):
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

        t = self.player.get_time()
        length = self.player.get_length()
        if length > 0:
            cur = '%d:%02d' % (t / 60000, (t % 60000) / 1000)
            tot = '%d:%02d' % (length / 60000, (length % 60000) / 1000)
            pct = int(100.0 * t / length)
            bar = '[' + '#' * (pct / 5) + '-' * (20 - pct / 5) + ']'
            time_str = '%s / %s %s %d%%' % (cur, tot, bar, pct)
        else:
            time_str = '--:-- / --:--'

        self.status.SetLabel('Stan: %s  |  %s  |  Glosnosc: %d%%' % (label, time_str, vol))

        if state == vlc.State.Error:
            print 'WYNIK: BLAD ODTWARZANIA'

    def on_close(self, event):
        self.timer.Stop()
        self.player.stop()
        self.Destroy()

if __name__ == '__main__':
    print '=== Test VLC embedded w wxPython ==='
    print 'URL testowy:', TEST_URL
    print 'Jesli film sie nie uruchamia sprawdz:'
    print '  1. sudo apt install vlc'
    print '  2. pip install python-vlc yt-dlp'
    print ''

    app = wx.App(False)
    frame = TestFrame()
    frame.Show()
    app.MainLoop()