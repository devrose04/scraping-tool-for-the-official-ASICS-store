# アシックス公式ストア巡回ツール

アシックス公式ストアの製品ページを巡回し、商品情報を取得するツールです。

## 機能

- 製品ページの存在確認
- 商品情報（価格、在庫状況）の取得
- 複数のURLパターンに対応
- エラー状態の詳細な記録
- 巡回結果のCSV保存
- 詳細な結果サマリーの表示

## 必要条件

- Python 3.8以上
- Chrome（Seleniumを使用する場合）

## インストール

1. リポジトリをクローン:
```bash
git clone [repository-url]
cd [repository-name]
```

2. 依存パッケージをインストール:
```bash
pip install -r requirements.txt
```

## 使用方法

### 基本的な使用方法

```bash
# 100個のURLを巡回（デフォルト）
python asics_scraper.py --output results.csv

# カスタム設定での使用
python asics_scraper.py --count 100 --min-delay 2.0 --max-delay 5.0 --timeout 30 --retries 3

# 特定のURLリストを使用
python asics_scraper.py --input urls.txt --output results.csv
```

### コマンドライン引数

- `--method`: スクレイピング方法（selenium または requests、デフォルト: requests）
- `--headless`: ブラウザをヘッドレスモードで実行（Seleniumのみ）
- `--input`: URLリストの入力ファイル（1行に1つのURL）
- `--output`: 出力CSVファイルのパス（デフォルト: asics_results.csv）
- `--count`: 入力ファイルがない場合のテストURL数（デフォルト: 100）
- `--base-url`: テストURL生成のためのベースURL（デフォルト: https://www.asics.com）
- `--chromedriver`: chromedriver実行ファイルへのパス（Selenium用）
- `--min-delay`: リクエスト間の最小遅延時間（秒、デフォルト: 2.0）
- `--max-delay`: リクエスト間の最大遅延時間（秒、デフォルト: 5.0）
- `--timeout`: リクエストタイムアウト（秒、デフォルト: 30）
- `--retries`: 失敗時の最大再試行回数（デフォルト: 3）

### 出力CSVの形式

- `url`: 巡回したURL
- `status`: 巡回結果の状態（成功、ページなし、商品情報なし、アクセス拒否、エラー）
- `title`: ページタイトル
- `product_id`: 製品ID
- `price`: 価格
- `availability`: 在庫状況
- `color`: カラーコード
- `category`: カテゴリ
- `timestamp`: 巡回日時

## トラブルシューティング

### よくある問題と解決方法

1. **アクセスが拒否される場合**
   - 遅延時間を長くする（`--min-delay`と`--max-delay`の値を増やす）
   - User-Agentを更新する
   - プロキシを使用する

2. **タイムアウトが発生する場合**
   - タイムアウト時間を延長する（`--timeout`の値を増やす）
   - ネットワーク接続を確認する

3. **商品情報が取得できない場合**
   - Seleniumモードに切り替える（`--method selenium`）
   - ページの読み込み待機時間を調整する

4. **ChromeDriverのエラー**
   - ChromeDriverのバージョンがChromeと一致していることを確認
   - `--chromedriver`オプションで正しいパスを指定

### 推奨設定

安定した巡回のための推奨設定：

```bash
python asics_scraper.py \
  --method requests \
  --min-delay 2.0 \
  --max-delay 5.0 \
  --timeout 30 \
  --retries 3 \
  --output results.csv
```

## 注意事項

- 過度なリクエストは避けてください
- サイトの利用規約を遵守してください
- 大量のURLを巡回する場合は、適切な遅延時間を設定してください

## ライセンス

MIT License