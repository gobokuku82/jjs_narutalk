import requests
import json

# API 서버 URL
BASE_URL = "http://localhost:8000"

def test_classify_and_write():
    """분류 및 작성 API 테스트"""
    
    # 1단계: 문서 분류 테스트
    print("1단계: 문서 분류 테스트")
    print("=" * 50)
    
    classify_data = {
        "user_input": "영업방문 결과보고서를 작성해줘"
    }
    
    response = requests.post(f"{BASE_URL}/api/docs/classify", json=classify_data)
    print(f"분류 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        classify_result = response.json()
        print("분류 결과:")
        print(json.dumps(classify_result, indent=2, ensure_ascii=False))
        
        if classify_result["success"]:
            state = classify_result["state"]
            
            # 2단계: 문서 작성 테스트
            print("\n2단계: 문서 작성 테스트")
            print("=" * 50)
            
            write_data = {
                "state": state,
                "user_input": """고객은 아이유이비인후과, 담당자와 방문자는 손현성, 방문자 소속은 좋은제약이야.
연락처는 010-3752-5265이고 고객사 개요는 최근 오픈한 이비인후과야
프로젝트 개요는 신약 거래처 확보이고
방문 및 협의내용은 25년 7월 16일 방문하여 새로운 신약 소개 및 가격과 로얄티 소개이고, 향후계획 및 일정은 25년 7월 18일 방문하여 가격 협상 및 로얄티 협상"""
            }
            
            response = requests.post(f"{BASE_URL}/api/docs/write", json=write_data)
            print(f"작성 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                write_result = response.json()
                print("작성 결과:")
                print(json.dumps(write_result, indent=2, ensure_ascii=False))
            else:
                print(f"작성 요청 실패: {response.text}")
        else:
            print(f"분류 실패: {classify_result['error']}")
    else:
        print(f"분류 요청 실패: {response.text}")

if __name__ == "__main__":
    test_classify_and_write()