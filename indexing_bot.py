import re
import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# ================= 설정 구간 =================
SITEMAP_URL = "https://goat-1.tistory.com/sitemap.xml" # 본인 블로그 주소로 변경
KEY_FILE = "credentials.json" # 다운받은 키 파일 경로
# ============================================

def get_urls_from_sitemap(xml_url):
    """사이트맵에서 포스팅 URL만 추출"""
    try:
        print(f"📡 사이트맵 다운로드 중...: {xml_url}")
        response = requests.get(xml_url)
        if response.status_code != 200:
            print("❌ 사이트맵을 가져오는데 실패했습니다.")
            return []

        # XML 파싱 대신 정규식으로 빠르고 간단하게 추출
        # <loc> 태그 안의 /entry/ 또는 /m/entry/가 포함된 URL 찾기
        xml_data = response.text
        pattern = r"<loc>(https:\/\/example\.tistory\.com\/(?:m\/)?entry\/[^<]+)<\/loc>"
        urls = re.findall(pattern, xml_data)

        # 중복 제거 (티스토리는 모바일 주소 등이 섞일 수 있음)
        urls = list(set(urls))
        print(f"✅ 총 {len(urls)}개의 포스팅 URL을 발견했습니다.")
        return urls
    except Exception as e:
        print(f"❌ URL 추출 중 오류 발생: {e}")
        return []

def notify_google_indexing(url_list):
    """구글 Indexing API에 요청 전송"""
    try:
        # 서비스 계정 인증 (Scope 설정 필수)
        SCOPES = ["https://www.googleapis.com/auth/indexing"]
        creds = service_account.Credentials.from_service_account_file(
            KEY_FILE, scopes=SCOPES
        )

        # 인증 토큰 갱신
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
            data = {
                "url": url,
                "type": "URL_UPDATED"
            }
            res = requests.post(endpoint, headers=headers, json=data)

            if res.status_code == 200:
                print(f"[성공] {url}")
                success_count += 1
            elif res.status_code == 403:
                print(f"[권한 오류] {url} - 서치 콘솔에 서비스 계정을 '소유자'로 추가했는지 확인하세요.")
            elif res.status_code == 429:
                print(f"[한도 초과] 요청이 너무 많습니다.")
                break
            else:
                print(f"[실패({res.status_code})] {url} : {res.text}")

        print(f"\n🎉 완료! 총 {success_count}/{len(url_list)} 건 요청 성공.")

    except Exception as e:
        print(f"❌ API 요청 중 치명적 오류: {e}")

if __name__ == "__main__":
    target_urls = get_urls_from_sitemap(SITEMAP_URL)
    if target_urls:
        notify_google_indexing(target_urls)
    else:
        print("보낼 URL이 없습니다.")
출처: https://betwe.tistory.com/entry/구글-SEO-구글-서치콘솔-색인-생성-자동화-완벽-가이드-Python-vs-n8n [개발과 육아사이:티스토리]
