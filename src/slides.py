# -*- coding: utf-8 -*-
"""原稿からJPEG画像を書き出す（Instagram APIはJPEGのみ対応）。"""
import os
from PIL import Image, ImageDraw
from . import design as D

KIND = dict(cover=D.slide_cover, point=D.slide_point, table=D.slide_table, cta=D.slide_cta)


def render_feed(post, outdir, stem):
    os.makedirs(outdir, exist_ok=True)
    files, n = [], len(post["slides"])
    for i, s in enumerate(post["slides"], 1):
        im, d = D.frame(1080, 1350, i, n)
        KIND[s["kind"]](s, im, d, 1080, 1350)
        path = os.path.join(outdir, f"{stem}_{i:02d}.jpg")
        im.save(path, "JPEG", quality=92)
        files.append(path)
    return files


def render_story(story, outdir, stem):
    os.makedirs(outdir, exist_ok=True)
    W, H = 1080, 1920
    im = Image.new("RGB", (W, H), D.BG)
    d = ImageDraw.Draw(im)
    top = 200
    d.rounded_rectangle((72, top, 72 + 560, top + 70), radius=35, fill=D.WHITE, outline=D.LINE, width=2)
    D.text(d, (100, top + 35), "PR｜楽天アフィリエイト広告", 34, D.INK, bold=True, anchor="lm")
    y = 420
    D.text(d, (88, y), story["title"], 38, D.TEAL, bold=True)
    y += 120
    for w in D.wrap(story["head"], 76, W - 176):
        D.text(d, (88, y), w, 76, D.INK, bold=True)
        y += 108
    y += 40
    tmp = ImageDraw.Draw(Image.new("RGB", (W, H)))
    end = D.para(tmp, 130, y + 60, story["body"], 50, W - 260)
    d.rounded_rectangle((72, y, W - 72, end + 40), radius=36, fill=D.WHITE)
    D.para(d, 130, y + 60, story["body"], 50, W - 260)
    ly = 1560
    d.rounded_rectangle((120, ly, W - 120, ly + 120), radius=60, fill=D.TEAL)
    D.text(d, (W / 2, ly + 60), story["foot"], 40, D.WHITE, bold=True, anchor="mm")
    D.text(d, (88, H - 120), D.HANDLE, 30, D.MUTED, anchor="ls")
    path = os.path.join(outdir, f"{stem}.jpg")
    im.save(path, "JPEG", quality=92)
    return [path]
