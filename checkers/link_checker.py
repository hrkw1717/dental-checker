"""
リンク切れチェッカー

ページ内の全リンクをチェックし、リンク切れを検出
"""

import requests
from typing import List
from bs4 import BeautifulSoup
from .base import BaseChecker, CheckResult


class LinkChecker(BaseChecker):
    """リンク切れをチェックするクラス"""
    
    def __init__(self, config: dict, auth: tuple = None):
        super().__init__(config)
        self.timeout = config.get("checks", {}).get("link_check", {}).get("timeout", 5)
        self.auth = auth  # Basic認証情報 (username, password)
    
    def check(self, page_url: str, page_content: str, soup: BeautifulSoup) -> List[CheckResult]:
        """
        ページ内の全リンクをチェック
        
        Args:
            page_url: ページのURL
            page_content: ページのテキストコンテンツ（未使用）
            soup: BeautifulSoupオブジェクト
        
        Returns:
            CheckResultのリスト
        """
        results = []
        severity = self.get_severity()
        
        # 全てのリンクを取得
        links = soup.find_all("a", href=True)
        
        if not links:
            results.append(CheckResult(
                page_url=page_url,
                check_name="リンク切れ",
                status="ok",
                details="チェック対象のリンクがありません",
                severity=severity
            ))
            return results
        
        # 各リンクをチェック
        broken_links = []
        for link in links:
            href = link["href"]
            
            # 相対URLや特殊なURLはスキップ
            if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("tel:"):
                continue
            
            # 絶対URLに変換
            if not href.startswith("http"):
                from urllib.parse import urljoin
                href = urljoin(page_url, href)
            
            # リンクをチェック
            if not self._check_link(href):
                broken_links.append(href)
        
        # 結果を作成
        if broken_links:
            results.append(CheckResult(
                page_url=page_url,
                check_name="リンク切れ",
                status="error",
                details=f"リンク切れを検出: {', '.join(broken_links[:5])}" + 
                        (f" 他{len(broken_links)-5}件" if len(broken_links) > 5 else ""),
                severity=severity
            ))
        else:
            results.append(CheckResult(
                page_url=page_url,
                check_name="リンク切れ",
                status="ok",
                details=f"{len(links)}個のリンクをチェック、問題なし",
                severity=severity
            ))
        
        return results
    
    def _check_link(self, url: str) -> bool:
        """
        リンクが有効かチェック
        
        Args:
            url: チェックするURL
        
        Returns:
            有効ならTrue、無効ならFalse
        """
        try:
            # まずHEADリクエストで試す（高速）
            response = requests.head(
                url, 
                timeout=self.timeout, 
                allow_redirects=True,
                auth=self.auth  # Basic認証情報を渡す
            )
            
            # HEADリクエストが成功した場合
            if response.status_code < 400:
                return True
            
            # HEADリクエストが失敗した場合（405 Method Not Allowedなど）
            # GETリクエストでリトライ
            if response.status_code in [405, 403, 501]:
                try:
                    response = requests.get(
                        url, 
                        timeout=self.timeout, 
                        allow_redirects=True,
                        auth=self.auth  # Basic認証情報を渡す
                    )
                    return response.status_code < 400
                except requests.exceptions.RequestException:
                    return False
            
            return False
        
        except requests.exceptions.RequestException:
            # HEADリクエスト自体が失敗した場合、GETリクエストで再試行
            try:
                response = requests.get(
                    url, 
                    timeout=self.timeout, 
                    allow_redirects=True,
                    auth=self.auth  # Basic認証情報を渡す
                )
                return response.status_code < 400
            except requests.exceptions.RequestException:
                return False
