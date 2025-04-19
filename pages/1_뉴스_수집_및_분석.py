import os
import sys
import streamlit as st
import subprocess
import pandas as pd
from datetime import datetime

# modules 경로 추가
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# ----------------------- 제목 -----------------------
st.set_page_config(page_title="금융사기 뉴스 분석기시대", page_icon="📰",layout="wide")
with st.container():
    st.markdown("""
    <div style="background-color:#f0f4f8; padding: 20px 25px; border-radius: 12px; border: 1px solid #dfe6ec">
        <h3 style='color: #174c88;'>📰 금융 사기 뉴스 통합 분석기</h2>
        <p style='font-size: 16px; color: #333;'>
        네이버 뉴스 API를 통해 키워드 기반 금융 사기 뉴스를 수집하고 요약합니다.
        </p>
    </div>
    <br>
    """, unsafe_allow_html=True)

# --------------------- 사이드바 ----------------------
st.sidebar.header('수집 기간')
def get_current_month():
    return datetime.now().strftime("%Y-%m")
selected_month = st.sidebar.text_input("📆수집할 뉴스의 년월을 입력하세요 (예: 2024-04)", value=get_current_month())

st.sidebar.header('키워드 선택')
DEFAULT_KEYWORDS = [
    "금융 사기", "보이스피싱", "스미싱", "파밍", "대출 사기",
    "카드 사기", "인터넷 사기", "은행 사기", "사이버 금융사기",
    "피싱 사기", "불법 대출", "신용카드 도용", "계좌 도용",
    "주식 사기", "가상화폐 사기", "코인 사기", "투자 사기",
    "폰지 사기", "불법 투자 권유", "전자 금융 사기"
]
selected_base = st.sidebar.multiselect(
    "수집할 키워드를 선택하세요",
    options=DEFAULT_KEYWORDS,
    default=DEFAULT_KEYWORDS
)

st.sidebar.markdown("원하는 키워드가 없다면, 추가할 수 있습니다.")
extra_input = st.sidebar.text_input("🔍 추가 키워드 입력 (쉼표로 구분)")
extra_keywords = [kw.strip() for kw in extra_input.split(',') if kw.strip()]
total_keywords = list(set(selected_base + extra_keywords))

# ----------------------- API ------------------------
st.sidebar.markdown("---")
st.sidebar.header("🔑 Naver API Key 입력")

user_client_id = st.sidebar.text_input("Client ID", type="password")
user_client_secret = st.sidebar.text_input("Client Secret", type="password")

# ---------------------- 탭 구조 ----------------------
tab1, tab2 = st.tabs(["1. 뉴스 수집", "2. 뉴스 분석"])

# 캐시된 파일 로드 함수
def get_csv_data(path):
    @st.cache_data(ttl=300) # 캐시 유지 5분 
    def _load_csv(p):
        return pd.read_csv(p)
    return _load_csv(path)

# ------------------ 수집 전 체크사항 ------------------
def load_existing_news():
    master_path = os.path.join("data", "news_raw.csv")
    if os.path.exists(master_path):
        return get_csv_data(master_path)
    return pd.DataFrame(columns=["link", "keyword", "pubDate"])

existing_df = load_existing_news()

already_collected = (
    (existing_df['keyword'].isin(total_keywords)) &
    (existing_df['pubDate'].str.startswith(selected_month))
).any()

# ------------------ Tab 1: 수집 단계 ------------------
with tab1:    
    if st.button("뉴스 수집 시작"):

        if already_collected:
            st.success("✅ 뉴스 수집 완료")
        
        else:            
            if not user_client_id or not user_client_secret:
                st.warning("API 키를 입력해주세요.")
            else:  
                env_vars = os.environ.copy()
                env_vars["CLIENT_ID"] = user_client_id
                env_vars["CLIENT_SECRET"] = user_client_secret

                script_path = os.path.join(BASE_DIR, "modules", "crawler.py")
                cmd = [sys.executable, script_path, "--extra"] + total_keywords + ["--month", selected_month, "--mode", "collect"]

                st.write("🔄 수집 중입니다. 아래에 로그가 표시됩니다.")
                with st.spinner("뉴스 수집 중..."):        
                    result = subprocess.run(cmd, capture_output=True, text=True, env=env_vars)
                    st.text_area("수집 로그", result.stdout + result.stderr, height=100)
                
                if result.returncode == 0:
                    st.success("✅ 뉴스 수집 완료")
                else:
                    st.error("❌ 수집 중 오류 발생")
    
    # 수집 결과 미리보기
    st.markdown("---")
    result_path = os.path.join("data", "news_raw.csv")

    if os.path.exists(result_path):
        df = get_csv_data(result_path)

        # 보기 좋게 전처리 
        df['pubDate'] = pd.to_datetime(df['pubDate'])
        df['pubDate'] = df['pubDate'].dt.strftime("%Y-%m-%d")
        df = df.rename(columns={
            "keyword": "KEYWORD",
            "title": "TITLE",
            "link": "URL",
            "description": "DESC",
            "pubDate": "PUB_DT",
            "loadDate": "LOAD_DT",
            "hostname": "HOST_NAME"
        })
        df = df[['PUB_DT','TITLE','KEYWORD','DESC','URL']]

        # 필터 UI 추가
        with st.expander("필터 옵션", expanded=False):
            keywords = list(set(DEFAULT_KEYWORDS + extra_keywords))            
            selected_keywords = st.multiselect("키워드 필터", options=keywords, default=keywords[:5])

            if 'PUB_DT' in df.columns:
                date_range = st.date_input("기간 필터", [])
                if len(date_range) == 2:
                    start, end = date_range
                    df = df[
                        (pd.to_datetime(df['PUB_DT']) >= pd.to_datetime(start)) &
                        (pd.to_datetime(df['PUB_DT']) <= pd.to_datetime(end))
                    ]

            df = df[df['KEYWORD'].apply(lambda x: any(k in str(x) for k in selected_keywords))]
            
            st.write(f"총 {len(df)}건의 분석된 뉴스가 있습니다.")
            st.dataframe(df.sort_values("PUB_DT", ascending=False).reset_index(drop=True))
    else:
        st.info("수집된 뉴스가 없습니다. 먼저 수집을 실행해주세요.")

# ------------------ Tab 2: 분석 단계 ------------------
with tab2:
    raw_path = os.path.join("data", f"{selected_month}_news_raw.csv")
    if os.path.exists(raw_path):
        raw_df = get_csv_data(raw_path)
        st.info(f"현재 수집된 뉴스 개수: {len(raw_df)}건")
        analyze_count = st.slider("분석할 기사 수 (최대)", min_value=1, max_value=len(raw_df), value=min(100, len(raw_df)))

        if st.button("뉴스 분석"):
            script_path = os.path.join(BASE_DIR, "modules", "crawler.py")
            os.environ["MAX_ANALYZE"] = str(analyze_count) 
            cmd = [sys.executable, script_path, "--month", selected_month, "--mode", "analyze"]

            st.write("🔄 분석 중입니다. 아래에 로그가 표시됩니다.")
            with st.spinner("뉴스 분석 중..."):     
                result = subprocess.run(cmd, capture_output=True, text=True)
                st.text_area("분석 로그", result.stdout + result.stderr, height=300)

            if result.returncode == 0:
                st.success("✅ 뉴스 분석 완료")
            else:
                st.error("❌ 분석 중 오류 발생")
    else:
        st.warning("수집된 뉴스가 없습니다. 먼저 수집을 실행해주세요.")

    # 분석 결과 미리보기
    st.markdown("---")
    result_path = os.path.join("data", f"{selected_month}_fraud_news.csv")
    if os.path.exists(result_path):
        df = get_csv_data(result_path)
        st.write(f"총 {len(df)}건의 분석된 뉴스가 있습니다.")
        st.dataframe(df.sort_values("pubDate", ascending=False).head(10))
    else:
        st.info("아직 분석된 결과가 없습니다. 먼저 뉴스 수집과 분석을 실행해주세요.")