"""
Router Agent

OpenAI GPT-4o Tool Calling을 사용하여 4개의 전문 Agent로 라우팅하는 메인 라우터
분리된 모듈 구조: Tool Calling, Graph Management, Agent Nodes
StateGraph 옵션 지원
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class RouterAgent:
    """메인 Router Agent - 분리된 모듈 구조 기반"""
    
    def __init__(self, use_state_graph: bool = False):
        """
        Router Agent 초기화
        
        Args:
            use_state_graph: StateGraph 사용 여부 (기본값: False)
        """
        self.use_state_graph = use_state_graph
        
        if use_state_graph:
            # StateGraph 기반 Router 사용
            from .state_graph_router import StateGraphRouter
            self.graph = StateGraphRouter()
            logger.info("Router Agent 초기화 완료 - StateGraph 기반")
        else:
            # 기존 Graph 기반 Router 사용
            from .router_agent_graph import RouterAgentGraph
            self.graph = RouterAgentGraph()
            logger.info("Router Agent 초기화 완료 - 분리된 모듈 구조")
    
    async def route_request(self, message: str, user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """
        사용자 요청을 분석하고 적절한 Agent로 라우팅
        """
        return await self.graph.route_request(message, user_id, session_id)
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """사용 가능한 Agent 목록 반환"""
        if hasattr(self.graph, 'get_available_agents'):
            return self.graph.get_available_agents()
        else:
            # StateGraph Router의 경우 기본 Agent 목록 반환
            return [
                {
                    "name": "db_agent",
                    "description": "내부 벡터 검색 Agent",
                    "capabilities": ["문서 검색", "정책 검색", "지식베이스 QA", "벡터 검색"]
                },
                {
                    "name": "docs_agent", 
                    "description": "문서 자동생성 및 규정 위반 검색 Agent",
                    "capabilities": ["문서 생성", "컴플라이언스 검토", "규정 위반 분석", "문서 템플릿"]
                },
                {
                    "name": "employee_agent",
                    "description": "내부 직원정보 검색 Agent", 
                    "capabilities": ["직원 검색", "조직도", "연락처", "부서 정보"]
                },
                {
                    "name": "client_agent",
                    "description": "거래처 분석 Agent",
                    "capabilities": ["고객 분석", "거래 이력", "매출 분석", "비즈니스 인사이트"]
                }
            ]
    
    def get_router_stats(self) -> Dict[str, Any]:
        """Router Agent 통계 정보"""
        if hasattr(self.graph, 'get_routing_stats'):
            routing_stats = self.graph.get_routing_stats()
            return {
                "router_name": "RouterAgent",
                "openai_model": "gpt-4o",
                "total_agents": routing_stats["tool_caller"]["total_functions"],
                "available_agents": routing_stats["tool_caller"]["available_functions"],
                "initialized": routing_stats["tool_caller"]["initialized"],
                "graph_status": routing_stats["status"],
                "node_status": routing_stats["agent_nodes"]["status"],
                "use_state_graph": self.use_state_graph
            }
        else:
            # StateGraph Router의 경우
            return {
                "router_name": "RouterAgent (StateGraph)",
                "openai_model": "gpt-4o",
                "total_agents": 4,
                "available_agents": ["db_agent", "docs_agent", "employee_agent", "client_agent"],
                "initialized": True,
                "use_state_graph": True,
                "state_management": "enabled"
            }
    
    # 추가 기능들 (Graph를 통한 접근)
    async def route_batch_requests(self, messages: List[str], user_id: str = None) -> List[Dict[str, Any]]:
        """배치 요청 라우팅"""
        if hasattr(self.graph, 'route_batch_requests'):
            return await self.graph.route_batch_requests(messages, user_id)
        else:
            # StateGraph Router의 경우 개별 처리
            results = []
            for message in messages:
                result = await self.route_request(message, user_id)
                results.append(result)
            return results
    
    async def route_with_fallback(self, message: str, primary_agent: str = None, user_id: str = None) -> Dict[str, Any]:
        """폴백이 있는 라우팅"""
        if hasattr(self.graph, 'route_with_fallback'):
            return await self.graph.route_with_fallback(message, primary_agent, user_id)
        else:
            # StateGraph Router의 경우 기본 라우팅 사용
            return await self.route_request(message, user_id)
    
    def validate_routing(self, message: str) -> Dict[str, Any]:
        """라우팅 유효성 검증"""
        if hasattr(self.graph, 'validate_routing'):
            return self.graph.validate_routing(message)
        else:
            # StateGraph Router의 경우 기본 검증
            if len(message) < 1:
                return {"valid": False, "error": "메시지가 너무 짧습니다."}
            if len(message) > 1000:
                return {"valid": False, "error": "메시지가 너무 깁니다."}
            return {"valid": True, "message": "라우팅 준비 완료"}
    
    def get_graph_info(self) -> Dict[str, Any]:
        """그래프 정보"""
        if hasattr(self.graph, 'get_graph_info'):
            return self.graph.get_graph_info()
        else:
            return {
                "graph_type": "StateGraphRouter",
                "routing_method": "OpenAI Tool Calling + StateGraph",
                "supported_agents": 4,
                "state_management": True,
                "conversation_history": True
            }
    
    def get_agent_health(self) -> Dict[str, Any]:
        """Agent 상태 정보"""
        if hasattr(self.graph, 'agent_nodes'):
            return self.graph.agent_nodes.get_agent_health()
        else:
            return {
                "total_agents": 4,
                "healthy_agents": 4,
                "agent_status": {
                    "db_agent": {"status": "healthy"},
                    "docs_agent": {"status": "healthy"},
                    "employee_agent": {"status": "healthy"},
                    "client_agent": {"status": "healthy"}
                }
            }
    
    def get_all_agents_info(self) -> List[Dict[str, Any]]:
        """모든 Agent 정보 조회"""
        if hasattr(self.graph, 'agent_nodes'):
            return self.graph.agent_nodes.get_all_agents_info()
        else:
            return self.get_available_agents()
    
    # StateGraph 전용 기능들
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """대화 기록 조회 (StateGraph 전용)"""
        if self.use_state_graph and hasattr(self.graph, 'get_conversation_history'):
            return self.graph.get_conversation_history(session_id)
        else:
            return []
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """세션 통계 조회 (StateGraph 전용)"""
        if self.use_state_graph and hasattr(self.graph, 'get_session_stats'):
            return self.graph.get_session_stats(session_id)
        else:
            return {
                "session_id": session_id,
                "message_count": 0,
                "state_management": "disabled"
            } 