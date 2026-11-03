# -*- coding: utf-8 -*-
"""原稿からJPEG画像を書き出す（Instagram APIはJPEGのみ対応）。"""
import io, os
import requests
from PIL import Image, ImageDraw
from . import design as D


def fetch_image(url):
    if not url:
        return None
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception:
        return None


CHAR = (44, 46, 47)        # 商品ページの背景（濃いグレー）
CHAR2 = (58, 61, 62)


def item_page(s, idx, total, W=1080, H=1350):
    """商品ページ：上に番号・商品名・価格、中央に商品画像（加工なし・サイズ変更のみ）、下にレビューと買う前のチェック。
    楽天アフィリエイトのガイドライン（2026-11-02確認）：画像の上に文字や装飾を入れない・切り抜かない。
    画像の外側（周りの帯）に文字を置くのは「周辺部分への加工」として可能。"""
    im = Image.new("RGB", (W, H), CHAR)
    d = ImageDraw.Draw(im)
    rf = D.rf
    # PRと枚数
    d.rounded_rectangle((60, 48, 150, 98), radius=25, fill=CHAR2)
    d.text((105, 73), "PR", font=rf(28), fill=D.WHITE, anchor="mm")
    d.rounded_rectangle((W - 160, 48, W - 60, 98), radius=25, fill=CHAR2)
    d.text((W - 110, 73), f"{idx}/{total}", font=rf(28), fill=D.WHITE, anchor="mm")
    # 番号｜商品名　価格
    top = 130
    d.text((70, top + 110), f"{s['no']:02d}", font=rf(96), fill=D.WHITE, anchor="lm")
    d.line([(225, top + 30), (225, top + 190)], fill=(150, 150, 150), width=4)
    name_w = W - 260 - 70
    size = 52
    while size > 36:
        lines = D.wrap(s["head"], size, name_w) if False else _wrap_r(s["head"], size, name_w)
        if len(lines) <= 3:
            break
        size -= 4
    lines = lines[:3]
    ny = top + 110 - (len(lines) - 1) * size * 0.65
    for ln in lines:
        d.text((260, ny), ln, font=rf(size), fill=D.WHITE, anchor="lm")
        ny += size * 1.3
    d.text((W - 70, top + 245), s["price"], font=rf(54), fill=D.MUSTARD, anchor="rs")
    d.text((260, top + 242), f"{s['date']}時点", font=rf(26), fill=(170, 170, 170), anchor="ls")
    # 商品画像の帯（白）
    band_top, band_h = 400, 560
    d.rectangle((0, band_top, W, band_top + band_h), fill=D.WHITE)
    src = fetch_image(s.get("url"))
    if src is not None:
        scale = min((band_h - 20) / src.height, (W - 40) / src.width)
        src = src.resize((max(1, int(src.width * scale)), max(1, int(src.height * scale))), Image.LANCZOS)
        im.paste(src, ((W - src.width) // 2, band_top + (band_h - src.height) // 2))
    else:
        d.text((W / 2, band_top + band_h / 2), "画像は商品ページで確認してください", font=rf(36), fill=D.MUTED, anchor="mm")
    # レビュー・送料・ショップ
    y = band_top + band_h + 28
    d.text((70, y + 30), s["review"], font=rf(58), fill=D.MUSTARD, anchor="lm")
    rw = rf(58).getlength(s["review"])
    d.text((70 + rw + 14, y + 38), f"（{s['count']}）", font=rf(30), fill=(200, 200, 200), anchor="lm")
    pill_txt = s["postage"]
    pw = rf(30).getlength(pill_txt) + 44
    d.rounded_rectangle((W - 70 - pw, y + 8, W - 70, y + 56), radius=24, outline=(200, 200, 200), width=2)
    d.text((W - 70 - pw / 2, y + 32), pill_txt, font=rf(30), fill=D.WHITE, anchor="mm")
    shop = s["shop"]
    while rf(28).getlength(shop) > W - 140 and len(shop) > 4:
        shop = shop[:-2] + "…"
    d.text((70, y + 92), shop, font=rf(28), fill=(170, 170, 170), anchor="lm")
    # 買う前のチェック
    y += 132
    d.rounded_rectangle((60, y, W - 60, H - 70), radius=28, fill=CHAR2)
    d.text((100, y + 46), "買う前に", font=rf(30), fill=D.MUSTARD, anchor="lm")
    d.text((100 + rf(30).getlength("買う前に") + 20, y + 46), s["check"], font=rf(40), fill=D.WHITE, anchor="lm")
    body = "".join(s["body"])
    by = y + 98
    for ln in _wrap_r(body, 30, W - 200)[:2]:
        d.text((100, by), ln, font=rf(30), fill=(215, 215, 215), anchor="lm")
        by += 44
    return im


def _wrap_r(text, size, width):
    out, cur = [], ""
    for tok in [t for t in __import__("re").split(r"( )", text) if t]:
        if D.rf(size).getlength(cur + tok) <= width:
            cur += tok
        elif tok == " ":
            out.append(cur); cur = ""
        elif cur and D.rf(size).getlength(tok) <= width:
            out.append(cur.strip()); cur = tok
        else:
            for ch in tok:
                if D.rf(size).getlength(cur + ch) > width:
                    out.append(cur); cur = ch
                else:
                    cur += ch
    out.append(cur)
    return [o.strip() for o in out if o.strip()] or [""]


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
        if s["kind"] == "item":
            pages.append(("item", s))
            continue
        if s["kind"] == "photo":
            im = photo_slide(s.get("url"))
            if im is not None:
                pages.append(("photo", im))
        else:
            pages.append((s, None))
    files, n = [], len(pages)
    for i, (s, im) in enumerate(pages, 1):
        if s == "item":
            s, im = im, item_page(im, i, n)
        if im is None and s["kind"] == "cover":
            im = D.photo_cover(s, Image.new("RGB", (1080, 1350)), 1080, 1350, i, n)
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
    label = "PR"
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
    # BGM：assets/bgm のオリジナル曲（tools/make_bgm.py で合成）を日替わりで使う。動画より短ければ繰り返す
    bgm_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "bgm")
    tracks = sorted(f for f in os.listdir(bgm_dir) if f.endswith(".m4a")) if os.path.isdir(bgm_dir) else []
    if tracks:
        track = os.path.join(bgm_dir, tracks[sum(map(ord, stem)) % len(tracks)])
        audio_in = ["-stream_loop", "-1", "-i", track]
        afilter = ["-af", f"loudnorm=I=-16:TP=-1.5:LRA=7,afade=t=in:d=0.3,afade=t=out:st={total - 1.2}:d=1.2"]
    else:
        audio_in = ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
        afilter = []
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", concat, *audio_in,
           "-t", str(total), "-vf", "fps=30,format=yuv420p", *afilter, "-c:v", "libx264", "-profile:v", "high",
           "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
           "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    return out
