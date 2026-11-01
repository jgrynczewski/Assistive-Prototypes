#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""Scenka na ekranie gry: szkolny zegar z wahadlem i ludziki, ktore sie
kreca - chodza, staja, czasem podchodza do siebie i "rozmawiaja".

Nic z fabuly nie zalezy od scenki - to tylko zywy podglad, zeby na ekranie
cos sie dzialo. Rysowane prostymi ksztaltami (bez plikow graficznych).

Scene - logika i rysowanie na dowolnym DC (bez okna; da sie wyrenderowac
podglad poza AP). Scenka - panel wx z zegarem (timer), uzywany w modules/gra.py.
"""

from __future__ import division

import math
import random
import time

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
class Scenka(wx.Panel):
    """Panel ze scenka - rusza sie, dopoki nie wywolac stop()."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)  # bez migotania - tlo rysuje onPaint
        self.scene = Scene()
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
