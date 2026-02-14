"""
統合AIチェッカー

Gemini APIを使用して、誤字脱字、NG表現、詳細情報の整合性を1回のリクエストで一括チェック
"""

import json
import re
from typing import List
from bs4 import BeautifulSoup
from .base import BaseChecker, CheckResult
from utils.ai_helper import AIHelper

class UnifiedAIChecker(BaseChecker):
    """複数のAIチェック機能を1つに集約したチェッカー"""
    
    def __init__(self, config: dict, master_data: dict = None, ng_rules: List[dict] = None):
        super().__init__(config)
        self.master_data = master_data or {}
        self.ng_rules = ng_rules or config.get("ng_words_rules", [])
        
        # 個別チェックの有効無効設定を取得
        self.typo_enabled = config.get("checks", {}).get("typo_check", {}).get("enabled", True)
        self.ng_enabled = config.get("checks", {}).get("ng_word_check", {}).get("enabled", True)
        self.consistency_enabled = config.get("checks", {}).get("consistency_check", {}).get("enabled", True)

        try:
            self.ai_helper = AIHelper(config)
            self.enabled = any([self.typo_enabled, self.ng_enabled, self.consistency_enabled])
        except Exception as e:
            print(f"警告 (UnifiedAIChecker): {e}")
            self.enabled = False
            self.ai_helper = None

    def check(self, page_url: str, page_content: str, soup: BeautifulSoup) -> List[CheckResult]:
        results = []
        if not self.enabled or not self.ai_helper:
            return results

        # 1. 外部サービス(GA4等)の非AI直接チェック
        if self.consistency_enabled:
            ga4_res = self._check_ga4_direct(soup, page_url)
            if ga4_res:
                results.append(ga4_res)

        # 2. AIによる統合チェック
        ai_res_list = self._check_with_ai_unified(page_url, page_content, soup)
        results.extend(ai_res_list)

        return results

    def _check_ga4_direct(self, soup: BeautifulSoup, page_url: str) -> CheckResult:
        """GA4コードの存在と正確性をソースから直接判定"""
        target_ga4 = self.master_data.get("GA4コード")
        if not target_ga4:
            return None

        html_str = str(soup)
        found = re.findall(r'G-[A-Z0-9]{5,}', html_str)
        
        if not found:
            return CheckResult(
                page_url=page_url,
                check_name="GA4設定",
                status="error",
                details=f"★ マスターデータに指定されたGA4コード（{target_ga4}）がソース内に見つかりません。",
                severity="high"
            )
        
        if target_ga4 not in found:
            return CheckResult(
                page_url=page_url,
                check_name="GA4設定",
                status="error",
                details=f"★ 検出されたGA4コード（{', '.join(set(found))}）が、マスターデータ（{target_ga4}）と一致しません。",
                severity="critical"
            )
        return None

    def _check_with_ai_unified(self, page_url: str, page_content: str, soup: BeautifulSoup) -> List[CheckResult]:
        """Geminiを使用して全項目を一括判定"""
        metadata = self._extract_metadata(soup)
        master_summary = json.dumps(self.master_data, ensure_ascii=False, indent=2)
        rules_text = "\n".join([f"- {r.get('bad')} ⇒ {r.get('good')}" for r in self.ng_rules])
        
        # 今日月日を取得
        import datetime
        now = datetime.datetime.now()
        today_str = now.strftime("%Y年%m月%d日")

        # 有効なチェック項目のリストを作成
        check_instructions = []
        if self.typo_enabled:
            check_instructions.append("1. **誤字脱字・不自然な表現**: 文脈の誤り、タイプミス、不自然な言い回し、日付の矛盾（現在は2026年）。")
        if self.ng_enabled:
            check_instructions.append(f"2. **NG表現**: 以下のリストに該当する（またはその変形、活用形）表現を検出。\n{rules_text}")
        if self.consistency_enabled:
            check_instructions.append("3. **詳細情報の整合性**: 医院名（統一性）、郵便番号・電話番号（半角推奨）、所在地住所（全角推奨）、診療時間、経歴の矛盾。")

        instructions_str = "\n".join(check_instructions)

        prompt = f"""あなたは歯科Webサイト制作と校正の専門家です。
【重要】本日は **{today_str}** です。現在は **2026年** であることを認識して精査してください。

以下の【ページ情報】を精査し、指定された【チェック項目】に基づき不備を指摘してください。

【ページ情報】
URL: {page_url}
Meta情報: {json.dumps(metadata, ensure_ascii=False, indent=2)}
本文（抜粋）:
{page_content[:4000]}

【マスターデータ (比較用)】
{master_summary}

【チェック項目】
{instructions_str}

【出力形式：厳守】
- 指摘がある場合のみ、以下の形式で出力してください。
- 複数の指摘がある場合は、間に必ず【空行】を1行入れてください。
- 行頭は必ず「★」で始めてください。
- 各指摘の冒頭に [項目名] を付けてください（[誤字脱字], [NG表現], [整合性] 等）。
- 挨拶や前置きは【絶対に】含めないでください。

形式例：
★ [誤字脱字]: 「該当箇所」 → 正: 「修正案（理由）」

★ [NG表現]: 該当箇所 ⇒ 正しい表現

★ [整合性]: 「該当箇所」 ⇒ 指摘理由と修正案

不備がない場合は「問題なし」とだけ回答してください。"""

        try:
            # AIHelper経由で取得（クリーニング処理済み）
            ai_output = self.ai_helper.check_text(prompt, check_type="unified")
            
            if not ai_output or "問題なし" in ai_output:
                return []

            # 項目ごとに分割して解析（簡易的に1つの結果としてまとめるが、詳細はAIに任せる）
            return [CheckResult(
                page_url=page_url,
                check_name="AI統合チェック",
                status="warning",
                details=ai_output,
                severity="medium"
            )]
        except Exception as e:
            print(f"AI統合分析エラー: {e}")
            return []

    def _extract_metadata(self, soup: BeautifulSoup) -> dict:
        """主要なメタデータを抽出"""
        meta_data = {}
        if soup.title:
            meta_data["title"] = soup.title.string.strip() if soup.title.string else ""
            
        desc = soup.find("meta", attrs={"name": "description"})
        if desc:
            meta_data["description"] = desc.get("content", "").strip()
            
        og_title = soup.find("meta", property="og:title")
        if og_title:
            meta_data["og:title"] = og_title.get("content", "").strip()
            
        return meta_data
