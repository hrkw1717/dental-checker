"""
電話番号チェッカー

ページ内の電話番号を抽出し、正しい番号と照合
"""

import re
from typing import List
from bs4 import BeautifulSoup
from .base import BaseChecker, CheckResult


class PhoneChecker(BaseChecker):
    """電話番号をチェックするクラス"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        # 正しい電話番号を設定から取得
        self.correct_phone = config.get("checks", {}).get("phone_check", {}).get("correct_phone")
    
    def check(self, page_url: str, page_content: str, soup: BeautifulSoup) -> List[CheckResult]:
        """
        ページ内の電話番号をチェック
        
        Args:
            page_url: ページのURL
            page_content: ページのテキストコンテンツ
            soup: BeautifulSoupオブジェクト
        
        Returns:
            CheckResultのリスト
        """
        results = []
        severity = self.get_severity()
        
        # 正しい電話番号が設定されていない場合
        if not self.correct_phone:
            results.append(CheckResult(
                page_url=page_url,
                check_name="電話番号",
                status="warning",
                details="正しい電話番号が設定されていません（config.yamlで設定してください）",
                severity=severity
            ))
            return results
        
        # tel:リンクをチェック
        tel_links = soup.find_all("a", href=re.compile(r'^tel:'))
        incorrect_tel_links = []
        
        correct_normalized = self._normalize_phone(self.correct_phone)
        
        for link in tel_links:
            tel_number = link["href"].replace("tel:", "")
            tel_normalized = self._normalize_phone(tel_number)
            
            if tel_normalized != correct_normalized:
                incorrect_tel_links.append(tel_number)
        
        # tel:リンクに誤りがある場合
        if incorrect_tel_links:
            results.append(CheckResult(
                page_url=page_url,
                check_name="電話番号",
                status="error",
                details=f"★ 電話番号リンク(tel:)が正しくありません。\n正: {self.correct_phone}\n誤: {', '.join(set(incorrect_tel_links))}",
                severity=severity
            ))
            return results
        
        # 電話番号を抽出（日本の電話番号形式）
        phone_pattern = r'\d{2,4}[-\s]?\d{2,4}[-\s]?\d{4}'
        found_phones = re.findall(phone_pattern, page_content)
        
        if not found_phones:
            results.append(CheckResult(
                page_url=page_url,
                check_name="電話番号",
                status="warning",
                details="電話番号が見つかりませんでした",
                severity=severity
            ))
            return results
        
        # 正規化して比較
        found_normalized = [self._normalize_phone(p) for p in found_phones]
        
        # 正しい番号が含まれているかチェック
        if correct_normalized in found_normalized:
            # 他の番号もチェック
            other_phones = [p for p in found_normalized if p != correct_normalized]
            if other_phones:
                results.append(CheckResult(
                    page_url=page_url,
                    check_name="電話番号",
                    status="warning",
                    details=f"★ 正しい番号({self.correct_phone})が見つかりましたが、他の番号も検出されました。\n他: {', '.join(set(other_phones))}",
                    severity=severity
                ))
            else:
                # ユーザーの要望: 正しいならリストアップしなくてよい
                # 何も追加せず空のリストを返す
                pass
        else:
            results.append(CheckResult(
                page_url=page_url,
                check_name="電話番号",
                status="error",
                details=f"★ 正しい番号({self.correct_phone})が見つかりません。\n検出された番号: {', '.join(set(found_phones))}",
                severity=severity
            ))
        
        return results
    
    def _normalize_phone(self, phone: str) -> str:
        """
        電話番号を正規化（ハイフンとスペースを除去）
        
        Args:
            phone: 電話番号
        
        Returns:
            正規化された電話番号
        """
        return re.sub(r'[-\s]', '', phone)
