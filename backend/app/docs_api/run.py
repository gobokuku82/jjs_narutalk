from typing import Optional
from langchain_core.messages import HumanMessage
from document_draft_agent import DocumentDraftAgent, State


def run_document_agent(user_request: Optional[str] = None) -> dict:
    """
    문서 작성 에이전트를 실행하고 결과를 반환합니다.
    
    Args:
        user_request: 사용자 요청 (None이면 입력 받음)
        
    Returns:
        최종 상태 딕셔너리
    """
    print("\n" + "="*60)
    print("🤖 지능형 문서 초안 작성 시스템")
    print("="*60)
    
    print("\n사용할 수 있는 문서 타입:")
    print("1. 영업방문 결과보고서")
    print("2. 제품설명회 시행 신청서") 
    print("3. 제품설명회 시행 결과보고서")
    
    if user_request is None:
        print("\n어떤 문서를 작성하시겠습니까?")
        user_request = input(">>> ")
        
    # 에이전트 생성
    agent = DocumentDraftAgent()
    
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
        final_state = agent.app.invoke(initial_state)
        
        print(f"\n" + "="*60)
        print("📊 최종 결과 요약")
        print("="*60)
        print(f"📋 문서 타입: {final_state.get('doc_type', 'N/A')}")
        print(f"🔄 재시도 횟수: {final_state.get('retry_count', 0)}")
        
        # 입력 데이터 상세 출력
        filled_data = final_state.get('filled_data', {})
        if filled_data:
            print(f"\n📝 파싱된 입력 데이터:")
            print("-" * 40)
            for key, value in filled_data.items():
                if value:  # 빈 값이 아닌 경우만 출력
                    print(f"• {key}: {value}")
            print("-" * 40)
        
        print(f"\n✅ 문서 작성 프로세스 완료!")
        
        return final_state
        
    except Exception as e:
        print(f"\n❌ 시스템 오류: {e}")
        print("문제가 지속되면 관리자에게 문의하세요.")
        return {}


def analyze_results(result: dict):
    """
    에이전트 실행 결과를 분석하고 요약 정보를 출력합니다.
    
    Args:
        result: 에이전트 실행 결과 딕셔너리
    """
    if not result:
        print("❌ 분석할 결과가 없습니다.")
        return
    
    print(f"\n" + "="*60)
    print("🔍 결과 분석")
    print("="*60)
    
    # 기본 정보
    doc_type = result.get('doc_type')
    retry_count = result.get('retry_count', 0)
    violation = result.get('violation')
    filled_data = result.get('filled_data', {})
    
    print(f"📋 문서 타입: {doc_type}")
    print(f"🔄 재시도 횟수: {retry_count}")
    print(f"🔍 규정 검사: {'통과' if violation == 'OK' else '위반 발견'}")
    
    # 데이터 완성도 분석
    if filled_data:
        total_fields = len(filled_data)
        filled_fields = sum(1 for value in filled_data.values() if value)
        completion_rate = (filled_fields / total_fields) * 100 if total_fields > 0 else 0
        
        print(f"📊 데이터 완성도: {completion_rate:.1f}% ({filled_fields}/{total_fields})")
        
        # 빈 필드 확인
        empty_fields = [key for key, value in filled_data.items() if not value]
        if empty_fields:
            print(f"⚠️ 빈 필드: {', '.join(empty_fields[:3])}{'...' if len(empty_fields) > 3 else ''}")
    
    # 처리 상태
    if retry_count == 0:
        print("✅ 처리 상태: 정상 완료")
    elif retry_count < 3:
        print(f"⚠️ 처리 상태: {retry_count}회 재시도 후 완료")
    else:
        print("❌ 처리 상태: 최대 재시도 횟수 초과")


# -----------------------
# 실행
# -----------------------
if __name__ == "__main__":
    # 문서 작성 에이전트 실행
    result = run_document_agent()
    
    # 결과 분석
    analyze_results(result)