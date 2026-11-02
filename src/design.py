# -*- coding: utf-8 -*-
"""投稿画像の共通デザイン（運用キットの画像と同じ見た目）。"""
import os
from PIL import Image, ImageDraw, ImageFont
HANDLE = "@kaumae._.memo"
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
    """幅に収まるよう折り返す。空白で区切れる所では単語を割らない（日本語は1文字ずつ）。"""
    out, cur = [], ""
    for tok in [t for t in __import__("re").split(r"( )", s) if t != ""]:
        if f(size).getlength(cur + tok) <= width:
            cur += tok
            continue
        if tok == " ":
            out.append(cur)
            cur = ""
            continue
        if cur and f(size).getlength(tok) <= width:
            out.append(cur.rstrip())
            cur = tok
            continue
        for ch in tok:
            if f(size).getlength(cur + ch) > width:
                out.append(cur)
                cur = ch
            else:
                cur += ch
    out.append(cur)
    return [o.strip() for o in out if o.strip()] or [""]


def para(d, x, y, lines, size, width, fill=INK, bold=False, gap=1.5):
    for ln in lines:
        if ln == "":
            y += int(size * 0.7)
            continue
        for w in wrap(ln, size, width):
            text(d, (x, y), w, size, fill, bold)
            y += int(size * gap)
    return y


DEEP = (18, 74, 70)          # 濃いティール（強調ページの背景）
CREAM = (250, 246, 236)


def frame(W, H, idx=None, total=None, dark=False):
    im = Image.new("RGB", (W, H), DEEP if dark else BG)
    d = ImageDraw.Draw(im)
    fg, sub = (WHITE, (176, 206, 200)) if dark else (INK, MUTED)
    # PR表記（ファーストビュー上部）
    label = "PR｜楽天アフィリエイト広告を含みます"
    tw = f(30).getlength(label)
    d.rounded_rectangle((72, 64, 72 + tw + 48, 64 + 56), radius=28,
                        fill=DEEP if dark else WHITE, outline=sub if dark else LINE, width=2)
    text(d, (96, 92), label, 30, fg, anchor="lm")
    if idx is not None:
        text(d, (W - 72, 92), f"{idx}/{total}", 30, sub, anchor="rm")
        # 進み具合のバー
        bx0, bx1, by = 72, W - 72, H - 128
        d.rounded_rectangle((bx0, by, bx1, by + 6), radius=3, fill=(40, 98, 93) if dark else LINE)
        d.rounded_rectangle((bx0, by, bx0 + (bx1 - bx0) * idx / total, by + 6), radius=3, fill=MUSTARD)
    text(d, (72, H - 64), HANDLE, 30, sub, anchor="ls")
    text(d, (W - 72, H - 64), ACCOUNT, 30, MUSTARD if dark else TEAL, bold=True, anchor="rs")
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
    """チェックのページ：上半分に大きな番号と見出し、下に説明のカード。"""
    num = "".join(ch for ch in s["label"] if ch.isdigit()) or "1"
    band = 700
    d.rectangle((0, 150, W, band), fill=DEEP)
    # 大きな番号（背景の飾り）
    text(d, (W - 60, 175), f"0{num}", 340, (34, 98, 92), bold=True, anchor="ra")
    text(d, (88, 210), "CHECK", 40, MUSTARD, bold=True)
    text(d, (88 + f(40).getlength("CHECK") + 16, 210), f"0{num}", 40, MUSTARD, bold=True)
    d.rectangle((88, 272, 88 + 90, 280), fill=MUSTARD)
    y = 360
    size = 84
    while size > 56:
        lines = wrap(s["head"], size, W - 176)
        if len(lines) <= 2 and (len(lines) == 1 or len(lines[-1]) >= 3):
            break
        size -= 4
    for w in wrap(s["head"], size, W - 176):
        text(d, (88, y), w, size, WHITE, bold=True)
        y += int(size * 1.32)
    # 説明カード
    top = band - 50
    tmp = ImageDraw.Draw(Image.new("RGB", (W, H)))
    end = para(tmp, 150, top + 120, s["body"], 52, W - 300)
    d.rounded_rectangle((72, top, W - 72, end + 80), radius=36, fill=WHITE, outline=LINE, width=2)
    pill(d, 120, top + 40, "やること", 32, DEEP, (255, 236, 200))
    d.rectangle((120, top + 126, 128, end - 10), fill=MUSTARD)
    para(d, 150, top + 120, s["body"], 52, W - 300)
    # ひとこと
    hint_y = min(max(end + 130, H - 360), H - 230)
    check_icon(d, 112, hint_y + 22, 26)
    text(d, (156, hint_y + 22), "商品ページの表記で確かめてから選ぶ", 38, TEAL, bold=True, anchor="lm")
    if s.get("note"):
        text(d, (88, H - 180), "※" + s["note"], 28, MUTED)


def slide_table(s, im, d, W, H):
    """例のページ：商品名と、価格・レビュー・送料の大きな数字のタイル。"""
    rows = {r[0]: r[1] for r in s["rows"][1:]}
    date = s["rows"][0][1]
    num = "".join(ch for ch in s["label"] if ch.isdigit()) or "1"
    y = 200
    text(d, (88, y), f"EXAMPLE 0{num}", 36, TEAL, bold=True)
    text(d, (W - 88, y), "レビュー件数の多い商品", 32, MUSTARD, bold=True, anchor="ra")
    y += 70
    lines = wrap(s["head"], 60, W - 176)[:3]
    for w in lines:
        text(d, (88, y), w, 60, INK, bold=True)
        y += 84
    y += 30
    gap = 24
    tw = (W - 144 - gap) / 2
    # 価格（大）
    def tile(x0, y0, x1, y1, label, value, sub=None, fill=WHITE, fg=INK, vsize=72):
        d.rounded_rectangle((x0, y0, x1, y1), radius=32, fill=fill, outline=None if fill != WHITE else LINE, width=2)
        text(d, (x0 + 36, y0 + 36), label, 30, fg if fill != WHITE else MUTED, bold=True)
        size = vsize
        while f(size).getlength(value) > (x1 - x0 - 72) and size > 36:
            size -= 4
        text(d, (x0 + 36, y0 + 82), value, size, fg, bold=True)
        if sub:
            text(d, (x0 + 36, y1 - 36), sub, 28, fg if fill != WHITE else MUTED, anchor="ls")
    price = rows.get("価格", "")
    tile(72, y, W - 72, y + 270, "価格（表示時点）", price, f"{date.replace('の表示', '')}時点の楽天市場の表示", fill=DEEP, fg=WHITE, vsize=104)
    y += 270 + gap
    rv = rows.get("レビュー", "")
    star, _, cnt = rv.partition("（")
    tile(72, y, 72 + tw, y + 240, "レビュー", star, "（" + cnt if cnt else None, fill=(255, 236, 200), fg=INK, vsize=72)
    tile(72 + tw + gap, y, W - 72, y + 240, "送料", rows.get("送料", ""), None, vsize=60)
    y += 240 + gap
    d.rounded_rectangle((72, y, W - 72, y + 120), radius=28, fill=WHITE, outline=LINE, width=2)
    y += 5
    text(d, (108, y + 55), "ショップ", 30, MUTED, bold=True, anchor="lm")
    shop = rows.get("ショップ", "")
    while f(36).getlength(shop) > W - 380 and len(shop) > 4:
        shop = shop[:-2] + "…"
    text(d, (260, y + 55), shop, 36, INK, bold=True, anchor="lm")
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
    """まとめのページ（濃い背景）：チェックリストと保存・リンクの案内。"""
    y = 190
    text(d, (88, y), "SAVE THIS", 36, MUSTARD, bold=True)
    y += 66
    text(d, (88, y), s["head"], 80, WHITE, bold=True)
    y += 150
    for i, c in enumerate(s["checks"], 1):
        d.rounded_rectangle((72, y, W - 72, y + 116), radius=28, fill=(28, 92, 87))
        d.rounded_rectangle((108, y + 30, 164, y + 86), radius=12, outline=MUSTARD, width=5)
        text(d, (196, y + 58), f"0{i}", 34, MUSTARD, bold=True, anchor="lm")
        for w in wrap(c, 42, W - 400)[:1]:
            text(d, (262, y + 58), w, 42, WHITE, bold=True, anchor="lm")
        y += 140
    y += 50
    # 保存のアイコン（しおり）
    bx = 88
    d.polygon([(bx, y), (bx + 44, y), (bx + 44, y + 60), (bx + 22, y + 44), (bx, y + 60)], fill=MUSTARD)
    text(d, (bx + 70, y + 30), "保存して、買う前に見返す", 40, WHITE, bold=True, anchor="lm")
    y += 100
    d.rounded_rectangle((72, y, W - 72, y + 130), radius=65, fill=MUSTARD)
    text(d, (W / 2, y + 65), s["foot"] + "  →", 42, DEEP, bold=True, anchor="mm")
    text(d, (W / 2, y + 180), "リンク先は楽天市場です。価格・在庫はリンク先で確認してください", 28, (176, 206, 200), anchor="mm")


KIND = dict(cover=slide_cover, point=slide_point, table=slide_table, product=slide_product, cta=slide_cta)


