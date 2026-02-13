"""
リンク切れチェッカー

ページ内の全リンクをチェックし、リンク切れを検出
"""

import requests
import time
from typing import List, Dict, Tuple
from bs4 import BeautifulSoup
from .base import BaseChecker, CheckResult


class LinkChecker(BaseChecker):
    """リンク切れをチェックするクラス"""
    
    def __init__(self, config: dict, auth: tuple = None):
        super().__init__(config)
        self.timeout = config.get("checks", {}).get("link_check", {}).get("timeout", 5)
        self.auth = auth  # Basic認証情報 (username, password)
        self._cache = {}  # チェック済みURLのキャッシュ {url: (is_valid, status_code)}
    
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
        broken_links_info = []
        for link in links:
            href = link["href"]
            
            # 相対URLや特殊なURL、または特定のSNSリンクはスキップ
            if (href.startswith("#") or href.startswith("javascript:") or 
                href.startswith("mailto:") or href.startswith("tel:")):
                continue
            
            # SNSリンクを除外 (Instagram, X, Facebook)
            sns_domains = ["instagram.com", "facebook.com", "twitter.com", "x.com"]
            if any(domain in href.lower() for domain in sns_domains):
                continue
            
            # 絶対URLに変換
            if not href.startswith("http"):
                from urllib.parse import urljoin
                href = urljoin(page_url, href)
            
            # リンクをチェック
            is_valid, status_code = self._check_link(href, base_domain)
            if not is_valid:
                broken_links_info.append(f"{href} (Status: {status_code})")
        
        # 結果を作成
        if broken_links_info:
            results.append(CheckResult(
                page_url=page_url,
                check_name="リンク切れ",
                status="error",
                details=f"リンク切れを検出\n" + "\n".join(broken_links_info[:10]) + 
                        (f"\n他{len(broken_links_info)-10}件" if len(broken_links_info) > 10 else ""),
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
    
    def _check_link(self, url: str, base_domain: str) -> Tuple[bool, str]:
        """
        リンクが有効かチェック
        
        Args:
            url: チェックするURL
            base_domain: チェック対象サイトのドメイン
        
        Returns:
            (有効ならTrue、ステータスコードまたはエラーメッセージ)
        """
        # 1. キャッシュチェック
        if url in self._cache:
            return self._cache[url]

        from urllib.parse import urlparse
        target_domain = urlparse(url).netloc
        
        # ドメイン正規化（www. を除外して比較）
        def normalize_domain(d):
            return d.replace("www.", "")
        
        is_internal = normalize_domain(target_domain) == normalize_domain(base_domain)
        
        # 2. 外部ドメインの場合のみ待機（レート制限回避）
        if not is_internal:
            time.sleep(1.0)
        
        # 同一ドメインの場合のみBasic認証を送信する
        request_auth = self.auth if is_internal else None
        
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
            
            # 200〜399なら成功とみなす
            if 200 <= response.status_code < 400:
                res = (True, str(response.status_code))
                self._cache[url] = res
                return res
            
            # HEADが失敗した場合（ステータスコードを問わず）、GETで再試行
            try:
                response = requests.get(
                    url, 
                    timeout=timeout, 
                    allow_redirects=True,
                    auth=request_auth,
                    headers=headers,
                    stream=True
                )
                if 200 <= response.status_code < 400:
                    res = (True, str(response.status_code))
                else:
                    res = (False, str(response.status_code))
                self._cache[url] = res
                return res
            except requests.exceptions.RequestException as e:
                res = (False, f"GET Error: {type(e).__name__}")
                self._cache[url] = res
                return res
            
        except requests.exceptions.RequestException as e:
            # HEAD自体が例外で失敗した場合、GETで再試行
            try:
                response = requests.get(
                    url, 
                    timeout=timeout, 
                    allow_redirects=True,
                    auth=request_auth,
                    headers=headers,
                    stream=True
                )
                if 200 <= response.status_code < 400:
                    res = (True, str(response.status_code))
                else:
                    res = (False, str(response.status_code))
                self._cache[url] = res
                return res
            except requests.exceptions.RequestException as e2:
                res = (False, f"Error: {type(e2).__name__}")
                self._cache[url] = res
                return res
