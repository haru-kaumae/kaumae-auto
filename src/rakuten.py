# -*- coding: utf-8 -*-
"""楽天ウェブサービス（楽天市場商品検索API）から商品を取る。"""
import random, re, time
import requests
from . import config as C


def _call(params):
    params = dict(params, applicationId=C.RAKUTEN_APP_ID, affiliateId=C.RAKUTEN_AFFILIATE_ID,
                  format="json", formatVersion=2)
    headers = {}
    if C.SITE_URL:
        # 楽天のアプリ設定の「許可するウェブサイト」と照合されるため、公開ページのURLを送る
        headers["Referer"] = C.SITE_URL + "/"
        headers["Origin"] = "/".join(C.SITE_URL.split("/")[:3])
    if C.RAKUTEN_ACCESS_KEY_MODE == "header":
        headers["accessKey"] = C.RAKUTEN_ACCESS_KEY
    else:
        params["accessKey"] = C.RAKUTEN_ACCESS_KEY
    for attempt in range(3):
        r = requests.get(C.RAKUTEN_SEARCH_URL, params=params, headers=headers, timeout=30)
        if r.status_code == 429:          # 呼び出しが多すぎる時は少し待つ
            time.sleep(2 + attempt * 3)
            continue
        if r.status_code >= 400:
            # 原因が分かるように、楽天からの返事（キーは含まない）をログに出す
            raise RuntimeError(f"楽天APIエラー {r.status_code}：{r.text[:500]}")
        return [it.get("Item", it) for it in r.json().get("Items", [])]
    raise RuntimeError("楽天APIの呼び出し回数の上限に達しました")


def _normalize(it):
    return dict(
        itemCode=it.get("itemCode", ""), rawName=it.get("itemName", ""), name=clean_name(it.get("itemName", "")),
        price=int(it.get("itemPrice") or 0), shop=it.get("shopName", ""), itemUrl=it.get("itemUrl", ""),
        affiliateUrl=it.get("affiliateUrl", ""), reviewCount=int(it.get("reviewCount") or 0),
        reviewAverage=float(it.get("reviewAverage") or 0), availability=int(it.get("availability", 1) or 0),
        postageFlag=int(it.get("postageFlag", 1) or 0), image=_image(it))


def _image(it):
    """商品の1枚目の画像URL（楽天の画像サーバー）。大きめのサイズを指定する。"""
    urls = it.get("mediumImageUrls") or []
    u = urls[0] if urls else ""
    if isinstance(u, dict):
        u = u.get("imageUrl", "")
    return re.sub(r"_ex=\d+x\d+", "_ex=600x600", u)


def search_genre(genre_id, page=None):
    """ジャンル内をレビュー件数の多い順に取る（売れ筋の目安）。在庫ありのみ。"""
    page = page or random.randint(1, 3)
    items = _call(dict(genreId=genre_id, sort="-reviewCount", availability=1, hits=30, page=page))
    return [_normalize(i) for i in items]


def lookup(item_code):
    """投稿済みの商品が今も買えるか確認する。"""
    items = _call(dict(itemCode=item_code, hits=1))
    return _normalize(items[0]) if items else None


# 商品名の先頭や途中に入る販促の文言（クーポン、ランキング、期限など）を取り除く
_BRACKETS = re.compile(r"[【\[［（(＼★☆《≪<＜].*?[】\]］）)／★☆》≫>＞]")
_PROMO = re.compile(r"(クーポン|OFF|ＯＦＦ|%|％|ポイント|P\d+倍|倍|SALE|セール|楽天\d*位|ランキング|送料無料|限定|先着|最大|半額|マラソン|スーパーセール|期間|まで|迄|\d+/\d+)")


def clean_name(name):
    s = name
    for _ in range(3):
        s = _BRACKETS.sub(" ", s)
    words = [w for w in re.split(r"\s+", s) if w and not _PROMO.search(w)]
    out = ""
    for w in words:
        if len(out) + len(w) + 1 > 34:
            if not out:             # 区切りのない長い商品名は、販促の文言を除いたものを途中で切る
                out = w[:33] + "…"
            break
        out = (out + " " + w).strip()
    return out or name[:34]
