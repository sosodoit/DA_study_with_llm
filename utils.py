from langchain_core.callbacks.base import BaseCallbackHandler
import streamlit as st

# 스트리밍
class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, inital_text=""):
        self.container = container
        self.text = inital_text
    
    # 토큰이 생성될때마다 컨테이너에 마크다운형식으로 찍히게됨
    def on_llm_new_token(self, token:str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)

def print_messages():
    # 이전 대화 기록을 출력해 주는 코드 
    if "messages" in st.session_state and len(st.session_state["messages"]) > 0:
        for chat_message in st.session_state["messages"]:
            st.chat_message(chat_message.role).write(chat_message.content)