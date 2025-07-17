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

# -----------------------
# LangGraph State Schema
# -----------------------
class State(TypedDict):
    messages: List[HumanMessage]
    doc_type: Optional[str]
    template_content: Optional[str]
    filled_data: Optional[dict]
    violation: Optional[str]
    final_doc: Optional[str]
    retry_count: int
    restart_classification: Optional[bool]

# -----------------------
# 툴 정의
# -----------------------
@tool
def check_policy_violation(content: Annotated[str, "작성된 문서 본문"]) -> str:
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

# -----------------------
# LLM 설정
# -----------------------
tools = [check_policy_violation]
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7).bind_tools(tools)

# -----------------------
# 노드 정의
# -----------------------
def classify_doc_type(state: State) -> State:
    """LLM을 사용해서 사용자 요청을 분석하고 문서 타입을 분류합니다."""
    # 재시작 플래그 초기화
    state["restart_classification"] = False
    
    user_message = state["messages"][-1].content
    
    classification_prompt = ChatPromptTemplate.from_messages([
        ("system", """
사용자의 요청을 분석하여 다음 문서 타입 중 하나로 분류해주세요:
1. 영업방문 결과보고서 - 고객 방문, 영업 활동 관련
2. 주간 영업보고서 - 주간 실적, 목표 달성 관련  
3. 매입 매출 보고서 - 재무, 회계 관련

앞에 숫자는 제거하고 정확한 문서 타입 이름만 응답해주세요.
        """),
        ("human", "{user_request}")
    ])
    
    try:
        response = llm.invoke(classification_prompt.format_messages(user_request=user_message))
        # response.content가 string인지 확인
        content = response.content
        if isinstance(content, str):
            doc_type = content.strip()
        else:
            doc_type = str(content).strip()
        
        # 유효한 문서 타입인지 확인
        valid_types = ["영업방문 결과보고서", "주간 영업보고서", "매입 매출 보고서"]
        if doc_type not in valid_types:
            doc_type = "영업방문 결과보고서"  # 기본값
              
        state["doc_type"] = doc_type
        print(f"📋 LLM 문서 타입 분류: {doc_type}")
        
    except Exception as e:
        print(f"⚠️ LLM 분류 실패, 기본값 사용: {e}")
        state["doc_type"] = "영업방문 결과보고서"
    
    return state



def ask_required_fields(state: State) -> State:
    """문서 타입에 따라 필요한 정보를 사용자에게 요청합니다."""
    doc_type = state.get("doc_type", "")
    
    prompts = {
        "영업방문 결과보고서": """
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
        "주간 영업보고서": """
다음 정보를 입력해주세요:
1. 주간 목표: 
2. 달성율: 
3. 주요 성과: 
4. 특이사항: 
5. 다음주 계획: 
        """,
        "매입 매출 보고서": """
다음 정보를 입력해주세요:
1. 매입 금액: 
2. 매출 금액: 
3. 이익률: 
4. 주요 거래처: 
5. 특이사항: 
        """
    }
    
    # 문서 타입 검증 - 없거나 유효하지 않으면 처음부터 다시 시작
    if not doc_type or doc_type not in prompts:
        print("❌ 문서 타입이 올바르게 설정되지 않았습니다.")
        print("🔄 문서 타입 분류부터 다시 시작합니다...")
        state["doc_type"] = None
        state["restart_classification"] = True
        return state
        
    prompt_text = prompts[doc_type]
    print(f"\n❓ 필수 정보 입력 요청:")
    print(prompt_text)
    print("\n아래에 정보를 입력해주세요:")
    
    # 실제 사용자 입력 받기
    user_input = input("\n>>> ")
    
    # 사용자 입력을 메시지에 추가
    state["messages"].append(HumanMessage(content=user_input))
    
    return state

def parse_user_input(state: State) -> State:
    """LLM을 사용해서 사용자 입력을 파싱하고 구조화된 데이터로 변환합니다."""
    user_input = str(state["messages"][-1].content)  # str로 변환하여 안전하게 처리
    doc_type = state["doc_type"]
    
    parsing_prompt = ChatPromptTemplate.from_messages([
        ("system", """
당신은 영업방문 결과보고서 작성 전문가입니다.

사용자가 입력한 내용은 필수 출력 항목들이 섞여 들어오는데, 잘개 쪼개서 분석하여 각각의 항목별 내용에 넣어주세요요.

그리고 다음 형식의 JSON으로 변환해주세요.

## 필수 출력 형식 (정확히 이 JSON 구조를 따라주세요):
```json
{{
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
}}
```

## 작성 지침:
1. 각 항목은 사용자 입력에서 파악 가능한 정보만 채워넣으세요
2. 파악되지 않는 정보는 빈 문자열("")로 처리하세요
3. "방문및협의내용", "향후계획및일정", "협조사항및공유사항"은 반드시 정중하고 공식적인 보고서 어투로 작성하세요
4. 구어체(했어, 갔어, 이야 등)는 격식 있는 표현(하였습니다, 방문하였습니다, 입니다 등)으로 변환하세요
5. 추측하지 말고 명확히 언급된 내용만 기록하세요

**응답은 오직 JSON만 출력하세요. 다른 설명이나 텍스트는 포함하지 마세요.**
        """),
        ("human", "{user_input}")
    ])
    
    try:
        response = llm.invoke(parsing_prompt.format_messages(user_input=user_input))
        
        # JSON 파싱 시도
        import json
        content = response.content
        if isinstance(content, str):
            json_str = content
        else:
            json_str = str(content)
        
        # JSON 부분만 추출 (```json ... ``` 형태에서)
        if "{" in json_str and "}" in json_str:
            start = json_str.find("{")
            end = json_str.rfind("}") + 1
            clean_json = json_str[start:end]
            
            parsed_data = json.loads(clean_json)
            state["filled_data"] = parsed_data
            print(f"📝 LLM 변환 완료: 사용자 입력을 구조화된 데이터로 변환했습니다.")
            print(f"📝 변환된 데이터: {parsed_data}")
        else:
            raise ValueError("구조화된 데이터 형식을 찾을 수 없음")
        
    except Exception as e:
        print(f"⚠️ LLM 데이터 변환 실패: {e}")
        print("🔄 기본 데이터로 처리합니다...")
        
        # 기본 데이터로 폴백 (원문 그대로 저장)
        state["filled_data"] = {
            "방문제목": "", "고객사명": "", "담당자": "", "방문Site": "", "담당자소속": "", 
            "연락처": "", "영업제공자": "", "방문자": "", "방문자소속": "", "고객사개요": "", 
            "프로젝트개요": "", "방문및협의내용": user_input, "향후계획및일정": "", "협조사항및공유사항": ""
        }

    
    return state

def run_check_policy_violation(state: State) -> State:
    """입력된 데이터가 회사 규정을 위반하는지 검사합니다."""
    filled_data = state["filled_data"] or {}
    content = " ".join(str(v) for v in filled_data.values())
    
    try:
        result = check_policy_violation.invoke({"content": content})
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

def inform_violation(state: State) -> State:
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



# -----------------------
# 조건부 라우팅 함수
# -----------------------
def ask_fields_router(state: State) -> str:
    """필수 정보 요청 후 다음 노드를 결정합니다."""
    if state.get("restart_classification"):
        return "classify_doc_type"
    else:
        return "parse_user_input"

def policy_check_router(state: State) -> str:
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

# -----------------------
# 그래프 정의
# -----------------------
graph = StateGraph(State)

graph.add_node("classify_doc_type", classify_doc_type)
graph.add_node("ask_required_fields", ask_required_fields)
graph.add_node("parse_user_input", parse_user_input)
graph.add_node("check_policy_violation", run_check_policy_violation)
graph.add_node("inform_violation", inform_violation)

# 흐름 연결
graph.set_entry_point("classify_doc_type")
graph.add_edge("classify_doc_type", "ask_required_fields")

# 조건부 분기 - 문서 타입 재시작 또는 정상 진행
graph.add_conditional_edges(
    "ask_required_fields",
    ask_fields_router,
    {
        "classify_doc_type": "classify_doc_type",  # 재시작
        "parse_user_input": "parse_user_input"    # 정상 진행
    }
)

graph.add_edge("parse_user_input", "check_policy_violation")

# 조건부 분기 - 규정 위반 시 재입력 루프, OK시 종료
graph.add_conditional_edges(
    "check_policy_violation",
    policy_check_router,
    {
        "END": END,
        "inform_violation": "inform_violation"
    }
)

# 규정 위반 시 재입력 → 파싱 → 검사 루프
graph.add_edge("inform_violation", "parse_user_input")

# -----------------------
# 실행
# -----------------------
app = graph.compile()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 지능형 문서 초안 작성 시스템")
    print("="*60)
    
    print("\n사용할 수 있는 문서 타입:")
    print("1. 영업방문 결과보고서")
    print("2. 주간 영업보고서") 
    print("3. 매입 매출 보고서")
    
    print("\n어떤 문서를 작성하시겠습니까?")
    user_request = input(">>> ")
    
    # 초기 상태 설정
    initial_state: State = {
        "messages": [HumanMessage(content=user_request)],
        "doc_type": None,
        "template_content": None,
        "filled_data": None,
        "violation": None,
        "final_doc": None,
        "retry_count": 0,
        "restart_classification": False
    }
    
    try:
        # 워크플로우 실행
        final_state = app.invoke(initial_state)
        
        print(f"\n" + "="*60)
        print("📊 최종 결과 요약")
        print("="*60)
        print(f"📋 문서 타입: {final_state.get('doc_type', 'N/A')}")
        print(f"📝 입력 데이터: {final_state.get('filled_data', {})}")
        print(f"🔄 재시도 횟수: {final_state.get('retry_count', 0)}")
        
    except Exception as e:
        print(f"\n❌ 시스템 오류: {e}")
        print("문제가 지속되면 관리자에게 문의하세요.")