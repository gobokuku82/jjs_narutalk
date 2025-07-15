import requests
import json
import time

def test_integration():
    print("=== NaruTalk AI 시스템 통합 테스트 ===\n")
    
    base_url = "http://localhost:8000"
    stream_url = f"{base_url}/api/v1/tool-calling/chat/stream"
    
    # 테스트 시나리오
    test_scenarios = [
        {
            "name": "직원 정보 검색",
            "query": "김철수 직원의 연락처를 알려주세요",
            "expected_agent": "employee_agent"
        },
        {
            "name": "문서 검색",
            "query": "회사 복리후생 정책을 찾아주세요", 
            "expected_agent": "db_agent"
        },
        {
            "name": "거래처 분석",
            "query": "주요 거래처 분석 결과를 보여주세요",
            "expected_agent": "client_agent"
        },
        {
            "name": "컴플라이언스 검토",
            "query": "영업 활동 중 규정 위반 사항을 검토해주세요",
            "expected_agent": "docs_agent"
        },
        {
            "name": "일반 대화",
            "query": "안녕하세요, 날씨가 좋네요",
            "expected_agent": "general_chat"
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"📋 테스트 {i}: {scenario['name']}")
        print(f"   질문: {scenario['query']}")
        
        data = {
            "message": scenario['query'],
            "user_id": "integration_test",
            "session_id": f"test_session_{i}"
        }
        
        try:
            start_time = time.time()
            response = requests.post(stream_url, json=data, stream=True, timeout=30)
            
            if response.status_code == 200:
                agent_detected = None
                token_count = 0
                response_text = ""
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                data_str = line_str[6:]
                                if data_str != '[DONE]':
                                    data_obj = json.loads(data_str)
                                    
                                    if data_obj.get('type') == 'start':
                                        agent_detected = data_obj.get('agent')
                                    elif data_obj.get('type') == 'token':
                                        token_count += 1
                                        response_text += data_obj.get('word', '')
                                    elif data_obj.get('type') == 'end':
                                        break
                            except:
                                continue
                
                end_time = time.time()
                response_time = round(end_time - start_time, 2)
                
                # 결과 평가
                agent_correct = agent_detected == scenario['expected_agent']
                has_response = len(response_text.strip()) > 0
                
                result = {
                    "scenario": scenario['name'],
                    "query": scenario['query'],
                    "expected_agent": scenario['expected_agent'],
                    "actual_agent": agent_detected,
                    "agent_correct": agent_correct,
                    "response_time": response_time,
                    "token_count": token_count,
                    "has_response": has_response,
                    "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text
                }
                
                results.append(result)
                
                # 결과 출력
                status = "✅ 성공" if agent_correct and has_response else "❌ 실패"
                print(f"   결과: {status}")
                print(f"   라우팅: {agent_detected} (예상: {scenario['expected_agent']})")
                print(f"   응답시간: {response_time}초, 토큰: {token_count}개")
                print(f"   응답미리보기: {result['response_preview'][:80]}...")
                
            else:
                print(f"   ❌ HTTP 오류: {response.status_code}")
                results.append({
                    "scenario": scenario['name'],
                    "error": f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            print(f"   ❌ 요청 실패: {str(e)}")
            results.append({
                "scenario": scenario['name'],
                "error": str(e)
            })
        
        print()
    
    # 전체 결과 요약
    print("=" * 60)
    print("📊 통합 테스트 결과 요약")
    print("=" * 60)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r.get('agent_correct') and r.get('has_response'))
    error_tests = sum(1 for r in results if 'error' in r)
    
    print(f"총 테스트: {total_tests}개")
    print(f"성공: {successful_tests}개")
    print(f"실패: {total_tests - successful_tests - error_tests}개")
    print(f"오류: {error_tests}개")
    print(f"성공률: {round(successful_tests / total_tests * 100, 1)}%")
    
    if successful_tests == total_tests - error_tests:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("✅ NaruTalk AI 시스템이 정상적으로 작동하고 있습니다.")
    else:
        print("\n⚠️  일부 테스트에서 문제가 발견되었습니다.")
        print("상세한 결과를 확인하여 문제를 해결해주세요.")
    
    return results

if __name__ == "__main__":
    test_integration() 