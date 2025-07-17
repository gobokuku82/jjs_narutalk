from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from typing import Annotated, TypedDict, List, Optional
import os
import docx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class State(TypedDict):
    messages: List[HumanMessage]
    doc_type: Optional[str]
    template_content: Optional[str]
    filled_data: Optional[dict]
    violation: Optional[str]
    final_doc: Optional[str]
    retry_count: int
    restart_classification: Optional[bool]
    classification_retry_count: Optional[int]
    end_process: Optional[bool]
    parse_retry_count: Optional[int]
    parse_failed: Optional[bool]

class DocumentDraftAgent:
    """지능형 문서 초안 작성 시스템"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.7):
        """
        DocumentDraftAgent 초기화
        
        Args:
            model_name: 사용할 OpenAI 모델명
            temperature: LLM 온도 설정
        """
        self.model_name = model_name
        self.temperature = temperature
        
        # 툴 정의
        self.tools = [self.check_policy_violation]
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=self.model_name, 
            temperature=self.temperature
        ).bind_tools(self.tools)
        
        # 그래프 초기화
        self.app = self._build_graph()
        
        # 문서 타입별 프롬프트 정의 (입력 요청 + 파싱 정보 통합)
        self.doc_prompts = {
            "영업방문 결과보고서": {
                "input_prompt": """
영업방문 결과보고서 작성을 위해 다음 정보를 입력해주세요:

【기본 정보】
- 방문 제목: 
- Client(고객사명): 
- 담당자: 
- 방문 Site: 
- 담당자 소속: 
- 연락처: 
- 영업제공자: 
- 방문자: 
- 방문자 소속: 

【내용】
- 고객사 개요 (신규 고객사인 경우): 
- 프로젝트 개요 (새 프로젝트인 경우): 
- 방문 및 협의내용: 
- 향후계획 및 일정: 
- 협조사항 및 공유사항: 

위 항목들을 자유롭게 작성해주세요.
                """,
                "system_prompt": """
당신은 영업방문 결과보고서 작성 전문가입니다.

사용자가 입력한 내용은 필수 출력 항목들이 섞여 들어오는데, 잘개 쪼개서 분석하여 각각의 항목별 내용에 넣어주세요.

그리고 다음 형식의 JSON으로 변환해주세요.

## 필수 출력 형식 (정확히 이 JSON 구조를 따라주세요. (중괄호) 는 기호로 인식하세요):
```json

(중괄호)
    "방문제목": "",
    "고객사명": "",
    "담당자": "",
    "방문Site": "",
    "담당자소속": "",
    "연락처": "",
    "영업제공자": "",
    "방문자": "",
    "방문자소속": "",
    "고객사개요": "",
    "프로젝트개요": "",
    "방문및협의내용": "",
    "향후계획및일정": "",
    "협조사항및공유사항": ""
(중괄호)
```

## 작성 지침:
1. 각 항목은 사용자 입력에서 파악 가능한 정보만 채워넣으세요. 없다면 공백 ("")으로 처리하세요
2. 파악되지 않는 정보는 빈 문자열("")로 처리하세요
3. "방문및협의내용", "향후계획및일정", "협조사항및공유사항"은 반드시 정중하고 공식적인 보고서 어투로 작성하세요
4. 구어체(했어, 갔어, 이야 등)는 격식 있는 표현(하였습니다, 방문하였습니다, 입니다 등)으로 변환하세요
5. 추측하지 말고 명확히 언급된 내용만 기록하세요

**응답은 오직 JSON형태로만 출력하세요. 다른 설명이나 텍스트는 포함하지 마세요.**
                """,
                "fallback_fields": {
                    "방문제목": "", "고객사명": "", "담당자": "", "방문Site": "", "담당자소속": "", 
                    "연락처": "", "영업제공자": "", "방문자": "", "방문자소속": "", "고객사개요": "", 
                    "프로젝트개요": "", "방문및협의내용": "", "향후계획및일정": "", "협조사항및공유사항": ""
                }
            },
            "제품설명회 시행 신청서": {
                "input_prompt": """
다음 정보를 입력해주세요:

【제품설명회 세부 내역】
- 구분 단일/복수:
- 일시:
- 제품명:
- PM 참석:
- 장소:
- 참석인원:
- 제품설명회 시행목적:
- 제품설명회 주요내용:

【참석자현황】
<직원인 경우>
- 팀명/이름 :

<보건의료 전문가인 경우>
- 의료기관명/이름:

위 항목들을 자유롭게 작성해주세요.
                """,
                "system_prompt": """
당신은 제품설명회 시행 신청서 작성 전문가입니다.

사용자가 입력한 내용은 필수 출력 항목들이 섞여 들어오는데, 잘개 쪼개서 분석하여 각각의 항목별 내용에 넣어주세요.

## 필수 출력 형식 (정확히 이 JSON 구조를 따라주세요. (중괄호) 는 기호로 인식하세요.):
```json
(중괄호)
    "구분단일복수": "",
    "일시": "",
    "제품명": "",
    "PM참석": "",
    "장소": "",
    "참석인원": "",
    "제품설명회시행목적": "",
    "제품설명회주요내용": "",
    "직원팀명이름": "",
    "의료기관명이름": ""
(중괄호)
```

## 작성 지침:
1. 각 항목은 사용자 입력에서 파악 가능한 정보만 채워넣으세요. 없다면 공백 ("")으로 처리하세요
2. 파악되지 않는 정보는 빈 문자열("")로 처리하세요
3. 공식적인 보고서 어투로 작성하세요
4. 구어체는 격식 있는 표현으로 변환하세요
5. 추측하지 말고 명확히 언급된 내용만 기록하세요

**응답은 오직 JSON형태로만 출력하세요. 다른 설명이나 텍스트는 포함하지 마세요.**
                """,
                "fallback_fields": {
                    "구분단일복수": "", "일시": "", "제품명": "", "PM참석": "", "장소": "",
                    "참석인원": "", "제품설명회시행목적": "", "제품설명회주요내용": "",
                    "직원팀명이름": "", "의료기관명이름": ""
                }
            },
            "제품설명회 시행 결과보고서": {
                "input_prompt": """
다음 정보를 입력해주세요:

【제품설명회 세부 내역】
- 구분 단일/복수:
- 일시:
- 제품명:
- PM 참석:
- 장소:
- 참석인원:
- 제품설명회 시행목적:
- 제품설명회 주요내용:

【참석자현황】
<직원인 경우>
- 팀명/이름 :

<보건의료 전문가인 경우>
- 의료기관명/이름:

【예산사용내역】
- 금액:
- 메뉴:
- 주류:
- 1인 금액:

위 항목들을 자유롭게 작성해주세요.
                """,
                "system_prompt": """
당신은 제품설명회 시행 결과보고서 작성 전문가입니다.

사용자가 입력한 문장을 분석하여 아래 JSON 형식에 맞게 각 항목에 정확히 대응되는 값을 채워주세요.

- 항목 외의 설명, 안내 문구, 개행 등의 추가 텍스트를 절대 출력하지 마세요.
- 반드시 JSON 객체 전체만 출력하세요. JSON 외 텍스트가 포함되면 안 됩니다.
- 값이 명확히 언급되지 않은 항목은 빈 문자열("")로 채우세요.

다음 JSON 구조를 정확히 그대로 사용하세요. (중괄호) 는 기호로 인식하세요.:

(중괄호)
    "구분단일복수": "",
    "일시": "",
    "제품명": "",
    "PM참석": "",
    "장소": "",
    "참석인원": "",
    "제품설명회시행목적": "",
    "제품설명회주요내용": "",
    "직원팀명이름": "",
    "의료기관명이름": "",
    "금액": "",
    "메뉴": "",
    "주류": "",
    "일인금액": ""
(중괄호)

## 작성 지침:
1. 각 항목은 사용자 입력에서 파악 가능한 정보만 채워넣으세요. 없다면 공백 ("")으로 처리하세요
2. 파악되지 않는 정보는 빈 문자열("")로 처리하세요
3. 공식적인 보고서 어투로 작성하세요
4. 구어체는 격식 있는 표현으로 변환하세요
5. 추측하지 말고 명확히 언급된 내용만 기록하세요

**응답은 오직 JSON형태로만 출력하세요. 다른 설명이나 텍스트는 포함하지 마세요.**
                """,
                "fallback_fields": {
                    "구분단일복수": "", "일시": "", "제품명": "", "PM참석": "", "장소": "",
                    "참석인원": "", "제품설명회시행목적": "", "제품설명회주요내용": "",
                    "직원팀명이름": "", "의료기관명이름": "", "금액": "", "메뉴": "", "주류": "", "일인금액": ""
                }
            }
        }
    
    @tool
    def check_policy_violation(self, content: Annotated[str, "작성된 문서 본문"]) -> str:
        """작성된 문서 내용이 회사 규정을 위반하는지 검사합니다."""
        # 실제 규정 검사 로직 (예시)
        violations = []
        
        # 금지어 체크
        forbidden_words = ["금지어", "부정적", "비밀", "기밀유출"]
        for word in forbidden_words:
            if word in content:
                violations.append(f"금지어 포함: '{word}'")
        
        # 기본적인 필수 항목만 체크 (너무 엄격하지 않게)
        if len(content.strip()) < 10:
            violations.append("입력 내용이 너무 짧습니다")
        
        # 최소한의 정보 확인
        basic_info_found = any(keyword in content for keyword in ["방문", "고객", "회사", "협의", "논의", "만나"])
        if not basic_info_found:
            violations.append("방문 관련 기본 정보가 부족합니다")
        
        if violations:
            return " | ".join(violations)
        return "OK"
    
    def classify_doc_type(self, state: State) -> State:
        """LLM을 사용해서 사용자 요청을 분석하고 문서 타입을 분류합니다."""
        # 재시도 카운터 초기화 (새로운 분류 시작시에만)
        if state.get("classification_retry_count") is None:
            state["classification_retry_count"] = 0
        
        user_message = state["messages"][-1].content
        
        classification_prompt = ChatPromptTemplate.from_messages([
            ("system", """
사용자의 요청을 분석하여 다음 문서 타입 중 하나로 분류해주세요:
1. 영업방문 결과보고서 - 고객 방문, 영업 활동 관련
2. 제품설명회 시행 신청서 - 제품설명회 진행 계획, 신청 관련
3. 제품설명회 시행 결과보고서 - 제품설명회 완료 후 결과 보고 관련

반드시 위 3가지 중 하나의 정확한 문서 타입 이름만 응답해주세요.
앞에 숫자는 제거하고 문서명만 출력하세요.
            """),
            ("human", "{user_request}")
        ])
        
        try:
            response = self.llm.invoke(classification_prompt.format_messages(user_request=user_message))
            # response.content가 string인지 확인
            content = response.content
            if isinstance(content, str):
                doc_type = content.strip()
            else:
                doc_type = str(content).strip()
            
            # 유효한 문서 타입인지 확인
            valid_types = ["영업방문 결과보고서", "제품설명회 시행 신청서", "제품설명회 시행 결과보고서"]
            if doc_type not in valid_types:
                doc_type = response
                
            state["doc_type"] = doc_type
            print(f"📋 LLM 문서 타입 분류: {doc_type}")
            
        except Exception as e:
            print(f"⚠️ LLM 분류 실패, 기본값 사용: {e}")
            state["doc_type"] = response
        
        return state

    def validate_doc_type(self, state: State) -> State:
        """분류된 문서 타입이 유효한지 확인합니다."""
        doc_type = state.get("doc_type", "")
        valid_types = ["영업방문 결과보고서", "제품설명회 시행 신청서", "제품설명회 시행 결과보고서"]
        
        if doc_type in valid_types:
            print(f"✅ 유효한 문서 타입: {doc_type}")
            # 분류 성공시 재시도 카운터 리셋
            state["classification_retry_count"] = 0
            return state
        else:
            # 재시도 횟수 증가
            current_count = state.get("classification_retry_count") or 0
            retry_count = current_count + 1
            state["classification_retry_count"] = retry_count
            
            print(f"❌ 유효하지 않은 문서 타입: '{doc_type}'")
            print(f"🔄 재분류 시도 {retry_count}/3")
            
            if retry_count >= 3:
                print("⚠️ 최대 재시도 횟수 초과. 처리를 종료합니다.")
                state["classification_retry_count"] = retry_count
                state["end_process"] = True
            else:
                print("📝 다시 문서 타입을 입력해주세요:")
                user_input = input("\n>>> ")
                state["messages"].append(HumanMessage(content=user_input))
            
            return state

    def ask_required_fields(self, state: State) -> State:
        """문서 타입에 따라 필요한 정보를 사용자에게 요청합니다."""
        doc_type = state.get("doc_type", "")
        
        # 파싱 실패 플래그 리셋
        state["parse_failed"] = False
        
        prompt_text = self.doc_prompts[doc_type]["input_prompt"]
        print(f"\n❓ 필수 정보 입력 요청:")
        print(prompt_text)
        print("\n아래에 정보를 입력해주세요:")
        
        # 실제 사용자 입력 받기
        user_input = input("\n>>> ")
        
        # 사용자 입력을 메시지에 추가
        state["messages"].append(HumanMessage(content=user_input))
        
        return state

    def parse_user_input(self, state: State) -> State:
        user_input = str(state["messages"][-1].content)
        doc_type = state["doc_type"]
        response = None  # 에러 발생 대비 초기화

        if state.get("parse_retry_count") is None:
            state["parse_retry_count"] = 0

        system_prompt = self.doc_prompts[doc_type]["system_prompt"]
        if not system_prompt:
            raise ValueError(f"문서 타입에 대한 시스템 프롬프트가 없습니다: {doc_type}")

        # 중괄호 이스케이프 처리
        escaped_input = user_input.replace("{", "{{").replace("}", "}}")

        parsing_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{user_input}")
        ])

        try:
            formatted_messages = parsing_prompt.format_messages(user_input=escaped_input)
            print("📨 LLM에 전달된 메시지:")
            for m in formatted_messages:
                print(f"[{m.type.upper()}] {m.content}")

            response = self.llm.invoke(formatted_messages)

            content = response.content
            json_str = content if isinstance(content, str) else str(content)
            print(f"\n🔍 LLM 응답 내용:\n{json_str}")

            if "{" in json_str and "}" in json_str:
                start = json_str.find("{")
                end = json_str.rfind("}") + 1
                clean_json = json_str[start:end]
                print(f"\n🔍 추출된 JSON:\n{clean_json}")

                import json
                parsed_data = json.loads(clean_json)
                state["filled_data"] = parsed_data
                state["parse_failed"] = False
                print("✅ 파싱 성공:", parsed_data)
            else:
                raise ValueError("구조화된 JSON 형식을 찾을 수 없음")

        except Exception as e:
            print("\n⚠️ 예외 발생!")
            if response:
                print("응답 내용:")
                print(response)
            else:
                print("⚠️ response 객체가 존재하지 않습니다.")
            print(f"⚠️ 예외 메시지: {e}")

            retry_count = state.get("parse_retry_count", 0) + 1
            state["parse_retry_count"] = retry_count

            if retry_count >= 3:
                print("⚠️ 파싱 재시도 초과. 기본값 사용.")
                fallback_data = self.doc_prompts[doc_type]["fallback_fields"]
                state["filled_data"] = fallback_data
            else:
                print(f"🔄 재시도 {retry_count}/3")
                state["parse_failed"] = True

        return state

    def run_check_policy_violation(self, state: State) -> State:
        """입력된 데이터가 회사 규정을 위반하는지 검사합니다."""
        filled_data = state["filled_data"] or {}
        content = " ".join(str(v) for v in filled_data.values())
        
        try:
            result = self.check_policy_violation.invoke({"content": content})
            state["violation"] = result
            print(f"🔍 규정 검사 결과: {result}")
            
            # 규정 위반이 없으면 parse_user_input 결과를 출력
            if result == "OK":
                print("\n✅ 규정 위반이 없습니다!")
                print("=" * 60)
                print("📝 파싱된 사용자 입력 데이터:")
                print("=" * 60)
                
                for key, value in filled_data.items():
                    if value:  # 빈 값이 아닌 경우만 출력
                        print(f"- {key}: {value}")
                
                print("=" * 60)
                print("✅ 문서 데이터 파싱 완료!")
                return state
            else:
                print("❌ 규정 위반이 발견되었으므로 재입력을 요청합니다.")
                return state
        
        except Exception as e:
            print(f"⚠️ 규정 검사 실패: {e}")
            state["violation"] = "OK"  # 안전한 기본값
            return state

    def inform_violation(self, state: State) -> State:
        """규정 위반이 발견되었을 때 사용자에게 알리고 재입력을 요청합니다."""
        violation = state["violation"]
        retry_count = state.get("retry_count", 0) + 1
        state["retry_count"] = retry_count
        
        print(f"\n⚠️ 규정 위반 사항 발견 (시도 #{retry_count}):")
        print(f"문제점: {violation}")
        print("\n다시 입력해주세요:")
        
        # 재입력 받기
        user_input = input("\n>>> ")
        state["messages"].append(HumanMessage(content=user_input))
        
        return state

    def doc_type_validation_router(self, state: State) -> str:
        """문서 타입 유효성 검사 결과에 따라 다음 노드를 결정합니다."""
        doc_type = state.get("doc_type", "")
        valid_types = ["영업방문 결과보고서", "제품설명회 시행 신청서", "제품설명회 시행 결과보고서"]
        retry_count = state.get("classification_retry_count") or 0
        
        if state.get("end_process"):
            return "END"
        elif doc_type in valid_types:
            return "ask_required_fields"
        else:
            return "classify_doc_type"

    def ask_fields_router(self, state: State) -> str:
        """필수 정보 요청 후 다음 노드를 결정합니다."""
        return "parse_user_input"
    
    def parse_router(self, state: State) -> str:
        """파싱 결과에 따라 다음 노드를 결정합니다."""
        if state.get("parse_failed"):
            return "ask_required_fields"
        else:
            return "check_policy_violation"

    def policy_check_router(self, state: State) -> str:
        """규정 검사 결과에 따라 다음 노드를 결정합니다."""
        if state.get("violation") == "OK":
            return "END"
        else:
            # 재시도 횟수 제한 (무한 루프 방지)
            retry_count = state.get("retry_count", 0)
            if retry_count >= 3:
                print("⚠️ 최대 재시도 횟수 초과, 처리를 종료합니다.")
                return "END"
            return "inform_violation"

    def _build_graph(self):
        """LangGraph 워크플로우를 구성합니다."""
        graph = StateGraph(State)

        # 노드 추가
        graph.add_node("classify_doc_type", self.classify_doc_type)
        graph.add_node("validate_doc_type", self.validate_doc_type)
        graph.add_node("ask_required_fields", self.ask_required_fields)
        graph.add_node("parse_user_input", self.parse_user_input)
        graph.add_node("check_policy_violation", self.run_check_policy_violation)
        graph.add_node("inform_violation", self.inform_violation)

        # 흐름 연결
        graph.set_entry_point("classify_doc_type")
        
        # 문서 타입 분류 → 유효성 검사
        graph.add_edge("classify_doc_type", "validate_doc_type")
        
        # 유효성 검사 결과에 따른 분기
        graph.add_conditional_edges(
            "validate_doc_type",
            self.doc_type_validation_router,
            {
                "ask_required_fields": "ask_required_fields",  # 유효한 타입
                "classify_doc_type": "classify_doc_type",      # 재분류 필요
                "END": END                                     # 최대 재시도 횟수 초과시 종료
            }
        )

        # 조건부 분기 - 문서 타입 재시작 또는 정상 진행
        graph.add_conditional_edges(
            "ask_required_fields",
            self.ask_fields_router,
            {
                "classify_doc_type": "classify_doc_type",  # 재시작
                "parse_user_input": "parse_user_input"    # 정상 진행
            }
        )

        # 파싱 결과에 따른 분기
        graph.add_conditional_edges(
            "parse_user_input",
            self.parse_router,
            {
                "ask_required_fields": "ask_required_fields",  # 파싱 실패시 재입력
                "check_policy_violation": "check_policy_violation"  # 파싱 성공시 규정 검사
            }
        )

        # 조건부 분기 - 규정 위반 시 재입력 루프, OK시 종료
        graph.add_conditional_edges(
            "check_policy_violation",
            self.policy_check_router,
            {
                "END": END,
                "inform_violation": "inform_violation"
            }
        )

        # 규정 위반 시 재입력 → 파싱 → 검사 루프
        graph.add_edge("inform_violation", "parse_user_input")

        return graph.compile()
    
    def run(self, user_input: str):
        """워크플로우를 실행하고 결과를 반환합니다."""
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "doc_type": None,
            "template_content": None,
            "filled_data": None,
            "violation": None,
            "final_doc": None,
            "retry_count": 0,
            "restart_classification": None,
            "classification_retry_count": None
        }
        
        # 그래프 실행
        final_state = self.app.invoke(initial_state)
        
        # 파싱 결과 반환
        if final_state.get("filled_data"):
            print("\n" + "="*50)
            print("📄 최종 파싱 결과:")
            print("="*50)
            
            import json
            result = json.dumps(final_state["filled_data"], indent=2, ensure_ascii=False)
            print(result)
            
            return final_state["filled_data"]
        else:
            print("\n❌ 파싱 결과가 없습니다.")
            return None

if __name__ == "__main__":
    # 에이전트 실행 예시
    agent = DocumentDraftAgent()
    
    print("🚀 문서 초안 작성 시스템을 시작합니다...")
    print("문서 작성 요청을 입력해주세요:")
    
    user_input = input("\n>>> ")
    
    # 에이전트 실행
    result = agent.run(user_input)
    
    if result:
        print("\n✅ 처리 완료!")
        print("반환된 결과:", result)
    else:
        print("\n❌ 처리 실패")