# かうまえメモ 自動運用

楽天市場の商品を選び、Instagramに毎日自動で投稿する仕組みです。GitHub Actions（無料枠）で動き、費用は0円を想定しています。

## 毎日やること（自動）

| いつ（日本時間） | 内容 |
|---|---|
| 毎日 13:00 | 毎日カルーセルとリールを1本ずつ（別のジャンル）：今月のジャンルから、楽天APIでレビューの多い商品を2つ選ぶ（レビュー300件以上・★4.2以上・在庫あり・90日以内に紹介していない・ショップが重ならない）。「買う前の3チェック」のカルーセル（6〜7枚）とキャプションを作る |
| 毎日 13:00 | ストーリーズ：最新の投稿のチェックを1つずつ紹介し、プロフィールのリンクへ誘導 |
| 投稿の直前 | 在庫と価格をもう一度確認。在庫切れ、または価格が10%以上変わっていたら投稿しない |
| 毎週日曜 21:00 | 紹介した商品の在庫確認（売り切れはリンク一覧で「販売終了の可能性」と表示）、投稿の数字を `state/metrics.csv` に記録 |
| 毎月1日・15日 | Instagramのトークン（60日有効）を延長 |

**規約チェック（`src/compliance.py`）**：次のどれかに当たる投稿は自動で止まり、GitHubのIssueで知らせます（GitHubからメールが届きます）。
- PR表記がない、キャプションにURLがある、確認日と注意書きがない
- 「買ってよかった」「実際に使」「最安」「絶対」「ダイエット」などの禁止表現（商品名に含まれる商品は最初から選ばない）
- アフィリエイトリンクがない、楽天以外のリンク、在庫切れ、価格が取れない

**プロフィールのリンク先**：`docs/index.html` が「紹介した商品の一覧（楽天市場）」ページとしてGitHub Pagesに自動で公開されます。リンクまとめサービスは不要です。

## 自動にできないこと

- アカウント登録、本人確認、規約への同意、APIキーやトークンの発行（下の準備）
- ストーリーズのリンクスタンプ（Instagram APIに方法の記載がないため、プロフィールのリンクへ誘導）
- 楽天アフィリエイトの成果レポートの取得（公開APIが見つからないため、月1回レポート画面で確認）
- コメント・DMへの返信

---

## 一度だけの準備（合計1〜2時間）

各サービスの画面の名前は変わることがあります。見当たらない場合は近い名前の項目を探してください。

### 1. 楽天アフィリエイトとInstagram（30分）

運用キットの「09 リンク設定手順書」の1と2、「Instagram側の準備」を行います。Instagramは **プロフェッショナルアカウント**（クリエイター）にしてください。APIでの投稿にはプロアカウントが必要です。

### 2. GitHubのリポジトリ（15分）

1. [GitHub](https://github.com/) のアカウントを作る（無料）
2. 新しいリポジトリを作る。名前：`kaumae-auto`、公開設定：**Public**（無料でGitHub Pagesを使い、画像を公開URLに置くため。キーやトークンはコードに含めません）
3. [Connect GitHub](https://claude.ai/connect-github) からClaudeとGitHubをつなぎ、`kaumae-auto` にClaudeのGitHubアプリを入れる
4. リポジトリ名（例：`haru/kaumae-auto`）をスレッドで教えてください。こちらでコードを入れます

### 3. GitHub Pages（5分）

1. リポジトリの Settings → Pages → Source を「Deploy from a branch」、Branch を `main`、フォルダを `/docs` にして保存
2. 表示されたURL（例：`https://haru.github.io/kaumae-auto`）を控える
3. Settings → Secrets and variables → Actions → **Variables** タブ → New repository variable：名前 `SITE_URL`、値に上のURL

### 4. 楽天ウェブサービスのキー（15分）

楽天ウェブサービスは2026年に新しい仕様（新ドメイン・Access Key）になりました。

1. [楽天ウェブサービス](https://webservice.rakuten.co.jp/) を開き、楽天IDでログイン
2. 「REGISTER A NEW APPLICATION」（アプリ登録）を開く
3. アプリ名：`kaumae-auto`、アプリURL：上の `SITE_URL`、許可するウェブサイト（Allowed websites）：`haru.github.io` のようにPagesのドメイン
4. 発行された **Application ID** と **Access Key** を控える
5. **アフィリエイトID** を控える（楽天ウェブサービスのアプリ情報画面、または楽天アフィリエイトの設定に表示されます。場所は要確認）

### 5. Instagram APIのトークン（30分）

1. [Meta for Developers](https://developers.facebook.com/) にログインし、開発者として登録
2. 「アプリを作成」→ ユースケースで **Instagram API**（Instagramログインを使う方）を選ぶ
3. 権限に `instagram_business_basic`、`instagram_business_content_publish`、`instagram_business_manage_insights` を追加
4. 「アクセストークンを生成」でご自身のInstagramアカウントを追加・ログインし、**アクセストークン**（長期）と **InstagramユーザーID** を控える

自分のアカウントにだけ投稿する場合、アプリ審査なしの開発モードで使える想定ですが、Meta側の条件は要確認です。

### 6. GitHubのSecretsに入れる（10分）

リポジトリの Settings → Secrets and variables → Actions → **Secrets** タブ → New repository secret で、次の6つを入れます。値はこちらには送らないでください。

| 名前 | 値 |
|---|---|
| `RAKUTEN_APP_ID` | 楽天のApplication ID |
| `RAKUTEN_ACCESS_KEY` | 楽天のAccess Key |
| `RAKUTEN_AFFILIATE_ID` | 楽天のアフィリエイトID |
| `IG_USER_ID` | InstagramユーザーID |
| `IG_ACCESS_TOKEN` | Instagramのアクセストークン |
| `GH_PAT` | GitHubの個人用アクセストークン（Fine-grained、対象は `kaumae-auto` だけ、権限は Secrets：Read and write）。トークン延長の自動保存に使います。有効期限が来たら作り直してください |

### 7. 仕上げ（10分）

1. 楽天アフィリエイトの「サイト情報の登録」に、`SITE_URL`（商品一覧ページ）も追加する
2. Instagramのプロフィールのリンクに `SITE_URL` を入れる（タイトル：紹介した商品｜楽天市場）
3. リポジトリの Actions →「daily」→「Run workflow」で `dry_run` を `1` のまま実行。投稿はされず、`docs/media/` に画像ができて、商品一覧ページが公開されることを確認する
4. 問題なければ、そのままにしておけば毎日13:00から自動で投稿されます

## 止め方・変え方

- 一時停止：Settings → Variables に `DRY_RUN` = `1` を追加（画像と原稿だけ作り、投稿しない）。再開は `0` に
- 完全に止める：Actions → 各ワークフロー →「Disable workflow」
- 投稿の曜日、ジャンル、選ぶ条件、チェック文、ハッシュタグ：`src/config.py`
- 禁止表現の追加：`src/compliance.py` の `BANNED`

## ファイル

| 場所 | 内容 |
|---|---|
| `src/rakuten.py` | 楽天市場商品検索API |
| `src/compose.py` | 商品選定と原稿 |
| `src/compliance.py` | 規約チェック |
| `src/slides.py` `src/design.py` | 画像（JPEG、1080×1350／1080×1920） |
| `src/instagram.py` | 投稿、数字の取得、トークン延長 |
| `src/site.py` | 商品一覧ページ |
| `state/posts.json` | 投稿の記録（何をいつ紹介したか） |
| `state/metrics.csv` | 毎週の数字 |
| `tests/test_offline.py` | ネットなしの動作確認 `python -m tests.test_offline` |

## 素材のライセンス

- 表紙の背景写真：`assets/bg/`。Openverse から CC0・パブリックドメインの写真だけを `tools/fetch_backgrounds.py` で取得し、作者・出どころ・ライセンスを `assets/bg/credits.json` に記録。人物の顔・酒類・古い白黒写真は目視で除外（2026-11-04）
- フォント：`assets/fonts/`（M PLUS Rounded 1c、SIL Open Font License）
- リールのBGM：`assets/bgm/`。`tools/make_bgm.py` で合成したオリジナル曲
- 商品画像：楽天市場の各ショップの画像を、文字入れ・切り抜きなしで使用（楽天アフィリエイトのガイドラインに従う）
