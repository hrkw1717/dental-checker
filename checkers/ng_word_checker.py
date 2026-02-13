"""
NG表現チェッカー

Gemini APIを使用して、指定されたルールに基づきテキストのNG表現（本文・メタデータ）をチェック
"""

from typing import List
import json
from bs4 import BeautifulSoup
from .base import BaseChecker, CheckResult
from utils.ai_helper import AIHelper


class NGWordChecker(BaseChecker):
    """NG表現をチェックするクラス（AI支援）"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.enabled = config.get("checks", {}).get("ng_word_check", {}).get("enabled", True)
        
        # NGリストの取得（config.yaml または外部から渡される）
        self.ng_rules = config.get("ng_words_rules", [])
        
        if self.enabled:
            try:
                self.ai_helper = AIHelper(config)
            except ValueError as e:
                print(f"警告 (NGWordChecker): {e}")
                self.enabled = False
                self.ai_helper = None
        else:
            self.ai_helper = None
    
    def check(self, page_url: str, page_content: str, soup: BeautifulSoup) -> List[CheckResult]:
        """
        ページのテキストとメタデータをチェック
        """
        results = []
        severity = self.get_severity()

        # AI機能が無効またはキー未設定の場合
        if not self.enabled or not self.ai_helper:
            results.append(CheckResult(
                page_url=page_url,
                check_name="NG表現",
                status="warning",
                details="AI機能が無効です（GEMINI_API_KEYをSecretsまたは環境変数に設定してください）",
                severity=severity
            ))
            return results
            
        if not self.ng_rules:
            return results
        
        # 1. メタデータの抽出
        metadata = self._extract_metadata(soup)
        
        # 2. プロンプト用にルールを文字列化
        rules_text = "\n".join([f"- {r.get('bad')} ⇒ {r.get('good')}" for r in self.ng_rules])
        
        # 3. 本文とメタデータを結合してチェック
        combined_text = f"【ページ本文】\n{page_content[:3000]}\n\n【メタデータ】\n{json.dumps(metadata, ensure_ascii=False, indent=2)}"
        
        prompt = f"""以下の歯科クリニックのウェブサイトの内容（本文およびメタデータ）を分析し、指定された【NG表現リスト】に該当する箇所があればすべて指摘してください。

動詞などの「活用（例：諦めた、諦めない、諦めれば）」についても、文脈から判断して適切に指摘に含めてください。

【NG表現リスト】
{rules_text}

【チェック対象テキスト】
{combined_text}

【出力形式の厳守】
該当箇所（NG表現またはその活用形）が見つかった場合のみ、以下の形式で回答してください。
複数の箇所で見つかった場合は、必ず全角の句点「、」でつなげて1行で回答してください。
形式： NG表現（または活用形）⇒正しい表現

例：
諦める⇒あきらめる
諦める⇒あきらめる、一旦⇒いったん、伺う⇒うかがう

問題がない場合は「問題なし」とだけ回答してください。
余計な解説や、見出し、箇条書きなどは一切含めないでください。"""

        # AIで分析
        try:
            ai_result = self.ai_helper.model.generate_content(prompt).text.strip()
        except Exception as e:
            print(f"AI分析エラー (NGWordChecker): {e}")
            return results
        
        if "問題なし" in ai_result or not ai_result:
            return results
        else:
            # ユーザー指定の形式で結果を作成
            results.append(CheckResult(
                page_url=page_url,
                check_name="NG表現",  # 指定：チェック列は「NG表現」
                status="error",       # 指定：結果列は「×」（config側で変換）
                details=ai_result,    # 指定：NG⇒改善案 の形式（AIが生成）
                severity=self.get_severity()
            ))
        
        return results

    def _extract_metadata(self, soup: BeautifulSoup) -> dict:
        """主要なメタデータを抽出"""
        meta_data = {}
        
        # Title
        if soup.title:
            meta_data["title"] = soup.title.string
            
        # Meta description
        desc = soup.find("meta", attrs={"name": "description"})
        if desc:
            meta_data["description"] = desc.get("content")
            
        # OGP
        og_title = soup.find("meta", property="og:title")
        if og_title:
            meta_data["og:title"] = og_title.get("content")
            
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            meta_data["og:description"] = og_desc.get("content")
            
        # Images alt/title
        img_texts = []
        for img in soup.find_all("img"):
            alt = img.get("alt")
            title = img.get("title")
            if alt: img_texts.append(f"alt: {alt}")
            if title: img_texts.append(f"title: {title}")
        if img_texts:
            meta_data["images"] = img_texts[:20]  # 多すぎる場合は制限
            
        # JSON-LD
        json_texts = []
        for script in soup.find_all("script", type="application/ld+json"):
            if script.string:
                json_texts.append(script.string.strip())
        if json_texts:
            meta_data["json-ld"] = json_texts
            
        return meta_data
