#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""Scenka na ekranie gry - zalezna od gry (sceneFor):
- Tajemnica zegara: szkolny zegar z wahadlem i ludziki, ktore sie kreca -
  chodza, staja, czasem podchodza do siebie i "rozmawiaja" (Scene);
- Ostatnia zwrotka: noc w ogrodzie willi - lampiony, basen, para na brzegu,
  Bigos (NightScene);
- gry z kreatora gier: ich animacja - klatki z serwera ap-gra (FramesScene).

Nic z fabuly nie zalezy od scenki - to tylko zywy podglad, zeby na ekranie
cos sie dzialo. Rysowane prostymi ksztaltami (bez plikow graficznych).

Scene - logika i rysowanie na dowolnym DC (bez okna; da sie wyrenderowac
podglad poza AP). Scenka - panel wx z zegarem (timer), uzywany w modules/gra.py.
"""

from __future__ import division

import math
import random
import time
from cStringIO import StringIO

import wx

FRAME_MS = 50               # 20 klatek na sekunde
PENDULUM_PERIOD = 2.0       # [s] pelne wahniecie tam i z powrotem
MINUTE_JUMP = 6.0           # [s] co tyle wskazowka minutowa przeskakuje

WALL = '#F3EBDD'
FLOOR = '#C9A77C'
FLOOR_LINE = '#9C7B52'
CASE = '#6B4226'
CASE_DARK = '#4A2C17'
GLASS = '#E9DFC9'
BRASS = '#D4A017'
FACE = '#FFFDF5'
INK = '#2B2B2B'
SKIN = '#F1C27D'
TROUSERS = '#3B3B4F'
SHIRTS = ['#1E6FD9', '#D93A2B', '#2E9E5B', '#8E44AD']


def _pen(colour, width=1):
    return wx.Pen(colour, max(1, int(round(width))))


def _brush(colour):
    return wx.Brush(colour)


#=============================================================================
class Person(object):
    """Ludzik: x - pozycja jako ulamek szerokosci; depth 0 (blisko) .. 1 (dalej)."""

    def __init__(self, shirt, x, depth):
        self.shirt = shirt
        self.x = x
        self.depth = depth
        self.facing = random.choice((-1, 1))
        self.speed = random.uniform(0.05, 0.09)
        self.target = x
        self.wait = random.uniform(0.5, 3.0)
        self.partner = None
        self.phase = 0.0

    def walking(self):
        return self.wait <= 0 and abs(self.target - self.x) > 1e-3

    def talking(self):
        p = self.partner
        return (self.wait > 0 and p is not None and not p.walking()
                and abs(p.x - self.x) < 0.14)

    def pickTarget(self, others):
        self.partner = None
        free = [o for o in others if o is not self]
        if free and random.random() < 0.4:
            # Podejdz do kogos i stan obok niego
            other = random.choice(free)
            side = -1 if self.x < other.x else 1
            self.target = min(0.92, max(0.08, other.x + side * 0.08))
            self.partner = other
        else:
            self.target = random.uniform(0.08, 0.92)

    def update(self, dt, others):
        if self.wait > 0:
            self.wait -= dt
            if self.wait <= 0:
                self.pickTarget(others)
            return
        distance = self.target - self.x
        step = self.speed * dt
        if abs(distance) <= step:
            self.x = self.target
            self.phase = 0.0
            p = self.partner
            if p is not None and abs(p.x - self.x) < 0.14:
                # Spotkanie: twarza w twarz, dluzszy postoj; partner zaczeka
                self.facing = 1 if p.x > self.x else -1
                self.wait = random.uniform(3.0, 6.0)
                if not p.walking():
                    p.facing = -self.facing
                    p.wait = max(p.wait, self.wait)
                    p.partner = self
            else:
                self.partner = None
                self.wait = random.uniform(0.8, 3.5)
        else:
            self.facing = 1 if distance > 0 else -1
            self.x += step * self.facing
            self.phase += dt * 9.0

    def draw(self, dc, w, h, now):
        size = h * 0.30 * (1.0 - 0.18 * self.depth)        # wzrost
        foot = h * (0.95 - 0.07 * self.depth)
        X = self.x * w
        head = size * 0.09
        top = foot - size
        neck = top + 2 * head
        hip = top + size * 0.56
        leg = foot - hip
        swing = math.sin(self.phase) * 0.45 if self.walking() else 0.0

        # Nogi
        dc.SetPen(_pen(TROUSERS, size * 0.07))
        for a in (swing, -swing):
            dc.DrawLine(int(X), int(hip), int(X + math.sin(a) * leg), int(hip + math.cos(a) * leg))
        # Tulow
        dc.SetPen(_pen(self.shirt, size * 0.12))
        dc.DrawLine(int(X), int(neck + size * 0.03), int(X), int(hip))
        # Rece (machaja w przeciwnym rytmie niz nogi)
        arm = size * 0.30
        shoulder = neck + size * 0.06
        dc.SetPen(_pen(self.shirt, size * 0.055))
        for a in (-swing * 0.8, swing * 0.8):
            dc.DrawLine(int(X), int(shoulder), int(X + math.sin(a) * arm), int(shoulder + math.cos(a) * arm))
        # Glowa, oko po stronie, w ktora patrzy
        dc.SetPen(_pen(INK, 1))
        dc.SetBrush(_brush(SKIN))
        dc.DrawCircle(int(X), int(top + head), int(head))
        dc.SetBrush(_brush(INK))
        dc.DrawCircle(int(X + self.facing * head * 0.45), int(top + head * 0.85), max(1, int(head * 0.14)))

        # Rozmowa: "..." nad glowa tego, kto patrzy w prawo (jeden dymek na pare; mruga)
        if self.talking() and self.facing > 0 and int(now * 1.5) % 2 == 0:
            dot = max(2, int(head * 0.22))
            bx = X + self.facing * head * 1.2
            by = top - head * 0.4
            dc.SetPen(_pen(INK, 1))
            dc.SetBrush(_brush('#FFFFFF'))
            dc.DrawRoundedRectangle(int(bx - head * 0.9), int(by - head * 0.6),
                                    int(head * 1.8), int(head * 1.2), int(head * 0.4))
            dc.SetBrush(_brush(INK))
            for i in (-1, 0, 1):
                dc.DrawCircle(int(bx + i * head * 0.5), int(by), dot)


#=============================================================================
class Scene(object):
    """Zegar + ludziki. update(dt) - ruch, draw(dc, w, h) - rysowanie."""

    def __init__(self, people=3):
        self.started = time.time()
        self.people = [Person(SHIRTS[i % len(SHIRTS)], random.uniform(0.15, 0.85), i / max(1, people - 1))
                       for i in range(people)]

    def update(self, dt):
        for person in self.people:
            person.update(dt, self.people)

    def draw(self, dc, w, h, now=None):
        if now is None:
            now = time.time() - self.started
        # Sciana i podloga
        dc.SetPen(_pen(WALL))
        dc.SetBrush(_brush(WALL))
        dc.DrawRectangle(0, 0, w, h)
        floorY = int(h * 0.80)
        dc.SetPen(_pen(FLOOR))
        dc.SetBrush(_brush(FLOOR))
        dc.DrawRectangle(0, floorY, w, h - floorY)
        dc.SetPen(_pen(FLOOR_LINE, max(2, h * 0.006)))
        dc.DrawLine(0, floorY, w, floorY)

        self.drawClock(dc, w, h, now)
        # Dalsi najpierw - blizsi zaslaniaja
        for person in sorted(self.people, key=lambda p: -p.depth):
            person.draw(dc, w, h, now)

    def drawClock(self, dc, w, h, now):
        r = min(w * 0.17, h * 0.11)
        cx = w / 2.0
        cy = h * 0.04 + 1.3 * r
        # Skrzynia
        dc.SetPen(_pen(CASE_DARK, r * 0.06))
        dc.SetBrush(_brush(CASE))
        dc.DrawRoundedRectangle(int(cx - 1.3 * r), int(cy - 1.3 * r), int(2.6 * r), int(4.6 * r), int(r * 0.25))
        # Okienko na wahadlo
        dc.SetBrush(_brush(GLASS))
        top = cy + 1.25 * r
        dc.DrawRectangle(int(cx - 0.8 * r), int(top), int(1.6 * r), int(2.15 * r))
        # Wahadlo
        angle = 0.28 * math.sin(2 * math.pi * now / PENDULUM_PERIOD)
        pivotY = top + 0.05 * r
        length = 1.55 * r
        bx = cx + math.sin(angle) * length
        by = pivotY + math.cos(angle) * length
        dc.SetPen(_pen(BRASS, r * 0.07))
        dc.DrawLine(int(cx), int(pivotY), int(bx), int(by))
        dc.SetPen(_pen(CASE_DARK, 1))
        dc.SetBrush(_brush(BRASS))
        dc.DrawCircle(int(bx), int(by), int(r * 0.26))
        # Tarcza
        dc.SetPen(_pen(INK, r * 0.05))
        dc.SetBrush(_brush(FACE))
        dc.DrawCircle(int(cx), int(cy), int(r))
        dc.SetPen(_pen(INK, r * 0.04))
        for i in range(12):
            a = i * math.pi / 6
            inner = 0.78 if i % 3 == 0 else 0.86
            dc.DrawLine(int(cx + math.sin(a) * r * inner), int(cy - math.cos(a) * r * inner),
                        int(cx + math.sin(a) * r * 0.94), int(cy - math.cos(a) * r * 0.94))
        # Wskazowki: od 7:55, minutowa przeskakuje co MINUTE_JUMP sekund
        minutes = 7 * 60 + 55 + int(now // MINUTE_JUMP)
        m = (minutes % 60) / 60.0 * 2 * math.pi
        hr = ((minutes / 60.0) % 12) / 12.0 * 2 * math.pi
        dc.SetPen(_pen(INK, r * 0.09))
        dc.DrawLine(int(cx), int(cy), int(cx + math.sin(hr) * r * 0.5), int(cy - math.cos(hr) * r * 0.5))
        dc.SetPen(_pen(INK, r * 0.05))
        dc.DrawLine(int(cx), int(cy), int(cx + math.sin(m) * r * 0.78), int(cy - math.cos(m) * r * 0.78))
        dc.SetBrush(_brush(INK))
        dc.DrawCircle(int(cx), int(cy), max(2, int(r * 0.06)))


#=============================================================================
# "Ostatnia zwrotka" (romans): noc w ogrodzie willi - gwiazdy, ksiezyc, okna
# willi, w ktorych ktos zapala i gasi swiatlo, girlanda lampionow na wietrze,
# basen z falami, dwie postacie z nogami w wodzie (czasem unosi sie
# serduszko), swietliki i Bigos na brzegu basenu.

SKY = ['#14213D', '#1B2B4F', '#26396A']
MOON = '#FFF3C4'
STAR = '#FFFFFF'
VILLA = '#0E1628'
WINDOW_ON = '#FFD27A'
WINDOW_OFF = '#1F2A44'
GRASS = '#1E3B2F'
POOL = '#2BB3C9'
POOL_EDGE = '#D9D2C3'
RIPPLE = '#A7EAF2'
CORD = '#5A5A6E'
LANTERNS = ['#FF6B6B', '#FFD166', '#06D6A0', '#4CC9F0', '#F78C6B', '#C77DFF', '#FFD166']
FIREFLY = '#E9FF70'
HEART = '#FF4D6D'
DOG = '#B07D4F'
NINA = '#E85D75'
HERO = '#3D7DD8'


def _heart(dc, x, y, size):
    """Serduszko: dwa kola i trojkat; (x, y) - srodek gornej czesci."""
    r = max(2, int(size * 0.3))
    dc.SetPen(_pen(HEART, 1))
    dc.SetBrush(_brush(HEART))
    dc.DrawCircle(int(x - r * 0.8), int(y), r)
    dc.DrawCircle(int(x + r * 0.8), int(y), r)
    dc.DrawPolygon([(int(x - r * 1.75), int(y + r * 0.35)), (int(x + r * 1.75), int(y + r * 0.35)),
                    (int(x), int(y + r * 2.6))])


class NightScene(object):
    """Noc w ogrodzie willi. update(dt) - ruch, draw(dc, w, h) - rysowanie."""

    def __init__(self):
        self.started = time.time()
        rnd = random.Random(7)  # te same gwiazdy i okna za kazdym razem
        self.stars = [(rnd.random(), rnd.random() * 0.33, rnd.uniform(0.7, 2.4), rnd.uniform(0, 6.3))
                      for i in range(30)]
        self.windows = [(col, row, rnd.uniform(0, 6.3), rnd.uniform(0.08, 0.25))
                        for col in range(3) for row in range(3)]
        self.flies = [(rnd.uniform(0.05, 0.95), rnd.uniform(0.5, 0.68), rnd.uniform(0, 6.3),
                       rnd.uniform(0.3, 0.7)) for i in range(6)]
        self.dogX, self.dogDir, self.dogWait = 0.8, -1, 2.0
        self.hearts = []
        self.nextHeart = 4.0

    def update(self, dt):
        # Bigos chodzi po brzegu basenu, czasem przystaje
        if self.dogWait > 0:
            self.dogWait -= dt
        else:
            self.dogX += self.dogDir * 0.07 * dt
            if self.dogX < 0.6 or self.dogX > 0.94:
                self.dogDir = -self.dogDir
                self.dogX = min(0.94, max(0.6, self.dogX))
                self.dogWait = random.uniform(1.5, 4.0)
            elif random.random() < 0.004:
                self.dogWait = random.uniform(1.0, 3.0)
        # Serduszko nad para - co kilka sekund
        self.nextHeart -= dt
        if self.nextHeart <= 0:
            self.hearts.append([0.0])
            self.nextHeart = random.uniform(6.0, 11.0)
        for heart in self.hearts:
            heart[0] += dt
        self.hearts = [heart for heart in self.hearts if heart[0] < 4.0]

    def draw(self, dc, w, h, now=None):
        if now is None:
            now = time.time() - self.started
        k = min(w, h) / 540.0  # skala

        # Niebo w trzech pasach, trawa
        horizon = int(h * 0.62)
        for i, colour in enumerate(SKY):
            dc.SetPen(_pen(colour))
            dc.SetBrush(_brush(colour))
            dc.DrawRectangle(0, int(horizon * i / 3.0), w, int(horizon / 3.0) + 2)
        dc.SetPen(_pen(GRASS))
        dc.SetBrush(_brush(GRASS))
        dc.DrawRectangle(0, horizon, w, h - horizon)

        # Gwiazdy migocza
        dc.SetPen(_pen(STAR))
        dc.SetBrush(_brush(STAR))
        for x, y, speed, phase in self.stars:
            r = (0.6 + 0.9 * (math.sin(now * speed + phase) + 1)) * k
            dc.DrawCircle(int(x * w), int(y * h), max(1, int(r)))

        # Ksiezyc (sierp: kolo nieba nachodzi na jasne kolo)
        mr = int(0.065 * min(w, h))
        mx, my = int(w * 0.84), int(h * 0.11)
        dc.SetPen(_pen(MOON))
        dc.SetBrush(_brush(MOON))
        dc.DrawCircle(mx, my, mr)
        dc.SetPen(_pen(SKY[0]))
        dc.SetBrush(_brush(SKY[0]))
        dc.DrawCircle(int(mx + mr * 0.45), int(my - mr * 0.2), mr)

        # Willa z oknami - ktos zapala i gasi swiatlo
        vx, vy, vw, vh = int(w * 0.04), int(h * 0.24), int(w * 0.38), horizon - int(h * 0.24)
        dc.SetPen(_pen(VILLA))
        dc.SetBrush(_brush(VILLA))
        dc.DrawRectangle(vx, vy, vw, vh)
        dc.DrawPolygon([(vx - int(w * 0.02), vy), (vx + vw + int(w * 0.02), vy),
                        (vx + vw / 2, vy - int(h * 0.09))])
        ww, wh = vw / 5.0, vh / 6.0
        for col, row, phase, speed in self.windows:
            lit = math.sin(now * speed + phase) > -0.35
            dc.SetPen(_pen(WINDOW_ON if lit else WINDOW_OFF))
            dc.SetBrush(_brush(WINDOW_ON if lit else WINDOW_OFF))
            dc.DrawRectangle(int(vx + ww * (0.6 + col * 1.5)), int(vy + wh * (0.6 + row * 1.7)),
                             int(ww), int(wh))

        # Girlanda lampionow - kolysze sie na wietrze
        def cord(t):
            return h * 0.2 + h * 0.03 * t + h * 0.09 * 4 * t * (1 - t)
        dc.SetPen(_pen(CORD, 2 * k))
        steps = 24
        for i in range(steps):
            t0, t1 = i / float(steps), (i + 1) / float(steps)
            dc.DrawLine(int(t0 * w), int(cord(t0)), int(t1 * w), int(cord(t1)))
        for i, colour in enumerate(LANTERNS):
            t = (i + 1) / float(len(LANTERNS) + 1)
            swing = math.sin(now * 1.4 + i * 0.9) * 6 * k
            x, y = t * w, cord(t)
            dc.SetPen(_pen(CORD, 1))
            dc.DrawLine(int(x), int(y), int(x + swing), int(y + 14 * k))
            dc.SetPen(_pen(colour))
            dc.SetBrush(_brush(colour))
            dc.DrawCircle(int(x + swing), int(y + 22 * k), max(3, int(11 * k)))

        # Basen z falami
        px, py, pw, ph = int(w * 0.08), int(h * 0.74), int(w * 0.84), int(h * 0.21)
        dc.SetPen(_pen(POOL_EDGE, 5 * k))
        dc.SetBrush(_brush(POOL))
        dc.DrawRoundedRectangle(px, py, pw, ph, int(12 * k))
        dc.SetPen(_pen(RIPPLE, 2 * k))
        for row in range(3):
            y0 = py + ph * (0.3 + 0.22 * row)
            segments = 16
            for i in range(segments):
                x0 = px + 12 * k + (pw - 24 * k) * i / float(segments)
                x1 = px + 12 * k + (pw - 24 * k) * (i + 1) / float(segments)
                f = lambda x: y0 + math.sin(x / (22.0 * k) + now * 1.6 + row) * 3 * k
                if i % 2 == 0:  # kreskowane fale
                    dc.DrawLine(int(x0), int(f(x0)), int(x1), int(f(x1)))

        # Para na brzegu, nogi w wodzie (widziana od tylu); Nina czasem opiera glowe
        lean = max(0.0, math.sin(now * 0.35)) * 7 * k
        for x, colour, headShift in ((w * 0.44, HERO, 0), (w * 0.53, NINA, -lean)):
            body = 46 * k
            dc.SetPen(_pen(SKIN, 4 * k))
            for dx in (-6 * k, 6 * k):  # nogi do wody
                dc.DrawLine(int(x + dx), int(py), int(x + dx * 1.3), int(py + 26 * k))
            dc.SetPen(_pen(colour))
            dc.SetBrush(_brush(colour))
            dc.DrawRoundedRectangle(int(x - 13 * k), int(py - body), int(26 * k), int(body),
                                    int(8 * k))
            dc.SetPen(_pen(INK, 1))
            dc.SetBrush(_brush('#3B2A20'))
            dc.DrawCircle(int(x + headShift), int(py - body - 11 * k), int(12 * k))
        for heart in self.hearts:
            age = heart[0]
            size = 18 * k * min(1.0, 0.4 + age) * (1.0 if age < 3.2 else max(0.2, (4.0 - age) / 0.8))
            _heart(dc, w * 0.485 + math.sin(age * 2.5) * 6 * k, py - 90 * k - age * 30 * k, size)

        # Swietliki
        dc.SetPen(_pen(FIREFLY))
        dc.SetBrush(_brush(FIREFLY))
        for x, y, phase, speed in self.flies:
            fx = (x + 0.06 * math.sin(now * speed + phase)) * w
            fy = (y + 0.04 * math.sin(now * speed * 1.7 + phase)) * h
            if math.sin(now * 2.3 + phase) > -0.3:  # mrugaja
                dc.DrawCircle(int(fx), int(fy), max(2, int(3 * k)))

        # Bigos na brzegu basenu, macha ogonem
        dx, dy = self.dogX * w, py - 4 * k
        face = self.dogDir if self.dogWait <= 0 else (1 if math.sin(now) > 0 else -1)
        dc.SetPen(_pen(DOG))
        dc.SetBrush(_brush(DOG))
        dc.DrawRoundedRectangle(int(dx - 18 * k), int(dy - 18 * k), int(36 * k), int(16 * k),
                                int(7 * k))
        dc.DrawCircle(int(dx + face * 20 * k), int(dy - 20 * k), int(9 * k))
        dc.SetPen(_pen(DOG, 3 * k))
        for leg in (-12 * k, 10 * k):
            dc.DrawLine(int(dx + leg), int(dy - 4 * k), int(dx + leg), int(dy + 4 * k))
        wag = math.sin(now * 12) * 6 * k
        dc.DrawLine(int(dx - face * 18 * k), int(dy - 14 * k), int(dx - face * 28 * k),
                    int(dy - 22 * k + wag))
        dc.SetPen(_pen(INK, 1))
        dc.SetBrush(_brush(INK))
        dc.DrawCircle(int(dx + face * 24 * k), int(dy - 22 * k), max(1, int(2 * k)))


#=============================================================================
class FramesScene(object):
    """Animacja gry z kreatora gier (ap-gra, docs/kreator-gier.md): klatki PNG
    z serwera w petli, fps klatek na sekunde; jedna klatka - nieruchomy
    obrazek. W pamieci tylko pliki (kilka-kilkanascie KB kazdy) - biezaca
    klatka jest dekodowana i skalowana przy zmianie klatki albo rozmiaru
    panelu (96 gotowych bitmap ekranowych zajeloby ok. 150 MB). Proporcje
    klatki zachowane; pasy po bokach w kolorze rogu klatki."""

    def __init__(self, paths, fps=None):
        self.data = []
        for path in paths:
            with open(path, 'rb') as f:
                self.data.append(f.read())
        self.fps = fps or 12
        self.started = time.time()
        self.key = None       # (klatka, w, h) obecnej bitmapy
        self.bitmap = None
        self.edge = '#000000'

    def update(self, dt):
        pass

    def _frame(self, index, w, h):
        image = wx.ImageFromStream(StringIO(self.data[index]), wx.BITMAP_TYPE_PNG)
        if index == 0:
            self.edge = wx.Colour(image.GetRed(0, 0), image.GetGreen(0, 0), image.GetBlue(0, 0))
        scale = min(w / float(image.GetWidth()), h / float(image.GetHeight()))
        size = (max(1, int(image.GetWidth() * scale)), max(1, int(image.GetHeight() * scale)))
        return wx.BitmapFromImage(image.Scale(size[0], size[1], wx.IMAGE_QUALITY_NORMAL))

    def draw(self, dc, w, h, now=None):
        if now is None:
            now = time.time() - self.started
        index = int(now * self.fps) % len(self.data)
        if self.key != (index, w, h):
            if self.bitmap is None and index != 0:
                self._frame(0, w, h)  # kolor pasow - z pierwszej klatki
            self.bitmap = self._frame(index, w, h)
            self.key = (index, w, h)
        dc.SetBackground(wx.Brush(self.edge))
        dc.Clear()
        dc.DrawBitmap(self.bitmap, (w - self.bitmap.GetWidth()) // 2, (h - self.bitmap.GetHeight()) // 2)


# Ktora scenka do ktorej gry (identyfikator gry na serwerze ap-gra)
SCENES = {'ostatnia_zwrotka': NightScene}


def sceneFor(game, frames=None, fps=None):
    """Scenka dla gry: gra z kreatora - jej klatki; Ostatnia zwrotka - ogrod;
    domyslnie zegar z ludzikami (Tajemnica zegara)."""
    if frames:
        try:
            return FramesScene(frames, fps)
        except (IOError, OSError) as e:  # klatki zniknely z dysku - scenka zastepcza
            import logging
            logging.getLogger('gra').error('klatki animacji: %r', e)
    return SCENES.get(game, Scene)()


#=============================================================================
class Scenka(wx.Panel):
    """Panel ze scenka - rusza sie, dopoki nie wywolac stop()."""

    def __init__(self, parent, scene=None):
        wx.Panel.__init__(self, parent, -1)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)  # bez migotania - tlo rysuje onPaint
        self.scene = scene or Scene()
        self.last = time.time()
        self.Bind(wx.EVT_PAINT, self.onPaint)
        self.Bind(wx.EVT_SIZE, self.onSize)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)
        self.timer.Start(FRAME_MS)

    def stop(self):
        self.timer.Stop()

    def onTimer(self, event):
        now = time.time()
        dt = min(now - self.last, 0.2)  # po przestoju nie skacze
        self.last = now
        self.scene.update(dt)
        self.Refresh(False)

    def onSize(self, event):
        self.Refresh(False)
        event.Skip()

    def onPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        w, h = self.GetClientSize()
        if w > 0 and h > 0:
            self.scene.draw(dc, w, h)
