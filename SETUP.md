# セットアップガイド

## 1. 依存ライブラリのインストール

```bash
cd C:\Users\sbs\Documents\Antigravity\dental-checker
pip install -r requirements.txt
```

---

## 2. Gemini API キーの設定

本ツールは Google Gemini API を使用します。

### 方法1: Streamlit Secrets に設定（推奨）

ローカル実行の場合は、プロジェクト直下の `.streamlit/secrets.toml` に以下のように記述してください：

```toml
GEMINI_API_KEY = "あなたのAPIキー"
```

### 方法2: 環境変数に設定

```bash
# PowerShellの場合
$env:GEMINI_API_KEY="あなたのAPIキー"

# コマンドプロンプトの場合
set GEMINI_API_KEY=あなたのAPIキー
```

---

## 3. 設定ファイルのカスタマイズ

`config.yaml` を編集して、チェック項目を調整できます：

```yaml
api:
  model: "gemini-3-flash"

checks:
  ng_word_check:
    enabled: true
```

---

## 4. アプリケーションの起動

```bash
streamlit run app.py
```

ブラウザで自動的に `http://localhost:8501` が開きます。

---

## 5. 使い方

1. **チェック対象URL** を入力
2. **DC-config.xlsx** をアップロード（「表記規定」シートにNGワードを記載）
3. **チェック開始** ボタンをクリック
4. 結果のExcelファイルをダウンロード

---

## トラブルシューティング

### エラー: `AI機能が無効です（GEMINI_API_KEYを...）`

→ 上記「2. Gemini API キーの設定」を実施してください。
→ 正しく設定してもエラーが出る場合は、Streamlitを一度終了（Ctrl+C）して再起動してください。
