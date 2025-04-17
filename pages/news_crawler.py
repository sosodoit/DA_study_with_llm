import streamlit as st
import subprocess
import pandas as pd
import os

st.set_page_config(page_title="뉴스 수집기", page_icon="📰")
st.title("📰 금융 사기 뉴스 수집기")
st.markdown("네이버 뉴스 API를 통해 키워드 기반 금융 사기 뉴스를 수집합니다.")

st.markdown("추가 키워드를 입력해서 뉴스 데이터를 수집하세요.")
user_keywords = st.text_area("📌 키워드 입력 (쉼표로 구분)", placeholder="예: 금융범죄, 고수익 보장")

if st.button("뉴스 수집 시작"):

    # 현재 파일 기준
    base_dir = os.path.dirname(__file__)
    script_path = os.path.join(base_dir, "..", "crawler.py")
        
    if user_keywords.strip():
        keyword_list = [k.strip() for k in user_keywords.split(",")]
        keyword_args = " ".join([f'"{kw}"' for kw in keyword_list])
        cmd = f"python {script_path} --extra {keyword_args}"
        
    else:
        cmd = f"python {script_path}"

    st.write("🟢 수집 중... 아래에 실시간 로그가 표시됩니다.")
    log_area = st.empty()

    try:
        with st.spinner("뉴스 수집 중..."):
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            st.success("뉴스 수집 완료")
            st.text_area("출력 로그", result.stdout + result.stderr, height=300)
    
    except FileNotFoundError:
        st.error("❌ `crawler.py` 파일을 찾을 수 없습니다. 경로를 다시 확인하세요.")
        
    except Exception as e:
        st.error(f"❌ 오류 발생: {e}")

# 수집 결과 미리보기
csv_path = "data/fraud_news.csv"
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    st.markdown(f"### 📰 수집된 뉴스 ({len(df)}건)")
    st.dataframe(df.sort_values("pubDate", ascending=False).head(10))
else:
    st.info("아직 수집된 뉴스가 없습니다.")
