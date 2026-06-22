#!/usr/bin/env python3
"""
LFC VBS 2026 "Deliverance" — full-page flyer, drawn PDF-first.

Print-first, image-forward: white paper, a large un-ghosted hero illustration
with the title set into its sky, a tight essentials line, and an open (un-boxed)
registration row with a vector QR. No HTML / browser in the pipeline.

Run:  /tmp/pdfenv/bin/python flyer.py   ->  site/flyer.pdf  (1 page, 8.5x11)
"""

import os
import qrcode
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

# --------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(ROOT, "assets", "fonts")
HERO_SRC = os.path.join(ROOT, "site", "assets", "hero-redsea.png")
OUT = os.path.join(ROOT, "site", "flyer.pdf")
TMP = "/tmp/_flyer_build"
os.makedirs(TMP, exist_ok=True)

# Units & geometry --------------------------------------------------------
IN = 72.0
PAGE_W, PAGE_H = 8.5 * IN, 11.0 * IN
MARGIN = 0.42                 # outer safe margin (in)
CL = MARGIN                   # content left
CR = 8.5 - MARGIN             # content right
CW = CR - CL                  # content width

def X(in_): return in_ * IN
def Y(top_in): return PAGE_H - top_in * IN

# Palette -----------------------------------------------------------------
WHITE   = HexColor("#FFFFFF")
INK_900 = HexColor("#1F1208")
INK_800 = HexColor("#2A1A0F")
INK_700 = HexColor("#3A2718")
INK_600 = HexColor("#5C4633")
INK_500 = HexColor("#7A6650")
CRIMSON = HexColor("#8B1A1A")
CRIMSON8= HexColor("#6B1414")
GOLD    = HexColor("#C5961A")
GOLD_5  = HexColor("#D4A937")
CREAM   = HexColor("#FBF5E3")

def rgba(hexcol, a):
    c = HexColor(hexcol); return Color(c.red, c.green, c.blue, alpha=a)

# Fonts -------------------------------------------------------------------
for name, fn in {
    "Fr": "Fraunces-600.ttf", "Fr5": "Fraunces-500.ttf",
    "Fr9": "Fraunces-900.ttf", "Fri": "Fraunces-400-italic.ttf",
    "Lora": "Lora-400.ttf", "Lora5": "Lora-500.ttf", "Lorai": "Lora-400-italic.ttf",
}.items():
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, fn)))

# Helpers -----------------------------------------------------------------
def tracked_width(c, font, size, text, tracking):
    return c.stringWidth(text, font, size) + tracking * max(0, len(text) - 1)

def _draw_tracked(c, x, baseline, font, size, text, tracking):
    c.setFont(font, size)
    for ch in text:
        c.drawString(x, baseline, ch)
        x += c.stringWidth(ch, font, size) + tracking

def draw_tracked_centre(c, cx, baseline, font, size, text, tracking, color):
    c.setFillColor(color)
    _draw_tracked(c, cx - tracked_width(c, font, size, text, tracking) / 2.0,
                  baseline, font, size, text, tracking)

def draw_tracked_left(c, x, baseline, font, size, text, tracking, color):
    c.setFillColor(color); _draw_tracked(c, x, baseline, font, size, text, tracking)

def hairline_grad(c, x0, x1, y, color, width=0.8, segments=40, fade="both"):
    seg = (x1 - x0) / segments
    c.setLineWidth(width)
    for i in range(segments):
        t = (i + 0.5) / segments
        a = (1 - abs(2 * t - 1)) if fade == "both" else (t if fade == "right" else 1 - t)
        c.setStrokeColor(Color(color.red, color.green, color.blue, alpha=min(1, a * 1.1)))
        xa = x0 + i * seg
        c.line(xa, y, xa + seg, y)

# Asset prep --------------------------------------------------------------
def build_hero(target_w_in, target_h_in, focus_y=0.46, focus_x=0.5):
    img = Image.open(HERO_SRC).convert("RGB")
    iw, ih = img.size
    target = target_w_in / target_h_in
    if (iw / ih) > target:               # source wider -> crop width
        new_w = int(round(ih * target))
        x0 = int(round((iw - new_w) * focus_x))
        box = (x0, 0, x0 + new_w, ih)
    else:                                # source taller -> crop height
        new_h = int(round(iw / target))
        y0 = int(round((ih - new_h) * focus_y))
        box = (0, y0, iw, y0 + new_h)
    path = os.path.join(TMP, "hero_crop.png")
    img.crop(box).save(path)
    return path

def build_qr(data):
    qr = qrcode.QRCode(border=0, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(data); qr.make(fit=True)
    return qr.get_matrix()

# Compose -----------------------------------------------------------------
def main():
    c = canvas.Canvas(OUT, pagesize=(PAGE_W, PAGE_H))
    c.setTitle("Deliverance — LFC VBS 2026 · Flyer")

    # white paper
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    cx = 4.25

    # =================================================== TITLE (above image)
    draw_tracked_centre(c, X(cx), Y(0.80), "Fr", 11.5,
                        "LITTLE FARMS CHAPEL · VBS 2026", 2.6, CRIMSON8)
    title, tsize = "Deliverance", 62
    c.setFillColor(INK_900); c.setFont("Fr", tsize)
    c.drawCentredString(X(cx), Y(1.50), title)
    # gold rule flanking an italic tagline
    tag = "A journey through Exodus"
    c.setFont("Fri", 12.5)
    tagw = c.stringWidth(tag, "Fri", 12.5)
    ry = Y(1.82); gap = tagw / 2 + 11
    hairline_grad(c, X(cx) - 1.8 * IN, X(cx) - gap, ry + 4, GOLD, 1.0, 26, "right")
    hairline_grad(c, X(cx) + gap, X(cx) + 1.8 * IN, ry + 4, GOLD, 1.0, 26, "left")
    c.setFillColor(INK_800)
    c.drawCentredString(X(cx), ry, tag)

    # =================================================== HERO (clean, large)
    hero_top = 2.06
    hero_h = 4.92
    hero_path = build_hero(CW, hero_h, focus_y=0.50)
    c.drawImage(ImageReader(hero_path), X(CL), Y(hero_top + hero_h),
                width=X(CW), height=hero_h * IN, mask='auto')
    c.setStrokeColor(rgba("#2A1A0F", 0.22)); c.setLineWidth(0.6)
    c.rect(X(CL), Y(hero_top + hero_h), X(CW), hero_h * IN, stroke=1, fill=0)

    # =================================================== LOWER BLOCK
    # one rule anchors the essentials + registration together
    c.setStrokeColor(rgba("#2A1A0F", 0.28)); c.setLineWidth(0.9)
    top_rule = 7.30
    c.line(X(CL), Y(top_rule), X(CR), Y(top_rule))

    # --- essentials row ---
    e_top = top_rule + 0.06
    ess = [("WHEN", ["July 21 – 23", "6:00 – 8:00 PM"]),
           ("WHERE", ["Little Farms Chapel", "Coopersville, MI"]),
           ("WHO", ["Age 3 –", "6th Grade"]),
           ("COST", ["Free", "All welcome"])]
    col_w = CW / 4.0
    for i, (lbl, vals) in enumerate(ess):
        ccx = CL + i * col_w + col_w / 2
        if i > 0:
            c.setStrokeColor(rgba("#2A1A0F", 0.16)); c.setLineWidth(0.5)
            c.line(X(CL + i * col_w), Y(e_top + 0.10), X(CL + i * col_w), Y(e_top + 0.66))
        draw_tracked_centre(c, X(ccx), Y(e_top + 0.22), "Fr", 7.5, lbl, 2.0, CRIMSON)
        c.setFillColor(INK_900); c.setFont("Fr5", 11.5)
        c.drawCentredString(X(ccx), Y(e_top + 0.45), vals[0])
        c.drawCentredString(X(ccx), Y(e_top + 0.635), vals[1])

    # --- registration (QR is the print call-to-action; no web button) ---
    matrix = build_qr("https://vbs.lfcopc.org")
    n = len(matrix)
    qr_side = 1.34
    qbx = CR - qr_side
    qr_top = 8.50
    mod = (qr_side * IN) / n
    ox = X(qbx); oy = Y(qr_top + qr_side)
    c.setFillColor(INK_900)
    for r, row in enumerate(matrix):
        for col, v in enumerate(row):
            if v:
                c.rect(ox + col * mod, oy + (n - 1 - r) * mod, mod + 0.3, mod + 0.3, stroke=0, fill=1)
    c.setStrokeColor(rgba("#2A1A0F", 0.30)); c.setLineWidth(0.6)
    pad = 0.06
    c.rect(X(qbx - pad), Y(qr_top + qr_side + pad), X(qr_side + 2 * pad), (qr_side + 2 * pad) * IN, stroke=1, fill=0)
    draw_tracked_centre(c, X(qbx + qr_side / 2), Y(qr_top - 0.15), "Fr", 7, "SCAN TO REGISTER", 1.8, CRIMSON)
    c.setFillColor(INK_700); c.setFont("Fr5", 9)
    c.drawCentredString(X(qbx + qr_side / 2), Y(qr_top + qr_side + 0.27), "vbs.lfcopc.org")

    tx = CL
    draw_tracked_left(c, X(tx), Y(8.46), "Fr", 9, "REGISTRATION · IT’S FREE", 2.2, CRIMSON)
    c.setFillColor(INK_900); c.setFont("Fr", 26)
    c.drawString(X(tx), Y(8.88), "Register your kids.")
    c.setFillColor(INK_600); c.setFont("Lora", 10.5)
    c.drawString(X(tx), Y(9.23), "Three evenings — Tuesday, Wednesday & Thursday, July 21–23,")
    c.drawString(X(tx), Y(9.44), "from 6 to 8 PM. Free for kids age 3 through 6th grade.")
    c.setFillColor(INK_800); c.setFont("Fr5", 10.5)
    c.drawString(X(tx), Y(9.74), "Scan the code to sign up — it only takes a minute.")

    # =================================================== FOOTER
    f_rule = 10.30
    c.setStrokeColor(rgba("#2A1A0F", 0.2)); c.setLineWidth(0.6)
    c.line(X(CL), Y(f_rule), X(CR), Y(f_rule))
    fb = 10.54
    c.setFillColor(INK_900); c.setFont("Fr", 9.5)
    c.drawString(X(CL), Y(fb), "Little Farms Chapel OPC")
    c.setFillColor(INK_600); c.setFont("Lora", 8.5)
    c.drawCentredString(X(4.25), Y(fb), "2518 Arthur Street · Coopersville, MI 49404")
    c.drawRightString(X(CR), Y(fb), "616.677.6170 · office@lfcopc.org")

    c.showPage(); c.save()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
