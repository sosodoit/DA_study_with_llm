import os
import time
import requests
import email.utils
from urllib.parse import urlparse
import pandas as pd
import argparse
from datetime import datetime
from dotenv import load_dotenv
from content_loader import get_article_content
from gpt_analyzer import analyze_article_with_rag
from multiprocessing import Pool, cpu_count
from collections import defaultdict

#------------------------ 환경 설정 ------------------------#
load_dotenv()
USER_AGENT = os.environ.get("USER_AGENT")

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
# OUTPUT_FILE = os.path.join(DATA_DIR, "fraud_news.csv")
#----------------------------------------------------------#

def get_news(query, start):
    """네이버 검색 API 뉴스 데이터 가져오기"""
    headers = {
        'User-Agent': USER_AGENT,
        'X-Naver-Client-Id': CLIENT_ID,
        'X-Naver-Client-Secret': CLIENT_SECRET,        
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

def filter_domain(df):    
    """네이버 관련 도메인만 가져오기"""
    df['hostname'] = df['link'].apply(lambda x: urlparse(x).netloc)
    df = df[df['hostname'].str.contains("naver", case=False, na=False)].reset_index(drop=True)
    return df

# 기능 추가 : 특정 년월로 필터링한 뉴스만 수집 및 저장
# 기능 추가 : 키워드별 중복 뉴스 처리
# 수집 단계
def collect_articles(keywords, target_date=None):
    """전체 키워드에 대해 뉴스 수집"""
    
    link_map = defaultdict(lambda: {
        "keywords": set()
    })

    for keyword in keywords:
        print(f"키워드 '{keyword}'로 데이터 수집 시작...")
        
        for start in range(1, MAX_RESULTS_PER_KEYWORD + 1, RESULTS_PER_REQUEST):            
            data = get_news(keyword, start)

            if data and 'items' in data:
                for item in data['items']:
                    link = item['link']
                    pub_date = email.utils.parsedate_to_datetime(item['pubDate'])
                    year_month = pub_date.strftime("%Y-%m")
                    
                    if target_date:
                        if year_month != target_date:
                            continue 
                    
                    link = item['link']
                    link_map[link]['title'] = item['title']
                    link_map[link]['description'] = item['description']
                    link_map[link]['pubDate'] = pub_date.strftime("%Y-%m-%d %H:%M:%S")
                    link_map[link]['loadDate'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    link_map[link]['keywords'].add(keyword)
            else:
                break  # 더 이상 결과가 없으면 중단

            time.sleep(0.5)

    # 데이터 저장
    if link_map:
        articles = []
        for link, content in link_map.items():
            articles.append({                
                "title": content['title'],                
                "description": content['description'],
                "link": link,
                "keyword": ", ".join(sorted(content["keywords"])),
                "pubDate": content['pubDate'],
                "loadDate": content['loadDate']
            })
        df = pd.DataFrame(articles)
        new_df = filter_domain(df) # 네이버 도메인 필터링        
        new_df = new_df.drop_duplicates(subset="link") # 최종 중복 제거   

        # 새로운 데이터 마스터 파일에 병합
        MASTER_FILE = os.path.join("data", "news_raw.csv")  
        if os.path.exists(MASTER_FILE):
            existing_df = pd.read_csv(MASTER_FILE)
            combined = pd.concat([existing_df, new_df], ignore_index=True)
            combined = combined.drop_duplicates(subset="link")
        else:
            combined = new_df
        combined.to_csv(MASTER_FILE, index=False, encoding='utf-8-sig')
        print(f"뉴스 수집 완료: {len(df)}건 저장됨 → {MASTER_FILE}")

    else:
        print(f"조건에 맞는 새로운 뉴스가 없습니다.")

# 병렬 처리 함수
def process_row(row):
    try:
        doc = get_article_content(row['link'])
        if not doc:
            return None
        parsed, _ = analyze_article_with_rag(doc)
        parsed.update(row)
        return parsed
    except Exception as e:
        print(f"[오류] {row['link']} 처리 실패: {e}")
        return None
    
# 분석 단계: 수집된 뉴스 본문 추출 및 LLM 분석
def analyze_articles(target_date):
    raw_path = os.path.join(DATA_DIR, f"{target_date}_news_raw.csv")

    if not os.path.exists(raw_path):
        print(f"{raw_path} 파일이 존재하지 않습니다. 먼저 뉴스 수집을 수행해주세요.")
        return

    df = pd.read_csv(raw_path)
    # Streamlit에서 슬라이더로 MAX_ANALYZE 받은 값만큼만 분석
    max_analyze = int(os.environ.get("MAX_ANALYZE", len(df)))
    df = df.head(max_analyze)
    rows = df.to_dict(orient='records')

    print(f"분석 시작: {len(rows)}건 병렬 처리 (코어 수: {cpu_count()})")
    with Pool(processes=cpu_count()) as pool:
        results = list(pool.map(process_row, rows))

    results = [r for r in results if r]
    if results:
        result_df = pd.DataFrame(results)
        filename = os.path.join(DATA_DIR, f"{target_date}_fraud_news.csv")
        result_df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"분석 완료: {len(result_df)}건 저장됨 → {filename}")
    else:
        print("분석 가능한 뉴스가 없습니다.")

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="뉴스 수집 및 분석")
    parser.add_argument(
        "--extra", nargs="*", default=[],
        help="추가적으로 수집할 키워드 리스트 (예: --extra '금융 범죄 고수익보장' '당일 대출')"
    )
    parser.add_argument(
        "--month", nargs="*", type=str, default=[], 
        help="수집할 연월 (예: 2024-04)"
    )
    parser.add_argument(
        "--mode", choices=["collect", "analyze"], required=True, 
        help="작업 모드: collect 또는 analyze"
    )
    args = parser.parse_args()

    if args.mode == "collect":
        collect_articles(args.extra, args.month)
    elif args.mode == "analyze":
        analyze_articles(args.month)