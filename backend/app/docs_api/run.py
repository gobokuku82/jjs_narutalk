from classify_docs import DocumentClassifyAgent
from write_docs import DocumentDraftAgent

def main():
    """메인 실행 함수: 문서 분류 → 문서 초안 작성 워크플로우"""
    
    print("🚀 문서 초안 작성 시스템을 시작합니다...")
    print("문서 작성 요청을 입력해주세요:")
    
    user_input = input("\n>>> ")
    
    # 1단계: 문서 분류
    print("\n" + "="*50)
    print("📋 1단계: 문서 타입 분류")
    print("="*50)
    
    classify_agent = DocumentClassifyAgent()
    classification_result = classify_agent.run(user_input)
    
    if not classification_result:
        print("\n❌ 문서 분류 실패로 인해 프로세스를 종료합니다.")
        return
    print('classification_result : ',classification_result)

    # 2단계: 문서 초안 작성
    print("\n" + "="*50)
    print("📝 2단계: 문서 초안 작성")
    print("="*50)
    
    # 분류된 문서 타입으로 DocumentDraftAgent 초기화
    doc_type = classification_result.get("doc_type")
    draft_agent = DocumentDraftAgent()
    
    # 분류 결과의 state를 전달하여 문서 초안 작성 실행
    # classification_result는 이미 완전한 State 객체이므로 그대로 전달
    draft_result = draft_agent.run_with_state(classification_result)
    
    if draft_result:
        print("\n" + "="*50)
        print("✅ 전체 프로세스 완료!")
        print("="*50)
        print(f"📋 문서 타입: {doc_type}")
        print("📝 파싱된 데이터:")
        for key, value in draft_result.items():
            if value:  # 빈 값이 아닌 경우만 출력
                print(f"  - {key}: {value}")
    else:
        print("\n❌ 문서 초안 작성 실패")

if __name__ == "__main__":
    main()