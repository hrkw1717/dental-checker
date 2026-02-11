# セットアップガイド

## 1. 依存ライブラリのインストール

```bash
cd C:\Users\sbs\Documents\Antigravity\dental-checker
pip install -r requirements.txt
```

✅ **完了済み**

---

## 2. Claude API キーの設定

### 方法1: 環境変数に設定（推奨）

```bash
# PowerShellの場合
$env:ANTHROPIC_API_KEY="your_api_key_here"

# コマンドプロンプトの場合
set ANTHROPIC_API_KEY=your_api_key_here
```

### 方法2: .envファイルを使用

1. `.env.example` を `.env` にコピー
2. `.env` ファイルを編集してAPIキーを設定

```
ANTHROPIC_API_KEY=your_actual_api_key
```

---

## 3. 設定ファイルのカスタマイズ

`config.yaml` を編集して、チェック項目を調整できます：

```yaml
checks:
  phone_check:
    enabled: true
    correct_phone: "03-1234-5678"  # 正しい電話番号を設定
```

---

## 4. アプリケーションの起動

```bash
streamlit run app.py
```

ブラウザで自動的に `http://localhost:8501` が開きます。

---

## 5. 使い方

1. **チェック対象URL** を入力（例: `https://example.com`）
2. **医院名** を入力（例: `テスト歯科医院`）
3. **電話番号** を入力（オプション、config.yamlで設定済みの場合は不要）
4. **Basic認証** が必要な場合は、IDとパスワードを入力
5. **チェック開始** ボタンをクリック
6. 結果が表示されたら、**結果をダウンロード** ボタンでExcelファイルを保存

---

## トラブルシューティング

### エラー: `ANTHROPIC_API_KEY環境変数が設定されていません`

→ 上記「2. Claude API キーの設定」を実施してください

### エラー: `ページの取得に失敗しました`

→ URLが正しいか確認してください
→ Basic認証が必要な場合は、IDとパスワードを入力してください

### 動作が遅い

→ AI機能（誤字脱字チェック）を使用しているため、ページ数が多いと時間がかかります
→ `config.yaml` で `typo_check: enabled: false` にすると高速化できます

---

## Phase 2以降の拡張

現在は3つのチェック機能のみですが、今後以下の機能を追加予定：

- 住所チェック
- 画像存在確認
- メタタグチェック
- 表記ゆれチェック
- NGワードチェック

新しいチェック機能は `checkers/` ディレクトリに追加していきます。
