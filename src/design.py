# -*- coding: utf-8 -*-
"""投稿画像の共通デザイン（運用キットの画像と同じ見た目）。"""
import os
from PIL import Image, ImageDraw, ImageFont
HANDLE = "@kaumae_memo"
ACCOUNT = "かうまえメモ"

FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"
OUT = os.path.join(os.path.dirname(__file__), "..", "images")

BG = (242, 244, 241)
INK = (30, 42, 44)
TEAL = (31, 111, 104)
TEAL_SOFT = (214, 231, 227)
MUSTARD = (226, 164, 59)
MUTED = (107, 119, 116)
WHITE = (255, 255, 255)
LINE = (205, 213, 210)


_fc = {}


def f(size):
    if size not in _fc:
        _fc[size] = ImageFont.truetype(FONT, size)
    return _fc[size]


def text(d, xy, s, size, fill=INK, bold=False, anchor="la"):
    d.text(xy, s, font=f(size), fill=fill, anchor=anchor,
           stroke_width=(2 if size >= 56 else 1) if bold else 0, stroke_fill=fill)


def wrap(s, size, width):
    """幅に収まるよう1文字ずつ折り返す（日本語向け）。"""
    out, cur = [], ""
    for ch in s:
        if f(size).getlength(cur + ch) > width:
            out.append(cur)
            cur = ch
        else:
            cur += ch
    out.append(cur)
    return out


def para(d, x, y, lines, size, width, fill=INK, bold=False, gap=1.5):
    for ln in lines:
        if ln == "":
            y += int(size * 0.7)
            continue
        for w in wrap(ln, size, width):
            text(d, (x, y), w, size, fill, bold)
            y += int(size * gap)
    return y


def frame(W, H, idx=None, total=None):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # PR表記（ファーストビュー上部）
    label = "PR｜楽天アフィリエイト広告を含みます"
    tw = f(30).getlength(label)
    d.rounded_rectangle((72, 64, 72 + tw + 48, 64 + 56), radius=28, fill=WHITE, outline=LINE, width=2)
    text(d, (96, 92), label, 30, INK, anchor="lm")
    if idx is not None:
        text(d, (W - 72, 92), f"{idx}/{total}", 30, MUTED, anchor="rm")
    text(d, (72, H - 72), HANDLE, 30, MUTED, anchor="ls")
    text(d, (W - 72, H - 72), ACCOUNT, 30, TEAL, bold=True, anchor="rs")
    return im, d


def check_icon(d, cx, cy, r, color=TEAL, bg=WHITE):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    w = max(6, r // 6)
    d.line([(cx - r * 0.45, cy + r * 0.02), (cx - r * 0.1, cy + r * 0.38), (cx + r * 0.5, cy - r * 0.35)],
           fill=bg, width=w, joint="curve")


def pill(d, x, y, s, size=34, fg=WHITE, bgc=TEAL):
    tw = f(size).getlength(s)
    d.rounded_rectangle((x, y, x + tw + 44, y + size + 30), radius=(size + 30) // 2, fill=bgc)
    text(d, (x + 22, y + (size + 30) // 2), s, size, fg, bold=True, anchor="lm")
    return y + size + 30


def slide_cover(s, im, d, W, H):
    y = 260
    text(d, (88, y), s["kicker"], 40, TEAL, bold=True)
    y += 110
    size = 104
    lines = [w for ln in s["title"].split("\n") for w in wrap(ln, size, W - 176)]
    if len(lines) > 3:
        size = 80
        lines = [w for ln in s["title"].split("\n") for w in wrap(ln, size, W - 176)]
    for ln in lines:
        text(d, (84, y), ln, size, INK, bold=True)
        y += int(size * 1.35)
    d.rectangle((88, y + 10, 88 + 220, y + 26), fill=MUSTARD)
    y += 80
    text(d, (88, y), s["sub"], 46, INK)
    check_icon(d, W - 230, H - 300, 120)
    text(d, (88, H - 190), "保存して、買う前に見返す", 34, MUTED)


def slide_point(s, im, d, W, H):
    y = pill(d, 88, 210, s["label"])
    y += 60
    for w in wrap(s["head"], 64, W - 176):
        text(d, (88, y), w, 64, INK, bold=True)
        y += 90
    y += 30
    tmp = ImageDraw.Draw(Image.new("RGB", (W, H)))
    end = para(tmp, 120, y + 60, s["body"], 46, W - 240)
    d.rounded_rectangle((72, y, W - 72, min(end + 40, H - 220)), radius=32, fill=WHITE)
    para(d, 120, y + 60, s["body"], 46, W - 240)
    if s.get("note"):
        text(d, (88, H - 170), "※" + s["note"], 28, MUTED)


def slide_table(s, im, d, W, H):
    y = pill(d, 88, 210, s["label"])
    y += 60
    for w in wrap(s["head"], 64, W - 176):
        text(d, (88, y), w, 64, INK, bold=True)
        y += 90
    y += 30
    rows = s["rows"]
    ncol = len(rows[0])
    x0, x1 = 72, W - 72
    first = 0.42 if ncol == 2 else 0.4
    if ncol == 2:
        xs = [x0, x0 + (x1 - x0) * first, x1]
    else:
        rest = (1 - first) / (ncol - 1)
        xs = [x0] + [x0 + (x1 - x0) * (first + rest * (i - 1)) for i in range(1, ncol)] + [x1]
    rh = 118 if len(rows) <= 4 else 100
    size = 40 if len(rows) <= 4 else 36
    for r, row in enumerate(rows):
        top = y + r * rh
        fill = TEAL if r == 0 else (WHITE if r % 2 else (250, 251, 250))
        rad = 24 if r in (0, len(rows) - 1) else 0
        d.rounded_rectangle((x0, top, x1, top + rh), radius=rad, fill=fill)
        for c, cell in enumerate(row):
            cw = xs[c + 1] - xs[c] - 48
            ls = wrap(cell, size, cw)
            cy = top + rh / 2 - (len(ls) - 1) * size * 0.6
            for i, ln in enumerate(ls):
                text(d, (xs[c] + 28, cy + i * size * 1.2), ln, size,
                     WHITE if r == 0 else INK, bold=(r == 0 or c == 0), anchor="lm")
    if s.get("note"):
        text(d, (88, H - 170), "※" + s["note"], 28, MUTED)


def dashed_rect(d, box, color, dash=22, gap=14, width=4):
    x0, y0, x1, y1 = box
    for x in range(int(x0), int(x1), dash + gap):
        d.line([(x, y0), (min(x + dash, x1), y0)], fill=color, width=width)
        d.line([(x, y1), (min(x + dash, x1), y1)], fill=color, width=width)
    for y in range(int(y0), int(y1), dash + gap):
        d.line([(x0, y), (x0, min(y + dash, y1))], fill=color, width=width)
        d.line([(x1, y), (x1, min(y + dash, y1))], fill=color, width=width)


def slide_product(s, im, d, W, H):
    y = 200
    for w in wrap(s["head"], 56, W - 176):
        text(d, (88, y), w, 56, INK, bold=True)
        y += 80
    y += 20
    box = (190, y, W - 190, y + 520)
    d.rectangle(box, fill=(235, 239, 237))
    dashed_rect(d, box, TEAL)
    cx = W / 2
    text(d, (cx, y + 170), "商品画像の枠（差し替え用）", 36, TEAL, bold=True, anchor="mm")
    for i, ln in enumerate([f"{s['pid']}：リンク作成ページから取得した画像を", "加工せずにこの枠へ配置", "画像の上に文字・装飾を重ねない", "差し替え時はこの説明文を消す"]):
        text(d, (cx, y + 250 + i * 50), ln, 30, MUTED, anchor="mm")
    y += 520 + 50
    for i, ln in enumerate(s["lines"]):
        size = 42 if i == 0 else 36
        for w in wrap(ln, size, W - 176):
            text(d, (88, y), w, size, INK, bold=(i == 0))
            y += int(size * 1.45)
    if s.get("note"):
        text(d, (88, H - 170), "※" + s["note"], 28, MUTED)


def slide_cta(s, im, d, W, H):
    y = 230
    text(d, (88, y), s["head"], 72, INK, bold=True)
    y += 150
    d.rounded_rectangle((72, y, W - 72, y + 120 + 130 * len(s["checks"])), radius=32, fill=WHITE)
    y += 70
    for c in s["checks"]:
        d.rounded_rectangle((128, y, 188, y + 60), radius=12, outline=TEAL, width=5)
        for w in wrap(c, 44, W - 360)[:2]:
            text(d, (220, y + 30), w, 44, INK, anchor="lm")
        y += 130
    y += 110
    d.rounded_rectangle((72, y, W - 72, y + 150), radius=75, fill=TEAL)
    text(d, (W / 2, y + 75), s["foot"], 42, WHITE, bold=True, anchor="mm")
    text(d, (W / 2, y + 220), "リンク先は楽天市場です。価格・在庫はリンク先で確認してください", 28, MUTED, anchor="mm")


KIND = dict(cover=slide_cover, point=slide_point, table=slide_table, product=slide_product, cta=slide_cta)


