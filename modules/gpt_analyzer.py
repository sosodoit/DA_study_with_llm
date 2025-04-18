import re
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.schema.runnable import RunnablePassthrough

# 1. 모델 설정
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

# 2. 프롬프트 템플릿
prompt = PromptTemplate.from_template(
    """당신은 질문-답변(Question-Answering)을 수행하는 친절한 AI 어시스턴트입니다. 당신의 임무는 주어진 문맥(context) 에서 주어진 질문(question) 에 답하는 것입니다.
검색된 다음 문맥(context) 을 사용하여 질문(question) 에 답하세요. 만약, 주어진 문맥(context) 에서 답을 찾을 수 없다면, 답을 모른다면 `주어진 정보에서 질문에 대한 정보를 찾을 수 없습니다` 라고 답하세요.
한글로 답변해 주세요. 단, 기술적인 용어나 이름은 번역하지 않고 그대로 사용해 주세요.

#Question: 
{question} 

#Context: 
{context} 

#Answer:"""
)

# 3. 분석 질문 템플릿
input_question = """
1. 이 기사는 어떤 유형입니까? (범죄 사건 / 대응 정책 / 기타 중 하나로)
2. 주요 내용을 한 줄로 요약해 주세요.
3. (범죄 기사일 경우) 대표적인 범죄 유형은 무엇입니까?
4. (범죄 기사일 경우) 피해자의 특징이 있다면 알려주세요.
5. (범죄 기사일 경우) 피해 형태는 무엇입니까?
6. (범죄 기사일 경우) 발생 원인은 무엇입니까?
7. (대응 정책일 경우) 정책인가요, 기술적 대응인가요?

각 답변은 번호를 붙여서 한 줄로 주세요.
"""

# 4. 문서 결합 함수
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 5. 파싱 함수
def parse_response(text):
    result = {
        "category": None,
        "summary": None,
        "crime_type": None,
        "victim_features": None,
        "damage": None,
        "cause": None,
        "response_type": None
    }

    for i in range(1, 8):
        match = re.search(rf"{i}\.\s*(.*)", text)
        if match:
            value = match.group(1).strip()
            match i:
                case 1: result["category"] = value
                case 2: result["summary"] = value
                case 3: result["crime_type"] = value
                case 4: result["victim_features"] = value
                case 5: result["damage"] = value
                case 6: result["cause"] = value
                case 7: result["response_type"] = value

    return result

# 6. 메인 분석 함수
def analyze_article_with_rag(documents, question=input_question):
    
    # 문서가 너무 짧아 split 되지 않음 > 원본 그대로 전달 
    if len(documents[0].page_content) < 1000:
        splits = documents

    else:
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        splits = splitter.split_documents(documents)
         
    vectorstore = FAISS.from_documents(splits, embedding=OpenAIEmbeddings())
    retriever = vectorstore.as_retriever()

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    response = rag_chain.invoke(question)
    return parse_response(response), response  # 구조화된 딕셔너리 + 원본문