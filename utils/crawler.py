"""
ウェブページクローラー

ウェブサイトからページを取得し、解析する
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
import time
import re


class WebCrawler:
    """ウェブページを取得・解析するクラス"""
    
    def __init__(self, config: Dict):
        """
        Args:
            config: 設定辞書
        """
        self.config = config
        self.crawler_config = config.get("crawler", {})
        self.user_agent = self.crawler_config.get("user_agent", "DentalCheckerBot/1.0")
        self.timeout = self.crawler_config.get("timeout", 10)
        self.max_pages = self.crawler_config.get("max_pages", 20)
        
        # 除外パターン
        self.exclude_patterns = self.crawler_config.get("exclude_patterns", [])
        
        # Basic認証情報
        self.auth = None
        auth_config = self.crawler_config.get("auth", {})
        if auth_config.get("username") and auth_config.get("password"):
            self.auth = (auth_config["username"], auth_config["password"])
    
    def set_auth(self, username: str, password: str):
        """Basic認証情報を設定"""
        if username and password:
            self.auth = (username, password)
    
    def is_excluded(self, url: str) -> bool:
        """
        URLが除外パターンにマッチするかチェック
        
        Args:
            url: チェックするURL
        
        Returns:
            除外対象ならTrue、そうでなければFalse
        """
        for pattern in self.exclude_patterns:
            if re.search(pattern, url):
                return True
        return False
    
    def fetch_page(self, url: str) -> Optional[Tuple[str, BeautifulSoup]]:
        """
        ページを取得してBeautifulSoupオブジェクトを返す
        
        Args:
            url: 取得するURL
        
        Returns:
            (テキストコンテンツ, BeautifulSoupオブジェクト) のタプル、失敗時はNone
        """
        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(
                url,
                headers=headers,
                auth=self.auth,
                timeout=self.timeout
            )
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # テキストコンテンツを抽出
            text_content = soup.get_text(separator="\n", strip=True)
            
            return text_content, soup
        
        except requests.exceptions.RequestException as e:
            print(f"ページ取得エラー ({url}): {e}")
            return None
    
    def get_internal_links(self, base_url: str, soup: BeautifulSoup) -> List[str]:
        """
        ページ内の内部リンクを取得
        
        Args:
            base_url: ベースURL
            soup: BeautifulSoupオブジェクト
        
        Returns:
            内部リンクのリスト
        """
        internal_links = set()
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(base_url, href)
            
            # 同じドメインのリンクのみ
            if urlparse(full_url).netloc == base_domain:
                # フラグメント（#）を除去
                full_url = full_url.split("#")[0]
                internal_links.add(full_url)
        
        return list(internal_links)
    
    def crawl_site(self, start_url: str) -> Dict[str, Tuple[str, BeautifulSoup]]:
        """
        サイト全体をクロール
        
        Args:
            start_url: 開始URL
        
        Returns:
            {URL: (テキストコンテンツ, BeautifulSoupオブジェクト)} の辞書
        """
        visited = {}
        to_visit = [start_url]
        excluded_count = 0
        
        while to_visit and len(visited) < self.max_pages:
            url = to_visit.pop(0)
            
            if url in visited:
                continue
            
            # 除外パターンチェック
            if self.is_excluded(url):
                print(f"除外: {url}")
                excluded_count += 1
                continue
            
            print(f"クロール中: {url}")
            result = self.fetch_page(url)
            
            if result:
                text_content, soup = result
                visited[url] = (text_content, soup)
                
                # 内部リンクを取得
                internal_links = self.get_internal_links(url, soup)
                for link in internal_links:
                    if link not in visited and link not in to_visit:
                        to_visit.append(link)
                
                # サーバーに負荷をかけないよう少し待機
                time.sleep(0.5)
        
        if excluded_count > 0:
            print(f"\n除外したページ: {excluded_count}件")
        
        return visited
