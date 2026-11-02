# -*- coding: utf-8 -*-
"""原稿からJPEG画像を書き出す（Instagram APIはJPEGのみ対応）。"""
import io, os
import requests
from PIL import Image, ImageDraw
from . import design as D


def photo_slide(url, W=1080, H=1350):
    """楽天の商品画像を、そのまま（文字入れ・切り抜きなし、サイズ変更のみ）無地の背景の中央に置く。
    楽天アフィリエイトのガイドライン（2026-11-02確認 https://affiliate.rakuten.co.jp/guideline/rule/）：
    「画像の上に直接文字や装飾を入れること、画像の一部を切り取って使用することは禁止」「サイズ変更…は可能」。
    取得できなければ None（その商品の画像の1枚を省くだけで、投稿は止めない）。"""
    if not url:
        return None
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        src = Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception:
        return None
    scale = min(960 / src.width, 960 / src.height)
    src = src.resize((max(1, int(src.width * scale)), max(1, int(src.height * scale))), Image.LANCZOS)
    im = Image.new("RGB", (W, H), D.WHITE)
    im.paste(src, ((W - src.width) // 2, (H - src.height) // 2))
    return im

KIND = dict(cover=D.slide_cover, point=D.slide_point, table=D.slide_table, cta=D.slide_cta)


def render_feed(post, outdir, stem):
    os.makedirs(outdir, exist_ok=True)
    pages = []
    for s in post["slides"]:
        if s["kind"] == "photo":
            im = photo_slide(s.get("url"))
            if im is not None:
                pages.append(("photo", im))
        else:
            pages.append((s, None))
    files, n = [], len(pages)
    for i, (s, im) in enumerate(pages, 1):
        if im is None:
            im, d = D.frame(1080, 1350, i, n, dark=(s["kind"] == "cta"))
            KIND[s["kind"]](s, im, d, 1080, 1350)
        path = os.path.join(outdir, f"{stem}_{i:02d}.jpg")
        im.save(path, "JPEG", quality=92)
        files.append(path)
    return files


def render_story(story, outdir, stem):
    """ストーリーズ（1080×1920）：フィードの中のページと同じデザイン。"""
    os.makedirs(outdir, exist_ok=True)
    W, H = 1080, 1920
    im = Image.new("RGB", (W, H), D.BG)
    d = ImageDraw.Draw(im)
    # 上の濃い帯
    d.rectangle((0, 0, W, 980), fill=D.DEEP)
    top = 200
    label = "PR｜楽天アフィリエイト広告"
    tw = D.f(34).getlength(label)
    d.rounded_rectangle((72, top, 72 + tw + 56, top + 70), radius=35, outline=(176, 206, 200), width=2)
    D.text(d, (100, top + 35), label, 34, D.WHITE, anchor="lm")
    y = 360
    D.text(d, (88, y), "TODAY'S CHECK", 40, D.MUSTARD, bold=True)
    d.rectangle((88, y + 66, 178, y + 74), fill=D.MUSTARD)
    y += 120
    size = 92
    while size > 60:
        lines = D.wrap(story["head"], size, W - 176)
        if len(lines) <= 3 and (len(lines) == 1 or len(lines[-1]) >= 3):
            break
        size -= 4
    for w in D.wrap(story["head"], size, W - 176):
        D.text(d, (88, y), w, size, D.WHITE, bold=True)
        y += int(size * 1.3)
    y += 20
    D.text(d, (88, y), story["title"], 36, (176, 206, 200), bold=True)
    # 説明カード
    y = 900
    tmp = ImageDraw.Draw(Image.new("RGB", (W, H)))
    end = D.para(tmp, 150, y + 130, story["body"], 54, W - 300)
    d.rounded_rectangle((72, y, W - 72, end + 90), radius=40, fill=D.WHITE, outline=D.LINE, width=2)
    D.pill(d, 120, y + 44, "やること", 34, D.DEEP, (255, 236, 200))
    d.rectangle((120, y + 136, 128, end - 10), fill=D.MUSTARD)
    D.para(d, 150, y + 130, story["body"], 54, W - 300)
    # 誘導
    ly = 1560
    d.rounded_rectangle((90, ly, W - 90, ly + 130), radius=65, fill=D.MUSTARD)
    D.text(d, (W / 2, ly + 65), story["foot"] + "  →", 42, D.DEEP, bold=True, anchor="mm")
    D.text(d, (88, H - 120), D.HANDLE, 30, D.MUTED, anchor="ls")
    D.text(d, (W - 88, H - 120), D.ACCOUNT, 30, D.TEAL, bold=True, anchor="rs")
    path = os.path.join(outdir, f"{stem}.jpg")
    im.save(path, "JPEG", quality=92)
    return [path]


def render_reel(image_paths, outdir, stem):
    """スライド（1080×1350）を縦長の動画（1080×1920、H.264、無音の音声トラック付き）にする。
    表紙3秒、ほかは1枚2.5秒。ffmpegを使う（GitHub Actionsのubuntuに入っている）。"""
    import subprocess, tempfile
    os.makedirs(outdir, exist_ok=True)
    tmpd = tempfile.mkdtemp()
    lst = []
    for i, p in enumerate(image_paths):
        src = Image.open(p).convert("RGB")
        canvas = Image.new("RGB", (1080, 1920), D.BG)
        canvas.paste(src, (0, (1920 - src.height) // 2))
        fp = os.path.join(tmpd, f"{i:02d}.jpg")
        canvas.save(fp, "JPEG", quality=92)
        lst.append((fp, 3.0 if i == 0 else 2.5))
    concat = os.path.join(tmpd, "list.txt")
    with open(concat, "w") as fp:
        for f_, dur in lst:
            fp.write(f"file '{f_}'\nduration {dur}\n")
        fp.write(f"file '{lst[-1][0]}'\n")
    total = sum(d for _, d in lst)
    out = os.path.join(outdir, f"{stem}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", concat,
           "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
           "-t", str(total), "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-profile:v", "high",
           "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-shortest",
           "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    return out
