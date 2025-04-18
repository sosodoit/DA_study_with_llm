import streamlit as st
from utils import print_messages, StreamHandler
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import ChatMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os 

#------------------------ 환경 설정 ------------------------#
load_dotenv()

# API KEY 설정 
# os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# streamlit에서 하나의 실행이 곧 페이지 새로고침(초기화)
# 우리의 대화를 기억할 수 있도록 수동 조정 필요
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 채팅 대화기록을 저장하는 store 변수
if "store" not in st.session_state:
    st.session_state["store"] = dict()

with st.sidebar:
    session_id = st.text_input("Session ID", value="jelly123")

    clear_btn = st.button("대화기록 초기화")
    if clear_btn:
        st.session_state["messages"] = []
        st.experimental_rerun()

# 이전 대화 기록을 출력해 주는 코드 
print_messages()

# 세션 ID를 기반으로 세션 기록을 가져오는 함수
def get_session_history(session_ids: str) -> BaseChatMessageHistory:
    print(session_ids)
    if session_ids not in st.session_state["store"]:
        st.session_state["store"][session_ids] = ChatMessageHistory()
    return st.session_state["store"][session_ids]
############################################################

#------------------------ 챗봇 설정 ------------------------#
if user_input := st.chat_input("메시지를 입력해 주세요."):

    #------------------------ 사용자 질문 입력 ------------------------#
    st.chat_message("user").write(f"{user_input}")
    st.session_state["messages"].append(ChatMessage(role="user", content=user_input))

    #----------------------- AI 답변 생성/출력 ------------------------#
    with st.chat_message("assistant"):
        stream_handler = StreamHandler(st.empty())

        # 1. 모델 생성
        llm = ChatOpenAI(streaming=True, callbacks=[stream_handler])

        # 2. 프롬프트 생성
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "당신은 {ability}에 능숙한 어시스턴트입니다. 질문에 짧고 간결하게 답변해 주세요.",
                ),
                # 대화 기록
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}")
            ]
        )

        # 3. 대화 기억하는 chain 생성
        runnable = prompt | llm
        
        chain_with_message_history = (
            RunnableWithMessageHistory(
                runnable,
                get_session_history,
                input_messages_key="question",
                history_messages_key="history",
            )
        )

        # 4. 답변 생성
        response = chain_with_message_history.invoke(
            {"ability": "math", "question": user_input},
            config={"configurable": {"session_id": session_id}},
        )

        st.session_state["messages"].append(
            ChatMessage(role="assistant", content=response.content)
        )
############################################################