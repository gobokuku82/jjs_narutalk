from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import yaml

# 환경 변수 로드
load_dotenv()

class Tools:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        self.prompts = self._load_prompts()
    
    def _load_prompts(self):
        """YAML 파일에서 프롬프트를 로드합니다."""
        try:
            with open('prompt.yaml', 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print("Warning: prompt.yaml 파일을 찾을 수 없습니다.")
            return {"prompts": {}}

    def get_keyword(self, user_input):
        # YAML에서 키워드 추출 프롬프트 가져오기
        keyword_template = self.prompts.get("prompts", {}).get("keyword_extraction", "")
        
        if not keyword_template:
            # 기본 템플릿 사용
            keyword_template = os.getenv("KEYWORD_TEMPLATE", 
                                       "당신은 반드시 키워드를 추출하는 챗봇입니다.\n사용자의 질문에서 키워드를 반드시 추출하세요.\n\n\"{user_question}\"\n\n아래 조건을 만족해서 출력하세요.\n\n1. 키워드는 리스트 형태로 반드시 출력\n\n2. 문자열은 큰따옴표로 감싸서 출력하세요.\n\n3. 리스트외에는 아무것도 출력하지 마세요.\n\n4. 키워드는 최대 5개까지 추출하세요.\n\n5. 복합어는 분해해서 의미 있는 단어 단위로 나눠줘\n\n예를 들어 '임직원 교육기간'이라면 '임직원', '교육', '기간'처럼 나눠줘. ")
        
        template = ChatPromptTemplate.from_template(keyword_template)
        messages = template.format_messages(user_question=user_input)
        response = self.llm.invoke(messages)
        return response.content

    def analyze_document(self, user_question, category, document):
        # YAML에서 문서 분석 프롬프트 가져오기
        analysis_template = self.prompts.get("prompts", {}).get("document_analysis", "")        
        template = ChatPromptTemplate.from_template(analysis_template)
        messages = template.format_messages(
            user_question=user_question,
            category=category,
            document=document
        )
        response = self.llm.invoke(messages)
        return response.content
        
    def get_document(self, category):
        s3_document = None
        if category == "매입 및 매출 일일보고서":
            s3_document = category
            return s3_document
        elif category == "사업실적 분석보고서":
            s3_document = category
            return s3_document
        elif category == "영업계획안":
            s3_document = category
            return s3_document
        elif category == "영업방문 결과보고서":
            s3_document = os.path.join("S3", "영업방문 결과보고서(기본형).doc")
            return s3_document
        elif category == "주간영업 보고서":
            s3_document = category
            return s3_document
        elif category == "판매실적 보고서":
            s3_document = category
            return s3_document

    def write_choan(self, user_input, category, document):
        # YAML에서 choan 템플릿 가져오기
        choan_template = self.prompts.get("prompts", {}).get("choan_template", "")
        
        if not choan_template:
            # 기본 템플릿 사용
            choan_template = """
            당신은 업무 보고서 작성 전문가입니다.
            다음 정보를 바탕으로 {category} 보고서를 작성해주세요.
            
            사용자 요청사항: {user_input}
            참고 문서: {document}
            """
        
        template = ChatPromptTemplate.from_template(choan_template)
        messages = template.format_messages(
            user_input=user_input,
            category=category,
            document=document
        )
        response = self.llm.invoke(messages)
        return response.content
        