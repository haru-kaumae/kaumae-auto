# -*- coding: utf-8 -*-
"""Instagram API（Instagramログイン版）で投稿する。

仕様（2026-10-31確認 https://developers.facebook.com/docs/instagram-platform/content-publishing/）：
- プロフェッショナルアカウントが必要。画像は公開URLに置かれたJPEGのみ
- カルーセルは最大20枚、1件として数える。24時間の投稿数に上限あり
- ストーリーズは media_type=STORIES。リンクスタンプを付ける方法は公式に記載なし
"""
import time
import requests
from . import config as C


def _url(path):
    return f"{C.IG_GRAPH}/{C.IG_API_VERSION}/{path}"


def _post(path, **data):
    r = requests.post(_url(path), data=dict(data, access_token=C.IG_ACCESS_TOKEN), timeout=60)
    if not r.ok:
        raise RuntimeError(f"Instagram API エラー {r.status_code}: {r.text[:300]}")
    return r.json()


def _get(path, **params):
    r = requests.get(_url(path), params=dict(params, access_token=C.IG_ACCESS_TOKEN), timeout=60)
    if not r.ok:
        raise RuntimeError(f"Instagram API エラー {r.status_code}: {r.text[:300]}")
    return r.json()


def _wait(container_id, tries=30):
    for _ in range(tries):
        st = _get(container_id, fields="status_code").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"メディアの準備に失敗しました（{st}）")
        time.sleep(5)
    raise RuntimeError("メディアの準備が時間内に終わりませんでした")


def publish_carousel(image_urls, caption):
    children = []
    for u in image_urls:
        c = _post(f"{C.IG_USER_ID}/media", image_url=u, is_carousel_item="true")["id"]
        _wait(c)
        children.append(c)
    parent = _post(f"{C.IG_USER_ID}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)["id"]
    _wait(parent)
    return _post(f"{C.IG_USER_ID}/media_publish", creation_id=parent)["id"]


def publish_story(image_url):
    c = _post(f"{C.IG_USER_ID}/media", image_url=image_url, media_type="STORIES")["id"]
    _wait(c)
    return _post(f"{C.IG_USER_ID}/media_publish", creation_id=c)["id"]


# 取れない指標があっても止まらないよう、1つずつ問い合わせる
METRICS = ["reach", "saved", "likes", "comments", "shares", "profile_visits", "total_interactions"]


def insights(media_id):
    out = {}
    for m in METRICS:
        try:
            data = _get(f"{media_id}/insights", metric=m).get("data", [])
            if data:
                v = data[0].get("values", [{}])[0].get("value", data[0].get("total_value", {}).get("value"))
                out[m] = v
        except RuntimeError:
            out[m] = None
    return out


def refresh_token():
    """60日有効の長期トークンを延長する。"""
    r = requests.get(f"{C.IG_GRAPH}/refresh_access_token",
                     params=dict(grant_type="ig_refresh_token", access_token=C.IG_ACCESS_TOKEN), timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]
