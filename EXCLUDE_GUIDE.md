# 除外機能の使い方

## 概要

ニュースやブログなど、チェック対象から除外したいページを設定できます。

---

## 設定方法

`config.yaml` の `exclude_patterns` に除外したいURLパターンを追加します。

### デフォルト設定

```yaml
crawler:
  exclude_patterns:
    - "/news/"           # ニュース
    - "/blog/"           # ブログ
    - "/category/"       # カテゴリページ
    - "/tag/"            # タグページ
    - "/author/"         # 著者ページ
    - "/\\d{4}/\\d{2}/"  # 日付形式のURL（例: /2024/01/）
    - "\\?p=\\d+"        # WordPressの投稿ID（例: ?p=123）
    - "/feed/"           # RSSフィード
    - "/wp-admin/"       # WordPress管理画面
    - "/wp-login"        # WordPressログイン
```

---

## パターンの書き方

### 基本的な文字列マッチ

```yaml
exclude_patterns:
  - "/news/"     # URLに /news/ が含まれるページを除外
  - "/blog/"     # URLに /blog/ が含まれるページを除外
```

**例**:
- ✅ 除外: `https://example.com/news/article-1`
- ✅ 除外: `https://example.com/blog/post-123`
- ❌ 対象: `https://example.com/about`

### 正規表現を使った高度なマッチ

```yaml
exclude_patterns:
  - "/\\d{4}/\\d{2}/"  # 日付形式（例: /2024/01/）
  - "\\?p=\\d+"        # クエリパラメータ（例: ?p=123）
  - "/news/.*\\.html$" # /news/配下の.htmlファイル
```

**例**:
- ✅ 除外: `https://example.com/2024/01/article`
- ✅ 除外: `https://example.com/post?p=456`
- ✅ 除外: `https://example.com/news/article.html`

---

## カスタマイズ例

### 例1: 特定のディレクトリを除外

```yaml
exclude_patterns:
  - "/news/"
  - "/blog/"
  - "/column/"
  - "/case-study/"
```

### 例2: 日付形式のURLを除外

```yaml
exclude_patterns:
  - "/\\d{4}/"           # 年（例: /2024/）
  - "/\\d{4}/\\d{2}/"    # 年月（例: /2024/01/）
  - "/\\d{4}/\\d{2}/\\d{2}/" # 年月日（例: /2024/01/15/）
```

### 例3: 特定のファイル拡張子を除外

```yaml
exclude_patterns:
  - "\\.pdf$"    # PDFファイル
  - "\\.zip$"    # ZIPファイル
  - "\\.xml$"    # XMLファイル（サイトマップなど）
```

### 例4: クエリパラメータを含むURLを除外

```yaml
exclude_patterns:
  - "\\?.*"      # 全てのクエリパラメータ
  - "\\?p=\\d+"  # WordPressの投稿ID
  - "\\?cat="    # カテゴリパラメータ
```

---

## 動作確認

除外されたページは、実行時にコンソールに表示されます：

```
クロール中: https://example.com/
除外: https://example.com/news/article-1
除外: https://example.com/blog/post-123
クロール中: https://example.com/about

除外したページ: 2件
```

---

## よくある質問

### Q: 除外パターンを無効にしたい

A: `exclude_patterns` を空にします：

```yaml
exclude_patterns: []
```

### Q: 特定のニュース記事だけチェックしたい

A: 除外パターンから `/news/` を削除します。

### Q: 正規表現が分からない

A: 基本的な文字列マッチで十分です。以下のパターンをコピーして使ってください：

```yaml
exclude_patterns:
  - "/news/"
  - "/blog/"
  - "/category/"
```

---

## 注意事項

- **バックスラッシュのエスケープ**: YAMLファイルでは `\` を `\\` と書く必要があります
  - 正: `"/\\d{4}/"`
  - 誤: `"/\d{4}/"`

- **大文字小文字**: パターンマッチは大文字小文字を区別します
  - `/News/` と `/news/` は別物

- **部分マッチ**: パターンはURL全体に対して部分マッチします
  - `/news/` は `https://example.com/news/article` にマッチ
