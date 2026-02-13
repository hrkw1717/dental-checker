import requests
from urllib.parse import urlparse

url = 'https://www.instagram.com/kawabata_ortho?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw=='
ua_browser = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'

headers = {"User-Agent": ua_browser}

print(f"Target URL: {url}")

def debug_request(method):
    print(f"\n--- Testing {method} ---")
    try:
        if method == "HEAD":
            r = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        else:
            r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        print(f"Status: {r.status_code}")
        print(f"Final URL: {r.url}")
        print(f"Redirects: {len(r.history)}")
        for i, hist in enumerate(r.history):
            print(f"  {i}: {hist.status_code} -> {hist.url}")
        
        # 404や403の場合、中身がどのようなものか確認（GETのみ）
        if method == "GET" and r.status_code >= 400:
            print(f"Content Snippet: {r.text[:200]}...")
            
    except Exception as e:
        print(f"Error: {e}")

debug_request("HEAD")
debug_request("GET")
