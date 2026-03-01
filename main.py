import os
from dotenv import load_dotenv
import feedparser
import requests
import io
from bs4 import BeautifulSoup

load_dotenv()

RSS_URL = os.getenv("RSS_URL")
MISSKEY_URL = os.getenv("MISSKEY_URL")
MISSKEY_TOKEN = os.getenv("MISSKEY_TOKEN")
LAST_LINK_FILE = "last_link.txt"

def get_last_link():
    try:
        with open(LAST_LINK_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def save_last_link(link):
    with open(LAST_LINK_FILE, "w") as f:
        f.write(link)

def upload_to_misskey(image_url):
    """이미지 URL을 받아 미스키 드라이브에 업로드하고 fileId를 반환"""
    try:
        # 1. 이미지 다운로드
        img_res = requests.get(image_url, timeout=10)
        img_res.raise_for_status()
        
        # 2. 미스키 드라이브에 업로드 (파일 이름은 대충 타임스탬프로)
        files = {
            'file': ('image.jpg', io.BytesIO(img_res.content), 'image/jpeg')
        }
        data = {'i': MISSKEY_TOKEN}
        
        res = requests.post(f"{MISSKEY_URL}drive/files/create", data=data, files=files)
        if res.status_code == 200:
            return res.json().get('id')
    except Exception as e:
        print(f"이미지 업로드 실패: {e}")
    return None

def post_to_misskey(content, link, image_urls):
    # 이미지 업로드 후 ID 목록 생성
    file_ids = []
    for url in image_urls[:16]:  # 미스키는 한 게시물당 최대 16장
        file_id = upload_to_misskey(url)
        if file_id:
            file_ids.append(file_id)

    # 본문 구성
    full_text = f"📝 {content}\n\n🔗 원문: {link}"

    payload = {
        "i": MISSKEY_TOKEN,
        "text": full_text,
        "fileIds": file_ids,  # 업로드한 파일 ID들 첨부
        "visibility": "home"
    }

    res = requests.post(f"{MISSKEY_URL}notes/create", json=payload)
    return res.status_code == 200

# 실행 로직
feed = feedparser.parse(RSS_URL)
last_link = get_last_link()

# 새 글이 있으면 (가장 최신글 하나만 예시)
if feed.entries:
    entry = feed.entries[0]
    if entry.link != last_link:
        # 본문(HTML)에서 이미지 태그 추출
        content_html = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
        soup = BeautifulSoup(content_html, "html.parser")
        # 모든 <img> 태그의 src 주소 가져오기
        image_urls = [img['src'] for img in soup.find_all('img') if img.get('src')]
        # 텍스트 정리
        content_text = soup.get_text(separator="\n").strip()
        # 포스팅 실행
        if post_to_misskey(content_text, entry.link, image_urls):
            save_last_link(entry.link)
            print("미스키 전송 성공!")
