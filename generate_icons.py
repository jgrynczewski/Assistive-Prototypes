#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PIL import Image, ImageDraw
import os

SIZE = 200
OUT = os.path.join(os.path.dirname(__file__), 'icons', 'iot')
os.makedirs(OUT, exist_ok=True)

BG = (255, 255, 255, 0)
FG = (20, 20, 20, 255)
LW = 6


def new_img():
    img = Image.new('RGBA', (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)
    return img, draw


def save(img, name):
    img.save(os.path.join(OUT, name))
    print('  {}'.format(name))


def draw_bulb(draw, cx=100, cy=95, r=52, stem_h=22, base_w=36):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=FG, width=LW)
    bx = cx - base_w // 2
    by = cy + r - 4
    draw.rectangle([bx, by, bx + base_w, by + stem_h], outline=FG, width=LW)
    draw.line([bx, by + stem_h, bx + base_w, by + stem_h], fill=FG, width=LW)
    draw.line([bx + base_w // 3, by + stem_h + 6, bx + 2 * base_w // 3, by + stem_h + 6], fill=FG, width=LW)


def draw_back_arrow(draw):
    pts = [40, 100, 80, 65, 80, 85, 150, 85, 150, 115, 80, 115, 80, 135]
    draw.polygon(pts, fill=FG)


def icon_zarowka():
    img, draw = new_img()
    draw_bulb(draw)
    save(img, 'zarowka.png')


def icon_zasilanie():
    img, draw = new_img()
    cx, cy, r = 100, 95, 52
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=50, end=130, fill=BG, width=0)
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=130, end=410, fill=FG, width=LW)
    gap_pts = [(cx - 8, cy - r - 2), (cx + 8, cy - r - 2), (cx + 8, cy - r + LW + 4), (cx - 8, cy - r + LW + 4)]
    draw.polygon(gap_pts, fill=BG)
    draw.line([cx, cy - r - 8, cx, cy - r + 20], fill=FG, width=LW)
    save(img, 'zasilanie.png')


def icon_jasnosc():
    img, draw = new_img()
    cx, cy, r = 100, 100, 30
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=FG, width=LW)
    for angle in range(0, 360, 45):
        import math
        a = math.radians(angle)
        x1 = int(cx + (r + 10) * math.cos(a))
        y1 = int(cy + (r + 10) * math.sin(a))
        x2 = int(cx + (r + 24) * math.cos(a))
        y2 = int(cy + (r + 24) * math.sin(a))
        draw.line([x1, y1, x2, y2], fill=FG, width=LW)
    save(img, 'jasnosc.png')


def icon_kolor():
    import math
    img, draw = new_img()
    cx, cy = 100, 100
    colors_api = [
        (255, 0,   0,   255),
        (255, 165, 0,   255),
        (255, 255, 0,   255),
        (0,   255, 0,   255),
        (0,   0,   255, 255),
        (128, 0,   128, 255),
        (255, 192, 203, 255),
        (255, 255, 255, 255),
    ]
    r_out, r_in = 75, 35
    for i, color in enumerate(colors_api):
        start = i * 45
        draw.pieslice([cx - r_out, cy - r_out, cx + r_out, cy + r_out],
                      start=start, end=start + 45, fill=color)
    draw.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out],
                 outline=FG, width=LW)
    draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in],
                 fill=(255, 255, 255, 255), outline=FG, width=LW)
    save(img, 'kolor.png')


def icon_temperatura():
    img, draw = new_img()
    cx = 100
    tube_top, tube_bot = 25, 140
    tube_r = 12
    bulb_r = 24
    bulb_cy = tube_bot + bulb_r - 4
    draw.rectangle([cx - tube_r, tube_top, cx + tube_r, tube_bot], outline=FG, width=LW)
    draw.ellipse([cx - bulb_r, bulb_cy - bulb_r, cx + bulb_r, bulb_cy + bulb_r], outline=FG, width=LW)
    draw.rectangle([cx - tube_r + LW, tube_top + 30, cx + tube_r - LW, tube_bot], fill=FG)
    draw.ellipse([cx - bulb_r + LW, bulb_cy - bulb_r + LW, cx + bulb_r - LW, bulb_cy + bulb_r - LW], fill=FG)
    for tick_y in range(tube_top + 20, tube_bot, 20):
        draw.line([cx + tube_r, tick_y, cx + tube_r + 12, tick_y], fill=FG, width=LW - 2)
    save(img, 'temperatura.png')


def icon_efekt():
    img, draw = new_img()
    pts = [100, 15, 115, 75, 160, 55, 105, 110, 150, 185, 90, 125, 40, 145, 85, 95, 45, 20, 85, 75]
    draw.polygon(pts, fill=FG)
    save(img, 'efekt.png')


def icon_jasnosc_level(level, filename):
    img, draw = new_img()
    alpha = int(20 + (level / 100.0) * 235)
    fg = (20, 20, 20, alpha)
    lw = max(3, int(LW * level / 100.0) + 2)
    draw_bulb(draw)
    if level < 100:
        overlay = Image.new('RGBA', (SIZE, SIZE), (255, 255, 255, 255 - alpha))
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)
        draw_bulb(draw)
    label_y = 160
    bar_w = int(140 * level / 100.0)
    draw.rectangle([30, label_y, 170, label_y + 14], outline=(20, 20, 20, 255), width=2)
    draw.rectangle([30, label_y, 30 + bar_w, label_y + 14], fill=(20, 20, 20, 255))
    save(img, filename)


def icon_color_circle(r, g, b, filename, outline_only=False):
    img, draw = new_img()
    cx, cy, radius = 100, 90, 65
    color = (r, g, b, 255)
    if outline_only:
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                     outline=(20, 20, 20, 255), width=LW + 2)
        draw.ellipse([cx - radius + LW + 2, cy - radius + LW + 2,
                      cx + radius - LW - 2, cy + radius - LW - 2],
                     fill=(240, 240, 240, 255))
    else:
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                     fill=color, outline=(20, 20, 20, 255), width=LW)
    bar_h = 10
    bar_y = cy + radius + 14
    draw.rectangle([30, bar_y, 170, bar_y + bar_h], fill=color, outline=(20, 20, 20, 255), width=2)
    save(img, filename)


def icon_temperatura_level(level, filename, color):
    img, draw = new_img()
    cx = 100
    tube_top, tube_bot = 25, 130
    tube_r = 12
    bulb_r = 22
    bulb_cy = tube_bot + bulb_r - 4
    fill_top = tube_top + int((tube_bot - tube_top) * (1 - level))
    draw.rectangle([cx - tube_r, tube_top, cx + tube_r, tube_bot], outline=FG, width=LW)
    draw.ellipse([cx - bulb_r, bulb_cy - bulb_r, cx + bulb_r, bulb_cy + bulb_r], outline=FG, width=LW)
    draw.rectangle([cx - tube_r + LW, fill_top, cx + tube_r - LW, tube_bot], fill=color)
    draw.ellipse([cx - bulb_r + LW, bulb_cy - bulb_r + LW, cx + bulb_r - LW, bulb_cy + bulb_r - LW], fill=color)
    for tick_y in range(tube_top + 20, tube_bot, 20):
        draw.line([cx + tube_r, tick_y, cx + tube_r + 12, tick_y], fill=FG, width=LW - 2)
    save(img, filename)


def icon_efekt_disco():
    import math
    img, draw = new_img()
    cx, cy, r = 100, 85, 45
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(20, 20, 20, 255), outline=FG, width=LW)
    draw.ellipse([cx - r + 12, cy - r + 12, cx + r - 12, cy + r - 12],
                 fill=(180, 180, 180, 255))
    ray_colors = [
        (255, 0,   0,   255),
        (255, 165, 0,   255),
        (255, 255, 0,   255),
        (0,   255, 0,   255),
        (0,   0,   255, 255),
        (128, 0,   128, 255),
        (255, 192, 203, 255),
        (255, 0,   0,   255),
    ]
    angles = [15, 60, 105, 150, 195, 240, 285, 330]
    for angle, color in zip(angles, ray_colors):
        a = math.radians(angle)
        x1 = int(cx + (r + 6) * math.cos(a))
        y1 = int(cy + (r + 6) * math.sin(a))
        x2 = int(cx + (r + 24) * math.cos(a))
        y2 = int(cy + (r + 24) * math.sin(a))
        draw.line([x1, y1, x2, y2], fill=color, width=5)
    note_pts = [68, 148, 68, 168, 60, 170, 60, 150]
    draw.polygon(note_pts, fill=FG)
    draw.line([(68, 148), (88, 143), (88, 163), (68, 168)], fill=FG, width=3)
    save(img, 'efekt_disco.png')


def icon_efekt_puls():
    img, draw = new_img()
    pts = [(20, 100), (55, 100), (70, 40), (85, 160), (100, 70), (115, 130), (130, 100), (180, 100)]
    pulse_colors = [
        (220, 30,  30,  255),
        (255, 80,  30,  255),
        (255, 140, 0,   255),
        (220, 30,  30,  255),
        (180, 0,   0,   255),
        (220, 30,  30,  255),
        (255, 80,  30,  255),
    ]
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=pulse_colors[i], width=LW + 1)
    save(img, 'efekt_puls.png')


def icon_efekt_stroboskop():
    img, draw = new_img()
    pts = [100, 10, 118, 78, 175, 65, 128, 108, 155, 175, 100, 138, 45, 175, 72, 108, 25, 65, 82, 78]
    draw.polygon(pts, fill=FG)
    save(img, 'efekt_stroboskop.png')


def icon_efekt_tecza():
    img, draw = new_img()
    cx, base_y = 100, 160
    colors = [(220, 30, 30, 255), (255, 140, 0, 255), (220, 220, 0, 255),
              (30, 180, 30, 255), (30, 130, 220, 255), (120, 30, 200, 255)]
    for i, color in enumerate(colors):
        r = 80 - i * 10
        draw.arc([cx - r, base_y - r, cx + r, base_y + r],
                 start=180, end=360, fill=color, width=8)
    save(img, 'efekt_tecza.png')


def icon_efekt_policja():
    img, draw = new_img()
    draw.rectangle([25, 30, 95, 105], fill=(220, 30, 30, 255), outline=FG, width=LW)
    draw.rectangle([105, 30, 175, 105], fill=(30, 60, 220, 255), outline=FG, width=LW)
    draw.rectangle([55, 110, 145, 175], fill=(20, 20, 20, 255), outline=FG, width=LW)
    draw.line([60, 67, 90, 67], fill=(255, 255, 255, 255), width=8)
    draw.line([75, 52, 75, 82], fill=(255, 255, 255, 255), width=8)
    draw.line([110, 52, 140, 82], fill=(255, 255, 255, 255), width=6)
    draw.line([140, 52, 110, 82], fill=(255, 255, 255, 255), width=6)
    save(img, 'efekt_policja.png')


def icon_efekt_ocean():
    import math
    img, draw = new_img()
    ocean_colors = [
        (0,   80,  200, 255),
        (0,   120, 220, 255),
        (30,  160, 230, 255),
        (80,  190, 240, 255),
    ]
    for i, y_off in enumerate(range(40, 160, 30)):
        amp = 18 - i * 2
        pts = []
        for x in range(10, 191, 4):
            y = y_off + int(amp * math.sin((x + i * 20) * 0.08))
            pts.append((x, y))
        for j in range(len(pts) - 1):
            draw.line([pts[j], pts[j + 1]], fill=ocean_colors[i], width=LW - 1)
    save(img, 'efekt_ocean.png')


def icon_efekt_stop():
    img, draw = new_img()
    draw.rectangle([35, 35, 165, 165], fill=FG, outline=FG, width=LW)
    save(img, 'efekt_stop.png')


def icon_reset():
    import math
    img, draw = new_img()
    cx, cy, r_out, r_in = 100, 100, 65, 42
    draw.arc([cx - r_out, cy - r_out, cx + r_out, cy + r_out], start=50, end=310, fill=FG, width=LW + 2)
    angle = math.radians(50)
    ax = int(cx + r_out * math.cos(angle))
    ay = int(cy + r_out * math.sin(angle))
    arrow_pts = [
        (ax, ay),
        (ax - 20, ay - 12),
        (ax - 8, ay + 4),
        (ax - 22, ay + 16),
        (ax + 2, ay + 22),
        (ax + 14, ay + 6),
    ]
    draw.polygon(arrow_pts, fill=FG)
    save(img, 'reset.png')


print('Generowanie ikon IoT...')

icon_zarowka()
icon_zasilanie()
icon_jasnosc()
icon_kolor()
icon_temperatura()
icon_efekt()

icon_jasnosc_level(25, 'jasnosc_25.png')
icon_jasnosc_level(50, 'jasnosc_50.png')
icon_jasnosc_level(75, 'jasnosc_75.png')
icon_jasnosc_level(100, 'jasnosc_100.png')

icon_color_circle(30,  80, 220, 'kolor_niebieski.png')
icon_color_circle(30, 180,  60, 'kolor_zielony.png')
icon_color_circle(255, 140,  0, 'kolor_pomaranczowy.png')
icon_color_circle(255,  80, 160, 'kolor_rozowy.png')
icon_color_circle(140,  30, 200, 'kolor_fioletowy.png')
icon_color_circle(220,  30,  30, 'kolor_czerwony.png')
icon_color_circle(240, 240, 240, 'kolor_bialy.png', outline_only=True)
icon_color_circle(240, 210,   0, 'kolor_zolty.png')

icon_temperatura_level(0.9, 'temp_ciepla.png',    (220, 80, 30, 255))
icon_temperatura_level(0.5, 'temp_neutralna.png',  (80, 160, 80, 255))
icon_temperatura_level(0.2, 'temp_zimna.png',      (60, 120, 220, 255))

icon_efekt_disco()
icon_efekt_puls()
icon_efekt_stroboskop()
icon_efekt_tecza()
icon_efekt_policja()
icon_efekt_ocean()
icon_efekt_stop()
icon_reset()

print('\nGotowe! Ikony zapisane w icons/iot/')