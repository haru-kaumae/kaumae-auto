# -*- coding: utf-8 -*-
"""プロフィールのリンク先になる「紹介した商品の一覧」ページ（GitHub Pages）を作る。"""
import html, os

PAGE = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>かうまえメモ｜紹介した商品（楽天市場）</title>
<style>
:root{{--bg:#f2f4f1;--card:#fff;--ink:#1e2a2c;--muted:#5f6d6a;--teal:#1f6f68;--line:#d3dbd8}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151b1c;--card:#1d2526;--ink:#e5ece9;--muted:#9aa9a5;--teal:#5fb8ae;--line:#2f3a3b}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.7 "Hiragino Sans","Yu Gothic",sans-serif}}
main{{max-width:560px;margin:0 auto;padding:24px 16px 64px}}
h1{{font-size:22px;margin:0 0 4px}} .pr{{font-size:13px;color:var(--muted);margin:0 0 20px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:0 0 14px}}
h2{{font-size:15px;margin:0 0 8px}} .d{{font-size:12px;color:var(--muted)}}
a.b{{display:block;margin:8px 0 0;padding:10px 12px;border-radius:8px;background:var(--teal);color:#fff;text-decoration:none;font-size:14px}}
.off{{font-size:13px;color:var(--muted);margin:8px 0 0}}
</style></head><body><main>
<h1>かうまえメモ｜紹介した商品</h1>
<p class="pr">PR｜このページのリンクは楽天アフィリエイト広告です。リンク先はすべて楽天市場です。価格・在庫はリンク先で確認してください。</p>
{sections}
</main></body></html>"""


def build(state, outdir):
    secs = []
    for p in sorted((x for x in state["posts"] if x.get("status") == "posted"), key=lambda x: x["date"], reverse=True):
        links = []
        for it in p["products"]:
            name = html.escape(it["name"])
            if it.get("soldOut"):
                links.append(f'<p class="off">{name}：販売終了または在庫切れの可能性があります</p>')
            else:
                links.append(f'<a class="b" href="{html.escape(it["affiliateUrl"])}" rel="sponsored noopener">{name}（楽天市場）</a>')
        secs.append(f'<section><span class="d">{p["date"]}の投稿</span><h2>{html.escape(p["title"])}</h2>{"".join(links)}</section>')
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "index.html"), "w", encoding="utf-8") as fp:
        fp.write(PAGE.format(sections="\n".join(secs) or "<p>まだ投稿はありません。</p>"))
