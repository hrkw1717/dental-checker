"""
基底チェッカークラス

全てのチェッカーの基底となる抽象クラス
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any


class CheckResult:
    """チェック結果を格納するクラス"""
    
    def __init__(
        self,
        page_url: str,
        check_name: str,
        status: str,  # "ok", "warning", "error"
        details: str = "",
        severity: str = "medium"  # "critical", "high", "medium", "low"
    ):
        self.page_url = page_url
        self.check_name = check_name
        self.status = status
        self.details = details
        self.severity = severity
    
    def to_dict(self) -> Dict[str, str]:
        """辞書形式に変換"""
        return {
            "page_url": self.page_url,
            "check_name": self.check_name,
            "status": self.status,
            "details": self.details,
            "severity": self.severity
        }


class BaseChecker(ABC):
    """全チェッカーの基底クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: 設定辞書
        """
        self.config = config
        self.check_name = self.__class__.__name__.replace("Checker", "")
    
    @abstractmethod
    def check(self, page_url: str, page_content: str, soup) -> List[CheckResult]:
        """
        チェックを実行
        
        Args:
            page_url: ページのURL
            page_content: ページのテキストコンテンツ
            soup: BeautifulSoupオブジェクト
        
        Returns:
            CheckResultのリスト
        """
        raise NotImplementedError
    
    def is_enabled(self) -> bool:
        """このチェッカーが有効かどうか"""
        check_key = self.check_name.lower() + "_check"
        if check_key in self.config.get("checks", {}):
            return self.config["checks"][check_key].get("enabled", True)
        return True
    
    def get_severity(self) -> str:
        """このチェッカーの重要度を取得"""
        check_key = self.check_name.lower() + "_check"
        if check_key in self.config.get("checks", {}):
            return self.config["checks"][check_key].get("severity", "medium")
        return "medium"
