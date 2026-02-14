"""
詳細情報整合性チェッカー

Gemini APIを使用して、ExcelのマスターデータとWebサイトの内容の整合性を多角的にチェック
"""

import re
import json
from typing import List
from bs4 import BeautifulSoup
from .base import BaseChecker, CheckResult
from utils.ai_helper import AIHelper

class ConsistencyChecker(BaseChecker):
    """詳細情報の整合性をチェックするクラス"""
    
    def __init__(self, config: dict, master_data: dict = None):
        super().__init__(config)
        self.master_data = master_data or {}
        # AIHelperの初期化はBaseCheckerで行うべきだが、既存の実装に倣う
        try:
            self.ai_helper = AIHelper(config)
            self.enabled = self.is_enabled()
        except Exception as e:
            print(f"警告 (ConsistencyChecker): {e}")
            self.enabled = False
            self.ai_helper = None

    def check(self, page_url: str, page_content: str, soup: BeautifulSoup) -> List[CheckResult]:
        results = []
        if not self.enabled or not self.ai_helper:
            return results

        # 1. GA4コードのチェック (ソースコードから直接判定)
        ga4_res = self._check_ga4(soup, page_url)
        if ga4_res:
            results.append(ga4_res)

        # 2. AIによる多角的整合性チェック
        ai_res_list = self._check_with_ai(page_url, page_content, soup)
        results.extend(ai_res_list)

        return results

    def _check_ga4(self, soup: BeautifulSoup, page_url: str) -> CheckResult:
        """GA4コードの存在と正確性をチェック"""
        target_ga4 = self.master_data.get("GA4コード")
        if not target_ga4:
            return None

        html_str = str(soup)
        # G- で始まるタグを検索
        found = re.findall(r'G-[A-Z0-9]{5,}', html_str)
        
        if not found:
            return CheckResult(
                page_url=page_url,
                check_name="GA4設定",
                status="error",
                details=f"マスターデータに指定されたGA4コード（{target_ga4}）がソース内に見つかりません。",
                severity="high"
            )
        
        if target_ga4 not in found:
            return CheckResult(
                page_url=page_url,
                check_name="GA4設定",
                status="error",
                details=f"検出されたGA4コード（{', '.join(set(found))}）が、マスターデータ（{target_ga4}）と一致しません。",
                severity="critical"
            )
        
        return None

    def _check_with_ai(self, page_url: str, page_content: str, soup: BeautifulSoup) -> List[CheckResult]:
        """Geminiを使用して不整合を判定"""
        metadata = self._extract_metadata(soup)
        master_summary = json.dumps(self.master_data, ensure_ascii=False, indent=2)
        
        prompt = f"""あなたは歯科Webサイト制作の専門家です。
以下の【マスターデータ】と【ページ内容】を比較し、情報の不備や不整合を厳しくチェックしてください。

【マスターデータ (DC-config.xlsx)】
{master_summary}

【チェック対象ページ情報】
URL: {page_url}
Meta情報: {json.dumps(metadata, ensure_ascii=False, indent=2)}
本文（抜粋）:
{page_content[:4000]}

【チェック項目と判断基準】
1. 医院名の統一: 略称や旧称が混ざっていないか。コピーライト表記も含む。
2. 郵便番号・住所の整合性と全角化: 
   - マスターデータと一致しているか。
   - 所在地（住所・ビル名・数字・ハイフン）がすべて【全角】で表記されているか。半角混在は不可。
3. 診療時間・休診日: ページ内の記述がマスターデータと矛盾していないか。
4. 経歴の整合性: ページ内にスタッフや院長の経歴がある場合、西暦や内容に矛盾がないか。
5. Descriptionの妥当性: ページ内容を適切に反映しているか。
6. 標榜科の矛盾: 「歯科」以外の無関係な診療科目（内科、眼科等）のキーワードが不自然に混入していないか。
7. レイアウトの一貫性: ヘッダーやフッターに、他ページと比べて重大な欠落や構成の違いがないか（特にブログページ）。

【出力形式】
不備がある場合のみ、以下の形式で簡潔に指摘してください。
- [項目名]: 「該当箇所の内容」 ⇒ 指摘理由と修正案

不備がない場合は「問題なし」とだけ回答してください。
余計な挨拶や解説は不要です。"""

        try:
            response = self.ai_helper.model.generate_content(prompt)
            ai_output = response.text.strip()
            
            if "問題なし" in ai_output or not ai_output:
                return []
            
            return [CheckResult(
                page_url=page_url,
                check_name="詳細情報の整合性",
                status="error",
                details=ai_output,
                severity="medium"
            )]
        except Exception as e:
            print(f"AI分析エラー (ConsistencyChecker): {e}")
            return []

    def _extract_metadata(self, soup: BeautifulSoup) -> dict:
        """主要なメタデータを抽出"""
        meta_data = {}
        if soup.title:
            meta_data["title"] = soup.title.string.strip() if soup.title.string else ""
            
        desc = soup.find("meta", attrs={"name": "description"})
        if desc:
            meta_data["description"] = desc.get("content", "").strip()
            
        # OGP
        og_title = soup.find("meta", property="og:title")
        if og_title:
            meta_data["og:title"] = og_title.get("content", "").strip()
            
        return meta_data
