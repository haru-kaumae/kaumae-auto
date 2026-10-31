# -*- coding: utf-8 -*-
"""投稿前の規約チェック。1つでも問題があれば投稿を止める。

根拠（2026-10-28確認）：
- 楽天アフィリエイトガイドライン https://affiliate.rakuten.co.jp/guideline/rule/
- ステマ規制の対応 https://affiliate.rakuten.co.jp/guideline/stealth_marketing_regulation/
- 消費者庁 ステマQ&A https://www.caa.go.jp/policies/policy/representation/fair_labeling/faq/stealth_marketing/
"""
import re
from .config import PR_LINE

# 使っていない商品の体験談、断定・誇大な表現、効能の表現
BANNED = ["買ってよかった", "使ってみた", "実際に使", "愛用", "リピ買い", "リピート確定", "最安", "絶対", "必ず", "100%", "１００％",
          "日本一", "世界一", "No.1", "ナンバーワン", "効果がある", "効く", "治る", "痩せ", "やせる", "ダイエット", "アンチエイジング",
          "副作用", "完全無料", "今だけ", "急いで"]
ALLOWED_LINK_HOSTS = ("hb.afl.rakuten.co.jp", "a.r10.to", "item.rakuten.co.jp")


def _texts(post):
    out = [post.get("caption", ""), post.get("title", ""), post.get("head", "")]
    for s in post.get("slides", []):
        out += [s.get("title", ""), s.get("sub", ""), s.get("head", ""), s.get("foot", ""), " ".join(s.get("body", []))]
        out += [" ".join(r) for r in s.get("rows", [])]
    out += post.get("body", [])
    return "\n".join(x for x in out if x)


def check(post, products=()):
    problems = []
    if post["kind"] == "feed":
        cap = post["caption"]
        if not cap.startswith(PR_LINE):
            problems.append("キャプション1行目にPR表記がありません")
        if re.search(r"https?://", cap):
            problems.append("キャプションにURLがあります（フィードではURLを書かない方針）")
        if len(cap) > 2200:
            problems.append(f"キャプションが長すぎます（{len(cap)}字）")
        if cap.count("#") > 30:
            problems.append("ハッシュタグが30個を超えています")
        if "確認してください" not in cap or "取得" not in cap:
            problems.append("確認日と注意書きがありません")
        if not 3 <= len(post["slides"]) <= 20:
            problems.append("スライド枚数が範囲外です")
    text = _texts(post)
    for w in BANNED:
        if w in text:
            problems.append(f"禁止表現「{w}」が含まれています")
    for p in products:
        if not p.get("affiliateUrl"):
            problems.append(f"{p['name']}：アフィリエイトリンクがありません")
        elif not any(h in p["affiliateUrl"] for h in ALLOWED_LINK_HOSTS):
            problems.append(f"{p['name']}：楽天以外のリンクです")
        if not p.get("availability"):
            problems.append(f"{p['name']}：在庫がありません")
        if p.get("price", 0) <= 0:
            problems.append(f"{p['name']}：価格を取得できません")
    return problems
