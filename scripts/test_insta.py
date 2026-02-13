import requests
from urllib.parse import urlparse

url = 'https://www.instagram.com/kawabata_ortho?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw=='
base_domain = 'kwbt-kyousei.com' # 本来のチェック対象ドメイン
ua_browser = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
dummy_auth = 'Basic dmlzY2E6NTE1MQ=='

print(f"Testing URL: {url}")
print(f"Base Domain: {base_domain}")

def test_final_logic(url, base_domain):
    target_domain = urlparse(url).netloc
    # LinkCheckerの新ロジック
    request_auth = dummy_auth if target_domain == base_domain else None
    headers = {"User-Agent": ua_browser}
    if request_auth:
        headers["Authorization"] = request_auth
    
    print(f"\n--- Testing with LinkChecker New Logic ---")
    print(f"Target Domain: {target_domain}")
    print(f"Auth Sent: {'Yes' if request_auth else 'No'}")
    
    try:
        r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        print(f"Result Status: {r.status_code}")
        if r.status_code < 400:
            print("Verdict: OK (Fixed!)")
        else:
            print("Verdict: Still Broken")
    except Exception as e:
        print(f"Error: {e}")

test_final_logic(url, base_domain)
