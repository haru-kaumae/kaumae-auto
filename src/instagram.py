# -*- coding: utf-8 -*-
"""Instagram API（Instagramログイン版）で投稿する。

仕様（2026-10-31確認 https://developers.facebook.com/docs/instagram-platform/content-publishing/）：
- プロフェッショナルアカウントが必要。画像は公開URLに置かれたJPEGのみ
- カルーセルは最大20枚、1件として数える。24時間の投稿数に上限あり
- ストーリーズは media_type=STORIES。リンクスタンプを付ける方法は公式に記載なし
"""
import os, time
import requests
from . import config as C


def graph_host():
    """トークンの種類で接続先を決める。Metaの「Unified login」画面で出るトークンは EAA で始まり、
    graph.facebook.com で使う。Instagramログインのトークン（IGで始まる）は graph.instagram.com。"""
    if C.IG_ACCESS_TOKEN.strip().startswith("EAA"):
        return "https://graph.facebook.com"
    return C.IG_GRAPH


def _url(path):
    return f"{graph_host()}/{C.IG_API_VERSION}/{path}"


def _post(path, **data):
    r = requests.post(_url(path), data=dict(data, access_token=C.IG_ACCESS_TOKEN.strip()), timeout=60)
    if not r.ok:
        raise RuntimeError(f"Instagram API エラー {r.status_code}: {r.text[:300]}")
    return r.json()


def _get(path, **params):
    r = requests.get(_url(path), params=dict(params, access_token=C.IG_ACCESS_TOKEN.strip()), timeout=60)
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


def token_info():
    """トークンの有効期限などを調べる（Facebook型のトークンのみ）。"""
    t = C.IG_ACCESS_TOKEN.strip()
    app_id, secret = os.environ.get("META_APP_ID", ""), os.environ.get("META_APP_SECRET", "")
    viewer = f"{app_id}|{secret}" if app_id and secret else t
    r = requests.get(f"https://graph.facebook.com/{C.IG_API_VERSION}/debug_token",
                     params=dict(input_token=t, access_token=viewer), timeout=30)
    return r.json().get("data", r.json())


def refresh_token():
    """長期トークンを延長する。Facebook型（EAA）は META_APP_ID と META_APP_SECRET があれば交換する。"""
    t = C.IG_ACCESS_TOKEN.strip()
    if t.startswith("EAA"):
        app_id, secret = os.environ.get("META_APP_ID", ""), os.environ.get("META_APP_SECRET", "")
        if not (app_id and secret):
            return None
        info = token_info()
        if isinstance(info, dict) and info.get("expires_at") == 0:
            return None                 # システムユーザーのトークンなど、期限のないものは延長不要
        r = requests.get(f"https://graph.facebook.com/{C.IG_API_VERSION}/oauth/access_token",
                         params=dict(grant_type="fb_exchange_token", client_id=app_id, client_secret=secret,
                                     fb_exchange_token=t), timeout=30)
        if not r.ok:
            raise RuntimeError(f"トークン延長エラー {r.status_code}: {r.text[:300]}")
        return r.json()["access_token"]
    r = requests.get(f"{C.IG_GRAPH}/refresh_access_token",
                     params=dict(grant_type="ig_refresh_token", access_token=C.IG_ACCESS_TOKEN.strip()), timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]
