import streamlit as st

st.set_page_config(page_title='LLM 프로젝트', page_icon='망고.png')
st.title("AI 기반 데이터 분석 프로젝트")

with st.sidebar:
    st.title("📂 메뉴")
    st.info("상단 메뉴에서 다른 프로젝트 페이지로 이동하세요.")
    
st.markdown("""
이 앱은 다양한 AI/데이터 기반 분석 프로젝트 내용을 담았습니다.  

---

### 🧩 현재 포함된 프로젝트

1. 📡 **금융 사기 뉴스 수집 크롤러**  
    - 네이버 뉴스 API를 이용해 보이스피싱, 투자 사기 등 관련 뉴스를 수집하고 분석합니다.
    - 수집된 데이터를 기반으로 추후 요약, 시각화, 트렌드 분석 가능

""")


