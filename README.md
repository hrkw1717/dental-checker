# 歯科クリニック公開前チェックツール

## 概要
歯科クリニックのウェブサイト公開前に、30項目のチェックポイントを自動/半自動でチェックし、結果をExcelファイルに出力するツールです。

## 主な機能
- 誤字脱字チェック
- リンク切れチェック
- 電話番号・住所の正確性チェック
- 不自然な日本語表現の検出
- NG情報の混入チェック
- 表記ゆれチェック
- チェック結果のExcel出力

## 開発フェーズ
### Phase 1: MVP（最小機能版）
- リンク切れチェック
- 電話番号チェック
- 誤字脱字チェック（AI支援）
- 基本的なExcel出力

### Phase 2: 基本チェック拡充
- 住所チェック
- 画像の存在確認
- メタタグチェック
- 表記ゆれチェック
- NGワードチェック

### Phase 3: AI高度化
- 不自然な日本語表現
- 文脈的な誤字
- 他院情報の混入チェック
- 文章の読みやすさ
- トーンの一貫性

### Phase 4: 完成版
- 残りの規定書ベースのチェック項目（15項目程度）

## 技術スタック
- **UI**: Streamlit
- **スクレイピング**: requests, beautifulsoup4
- **AI**: Claude API (Anthropic)
- **Excel出力**: openpyxl, pandas
- **テキスト処理**: re, difflib

## 使い方
```bash
# 依存ライブラリのインストール
pip install -r requirements.txt

# アプリケーション起動
streamlit run app.py
```

ブラウザで `http://localhost:8501` にアクセスし、チェック対象URLと医院名を入力して実行します。

### 社内共有（他のPCからアクセスする）
同じ社内LAN内の他のPC（山田さんのPCなど）からアクセスする方法については、[アプリ共有ガイド (SHARING.md)](file:///c:/Users/sbs/Documents/Antigravity/dental-checker/SHARING.md) を参照してください。

## プロジェクト構成
```
dental-checker/
├── README.md              # このファイル
├── requirements.txt       # 依存ライブラリ
├── config.yaml           # 設定ファイル
├── app.py                # Streamlit UI
├── checkers/             # チェックモジュール
│   ├── __init__.py
│   ├── base.py           # 基底クラス
│   ├── link_checker.py   # リンクチェック
│   ├── phone_checker.py  # 電話番号チェック
│   └── typo_checker.py   # 誤字脱字チェック
└── utils/                # ユーティリティ
    ├── __init__.py
    ├── crawler.py        # ページ取得
    ├── reporter.py       # Excel生成
    └── ai_helper.py      # Claude API連携
```

## 設計思想
- **段階的実装**: Phase 1から順に機能を追加
- **モジュール設計**: 新しいチェック項目を簡単に追加可能
- **シンプルなUI**: 校正者が迷わず使える
- **拡張性**: 将来的な機能追加に対応

## ライセンス
社内利用
