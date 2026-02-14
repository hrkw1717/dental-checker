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
            return self._cleanup_ai_response(response.text)
        
        except Exception as e:
            print(f"AI分析エラー: {e}")
            return None
        
    def _cleanup_ai_response(self, text: str) -> str:
        """AI応答から不要な挨拶や前置きを削除"""
        if not text:
            return ""
        
        lines = text.strip().split("\n")
        cleaned_lines = []
        
        # 「問題なし」が含まれる場合はそれだけを返す
        if "問題なし" in text and len(text) < 50:
            return "問題なし"
            
        for line in lines:
            line = line.strip()
            # 行頭が ★ で始まる行、または前の行からの続きと思われる行のみ保持
            if line.startswith("★") or (cleaned_lines and line):
                # 挨拶と思われる文言が含まれる行はスキップ
                greetings = ["指摘いたします", "校正者として", "提示いただいた", "以下の通り", "分析しました"]
                if any(g in line for g in greetings) and not line.startswith("★"):
                    continue
                cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines).strip()
    
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

【指摘形式：厳守】
- 冒頭の「プロの校正者として～」などの挨拶や前置きは【絶対に】書かないでください。
- 指摘がある場合のみ、以下の形式で出力してください。
- 指摘が複数ある場合は、間に必ず【空行】を1行入れてください。
- 行頭は必ず「★ 誤:」で始めてください。

形式：
★ 誤: 「不適切な箇所」 → 正: 「修正案（理由）」

問題がない場合は「問題なし」とだけ回答してください。"""
        
        elif check_type == "natural":
            return f"""以下の歯科クリニックのウェブサイトのテキストを分析し、不自然な日本語表現を指摘してください。

【チェック対象テキスト】
{text}

【指摘形式：厳守】
- 冒頭の挨拶や前置きは【絶対に】書かないでください。
- 不自然な表現が見つかった場合のみ、以下の形式で出力してください。
- 指摘が複数ある場合は、間に必ず【空行】を1行入れてください。
- 行頭は必ず「★ 不自然:」で始めてください。

形式：
★ 不自然: 「該当箇所」 → 改善案: 「より自然な表現」

問題がない場合は「問題なし」とだけ回答してください。"""
        
        elif check_type == "unified":
            # 統合チェッカーの場合は、すでに完成したプロンプトが渡されるためそのまま返す
            return text
        
        else:
            return f"""以下のテキストをチェックしてください：\n\n{text}"""
