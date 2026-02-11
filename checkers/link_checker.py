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
        
        # ベースドメインを取得（認証情報の送信判定用）
        from urllib.parse import urlparse
        base_domain = urlparse(page_url).netloc
        
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
            if not self._check_link(href, base_domain):
                broken_links.append(href)
        
        # 結果を作成
        if broken_links:
            results.append(CheckResult(
                page_url=page_url,
                check_name="リンク切れ",
                status="error",
                details=f"リンク切れを検出\n" + "\n".join(broken_links[:10]) + 
                        (f"\n他{len(broken_links)-10}件" if len(broken_links) > 10 else ""),
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
    
    def _check_link(self, url: str, base_domain: str) -> bool:
        """
        リンクが有効かチェック
        
        Args:
            url: チェックするURL
            base_domain: チェック対象サイトのドメイン
        
        Returns:
            有効ならTrue、無効ならFalse
        """
        from urllib.parse import urlparse
        target_domain = urlparse(url).netloc
        
        # 同一ドメインの場合のみBasic認証を送信する
        request_auth = self.auth if target_domain == base_domain else None
        
        # ブラウザ風のUser-Agentを設定
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
        
        # タイムアウトを長めに設定
        timeout = 10
        
        try:
            # まずHEADリクエストで試す（高速）
            response = requests.head(
                url, 
                timeout=timeout, 
                allow_redirects=True,
                auth=request_auth,
                headers=headers
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
                        timeout=timeout, 
                        allow_redirects=True,
                        auth=request_auth,
                        headers=headers
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
                    timeout=timeout, 
                    allow_redirects=True,
                    auth=request_auth,
                    headers=headers
                )
                return response.status_code < 400
            except requests.exceptions.RequestException:
                return False
