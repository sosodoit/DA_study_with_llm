import streamlit as st

st.set_page_config(page_title='AI 포트폴리오', page_icon='망고.png', layout="wide")
st.markdown("<h2 style='margin-bottom: 0;'>AI 기반 데이터 분석 포트폴리오</h2>", unsafe_allow_html=True)
    
# 소개 섹션
st.markdown("""
안녕하세요👋<br>
저는 **데이터 분석과 자동화 파이프라인 구축**, 그리고 **LLM 활용 인텔리전스 분석**에 특화된 분석가로 소개드리고 싶습니다.<br>

환경이 사람을 만든다고 생각합니다. 
기술적으로 부족해 보일 수 있으나 넓은 시각으로 원하는 목표물을 구현하고 실험할 수 있는 능력으로, 함께 하여 성장형 팀원으로써 만족할 수 있으실거라 약속드립니다.<br>
            
이 앱은 **AI 프로젝트 및 데이터 분석 결과물**을 시각적으로 담은 포트폴리오입니다.

---

### 💡 주요 역량

- **데이터 수집 & 처리**: API/크롤링 자동화, 대용량 데이터 정제
- **NLP / LLM 활용**: 뉴스 요약, 분류, 정보 추출 (GPT 기반)
- **AI 기반 분류/예측 모델링**: 사기탐지, 사용자 행동 분석 등
- **시각화 대시보드 개발**: Streamlit / Tableau / Power BI
- **자동화 파이프라인 구성**: 스케줄링, 파이프라인 모듈화

---

### 🧩 포함된 프로젝트

#### 1. 금융 사기 뉴스 수집 & LLM 분석기
- 네이버 뉴스 API로 뉴스 수집 + 본문 자동 크롤링
- GPT 기반 기사 분류/요약/피해 정보 추출
- Streamlit 대시보드에서 기사 요약 확인 및 시각화

---

#### 🛠️ 기술 스택

- **Python**, **LangChain**, **OpenAI API**, **Pandas**, **BeautifulSoup**
- **Streamlit**, **Matplotlib**, **FAISS**, **GPT-3.5-turbo**

---
""", unsafe_allow_html=True)
