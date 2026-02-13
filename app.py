"""
歯科クリニック公開前チェックツール - Streamlit UI

Phase 1: リンク切れ、電話番号、誤字脱字の3つのチェック機能
"""

import streamlit as st
import yaml
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from utils.crawler import WebCrawler
from utils.reporter import ExcelReporter
from utils.excel_handler import ExcelHandler
from checkers import LinkChecker, PhoneChecker, TypoChecker, NGWordChecker


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
    
    # 背景画像を読み込み（Base64エンコード）
    import base64
    def get_base64_image(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()

    try:
        bg_image = get_base64_image("dog.png")
        st.markdown(f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{bg_image}");
                background-size: contain;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            .main > div {{
                background-color: rgba(255, 255, 255, 0.9);
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass
    
    # タイトル
    st.title("📋 クリニック公開前チェック")
    st.sidebar.caption("最終更新: 2026/02/13 22:45")
    st.markdown("---")
    
    # 設定読み込み
    config = load_config()

    # Basic認証設定（Secretsから取得、UIには表示しない）
    try:
        auth_id = st.secrets.get("BASIC_AUTH_ID", "")
        auth_pass = st.secrets.get("BASIC_AUTH_PASS", "")
    except Exception:
        auth_id = ""
        auth_pass = ""
    
    # Excelファイルのアップロード
    st.subheader("📁 設定ファイルのロード")
    uploaded_file = st.file_uploader(
        "DC-config.xlsxをアップロードしてください",
        type=["xlsx"],
        help="プレミアムプラン用の情報を同期し、チェック対象を取得します"
    )

    url = ""
    clinic_name = ""
    correct_phone = ""

    if uploaded_file:
        # ファイルの保存
        temp_path = "DC-config.xlsx"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Excel操作
        handler = ExcelHandler(temp_path)
        if handler.load():
            with st.spinner("シート間を同期しています..."):
                handler.sync_sheets()
            
            # 情報取得
            url, clinic_name, correct_phone = handler.get_basic_info()
            
            if url and clinic_name:
                st.success(f"✅ 設定を読み込みました: **{clinic_name}**")
                
                # 取得情報の確認用表示
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"🌐 **URL**: {url}")
                with col2:
                    st.info(f"📞 **電話**: {correct_phone}")
                
                # --- URLリストの自動収集と表示 ---
                if "target_urls" not in st.session_state or st.session_state.get("last_uploaded_url") != url:
                    with st.spinner("処理対象のURLを抽出しています..."):
                        pre_crawler = WebCrawler(config)
                        if auth_id and auth_pass:
                            pre_crawler.set_auth(auth_id, auth_pass)
                        pages = pre_crawler.crawl_site(url)
                        st.session_state.target_urls = "\n".join(pages.keys())
                        st.session_state.last_uploaded_url = url

                st.markdown("---")
                st.markdown("**【処理対象のURL一覧】不備があれば正しいURLリストをセットして下さい。**")
                target_urls_input = st.text_area(
                    "URLリスト入力欄",
                    value=st.session_state.target_urls,
                    height=200,
                    label_visibility="collapsed",
                    key="url_editor"
                )
                st.session_state.target_urls = target_urls_input

                # チェック開始ボタン（テキストボックスの下に配置）
                if st.button("🚀 チェック開始", type="primary", use_container_width=True):
                    # 入力チェック
                    url_list = [u.strip() for u in st.session_state.target_urls.split("\n") if u.strip()]
                    if not url_list or not clinic_name:
                        st.error("❌ 医院名と処理対象のURLを入力してください")
                    else:
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
                                # NG表現ルールをExcelから取得
                                ng_rules = handler.get_ng_rules()
                                results, checked_urls = run_checks(url_list, config, auth_id, auth_pass, ng_rules=ng_rules)
                            
                            # 状態を保存
                            st.session_state.results = results
                            st.session_state.checked_urls = checked_urls
                            st.session_state.last_clinic_name = clinic_name
                            
                            # Excelレポート生成
                            reporter = ExcelReporter(config)
                            st.session_state.excel_data = reporter.generate_report(clinic_name, results)
                            
                            st.success("✅ チェック完了！")
                        except Exception as e:
                            st.error(f"❌ エラーが発生しました: {str(e)}")
                            st.exception(e)
            else:
                st.warning("⚠️ Excel内からURLまたは医院名が見つかりませんでした。")
    else:
        st.info("💡 まずは DC-config.xlsx をアップロードしてください。")

    # session_stateの初期化
    if "results" not in st.session_state:
        st.session_state.results = None
    if "checked_urls" not in st.session_state:
        st.session_state.checked_urls = None
    if "excel_data" not in st.session_state:
        st.session_state.excel_data = None
    if "last_clinic_name" not in st.session_state:
        st.session_state.last_clinic_name = None

    # チェック結果が表示可能な場合に表示（ボタンの外側に配置して永続化）
    if st.session_state.results and st.session_state.checked_urls:
        st.markdown("---")
        st.subheader("📊 チェック結果サマリー")
        
        # チェックしたURL一覧を表示
        st.markdown("""
            <div style="background-color: #d4edda; padding: 1rem; border-radius: 5px; margin-bottom: 1rem;">
                <strong>チェックしたページ:</strong><br>
                {}
            </div>
        """.format("<br>".join(st.session_state.checked_urls)), unsafe_allow_html=True)
        
        ok_count = sum(1 for r in st.session_state.results if r["status"] == "ok")
        warning_count = sum(1 for r in st.session_state.results if r["status"] == "warning")
        error_count = sum(1 for r in st.session_state.results if r["status"] == "error")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ OK", ok_count)
        with col2:
            st.metric("⚠️ 警告", warning_count)
        with col3:
            st.metric("❌ エラー", error_count)
        
        # ダウンロードボタン
        if st.session_state.excel_data:
            st.download_button(
                label="📥 結果をダウンロード (Excel)",
                data=st.session_state.excel_data,
                file_name=f"{st.session_state.last_clinic_name}チェック結果.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )


def run_checks(urls: List[str], config: dict, auth_id: str = "", auth_pass: str = "", ng_rules: List[dict] = None):
    """
    チェックを実行
    
    Args:
        urls: チェック対象URLリスト
        config: 設定辞書
        auth_id: Basic認証ID
        auth_pass: Basic認証パスワード
        ng_rules: NG表現ルールのリスト
    
    Returns:
        (チェック結果のリスト, チェックしたURLのリスト)
    """
    all_results = []
    
    # 既存の設定を上書きしないようにコピー
    run_config = config.copy()
    if ng_rules:
        run_config["ng_words_rules"] = ng_rules
    
    # Basic認証情報
    auth = None
    if auth_id and auth_pass:
        auth = (auth_id, auth_pass)
    
    # クローラー初期化
    crawler = WebCrawler(run_config)
    if auth:
        crawler.set_auth(auth_id, auth_pass)
    
    # ページ取得
    pages = {}
    progress_text = st.empty()
    fetch_progress = st.progress(0)
    
    for i, url in enumerate(urls):
        progress_text.text(f"ページの内容を取得中 ({i+1}/{len(urls)}): {url}")
        result = crawler.fetch_page(url)
        if result:
            pages[url] = result
        fetch_progress.progress((i + 1) / len(urls))
    
    fetch_progress.empty()
    progress_text.empty()
    
    if not pages:
        st.error("入力されたURLから有効なページ情報を取得できませんでした")
        return [], []
    
    # チェックしたURLのリスト
    checked_urls = list(pages.keys())
    
    # チェッカーを初期化
    checkers = [
        LinkChecker(run_config, auth=auth),
        PhoneChecker(run_config),
        TypoChecker(run_config),
        NGWordChecker(run_config)
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
