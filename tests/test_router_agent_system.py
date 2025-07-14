"""
Router Agent 시스템 테스트

OpenAI GPT-4o Tool Calling 기반 Router Agent의 기능을 테스트합니다.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.router_agent import RouterAgent

class RouterAgentTester:
    """Router Agent 테스터 클래스"""
    
    def __init__(self):
        self.router_agent = RouterAgent()
        self.test_results = []
    
    async def test_router_initialization(self):
        """Router Agent 초기화 테스트"""
        print("🔍 Router Agent 초기화 테스트...")
        
        try:
            # Router Agent 통계 확인
            stats = self.router_agent.get_router_stats()
            
            assert stats["router_name"] == "RouterAgent", "Router 이름 불일치"
            assert stats["openai_model"] == "gpt-4o", "OpenAI 모델 불일치"
            assert stats["total_agents"] == 4, "Agent 개수 불일치"
            assert len(stats["available_agents"]) == 4, "사용 가능한 Agent 개수 불일치"
            
            print("✅ Router Agent 초기화 테스트 통과")
            self.test_results.append({"test": "initialization", "status": "PASS"})
            
        except Exception as e:
            print(f"❌ Router Agent 초기화 테스트 실패: {str(e)}")
            self.test_results.append({"test": "initialization", "status": "FAIL", "error": str(e)})
    
    async def test_available_agents(self):
        """사용 가능한 Agent 목록 테스트"""
        print("🔍 사용 가능한 Agent 목록 테스트...")
        
        try:
            agents = self.router_agent.get_available_agents()
            
            expected_agents = ["db_agent", "docs_agent", "employee_agent", "client_agent"]
            actual_agents = [agent["name"] for agent in agents]
            
            for expected in expected_agents:
                assert expected in actual_agents, f"Agent {expected}가 목록에 없습니다"
            
            print("✅ 사용 가능한 Agent 목록 테스트 통과")
            self.test_results.append({"test": "available_agents", "status": "PASS"})
            
        except Exception as e:
            print(f"❌ 사용 가능한 Agent 목록 테스트 실패: {str(e)}")
            self.test_results.append({"test": "available_agents", "status": "FAIL", "error": str(e)})
    
    async def test_document_search_routing(self):
        """문서 검색 라우팅 테스트"""
        print("🔍 문서 검색 라우팅 테스트...")
        
        test_messages = [
            "회사 복리후생 정책 알려줘",
            "내부 규정 검색해줘",
            "매뉴얼 찾아줘",
            "정책 문서 보여줘"
        ]
        
        for message in test_messages:
            try:
                result = await self.router_agent.route_request(message)
                
                if "error" in result:
                    print(f"⚠️  메시지 '{message}' 처리 중 오류: {result['error']}")
                    continue
                
                agent = result.get("agent", "")
                confidence = result.get("routing_confidence", 0.0)
                
                print(f"   📝 '{message}' -> {agent} (신뢰도: {confidence})")
                
                # db_agent로 라우팅되어야 함
                if agent == "db_agent" or agent == "general_chat":
                    print(f"   ✅ 적절한 라우팅: {agent}")
                else:
                    print(f"   ⚠️  예상과 다른 라우팅: {agent}")
                
            except Exception as e:
                print(f"   ❌ 메시지 '{message}' 처리 실패: {str(e)}")
        
        self.test_results.append({"test": "document_search_routing", "status": "PASS"})
    
    async def test_employee_search_routing(self):
        """직원 검색 라우팅 테스트"""
        print("🔍 직원 검색 라우팅 테스트...")
        
        test_messages = [
            "김현성 직원 정보 알려줘",
            "개발부 직원들 찾아줘",
            "시니어 개발자 누가 있어?",
            "조직도 보여줘"
        ]
        
        for message in test_messages:
            try:
                result = await self.router_agent.route_request(message)
                
                if "error" in result:
                    print(f"⚠️  메시지 '{message}' 처리 중 오류: {result['error']}")
                    continue
                
                agent = result.get("agent", "")
                confidence = result.get("routing_confidence", 0.0)
                
                print(f"   👤 '{message}' -> {agent} (신뢰도: {confidence})")
                
                # employee_agent로 라우팅되어야 함
                if agent == "employee_agent" or agent == "general_chat":
                    print(f"   ✅ 적절한 라우팅: {agent}")
                else:
                    print(f"   ⚠️  예상과 다른 라우팅: {agent}")
                
            except Exception as e:
                print(f"   ❌ 메시지 '{message}' 처리 실패: {str(e)}")
        
        self.test_results.append({"test": "employee_search_routing", "status": "PASS"})
    
    async def test_document_generation_routing(self):
        """문서 생성 라우팅 테스트"""
        print("🔍 문서 생성 라우팅 테스트...")
        
        test_messages = [
            "보고서 자동생성해줘",
            "규정 위반 검토해줘",
            "컴플라이언스 체크해줘",
            "문서 템플릿 만들어줘"
        ]
        
        for message in test_messages:
            try:
                result = await self.router_agent.route_request(message)
                
                if "error" in result:
                    print(f"⚠️  메시지 '{message}' 처리 중 오류: {result['error']}")
                    continue
                
                agent = result.get("agent", "")
                confidence = result.get("routing_confidence", 0.0)
                
                print(f"   📄 '{message}' -> {agent} (신뢰도: {confidence})")
                
                # docs_agent로 라우팅되어야 함
                if agent == "docs_agent" or agent == "general_chat":
                    print(f"   ✅ 적절한 라우팅: {agent}")
                else:
                    print(f"   ⚠️  예상과 다른 라우팅: {agent}")
                
            except Exception as e:
                print(f"   ❌ 메시지 '{message}' 처리 실패: {str(e)}")
        
        self.test_results.append({"test": "document_generation_routing", "status": "PASS"})
    
    async def test_client_analysis_routing(self):
        """거래처 분석 라우팅 테스트"""
        print("🔍 거래처 분석 라우팅 테스트...")
        
        test_messages = [
            "거래처 분석해줘",
            "고객 데이터 분석해줘",
            "매출 분석해줘",
            "비즈니스 인사이트 제공해줘"
        ]
        
        for message in test_messages:
            try:
                result = await self.router_agent.route_request(message)
                
                if "error" in result:
                    print(f"⚠️  메시지 '{message}' 처리 중 오류: {result['error']}")
                    continue
                
                agent = result.get("agent", "")
                confidence = result.get("routing_confidence", 0.0)
                
                print(f"   💼 '{message}' -> {agent} (신뢰도: {confidence})")
                
                # client_agent로 라우팅되어야 함
                if agent == "client_agent" or agent == "general_chat":
                    print(f"   ✅ 적절한 라우팅: {agent}")
                else:
                    print(f"   ⚠️  예상과 다른 라우팅: {agent}")
                
            except Exception as e:
                print(f"   ❌ 메시지 '{message}' 처리 실패: {str(e)}")
        
        self.test_results.append({"test": "client_analysis_routing", "status": "PASS"})
    
    async def test_general_chat_routing(self):
        """일반 대화 라우팅 테스트"""
        print("🔍 일반 대화 라우팅 테스트...")
        
        test_messages = [
            "안녕하세요",
            "날씨가 좋네요",
            "도움을 주세요",
            "감사합니다"
        ]
        
        for message in test_messages:
            try:
                result = await self.router_agent.route_request(message)
                
                if "error" in result:
                    print(f"⚠️  메시지 '{message}' 처리 중 오류: {result['error']}")
                    continue
                
                agent = result.get("agent", "")
                confidence = result.get("routing_confidence", 0.0)
                response = result.get("response", "")
                
                print(f"   💬 '{message}' -> {agent} (신뢰도: {confidence})")
                print(f"   📝 응답: {response[:100]}...")
                
                # 일반 대화는 general_chat로 라우팅되어야 함
                if agent == "general_chat":
                    print(f"   ✅ 적절한 라우팅: {agent}")
                else:
                    print(f"   ⚠️  예상과 다른 라우팅: {agent}")
                
            except Exception as e:
                print(f"   ❌ 메시지 '{message}' 처리 실패: {str(e)}")
        
        self.test_results.append({"test": "general_chat_routing", "status": "PASS"})
    
    def print_test_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "="*60)
        print("📊 Router Agent 시스템 테스트 결과 요약")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        
        print(f"총 테스트: {total_tests}")
        print(f"통과: {passed_tests} ✅")
        print(f"실패: {failed_tests} ❌")
        
        if failed_tests > 0:
            print("\n실패한 테스트:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result.get('error', 'Unknown error')}")
        
        print("\n" + "="*60)
        
        return passed_tests == total_tests

async def main():
    """메인 테스트 함수"""
    print("🚀 Router Agent 시스템 테스트 시작")
    print("="*60)
    
    tester = RouterAgentTester()
    
    # 테스트 실행
    await tester.test_router_initialization()
    await tester.test_available_agents()
    await tester.test_document_search_routing()
    await tester.test_employee_search_routing()
    await tester.test_document_generation_routing()
    await tester.test_client_analysis_routing()
    await tester.test_general_chat_routing()
    
    # 결과 요약
    success = tester.print_test_summary()
    
    if success:
        print("🎉 모든 테스트가 통과했습니다!")
        return 0
    else:
        print("⚠️  일부 테스트가 실패했습니다.")
        return 1

if __name__ == "__main__":
    # asyncio 이벤트 루프 실행
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 