"""
誤字脱字チェッカー

Gemini API を使用してテキストの誤字脱字をチェック
"""

from typing import List
from bs4 import BeautifulSoup
from .base import BaseChecker, CheckResult
from utils.ai_helper import AIHelper


class TypoChecker(BaseChecker):
    """誤字脱字をチェックするクラス（AI支援）"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.use_ai = config.get("checks", {}).get("typo_check", {}).get("use_ai", True)
        
        # AI機能を使用する場合のみAIHelperを初期化
        if self.use_ai:
            try:
                self.ai_helper = AIHelper(config)
            except ValueError as e:
                print(f"警告 (TypoChecker): {e}")
                self.use_ai = False
                self.ai_helper = None
        else:
            self.ai_helper = None
    
    def check(self, page_url: str, page_content: str, soup: BeautifulSoup) -> List[CheckResult]:
        """
        ページのテキストをAIでチェック
        """
        results = []
        severity = self.get_severity()
        
        # AI機能が無効の場合
        if not self.use_ai or not self.ai_helper:
            results.append(CheckResult(
                page_url=page_url,
                check_name="誤字脱字",
                status="warning",
                details="AI機能が無効です（GEMINI_API_KEYをSecretsまたは環境変数に設定してください）",
                severity=severity
            ))
            return results
        
        # テキストが長すぎる場合は分割（最初の3000文字のみ）
        text_to_check = page_content[:3000]
        if len(page_content) > 3000:
            text_to_check += "\n\n（※ テキストが長いため、最初の3000文字のみチェックしています）"
        
        # AIでチェック
        ai_result = self.ai_helper.check_text(text_to_check, check_type="typo")
        
        if ai_result is None:
            results.append(CheckResult(
                page_url=page_url,
                check_name="誤字脱字",
                status="warning",
                details="AI分析でエラーが発生しました",
                severity=severity
            ))
            return results
        
        # AI応答を解析
        if "問題なし" in ai_result or "問題は見つかりませんでした" in ai_result:
            results.append(CheckResult(
                page_url=page_url,
                check_name="誤字脱字",
                status="ok",
                details="AIチェック: 問題なし",
                severity=severity
            ))
        else:
            # 問題が見つかった場合
            results.append(CheckResult(
                page_url=page_url,
                check_name="誤字脱字",
                status="warning",
                details=f"AIチェック結果:\n{ai_result}",
                severity=severity
            ))
        
        return results
