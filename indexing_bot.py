import re
import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# ================= 설정 구간 =================
SITEMAP_URL = "https://goat-1.tistory.com/sitemap.xml"
KEY_FILE = "credentials.json"
# ============================================

def get_urls_from_sitemap(xml_url):
    try:
        print(f"📡 사이트맵 다운로드 중...: {xml_url}")
        response = requests.get(xml_url)
        if response.status_code != 200:
            print("❌ 사이트맵을 가져오는데 실패했습니다.")
            return []

        xml_data = response.text
        pattern = r"<loc>(https:\/\/goat\-1\.tistory\.com\/(?:m\/)?entry\/[^<]+)<\/loc>"
        urls = re.findall(pattern, xml_data)
        
        urls = list(set(urls))
        print(f"✅ 총 {len(urls)} 개의 포스팅 URL을 발견했습니다.")
        return urls
    except Exception as e:
        print(f"❌ URL 추출 중 오류 발생: {e}")
        return []

def notify_google_indexing(url_list):
    try:
        SCOPES = ["https://www.googleapis.com/auth/indexing"]
        creds = service_account.Credentials.from_service_account_file(
            KEY_FILE, scopes=SCOPES
        )
        creds.refresh(Request())
        access_token = creds.token

        endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        success_count = 0
        print("🚀 구글에 색인 요청을 시작합니다...")
        for url in url_list:
            data = {"url": url, "type": "URL_UPDATED"}
            res = requests.post(endpoint, headers=headers, json=data)
            if res.status_code == 200:
                print(f"[성공] {url}")
                success_count += 1
            elif res.status_code == 403:
                print(f"[권한 오류] {url} - 서치 콘솔 설정을 확인하세요.")
            elif res.status_code == 429:
                print(f"[한도 초과] 요청이 너무 많습니다.")
                break
            else:
                print(f"[실패({res.status_code})] {url} : {res.text}")
        print(f"\n🎉 완료! 총 {success_count} / {len(url_list)} 건 요청 성공.")
    except Exception as e:
        print(f"❌ API 요청 중 치명적 오류: {e}")

if __name__ == "__main__":
    target_urls = get_urls_from_sitemap(SITEMAP_URL)
    if target_urls:
        notify_google_indexing(target_urls)
    else:
        print("보낼 URL이 없습니다.")
