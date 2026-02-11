"""
歯科クリニック公開前チェックツール - Streamlit UI

Phase 1: リンク切れ、電話番号、誤字脱字の3つのチェック機能
"""

import streamlit as st
import yaml
from pathlib import Path

from utils.crawler import WebCrawler
from utils.reporter import ExcelReporter
from checkers import LinkChecker, PhoneChecker, TypoChecker


def load_config():
    """設定ファイルを読み込み"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    """メインアプリケーション"""
    
    # ページ設定
    st.set_page_config(
        page_title="クリニック公開前チェック",
        page_icon="📋",
        layout="centered"
    )
    
    # 背景画像を設定
    st.markdown("""
        <style>
        .stApp {
            background-image: url('./app/static/dog.png');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
        }
        .main > div {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            border-radius: 10px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # タイトル
    st.title("📋 クリニック公開前チェック")
    st.markdown("---")
    
    # 設定読み込み
    config = load_config()
    
    # 入力フォーム
    st.subheader("チェック対象情報")
    
    url = st.text_input(
        "🌐 チェック対象URL",
        placeholder="https://example.com",
        help="チェックするウェブサイトのトップページURLを入力してください"
    )
    
    clinic_name = st.text_input(
        "🏥 医院名",
        placeholder="〇〇歯科医院",
        help="レポートファイル名に使用されます"
    )
    
    # 電話番号設定（オプション）
    st.subheader("正しい連絡先情報")
    correct_phone = st.text_input(
        "電話番号",
        placeholder="03-1234-5678",
        help="この番号と照合します（ハイフン付きで入力）"
    )
    
    # Basic認証設定（Secretsから取得、UIには表示しない）
    try:
        auth_id = st.secrets.get("BASIC_AUTH_ID", "")
        auth_pass = st.secrets.get("BASIC_AUTH_PASS", "")
    except Exception:
        auth_id = ""
        auth_pass = ""
    
    st.markdown("---")
    
    # チェック開始ボタン
    if st.button("🚀 チェック開始", type="primary", use_container_width=True):
        
        # 入力チェック
        if not url or not clinic_name:
            st.error("❌ URLと医院名を入力してください")
            return
        
        # 設定を更新
        if correct_phone:
            if "checks" not in config:
                config["checks"] = {}
            if "phone_check" not in config["checks"]:
                config["checks"]["phone_check"] = {}
            config["checks"]["phone_check"]["correct_phone"] = correct_phone
        
        # チェック実行
        try:
            with st.spinner("チェック実行中..."):
                results, checked_urls = run_checks(url, config, auth_id, auth_pass)
            
            # 結果サマリー
            st.success("✅ チェック完了！")
            
            # チェックしたURL一覧を表示
            st.markdown("""
                <div style="background-color: #d4edda; padding: 1rem; border-radius: 5px; margin-bottom: 1rem;">
                    <strong>チェックしたページ:</strong><br>
                    {}
                </div>
            """.format("<br>".join(checked_urls)), unsafe_allow_html=True)
            
            ok_count = sum(1 for r in results if r["status"] == "ok")
            warning_count = sum(1 for r in results if r["status"] == "warning")
            error_count = sum(1 for r in results if r["status"] == "error")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ OK", ok_count)
            with col2:
                st.metric("⚠️ 警告", warning_count)
            with col3:
                st.metric("❌ エラー", error_count)
            
            # Excelレポート生成
            reporter = ExcelReporter(config)
            excel_data = reporter.generate_report(clinic_name, results)
            
            # ダウンロードボタン
            st.download_button(
                label="📥 結果をダウンロード (Excel)",
                data=excel_data,
                file_name=f"{clinic_name}チェック結果.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        except Exception as e:
            st.error(f"❌ エラーが発生しました: {str(e)}")
            st.exception(e)


def run_checks(url: str, config: dict, auth_id: str = "", auth_pass: str = ""):
    """
    チェックを実行
    
    Args:
        url: チェック対象URL
        config: 設定辞書
        auth_id: Basic認証ID
        auth_pass: Basic認証パスワード
    
    Returns:
        (チェック結果のリスト, チェックしたURLのリスト)
    """
    all_results = []
    
    # Basic認証情報
    auth = None
    if auth_id and auth_pass:
        auth = (auth_id, auth_pass)
    
    # クローラー初期化
    crawler = WebCrawler(config)
    if auth:
        crawler.set_auth(auth_id, auth_pass)
    
    # ページ取得
    pages = crawler.crawl_site(url)
    
    if not pages:
        st.error("ページの取得に失敗しました")
        return [], []
    
    # チェックしたURLのリスト
    checked_urls = list(pages.keys())
    
    # チェッカーを初期化（Basic認証情報を渡す）
    checkers = [
        LinkChecker(config, auth=auth),  # 認証情報を渡す
        PhoneChecker(config),
        TypoChecker(config)
    ]
    
    # 各ページをチェック
    progress_bar = st.progress(0)
    total_checks = len(pages) * len(checkers)
    current_check = 0
    
    for page_url, (page_content, soup) in pages.items():
        for checker in checkers:
            if checker.is_enabled():
                results = checker.check(page_url, page_content, soup)
                for result in results:
                    all_results.append(result.to_dict())
            
            current_check += 1
            progress_bar.progress(current_check / total_checks)
    
    progress_bar.empty()
    
    return all_results, checked_urls


if __name__ == "__main__":
    main()
