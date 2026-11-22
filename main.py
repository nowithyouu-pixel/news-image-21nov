#!/usr/bin/env python3
"""World news of Saturday 21 November 2026, summed up in one image.

A pure-stdlib Python program (no third-party packages, no network): it
draws a one-page newspaper front page -- masthead, lead story and six
further stories from 21 November 2026 -- onto a 1024x1024 canvas with a
small built-in 5x7 bitmap font, and writes it as a PNG to
$MAKEFUN_OUTPUT_DIR/entry.png (or /output/entry.png).

The run is fully deterministic: the same bytes come out every time.

Run locally:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 232)   # warm newsprint
INK = (20, 20, 20)        # near-black text
NAVY = (15, 42, 74)       # masthead band
NAVY_LT = (28, 68, 110)
RED = (179, 39, 30)       # lead accent
GOLD = (201, 162, 39)
WHITE = (255, 255, 255)
GREY = (90, 88, 80)
LINE = (190, 184, 168)
TEAL = (14, 110, 105)
MAROON = (122, 28, 48)
GREEN = (46, 110, 44)
SLATE = (70, 84, 102)
BROWN = (120, 72, 32)

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph is 7 rows of 5 bits, most significant bit on the left.
# Only capitals, digits and common punctuation: all copy is set in caps.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ",": (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    "-": (0, 0, 0, 0x1F, 0, 0, 0),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0, 0x04),
    "%": (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "+": (0, 0x04, 0x04, 0x0E, 0x04, 0x04, 0),
    "=": (0, 0, 0x1F, 0, 0x1F, 0, 0),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    ";": (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08),
    '"': (0x0A, 0x0A, 0x0A, 0, 0, 0, 0),
    "*": (0, 0x04, 0x15, 0x0E, 0x15, 0x04, 0),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "<": (0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02),
    ">": (0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08),
    "#": (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
    "_": (0, 0, 0, 0, 0, 0, 0x1F),
}


def glyph(ch):
    """Return the 7-row bitmap for a character, upper-cased, or blank."""
    return FONT.get(ch.upper(), FONT["?"])


# ------------------------------------------------------------------ canvas
class Canvas:
    """An RGB canvas backed by one bytearray per row (fast slice fills)."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        row = bytes(bg) * w
        self.px = [bytearray(row) for _ in range(h)]

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        fill = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            self.px[yy][x0 * 3:x1 * 3] = fill

    def hline(self, x, y, w, color, t=1):
        self.rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.rect(x, y, t, h, color)

    def frame(self, x, y, w, h, color, t=2):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def disc(self, cx, cy, r, color):
        """Filled circle by scanlines."""
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.rect(cx - dx, cy + dy, dx * 2 + 1, 1, color)

    def ring(self, cx, cy, r, color, t=3):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            inner = int(max(0, (r - t) * (r - t) - dy * dy) ** 0.5) \
                if abs(dy) < r - t else 0
            self.rect(cx - dx, cy + dy, dx - inner, 1, color)
            self.rect(cx + inner + 1, cy + dy, dx - inner, 1, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        """Bresenham line, optionally thickened to t pixels."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            self.rect(x - t // 2, y - t // 2, t, t, color)
            if x == x1 and y == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def tri(self, x0, y0, x1, y1, x2, y2, color):
        """Filled triangle by scanline fill between its edges."""
        pts = sorted(((x0, y0), (x1, y1), (x2, y2)), key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        for y in range(ay, cy + 1):
            xs = []
            for (px0, py0), (px1, py1) in (((ax, ay), (bx, by)),
                                           ((bx, by), (cx, cy)),
                                           ((ax, ay), (cx, cy))):
                if py0 <= y <= py1 and py1 != py0:
                    xs.append(px0 + (px1 - px0) * (y - py0) / (py1 - py0))
                elif y == py0 == py1:
                    xs.extend((px0, px1))
            if len(xs) >= 2:
                xa, xb = int(min(xs)), int(max(xs))
                self.rect(xa, y, xb - xa + 1, 1, color)

    # ------------------------------------------------------------ text
    def text(self, x, y, s, color, scale=2):
        """Draw upper-cased text; returns the x just past the last glyph."""
        cx = x
        for ch in s:
            rows = glyph(ch)
            for ry in range(7):
                bits = rows[ry]
                if not bits:
                    continue
                yy = y + ry * scale
                for bx in range(5):
                    if bits & (0x10 >> bx):
                        self.rect(cx + bx * scale, yy, scale, scale, color)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale=2):
        return len(s) * 6 * scale - scale

    def text_center(self, cx, y, s, color, scale=2):
        self.text(cx - self.text_w(s, scale) // 2, y, s, color, scale)

    def wrap(self, s, max_w, scale=2):
        """Greedy word wrap; returns a list of lines fitting max_w pixels."""
        lines, cur = [], ""
        for word in s.split(" "):
            trial = (cur + " " + word).strip()
            if self.text_w(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, s, color, max_w, scale=2, leading=4, max_lines=None):
        lines = self.wrap(s, max_w, scale)
        if max_lines is not None:
            lines = lines[:max_lines]
        for i, ln in enumerate(lines):
            self.text(x, y + i * (7 * scale + leading), ln, color, scale)
        return y + len(lines) * (7 * scale + leading)


# ------------------------------------------------------------- PNG writer
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_png(path, canvas):
    raw = bytearray()
    for row in canvas.px:
        raw.append(0)  # filter: none
        raw += row
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


# ------------------------------------------------------------ pictograms
# Small flat icons drawn from primitives, one per story, in a square box.

def icon_explosion(cv, x, y, s, c1, c2):
    """Blast starburst: triangles radiating from a bright core."""
    cx, cy = x + s // 2, y + s // 2
    for k in range(8):
        ang = k * 3.14159 / 4
        ex, ey = int(cx + (s * 0.52) * _cos(ang)), int(cy + (s * 0.52) * _sin(ang))
        px, py = int(cx + (s * 0.16) * _cos(ang + 0.5)), int(cy + (s * 0.16) * _sin(ang + 0.5))
        qx, qy = int(cx + (s * 0.16) * _cos(ang - 0.5)), int(cy + (s * 0.16) * _sin(ang - 0.5))
        cv.tri(ex, ey, px, py, qx, qy, c1)
    cv.disc(cx, cy, s // 5, c2)


def _cos(a):
    return math.cos(a)


def _sin(a):
    return math.sin(a)


def icon_globe(cv, x, y, s, c1, c2):
    cx, cy = x + s // 2, y + s // 2
    r = s // 2 - 2
    cv.disc(cx, cy, r, c1)
    cv.ring(cx, cy, r, c2, 3)
    cv.hline(cx - r, cy, 2 * r, c2, 3)
    cv.vline(cx, cy - r, 2 * r, c2, 3)
    cv.line(cx - r + 4, cy - r + 8, cx + r - 4, cy + r - 8, c2, 3)
    cv.line(cx - r + 4, cy + r - 8, cx + r - 4, cy - r + 8, c2, 3)


def icon_scales(cv, x, y, s, c1, c2):
    cx, cy = x + s // 2, y + s // 2
    cv.vline(cx, y + s // 8, s * 3 // 4, c1, 4)
    cv.hline(cx - s // 3, y + s // 8, s * 2 // 3, c1, 4)
    cv.disc(cx, y + s // 8, s // 12, c2)
    cv.disc(cx, y + s * 7 // 8, s // 10, c1)
    for sx in (cx - s // 3, cx + s // 3):
        cv.line(sx, y + s // 8, sx, y + s // 2, c1, 3)
        cv.tri(sx - s // 7, y + s // 2, sx + s // 7, y + s // 2,
               sx, y + s * 5 // 8, c2)
        cv.hline(sx - s // 7, y + s // 2, s * 2 // 7, c2, 3)


def icon_leaf(cv, x, y, s, c1, c2):
    cx, cy = x + s // 2, y + s // 2
    cv.disc(cx, cy, s // 3, c1)
    cv.line(cx - s // 4, cy + s // 4, cx + s // 4, cy - s // 4, PAPER, 4)
    cv.line(cx + s // 4, cy + s // 4, cx + s // 2, cy + s // 2, c1, 4)


def icon_chart(cv, x, y, s, c1, c2):
    base = y + s * 3 // 4
    bw = s // 6
    heights = (s // 4, s // 2, s * 5 // 12, s // 6)
    for i, hh in enumerate(heights):
        cv.rect(x + 4 + i * (bw + 4), base - hh, bw, hh, c1)
    cv.line(x + 2, y + s // 6, x + s - 4, y + s // 2, c2, 5)
    cv.tri(x + s - 4, y + s // 2, x + s - 14, y + s // 2 - 8,
           x + s - 14, y + s // 2 + 8, c2)


def icon_badge(cv, x, y, s, c1, c2):
    cx, cy = x + s // 2, y + s // 2
    cv.disc(cx, cy, s // 3, c1)
    cv.ring(cx, cy, s // 3, c2, 3)
    cv.line(cx - s // 6, cy, cx - s // 18, cy + s // 6, WHITE, 5)
    cv.line(cx - s // 18, cy + s // 6, cx + s // 5, cy - s // 6, WHITE, 5)


def icon_rocket(cv, x, y, s, c1, c2):
    cx = x + s // 2
    cv.tri(cx, y + 2, cx - s // 6, y + s // 2, cx + s // 6, y + s // 2, c1)
    cv.rect(cx - s // 6, y + s // 2, s // 3, s // 4, c1)
    cv.tri(cx - s // 6, y + s // 2, cx - s // 3, y + s * 3 // 4,
           cx - s // 6, y + s * 3 // 4, c2)
    cv.tri(cx + s // 6, y + s // 2, cx + s // 3, y + s * 3 // 4,
           cx + s // 6, y + s * 3 // 4, c2)
    cv.tri(cx, y + s, cx - s // 8, y + s * 3 // 4, cx + s // 8, y + s * 3 // 4, GOLD)


ICONS = {
    "explosion": icon_explosion,
    "globe": icon_globe,
    "scales": icon_scales,
    "leaf": icon_leaf,
    "chart": icon_chart,
    "badge": icon_badge,
    "rocket": icon_rocket,
}

# ------------------------------------------------------------- the stories
# Researched from the day's reporting (21 Nov 2026). Wording is the
# program's own summary; figures are the numbers the wires reported.
LEAD = {
    "kicker": "LEAD STORY  -  THE GULF ON THE BRINK",
    "headline": "IRAN SAYS IT HIT TWO US BASES IN BAHRAIN",
    "body": "TEHRAN SAID ITS FORCES STRUCK US POSITIONS AT AL-RIFFA AND "
            "AWALI. BAHRAIN SAID THE BLAST HIT A CIVILIAN PLANT, STARTED "
            "A FIRE AND HURT NO ONE. OIL SHIPMENTS THROUGH HORMUZ FELL 15%.",
    "icon": "explosion",
    "accent": RED,
}

STORIES = [
    {
        "kicker": "UKRAINE  -  WAR IN EUROPE",
        "headline": "RUSSIA'S RECORD BARRAGE SPILLS INTO POLAND",
        "body": "404 DRONES AND 111 MISSILES HIT UKRAINE OVERNIGHT, KILLING "
                "AT LEAST 8. TWO CAME DOWN IN POLAND.",
        "icon": "rocket",
        "accent": MAROON,
    },
    {
        "kicker": "DIPLOMACY  -  SHENZHEN",
        "headline": "TRUMP, XI AND PUTIN MEET IN SHENZHEN",
        "body": "THREE LEADERS HELD A FIRST SUMMIT IN CHINA AND ISSUED A "
                "JOINT PEACE DECLARATION. KYIV SAID IT FAILED RUSSIA.",
        "icon": "globe",
        "accent": NAVY_LT,
    },
    {
        "kicker": "JUSTICE  -  THE HAGUE",
        "headline": "WORLD COURT: MYANMAR COMMITTED GENOCIDE",
        "body": "IN A LANDMARK 9-6 RULING, THE COURT FOUND MYANMAR GUILTY "
                "OF ROHINGYA GENOCIDE.",
        "icon": "scales",
        "accent": TEAL,
    },
    {
        "kicker": "CLIMATE  -  ANTALYA",
        "headline": "COP31 RUNS PAST DEADLINE AS FOSSIL PLEDGE DROPS",
        "body": "TALKS IN TURKEY WENT INTO OVERTIME WITH NO DEAL. THE DRAFT "
                "CUT THE FOSSIL-FUEL PLEDGE; 1.5C WILL BE OVERSHOT.",
        "icon": "leaf",
        "accent": GREEN,
    },
    {
        "kicker": "MARKETS  -  NEW YORK",
        "headline": "AI SELL-OFF DRAGS US STOCKS INTO CORRECTION",
        "body": "SHARES FELL SHARPLY AS THE AI AND CHIP ROUT DEEPENED. "
                "CHINESE TECH HAS LOST ABOUT $1.7 TRILLION SINCE JUNE.",
        "icon": "chart",
        "accent": SLATE,
    },
    {
        "kicker": "MEXICO  -  CARTELS",
        "headline": "MOST-WANTED CARTEL BOSS CAPTURED IN SINALOA",
        "body": "SPECIAL FORCES SEIZED CHAPO ISIDRO, ON THE FBI'S "
                "MOST-WANTED LIST. THE VIOLENCE THAT FOLLOWED LEFT 11 DEAD.",
        "icon": "badge",
        "accent": BROWN,
    },
]

TICKER = ("ALSO: PERU QUAKE 6.7  *  HOUTHIS HIT RIYADH  *  "
          "EU GIVES UKRAINE 7.9 BN EURO")


# ----------------------------------------------------------------- layout
def draw_masthead(cv):
    cv.rect(0, 0, W, 132, NAVY)
    cv.rect(0, 132, W, 4, GOLD)
    cv.text_center(W // 2, 18, "THE WORLD IN ONE PAGE", WHITE, 6)
    cv.text_center(W // 2, 76, "SATURDAY  -  21 NOVEMBER 2026", GOLD, 3)
    cv.text_center(W // 2, 104, "THE DAY'S WORLD NEWS, IN ONE IMAGE", WHITE, 2)


def draw_lead(cv, x, y, w, h):
    cv.frame(x, y, w, h, INK, 3)
    cv.rect(x + 3, y + 3, w - 6, 34, RED)
    cv.text(x + 16, y + 12, LEAD["kicker"], WHITE, 2)
    icon = ICONS[LEAD["icon"]]
    box = 148
    ix, iy = x + w - box - 18, y + 52
    cv.rect(ix - 6, iy - 6, box + 12, box + 12, PAPER)
    cv.frame(ix - 6, iy - 6, box + 12, box + 12, LINE, 2)
    icon(cv, ix, iy, box, LEAD["accent"], GOLD)
    tx = x + 16
    tw = w - box - 16 - 32
    lines = cv.wrap(LEAD["headline"], tw, 4)
    yy = y + 52
    for ln in lines[:2]:
        cv.text(tx, yy, ln, INK, 4)
        yy += 7 * 4 + 8
    cv.hline(tx, yy + 2, tw, RED, 4)
    cv.para(tx, yy + 14, LEAD["body"], INK, tw, 2, 5, max_lines=3)


def draw_story(cv, x, y, w, h, story):
    cv.frame(x, y, w, h, INK, 2)
    cv.rect(x + 2, y + 2, w - 4, 26, story["accent"])
    cv.text(x + 12, y + 9, story["kicker"], WHITE, 2)
    lines = cv.wrap(story["headline"], w - 24, 3)
    yy = y + 36
    for ln in lines[:2]:
        cv.text(x + 12, yy, ln, INK, 3)
        yy += 7 * 3 + 5
    icon = ICONS[story["icon"]]
    box = 84
    ix, iy = x + w - box - 12, y + 96
    icon(cv, ix, iy, box, story["accent"], GOLD)
    cv.para(x + 12, y + 98, story["body"], INK, w - box - 36, 2, 4,
            max_lines=4)


def draw_footer(cv, y):
    cv.rect(0, y, W, 52, NAVY)
    cv.text_center(W // 2, y + 10, TICKER, GOLD, 2)
    cv.text_center(W // 2, y + 30, "21 NOVEMBER 2026  -  DRAWN FROM THE DAY'S REPORTING",
                   WHITE, 2)


def build():
    cv = Canvas(W, H, PAPER)
    cv.rect(0, 0, W, H, PAPER)
    draw_masthead(cv)
    draw_lead(cv, 24, 148, W - 48, 216)
    gx, gy = 24, 376
    cw, chh = (W - 48 - 16) // 2, 188
    for i, story in enumerate(STORIES):
        cx = gx + (i % 2) * (cw + 16)
        cy = gy + (i // 2) * (chh + 12)
        draw_story(cv, cx, cy, cw, chh, story)
    draw_footer(cv, 972)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(path, build())
    print(f"wrote {path} ({size} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
