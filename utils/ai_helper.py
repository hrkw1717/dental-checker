"""
Claude API連携ヘルパー

Claude APIを使用したテキスト分析機能を提供
"""

import os
from typing import Optional
from anthropic import Anthropic


class AIHelper:
    """Claude APIを使用したAI支援機能"""
    
    def __init__(self, config: dict):
        """
        Args:
            config: 設定辞書
        """
        self.config = config
        api_config = config.get("api", {})
        
        # APIキーを環境変数から取得
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY環境変数が設定されていません。\n"
                "Claude APIを使用するには、環境変数にAPIキーを設定してください。"
            )
        
        self.client = Anthropic(api_key=api_key)
        self.model = api_config.get("model", "claude-sonnet-4.5")
        self.max_tokens = api_config.get("max_tokens", 4000)
    
    def check_text(self, text: str, check_type: str = "typo") -> Optional[str]:
        """
        テキストをAIでチェック
        
        Args:
            text: チェック対象のテキスト
            check_type: チェックタイプ ("typo", "natural", "consistency"など)
        
        Returns:
            AIの分析結果、エラー時はNone
        """
        try:
            # チェックタイプに応じたプロンプトを生成
            prompt = self._get_prompt(text, check_type)
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
        
        except Exception as e:
            print(f"AI分析エラー: {e}")
            return None
    
    def _get_prompt(self, text: str, check_type: str) -> str:
        """チェックタイプに応じたプロンプトを生成"""
        
        if check_type == "typo":
            return f"""以下の歯科クリニックのウェブサイトのテキストを分析し、誤字脱字や明らかな間違いを指摘してください。

【チェック対象テキスト】
{text}

【指摘形式】
問題が見つかった場合のみ、以下の形式で指摘してください：
- 誤: 「間違った表現」 → 正: 「正しい表現」

問題がない場合は「問題なし」とだけ回答してください。"""
        
        elif check_type == "natural":
            return f"""以下の歯科クリニックのウェブサイトのテキストを分析し、不自然な日本語表現を指摘してください。

【チェック対象テキスト】
{text}

【指摘形式】
不自然な表現が見つかった場合のみ、以下の形式で指摘してください：
- 不自然: 「該当箇所」 → 改善案: 「より自然な表現」

問題がない場合は「問題なし」とだけ回答してください。"""
        
        else:
            return f"""以下のテキストをチェックしてください：\n\n{text}"""
