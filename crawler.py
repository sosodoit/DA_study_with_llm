import os
import time
import requests
import email.utils
import pandas as pd
import argparse
from datetime import datetime
from dotenv import load_dotenv

#------------------------ 환경 설정 ------------------------#
load_dotenv()

# 네이버 검색 API 설정
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
BASE_URL = 'https://openapi.naver.com/v1/search/news.json'

# 검색 파라미터
RESULTS_PER_REQUEST = 100   # 한 번 요청당 가져올 최대 기사 수 (최대 100)
MAX_RESULTS_PER_KEYWORD = 1000 # 키워드별 최대 기사 수

# 검색 키워드 리스트
BASE_KEYWORDS = [
    "금융 사기", "보이스피싱", "스미싱", "파밍", "대출 사기",
    "카드 사기", "인터넷 사기", "은행 사기", "사이버 금융사기",
    "피싱 사기", "불법 대출", "신용카드 도용", "계좌 도용",
    "주식 사기", "가상화폐 사기", "코인 사기", "투자 사기",
    "폰지 사기", "불법 투자 권유", "금융 사기 범죄","전자 금융 사기"
]

# EXTRA_KEYWORDS = []  # 사용자가 원하는 추가 키워드
# KEYWORDS = list(set(BASE_KEYWORDS + EXTRA_KEYWORDS))  # 중복 제거

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(DATA_DIR, "fraud_news.csv")
#----------------------------------------------------------#

def get_news(query, start):
    """네이버 검색 API 뉴스 데이터 가져오기"""
    headers = {
        'X-Naver-Client-Id': CLIENT_ID,
        'X-Naver-Client-Secret': CLIENT_SECRET
    }
    params = {
        'query': f"{query}",
        'display': RESULTS_PER_REQUEST,
        'start': start,
        'sort': 'date'
    }
    response = requests.get(BASE_URL, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def load_existing_links(filepath):
    """기존 뉴스 파일 로드 (중복 방지를 위해 링크 수집)"""
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)

        if 'link' in df.columns:
            # 결측치 제거 + 고유 링크만 추출
            link_set = set(df['link'].dropna().unique())
            return df, link_set
        else:
            print("⚠️ 경고: 기존 파일에 'link' 컬럼이 없습니다.")
            return df, set()
    else:
        return pd.DataFrame(), set()

def collect_articles(keywords):
    """전체 키워드에 대해 뉴스 수집"""
    articles = []    
    existing_df, existing_links = load_existing_links(OUTPUT_FILE)

    for keyword in keywords:
        print(f"키워드 '{keyword}'로 데이터 수집 시작...")
        
        for start in range(1, MAX_RESULTS_PER_KEYWORD + 1, RESULTS_PER_REQUEST):            
            data = get_news(keyword, start)

            if data and 'items' in data:
                for item in data['items']:
                    link = item['link']
                    if link in existing_links:
                        continue  # 중복된 뉴스는 건너뛰기
                    pub_date = email.utils.parsedate_to_datetime(item['pubDate'])
                    articles.append({
                        "keyword": keyword,
                        "title": item['title'],
                        "link": item['link'],
                        "description": item['description'],
                        "pubDate": pub_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            else:
                break  # 더 이상 결과가 없으면 중단

            time.sleep(0.1)

    # 데이터 저장
    if articles:
        df = pd.DataFrame(articles)
        new_df = pd.concat([existing_df, df], ignore_index=True)
        # 최종 중복 제거
        new_df = new_df.drop_duplicates(subset="link")
        new_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"저장 경로 : {OUTPUT_FILE}")
        print(f"{len(articles)}개의 기사를 저장했습니다.")

    else:
        print(f"새로운 기사가 없습니다.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="뉴스 크롤러")
    parser.add_argument(
        "--extra", nargs="*", default=[],
        help="추가적으로 수집할 키워드 리스트 (예: --extra '금융 범죄 고수익보장' '당일 대출')"
    )
    args = parser.parse_args()

    # 키워드 병합
    total_keywords = list(set(BASE_KEYWORDS + args.extra))

    print(f"총 수집 키워드 개수: {len(total_keywords)}")
    collect_articles(total_keywords)