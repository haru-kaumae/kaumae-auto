# -*- coding: utf-8 -*-
"""毎日・毎週・毎月の処理の入り口。

  python -m src.main daily    # フィード（月水金）とストーリーズ（毎日）を作って投稿
  python -m src.main weekly   # 在庫・リンクの確認、投稿の数字の記録
  python -m src.main publish  # 規約チェックを通った投稿をInstagramに公開
  python -m src.main refresh  # Instagramのトークンを延長してファイルに書く
"""
import csv, datetime as dt, json, os, sys, time
import requests
from . import config as C, rakuten, compose, compliance, slides, instagram, site

ROOT = os.path.join(os.path.dirname(__file__), "..")
STATE = os.path.join(ROOT, "state", "posts.json")
METRICS = os.path.join(ROOT, "state", "metrics.csv")
DOCS = os.path.join(ROOT, "docs")
ALERTS = os.path.join(ROOT, "alerts_new.md")  # コミットしない。ワークフローがIssueにする


def load():
    state = json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {}
    state.setdefault("posts", [])
    state.setdefault("stories", [])
    return state


def save(state):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(state, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def alert(msg):
    """問題があった時の記録。ワークフローがこのファイルを見てGitHubのIssue（メール通知）を作る。"""
    with open(ALERTS, "a", encoding="utf-8") as fp:
        fp.write(f"- {dt.datetime.now(compose.JST):%Y-%m-%d %H:%M} {msg}\n")
    print("ALERT:", msg)


def public_urls(paths):
    if not C.SITE_URL:
        raise RuntimeError("SITE_URL が設定されていません")
    urls = [f"{C.SITE_URL}/{os.path.relpath(p, DOCS).replace(os.sep, '/')}" for p in paths]
    return urls


def wait_public(urls, timeout=900):
    """GitHub Pagesに画像が公開されるまで待つ（APIは公開URLから画像を読み込むため）。"""
    end = time.time() + timeout
    for u in urls:
        while True:
            try:
                if requests.head(u, timeout=15).status_code == 200:
                    break
            except requests.RequestException:
                pass
            if time.time() > end:
                raise RuntimeError(f"画像が公開されませんでした：{u}")
            time.sleep(15)


def prepare(state, day):
    """画像と原稿を作り、規約チェックを通ったものを state に「ready」で積む。投稿は publish() で行う。"""
    made = []
    # 試運転（DRY_RUN）で作ったものは "dry_run" にして、本番の投稿・選定・重複判定に使わない
    new_status = "dry_run" if C.DRY_RUN else "ready"
    real = {"posted", "ready", "blocked", "failed"}
    feed_day = day.weekday() in C.FEED_WEEKDAYS or C.FORCE_FEED
    if feed_day and not any(p["date"] == day.isoformat() and p["status"] in real for p in state["posts"]):
        genre = compose.pick_genre(state, day)
        items = rakuten.search_genre(C.GENRES[genre]["id"])
        prods = compose.pick_products(items, state, day)
        if len(prods) < 1:
            alert(f"{C.GENRES[genre]['name']}で条件に合う商品が見つからず、フィード投稿を見送りました")
        else:
            post = compose.build_feed(genre, prods, day, len(state["posts"]))
            problems = compliance.check(post, prods)
            stem = f"{day.isoformat()}_feed"
            rec = dict(date=day.isoformat(), genre=genre, title=post["title"], caption=post["caption"],
                       slides=post["slides"], products=prods, status=new_status)
            if problems:
                rec["status"] = "blocked"
                alert(f"フィード「{post['title']}」を規約チェックで止めました：" + "／".join(problems))
            else:
                rec["images"] = [os.path.relpath(p, ROOT) for p in slides.render_feed(post, os.path.join(DOCS, "media"), stem)]
            state["posts"].append(rec)
            made.append(rec)
    usable = ("posted", "ready", "dry_run") if C.DRY_RUN else ("posted", "ready")
    latest = next((p for p in reversed(state["posts"]) if p["status"] in usable), None)
    if C.STORY_EVERY_DAY and latest and not any(s["date"] == day.isoformat() and s["status"] in real for s in state["stories"]):
        story = compose.build_story(latest, day)
        problems = compliance.check(story)
        rec = dict(date=day.isoformat(), title=story["title"], head=story["head"], status=new_status)
        if problems:
            rec["status"] = "blocked"
            alert("ストーリーズを規約チェックで止めました：" + "／".join(problems))
        else:
            rec["images"] = [os.path.relpath(p, ROOT) for p in slides.render_story(story, os.path.join(DOCS, "media"), f"{day.isoformat()}_story")]
        state["stories"].append(rec)
        made.append(rec)
    site.build(state, DOCS)
    return made


def publish(state):
    """ready の投稿を Instagram に公開する。DRY_RUN では何もしない。"""
    if C.DRY_RUN:
        print("DRY_RUN：投稿はしません")
        return
    for rec in [p for p in state["posts"] if p["status"] == "ready"] + [s for s in state["stories"] if s["status"] == "ready"]:
        try:
            # 投稿直前にもう一度、在庫と価格を確かめる
            for it in rec.get("products", []):
                now = rakuten.lookup(it["itemCode"])
                if not now or not now["availability"]:
                    raise RuntimeError(f"{it['name']} が在庫切れになりました")
                if abs(now["price"] - it["price"]) > it["price"] * 0.1:
                    raise RuntimeError(f"{it['name']} の価格が取得時から10%以上変わりました（{it['price']}→{now['price']}円）")
            urls = public_urls([os.path.join(ROOT, p) for p in rec["images"]])
            wait_public(urls)
            if "caption" in rec:
                rec["media_id"] = instagram.publish_carousel(urls, rec["caption"])
            else:
                rec["media_id"] = instagram.publish_story(urls[0])
            rec["status"] = "posted"
        except Exception as e:  # 1件の失敗で他を止めない
            rec["status"] = "failed"
            alert(f"「{rec['title']}」の投稿に失敗しました：{e}")
    site.build(state, DOCS)


def weekly(state):
    for p in state["posts"]:
        if p["status"] != "posted":
            continue
        for it in p["products"]:
            try:
                now = rakuten.lookup(it["itemCode"])
                it["soldOut"] = not now or not now["availability"]
            except Exception as e:
                alert(f"{it['name']} の在庫確認に失敗：{e}")
    site.build(state, DOCS)
    new = not os.path.exists(METRICS)
    with open(METRICS, "a", encoding="utf-8-sig", newline="") as fp:
        w = csv.writer(fp)
        if new:
            w.writerow(["記録日", "投稿日", "種類", "タイトル", "media_id"] + instagram.METRICS)
        for p in state["posts"]:
            if p["status"] == "posted" and p.get("media_id"):
                m = instagram.insights(p["media_id"]) if not C.DRY_RUN else {}
                w.writerow([compose.today().isoformat(), p["date"], "feed", p["title"], p["media_id"]] + [m.get(k) for k in instagram.METRICS])


def main(cmd):
    state = load()
    if cmd == "daily":
        made = prepare(state, compose.today())
        print(f"作成：{len(made)}件", *[f"・{r.get('title')}（{r['status']}）" for r in made], sep="\n")
        if not made:
            print("今日は作るものがありません（フィードは月・水・金。ストーリーズは最初のフィードの後から）")
        save(state)
    elif cmd == "publish":
        publish(state)
        save(state)
    elif cmd == "weekly":
        weekly(state)
        save(state)
    elif cmd == "refresh":
        # トークンはログに出さず、ワークフローが読むファイルにだけ書く
        with open(os.environ.get("TOKEN_OUT", "new_token.txt"), "w") as fp:
            fp.write(instagram.refresh_token())
    else:
        sys.exit(f"不明なコマンド：{cmd}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "daily")
