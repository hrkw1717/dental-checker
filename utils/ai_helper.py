"""
Claude API連携ヘルパー

Claude APIを使用したテキスト分析機能を提供
"""

import os
import streamlit as st
from typing import Optional
import google.generativeai as genai


class AIHelper:
    """Gemini APIを使用したAI支援機能"""
    
    def __init__(self, config: dict):
        """
        Args:
            config: 設定辞書
        """
        self.config = config
        api_config = config.get("api", {})
        
        # APIキーの取得候補
        key_names = ["GEMINI_API_KEY", "GOOGLE_API_KEY"]
        api_key = None
        
        # 1. st.secrets から取得
        try:
            for kn in key_names:
                if kn in st.secrets:
                    api_key = st.secrets[kn]
                    break
            
            # セクション分けされている場合([gemini] api_key = "...")
            if not api_key:
                if "gemini" in st.secrets and "api_key" in st.secrets["gemini"]:
                    api_key = st.secrets["gemini"]["api_key"]
                elif "google" in st.secrets and "api_key" in st.secrets["google"]:
                    api_key = st.secrets["google"]["api_key"]
        except Exception:
            # st.secrets が使えない環境（通常実行時など）
            pass
            
        # 2. 環境変数 から取得
        if not api_key:
            for kn in key_names:
                api_key = os.environ.get(kn)
                if api_key:
                    break
            
        if not api_key:
            raise ValueError(
                "Gemini APIキーが見つかりません。\n"
                "以下のいずれかを設定してください：\n"
                "1. Streamlit Secrets (GEMINI_API_KEY または GOOGLE_API_KEY)\n"
                "2. 環境変数 (GEMINI_API_KEY または GOOGLE_API_KEY)"
            )
        
        genai.configure(api_key=api_key)
        self.model_name = api_config.get("model", "gemini-2.0-flash")
        self.model = genai.GenerativeModel(self.model_name)
    
    def check_text(self, text: str, check_type: str = "typo") -> Optional[str]:
        """
        テキストをAIでチェック
        
        Args:
            text: チェック対象のテキスト
            check_type: チェックタイプ ("typo", "natural", "consistency"など)
        
        Returns:
            AIの分析結果、エラー時はNone
        """
        try:
            # チェックタイプに応じたプロンプトを生成
            prompt = self._get_prompt(text, check_type)
            
            response = self.model.generate_content(prompt)
            
            return response.text
        
        except Exception as e:
            print(f"AI分析エラー: {e}")
            return None
    
    def _get_prompt(self, text: str, check_type: str) -> str:
        """チェックタイプに応じたプロンプトを生成"""
        import datetime
        now = datetime.datetime.now()
        today_str = now.strftime("%Y年%m月%d日")
        
        if check_type == "typo":
            return f"""あなたはプロの校正者です。歯科クリニックのWebサイトを本日（{today_str}）の視点で精査してください。

【重要：日付の扱い】
- 現在は **2026年** です。
- テキスト内に「2025年の予定」や「2025年開催」といった、すでに過ぎた時期を「未来形」で表現している箇所があれば、それは古い情報（更新漏れ）として指摘してください。
- 2025年の出来事が「過去のこと」として書かれている場合は問題ありません。

【チェック対象テキスト】
{text}

【指摘形式】
問題が見つかった場合のみ、冒頭の挨拶などは一切含めず、以下の形式で指摘してください（指摘が複数ある場合は、間に必ず1行の【空行】を入れてください）：
★ 誤: 「不適切な箇所」 → 正: 「修正案（理由）」

問題がない場合は「問題なし」とだけ回答してください。"""
        
        elif check_type == "natural":
            return f"""以下の歯科クリニックのウェブサイトのテキストを分析し、不自然な日本語表現を指摘してください。

【チェック対象テキスト】
{text}

【指摘形式】
不自然な表現が見つかった場合のみ、冒頭の挨拶などは一切含めず、以下の形式で指摘してください（指摘が複数ある場合は、間に必ず1行の【空行】を入れてください）：
★ 不自然: 「該当箇所」 → 改善案: 「より自然な表現」

問題がない場合は「問題なし」とだけ回答してください。"""
        
        else:
            return f"""以下のテキストをチェックしてください：\n\n{text}"""
