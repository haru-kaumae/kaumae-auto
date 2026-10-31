# -*- coding: utf-8 -*-
"""ネットにつながずに、商品選定→原稿→規約チェック→画像→一覧ページまでを確かめる。
   python -m tests.test_offline
"""
import datetime as dt, os, shutil, tempfile
from src import rakuten, compose, compliance, main

SAMPLE = [
    dict(itemCode="shopA:1", itemName="【クーポンで50％OFF】【楽天1位】排気口カバー フラット 日本製 60cm 75cm ステンレス", itemPrice=3380,
         shopName="ショップA", itemUrl="https://item.rakuten.co.jp/a/1/", affiliateUrl="https://hb.afl.rakuten.co.jp/hgc/x/?pc=1",
         reviewCount=27199, reviewAverage=4.75, availability=1, postageFlag=0),
    dict(itemCode="shopA:2", itemName="同じショップの別商品", itemPrice=1000, shopName="ショップA", itemUrl="", affiliateUrl="https://hb.afl.rakuten.co.jp/x",
         reviewCount=5000, reviewAverage=4.6, availability=1, postageFlag=0),
    dict(itemCode="shopB:1", itemName="干し芋 訳あり 1kg ダイエット おやつ", itemPrice=2990, shopName="ショップB", itemUrl="",
         affiliateUrl="https://hb.afl.rakuten.co.jp/y", reviewCount=37000, reviewAverage=4.56, availability=1, postageFlag=0),
    dict(itemCode="shopC:1", itemName="＼10/27まで／ 真空保存容器 電動 強力密閉 BPAフリー", itemPrice=2780, shopName="ショップC", itemUrl="",
         affiliateUrl="https://hb.afl.rakuten.co.jp/z", reviewCount=6035, reviewAverage=4.73, availability=1, postageFlag=1),
]


def run():
    rakuten._call = lambda params: SAMPLE if "genreId" in params else SAMPLE[:1]
    tmp = tempfile.mkdtemp()
    main.STATE = os.path.join(tmp, "state", "posts.json")
    main.DOCS = os.path.join(tmp, "docs")
    main.ALERTS = os.path.join(tmp, "alerts.md")
    main.ROOT = tmp
    state = main.load()
    day = dt.date(2026, 11, 2)  # 月曜
    made = main.prepare(state, day)
    feed = state["posts"][0]
    assert feed["status"] == "ready", feed
    names = [p["name"] for p in feed["products"]]
    assert "排気口カバー フラット 日本製 60cm 75cm ステンレス" in names, names
    assert not any("ダイエット" in n for n in names), "禁止語を含む商品が選ばれた"
    assert len({p["shop"] for p in feed["products"]}) == len(feed["products"]), "同じショップが重複"
    assert feed["caption"].startswith(compose.PR_LINE)
    assert len(feed["images"]) == len(feed["slides"]) and all(p.endswith(".jpg") for p in feed["images"])
    assert state["stories"][0]["status"] == "ready"
    # 規約チェックが止めることの確認
    bad = dict(feed, kind="feed", caption=feed["caption"].replace(compose.PR_LINE, "") + " 買ってよかった https://x")
    probs = compliance.check(bad, feed["products"])
    assert len(probs) >= 3, probs
    # 投稿済みにして一覧ページ
    feed["status"] = "posted"
    from src import site
    site.build(state, main.DOCS)
    page = open(os.path.join(main.DOCS, "index.html"), encoding="utf-8").read()
    assert "PR｜" in page and "hb.afl.rakuten.co.jp" in page and 'rel="sponsored' in page
    # 次の水曜は別ジャンル、同じ商品は選ばない
    main.prepare(state, day + dt.timedelta(days=2))
    assert state["posts"][1]["genre"] != feed["genre"]
    out = os.path.join(os.path.dirname(__file__), "..", "preview")
    shutil.rmtree(out, ignore_errors=True)
    shutil.copytree(os.path.join(main.DOCS), out)
    print("OK", len(made), "件。画像の見本：preview/", "| 2本目のジャンル：", state["posts"][1]["genre"], state["posts"][1]["status"])
    print(feed["caption"])


if __name__ == "__main__":
    run()
