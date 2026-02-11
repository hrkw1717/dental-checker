# リンクチェッカーの誤検知問題と修正

## 🔍 問題の原因

**Basic認証が必要なサイトの内部リンクをチェックする際に、認証情報が渡されていなかった**

### 具体的な状況

```
チェック対象: https://visca-137.sub.jp/itami-ganka.com/
Basic認証: ID=your_id, pass=your_password

ページ内のリンク: https://visca-137.sub.jp/itami-ganka.com/eye/
```

**修正前の動作**:
1. クローラーがBasic認証でページを取得 ✅
2. リンクチェッカーが**認証なし**でリンクをチェック ❌
3. 認証が必要なため、401エラー → 「リンク切れ」と誤判定

---

## ✅ 修正内容

### 1. `LinkChecker` にBasic認証情報を渡せるように修正

**修正前**:
```python
class LinkChecker(BaseChecker):
    def __init__(self, config: dict):
        super().__init__(config)
        self.timeout = config.get("checks", {}).get("link_check", {}).get("timeout", 5)
```

**修正後**:
```python
class LinkChecker(BaseChecker):
    def __init__(self, config: dict, auth: tuple = None):
        super().__init__(config)
        self.timeout = config.get("checks", {}).get("link_check", {}).get("timeout", 5)
        self.auth = auth  # Basic認証情報 (username, password)
```

### 2. リンクチェック時に認証情報を使用

**修正前**:
```python
response = requests.head(url, timeout=self.timeout, allow_redirects=True)
```

**修正後**:
```python
response = requests.head(
    url, 
    timeout=self.timeout, 
    allow_redirects=True,
    auth=self.auth  # Basic認証情報を渡す
)
```

### 3. `app.py` で認証情報を渡すように修正

**修正前**:
```python
checkers = [
    LinkChecker(config),
    PhoneChecker(config),
    TypoChecker(config)
]
```

**修正後**:
```python
# Basic認証情報
auth = None
if auth_id and auth_pass:
    auth = (auth_id, auth_pass)

checkers = [
    LinkChecker(config, auth=auth),  # 認証情報を渡す
    PhoneChecker(config),
    TypoChecker(config)
]
```

---

## 🎯 修正後の動作

```
チェック対象: https://visca-137.sub.jp/itami-ganka.com/
Basic認証: ID=your_id, pass=your_password

ページ内のリンク: https://visca-137.sub.jp/itami-ganka.com/eye/
```

**修正後の動作**:
1. クローラーがBasic認証でページを取得 ✅
2. リンクチェッカーが**認証付き**でリンクをチェック ✅
3. 正常にアクセス可能 → 「OK」と正しく判定 ✅

---

## 📝 影響範囲

- **Basic認証が必要なサイト**: 正しくリンクチェックされるようになる
- **Basic認証が不要なサイト**: 影響なし（`auth=None` として動作）

---

## 🚀 次のステップ

Streamlitアプリを再起動して、再度チェックを実行してください。

今度は正常なリンクが「リンク切れ」と誤判定されることはなくなります。👍
