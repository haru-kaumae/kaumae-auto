# -*- coding: utf-8 -*-
"""商品を選び、フィードとストーリーズの原稿（スライドとキャプション）を組み立てる。"""
import datetime as dt
from . import config as C
from .config import PR_LINE
from .compliance import BANNED

JST = dt.timezone(dt.timedelta(hours=9))


def today():
    return dt.datetime.now(JST).date()


def pick_genre(state, day):
    """今月のローテーションのうち、最近いちばん使っていないジャンルを選ぶ。"""
    order = C.MONTH_ROTATION[day.month]
    last = {}
    for p in state["posts"]:
        if p.get("status") == "dry_run":
            continue
        last[p["genre"]] = max(last.get(p["genre"], ""), p["date"])
    return sorted(order, key=lambda g: (last.get(g, ""), order.index(g)))[0]


def product_word(name):
    """商品名から商品の種類（例：水切りラック）を探す。なければ空文字。"""
    for w in C.PRODUCT_WORDS:
        if w in name:
            return w
    return ""


def pick_products(items, state, day, n=C.PRODUCTS_PER_POST):
    recent = set()
    limit = (day - dt.timedelta(days=C.REPOST_COOLDOWN_DAYS)).isoformat()
    for p in state["posts"]:
        if p["date"] >= limit and p.get("status") != "dry_run":
            recent.update(x["itemCode"] for x in p["products"])
    out, shops = [], set()
    for it in items:
        if (it["itemCode"] in recent or it["shop"] in shops or not it["availability"]
                or it["reviewCount"] < C.MIN_REVIEW_COUNT or it["reviewAverage"] < C.MIN_REVIEW_AVERAGE
                or not it["affiliateUrl"] or any(w in it["name"] for w in BANNED)):
            continue
        out.append(it)
        shops.add(it["shop"])          # 同じショップの商品を並べない
    # 1つの投稿は同じ種類の商品でそろえる（比べやすく、表紙で何の話か伝わるように）
    by_word = {}
    for it in out:
        by_word.setdefault(product_word(it["name"]), []).append(it)
    same = [g for w, g in by_word.items() if w and len(g) >= n]
    if same:
        return same[0][:n]
    return out[:n]


def yen(n):
    return f"{n:,}円"


def build_feed(genre_key, products, day, number):
    g = C.GENRES[genre_key]
    checks = C.CHECKS[genre_key]
    word = product_word(products[0]["name"]) if products else ""
    if word and not all(product_word(p["name"]) == word for p in products):
        word = ""                       # 種類がそろわない時はジャンル名にする
    topic = word or g["name"]
    cover = C.TITLES[number % len(C.TITLES)].format(g=topic)
    title = cover.replace("\n", "")
    date_ja = f"{day.year}/{day.month}/{day.day}"
    pre, num, post = C.COVERS[number % len(C.COVERS)]
    slides = [dict(kind="cover", kicker=f"{g['name']}｜買う前メモ", title=cover, sub="楽天市場でレビューの多い商品つき",
                   genre=genre_key, topic=topic, pre=pre, num=num, post=post, month=f"{day.year}.{day.month}月",
                   seed=f"{day.isoformat()}{number}")]
    # 2枚目からは商品ごとに1ページ（商品画像・名前・価格・レビュー・買う前のチェック1つ）
    for i, p in enumerate(products, 1):
        head, body = checks[(i - 1) % len(checks)]
        slides.append(dict(kind="item", no=i, head=p["name"], url=p.get("image", ""), price=yen(p["price"]),
                           review=f"★{p['reviewAverage']:.2f}", count=f"{p['reviewCount']:,}件",
                           postage="送料込み" if p["postageFlag"] == 0 else "送料別",
                           shop=p["shop"], check=head, body=body, date=date_ja))

    lines = [f"{PR_LINE}{topic}、買う前にここだけは確認👇", "",
             f"{topic}を選ぶ時に、商品ページで先に見ておきたい3つをまとめました。", ""]
    for i, (head, body) in enumerate(checks, 1):
        lines += [f"✔ CHECK{i}　{head}", "".join(body), ""]
    lines.append(f"■ 例として、{date_ja}に楽天市場でレビューの多かった商品")
    for p in products:
        lines.append(f"・{p['name']}（{p['shop']}）{yen(p['price'])}、★{p['reviewAverage']:.2f}／{p['reviewCount']:,}件")
    lines += ["",
              f"※{date_ja}に楽天ウェブサービスで取得した情報です。価格・在庫・仕様は変わることがあるので、購入前にリンク先で確認してください。",
              "※使用した感想ではなく、公開されている商品情報を整理して紹介しています。",
              "※商品画像は楽天市場の各ショップのものです。", "",
              "紹介した商品は、プロフィールのリンク（楽天市場）から見られます。",
              "📌 保存しておくと、買う前に見返せます。",
              f"💬 {topic}を選ぶ時、ほかに何を確認していますか？コメントで教えてください。", "",
              (f"#{word} " if word else "") + f"{C.HASHTAGS[genre_key]} {C.COMMON_TAGS}"]
    return dict(kind="feed", genre=genre_key, topic=topic, title=title, slides=slides, caption="\n".join(lines))


def build_story(latest, day):
    """直近のフィード投稿のチェックを1つずつ紹介する。リンクはプロフィールへ誘導。"""
    checks = [(s["head"], s["body"]) for s in latest["slides"] if s["kind"] == "point"]
    checks += [(s["check"], s["body"]) for s in latest["slides"] if s["kind"] == "item"]
    if not checks:
        checks = C.CHECKS.get(latest["genre"], [("買う前に確認", ["サイズと仕様を商品ページで確かめる。"])])
    head, body = checks[day.toordinal() % len(checks)]
    items = [s for s in latest["slides"] if s["kind"] == "item"]
    item = items[0] if items else None      # 1枚目の商品（いちばんレビューの多いもの）を画像つきで見せる
    return dict(kind="story", genre=latest["genre"], title=latest["title"], topic=latest.get("topic", ""),
                head=head, body=body, item=item, count=len(items), foot="商品の一覧はプロフィールのリンクから")
