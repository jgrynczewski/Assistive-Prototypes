#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os, sys, time, subprocess, threading
import wx

import vlc

# 5 krotkich filmow (10-15s) - YouTube Shorts PL trending
PLAYLIST = [
    'https://www.youtube.com/watch?v=UF0FXYDQ634',  # 10s
    'https://www.youtube.com/watch?v=nB54sR0hqwg',  # 10s
    'https://www.youtube.com/watch?v=jbGI8EL63uc',  # 11s
    'https://www.youtube.com/watch?v=eLfAMuyrWsQ',  # 12s
    'https://www.youtube.com/watch?v=Zfg1B_uSk9s',  # 13s
]

YTDLP = '/home/radoslaw/.local/bin/yt-dlp'
FMT = 'bestvideo[height<=480][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio'

def get_urls(youtube_url):
    print '[YTDLP] resolving:', youtube_url
    try:
        result = subprocess.check_output(
            [YTDLP, '--print', '%(duration)s', '-g', '-f', FMT, youtube_url],
            stderr=open(os.devnull, 'w')
        )
        lines = result.strip().split('\n')
        duration_s = float(lines[0]) if lines[0].replace('.','').isdigit() else 0
        video_url = lines[1]
        audio_url = lines[2] if len(lines) > 2 else None
        print '[YTDLP] OK  duration=%.1fs  audio=%s' % (duration_s, 'tak' if audio_url else 'nie')
        return video_url, audio_url, duration_s
    except Exception as e:
        print '[YTDLP] BLAD:', e
        return None, None, 0


PIPE_PATH = '/tmp/vlc_yt_pipe'

def start_ffmpeg_pipe(video_url, audio_url):
    if os.path.exists(PIPE_PATH):
        os.remove(PIPE_PATH)
    os.mkfifo(PIPE_PATH)
    proc = subprocess.Popen(
        ['ffmpeg', '-loglevel', 'quiet',
         '-i', video_url, '-i', audio_url,
         '-c', 'copy', '-f', 'matroska', PIPE_PATH],
        stderr=open(os.devnull, 'w')
    )
    return proc


class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, 'VLC Playback Test', size=(800, 600))

        self.current_index = 0
        self._play_start_time = None
        self._intentional_stop = False
        self._length_ms = 0
        self._ffmpeg_proc = None

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

        self.status = wx.StaticText(self, -1, 'Ladowanie...')

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.vlc_panel, proportion=4, flag=wx.EXPAND)
        vbox.Add(self.status, 0, wx.ALL, 4)
        vbox.Add(btn_sizer, 0, wx.EXPAND)
        self.SetSizer(vbox)

        self.Bind(wx.EVT_CLOSE, self._on_close)

        self._progress_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_progress_timer, self._progress_timer)
        self._progress_timer.Start(200)

        self._play_current()

    def _play_current(self):
        url = PLAYLIST[self.current_index]
        self.status.SetLabel('[%d/%d] Ladowanie...' % (self.current_index+1, len(PLAYLIST)))
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
            wx.CallAfter(self._start_play, fd_path, None)
        else:
            wx.CallAfter(self._start_play, video_url, None)

    def _start_play(self, video_url, audio_url):
        self.player.set_xwindow(self.vlc_panel.GetHandle())
        media = self.vlc_instance.media_new(video_url)
        self.player.set_media(media)
        self.player.play()

    def _on_playing(self):
        self._play_start_time = time.time()
        print '[VLC] PLAYING  length=%.1fs' % (self._length_ms/1000.0)

    def _on_progress_timer(self, event):
        if self.player.get_state() not in (vlc.State.Playing, vlc.State.Paused):
            return
        length = self.player.get_length()
        if length <= 0:
            length = self._length_ms
        elapsed = time.time() - self._play_start_time if self._play_start_time else 0.0
        self.status.SetLabel('[%d/%d]  %.1fs / %.1fs' % (
            self.current_index + 1, len(PLAYLIST),
            elapsed, length / 1000.0))

    def _is_real_end(self, elapsed, length_ms):
        if length_ms <= 0 or elapsed < 0:
            return True
        return elapsed >= (length_ms / 1000.0) * 0.85

    def _on_end(self):
        elapsed = time.time() - self._play_start_time if self._play_start_time else -1
        length = self.player.get_length()
        print '[VLC] END_REACHED  elapsed=%.1fs  length=%.1fs  real=%s' % (
            elapsed, length/1000.0, self._is_real_end(elapsed, length))
        if not self._is_real_end(elapsed, length):
            print '[VLC] ZA WCZESNIE - ignoruje'
            return
        self._next()

    def _on_stopped(self):
        elapsed = time.time() - self._play_start_time if self._play_start_time else -1
        length = self.player.get_length()
        print '[VLC] STOPPED  elapsed=%.1fs  intentional=%s' % (elapsed, self._intentional_stop)
        if self._intentional_stop:
            self._intentional_stop = False
            return
        if not self._is_real_end(elapsed, length):
            print '[VLC] STOPPED za wczesnie - wznawiamy'
            wx.CallLater(500, self.player.play)

    def _on_error(self):
        elapsed = time.time() - self._play_start_time if self._play_start_time else -1
        print '[VLC] ERROR!  elapsed=%.1fs' % elapsed
        wx.CallAfter(self._next)

    def _next(self):
        print '[NAV] NASTEPNY  %d -> %d' % (self.current_index, self.current_index+1)
        if self.current_index < len(PLAYLIST) - 1:
            self.current_index += 1
            self._play_current()
        else:
            print '[NAV] Koniec playlisty'
            self.status.SetLabel('Koniec playlisty')

    def _prev(self):
        print '[NAV] POPRZEDNI  %d -> %d' % (self.current_index, self.current_index-1)
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
        self.player.stop()
        self.Destroy()


if __name__ == '__main__':
    app = wx.App(False)
    frame = TestFrame()
    frame.Show(True)
    app.MainLoop()