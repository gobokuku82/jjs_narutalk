from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()

class Get_Keyword:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# 프롬프트 템플릿 정의
template = ChatPromptTemplate.from_template(
    "당신은 친절한 조언가입니다. 사용자가 다음과 같은 고민을 하고 있어요:\n\n\"{user_question}\"\n\n이에 대해 따뜻하고 유용한 조언을 해주세요."
)

# 사용자 입력 예시
user_input = input("고민을 입력하세요: ")

# 템플릿에 사용자 입력 삽입
messages = template.format_messages(user_question=user_input)

# 응답 생성
response = llm(messages)

# 출력
print("\n🤖 ChatGPT의 조언:")
print(response.content)
