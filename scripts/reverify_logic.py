
import sys
import os
from bs4 import BeautifulSoup

# プロジェクトルートをパスに追加
sys.path.append(os.getcwd())

from checkers.link_checker import LinkChecker
from checkers.phone_checker import PhoneChecker
from utils.ai_helper import AIHelper

def test_sns_exclusion():
    print("--- Testing SNS Exclusion ---")
    config = {"checks": {"link_check": {"timeout": 5}}}
    checker = LinkChecker(config)
    
    html = """
    <a href="https://www.instagram.com/kawabata/">Insta</a>
    <a href="https://twitter.com/kawabata">Twitter</a>
    <a href="https://facebook.com/kawabata">FB</a>
    <a href="https://x.com/kawabata">X</a>
    <a href="https://google.com">Valid</a>
    """
    soup = BeautifulSoup(html, "html.parser")
    # _check_link をモック化してネットワーク通信を避ける
    checker._check_link = lambda url, domain: (True, "200")
    
    results = checker.check("https://example.com", "", soup)
    for r in results:
        print(f"Status: {r.status}, Details: {r.details}")
    
    # 5個中4個がSNSなので、1個だけチェックされるはず
    if "1個のリンクをチェック" in results[0].details:
        print("SUCCESS: SNS links were excluded.")
    else:
        print(f"FAILURE: Expected 1 link checked, but got: {results[0].details}")

def test_phone_exclusion():
    print("\n--- Testing Phone Exclusion ---")
    config = {
        "checks": {
            "phone_check": {
                "correct_phone": "0778-42-5587"
            }
        }
    }
    checker = PhoneChecker(config)
    
    # パターン1: 正しい番号のみ
    html1 = "<div>お電話はこちら: 0778-42-5587</div>"
    soup1 = BeautifulSoup(html1, "html.parser")
    results1 = checker.check("https://example.com", "0778-42-5587", soup1)
    print(f"Pattern 1 (Correct only) results: {len(results1)}")
    if not results1:
        print("SUCCESS: Correct phone number was not reported.")
    else:
        print(f"FAILURE: Correct phone number was reported: {results1[0].details}")

    # パターン2: 違う番号
    html2 = "<div>お電話はこちら: 03-1111-2222</div>"
    soup2 = BeautifulSoup(html2, "html.parser")
    results2 = checker.check("https://example.com", "03-1111-2222", soup2)
    if results2 and results2[0].status == "error":
        print("SUCCESS: Incorrect phone number was reported.")
    else:
        print(f"FAILURE: Incorrect phone number was not reported as error.")

def test_ai_date():
    print("\n--- Testing AI Date Prompt ---")
    config = {"api": {"model": "gemini-3-flash-preview"}}
    # AIHelperの初期化はキーが必要なので、_get_prompt だけチェック
    try:
        helper = AIHelper(config)
    except Exception:
        # キーがない場合はダミーで作成
        class MockAIHelper(AIHelper):
            def __init__(self): pass
        helper = MockAIHelper()
    
    prompt = helper._get_prompt("Test text", "typo")
    print(f"Prompt preview: {prompt[:150]}...")
    if "2025年" in prompt and "2024年" in prompt:
        print("SUCCESS: Date instruction found in prompt.")
    else:
        print("FAILURE: Date instruction missing in prompt.")

if __name__ == "__main__":
    test_sns_exclusion()
    test_phone_exclusion()
    test_ai_date()
