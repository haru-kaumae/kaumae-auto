# -*- coding: utf-8 -*-
"""表紙の背景写真を集める（GitHub Actions上で実行。Claudeの作業環境からは外部の画像サイトにつながらないため）。
Openverse（https://openverse.org、WordPress財団の画像検索）から、CC0（パブリックドメイン扱い・商用利用可・
クレジット不要）とPDM（パブリックドメイン）の写真だけを取る。出どころとライセンスは assets/bg/credits.json に記録する。
  python tools/fetch_backgrounds.py"""
import datetime as dt, io, json, os, time
import requests
from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "assets", "bg")
QUERIES = {
    "kitchen": ["kitchen interior", "kitchen counter", "cooking kitchen"],
    "clean": ["cleaning home", "clean living room", "laundry room"],
    "storage": ["storage shelves home", "closet organization", "bookshelf interior"],
    "daily": ["bathroom interior", "household supplies", "living room interior"],
    "humid": ["cozy bedroom", "living room winter", "humidifier"],
    "blanket": ["cozy blanket", "winter sofa blanket", "knitted blanket"],
    "sweets": ["snacks table", "japanese sweets", "coffee and cake"],
    "gift": ["gift box", "wrapped present", "gift wrapping"],
}
PER_GENRE = 8
HEAD = {"User-Agent": "kaumae-auto/1.0 (background photo collection)"}


def search(q):
    r = requests.get("https://api.openverse.org/v1/images/", headers=HEAD, timeout=30, params=dict(
        q=q, license="cc0,pdm", size="large", mature="false", page_size=20, category="photograph"))
    r.raise_for_status()
    return r.json().get("results", [])


def main():
    os.makedirs(OUT, exist_ok=True)
    cpath = os.path.join(OUT, "credits.json")
    credits = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else {}
    for genre, qs in QUERIES.items():
        gdir = os.path.join(OUT, genre)
        os.makedirs(gdir, exist_ok=True)
        have = len([f for f in os.listdir(gdir) if f.endswith(".jpg")])
        seen = {c["id"] for c in credits.values()}
        for q in qs:
            if have >= PER_GENRE:
                break
            try:
                results = search(q)
            except Exception as e:
                print("検索失敗", q, e)
                continue
            for it in results:
                if have >= PER_GENRE:
                    break
                if it["id"] in seen or it.get("license") not in ("cc0", "pdm"):
                    continue
                if (it.get("width") or 0) < 1200 or (it.get("height") or 0) < 900:
                    continue
                try:
                    img = requests.get(it["url"], headers=HEAD, timeout=60)
                    img.raise_for_status()
                    im = Image.open(io.BytesIO(img.content)).convert("RGB")
                except Exception as e:
                    print("取得失敗", it["url"], e)
                    continue
                im.thumbnail((1600, 1600))
                k = 1
                while os.path.exists(os.path.join(OUT, f"{genre}/{k:02d}.jpg")):
                    k += 1
                name = f"{genre}/{k:02d}.jpg"
                im.save(os.path.join(OUT, name), "JPEG", quality=88)
                credits[name] = dict(id=it["id"], title=it.get("title"), creator=it.get("creator"),
                                     source=it.get("source"), landing=it.get("foreign_landing_url"),
                                     license=it.get("license"), license_url=it.get("license_url"),
                                     query=q, fetched=dt.date.today().isoformat())
                seen.add(it["id"])
                have += 1
                print("取得", name, it.get("license"), it.get("foreign_landing_url"))
                time.sleep(1)
    json.dump(credits, open(cpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
