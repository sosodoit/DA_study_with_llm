import os
import sys

# modules 경로 추가
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import streamlit as st
import subprocess
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="금융사기 뉴스 분석기시대", page_icon="📰")
st.title("📰 금융 사기 뉴스 통합 분석기")
st.markdown("네이버 뉴스 API를 통해 키워드 기반 금융 사기 뉴스를 수집합니다.")

# 수집 연월 선택
def get_current_month():
    return datetime.now().strftime("%Y-%m")
st.markdown("수집할 연월 선택")
selected_month = st.text_input("📆수집할 뉴스의 연월을 입력하세요 (예: 2024-04)", value=get_current_month())

# 키워드 입력
DEFAULT_KEYWORDS = [
    "금융 사기", "보이스피싱", "스미싱", "파밍", "대출 사기",
    "카드 사기", "인터넷 사기", "은행 사기", "사이버 금융사기",
    "피싱 사기", "불법 대출", "신용카드 도용", "계좌 도용",
    "주식 사기", "가상화폐 사기", "코인 사기", "투자 사기",
    "폰지 사기", "불법 투자 권유", "전자 금융 사기"
]

st.markdown("수집할 키워드 선택")
selected_base = st.multiselect(
    "수집할 키워드 선택",
    options=DEFAULT_KEYWORDS,
    default=DEFAULT_KEYWORDS[:1]
)

st.markdown("추가 키워드 입력")
extra_input = st.text_input("🔍 추가 키워드 입력 (쉼표로 구분)")
extra_keywords = [kw.strip() for kw in extra_input.split(',') if kw.strip()]
total_keywords = list(set(selected_base + extra_keywords))

# 수집 버튼
if st.button("뉴스 수집 시작"):
    script_path = os.path.join(BASE_DIR, "modules", "crawler.py")
    cmd = [sys.executable, script_path, "--extra", total_keywords,"--month", selected_month, "--mode", "collect"]

    st.write("🔄 수집 중입니다. 아래에 로그가 표시됩니다.")
    with st.spinner("뉴스 수집 중..."):        
        result = subprocess.run(cmd, capture_output=True, text=True)
        st.text_area("수집 로그", result.stdout + result.stderr, height=300)
    
    if result.returncode == 0:
        st.success("✅ 뉴스 수집 완료")
    else:
        st.error("❌ 수집 중 오류 발생")

# 분석 버튼
raw_path = os.path.join("data", f"{selected_month}_news_raw.csv")
if os.path.exists(raw_path):
    raw_df = pd.read_csv(raw_path)
    st.info(f"현재 수집된 뉴스 개수: {len(raw_df)}건")
    analyze_count = st.slider("분석할 기사 수 (최대)", min_value=1, max_value=len(raw_df), value=min(100, len(raw_df)))

    if st.button("뉴스 분석"):
        script_path = os.path.join(BASE_DIR, "modules", "crawler.py")
        os.environ["MAX_ANALYZE"] = str(analyze_count)  # 환경변수로 전달
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

# 수집 결과 미리보기
st.markdown("---")
result_path = os.path.join("data", f"{selected_month}_fraud_news.csv")
if os.path.exists(result_path):
    df = pd.read_csv(result_path)
    st.write(f"총 {len(df)}건의 분석된 뉴스가 있습니다.")
    st.dataframe(df.sort_values("pubDate", ascending=False).head(10))
    st.download_button(
        label="📥 CSV 다운로드",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=os.path.basename(result_path),
        mime='text/csv'
    )
else:
    st.info("아직 분석된 결과가 없습니다. 먼저 뉴스 수집과 분석을 실행해주세요.")