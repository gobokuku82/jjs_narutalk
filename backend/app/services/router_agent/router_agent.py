"""
Router Agent

OpenAI GPT-4o Tool Calling을 사용하여 4개의 전문 Agent로 라우팅하는 메인 라우터
분리된 모듈 구조: Tool Calling, Graph Management, Agent Nodes
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class RouterAgent:
    """메인 Router Agent - 분리된 모듈 구조 기반"""
    
    def __init__(self):
        # Lazy import to avoid circular dependency
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
        return self.graph.get_available_agents()
    
    def get_router_stats(self) -> Dict[str, Any]:
        """Router Agent 통계 정보"""
        routing_stats = self.graph.get_routing_stats()
        
        return {
            "router_name": "RouterAgent",
            "openai_model": "gpt-4o",
            "total_agents": routing_stats["tool_caller"]["total_functions"],
            "available_agents": routing_stats["tool_caller"]["available_functions"],
            "initialized": routing_stats["tool_caller"]["initialized"],
            "graph_status": routing_stats["status"],
            "node_status": routing_stats["agent_nodes"]["status"]
        }
    
    # 추가 기능들 (Graph를 통한 접근)
    async def route_batch_requests(self, messages: List[str], user_id: str = None) -> List[Dict[str, Any]]:
        """배치 요청 라우팅"""
        return await self.graph.route_batch_requests(messages, user_id)
    
    async def route_with_fallback(self, message: str, primary_agent: str = None, user_id: str = None) -> Dict[str, Any]:
        """폴백이 있는 라우팅"""
        return await self.graph.route_with_fallback(message, primary_agent, user_id)
    
    def validate_routing(self, message: str) -> Dict[str, Any]:
        """라우팅 유효성 검증"""
        return self.graph.validate_routing(message)
    
    def get_graph_info(self) -> Dict[str, Any]:
        """그래프 정보"""
        return self.graph.get_graph_info()
    
    def get_agent_health(self) -> Dict[str, Any]:
        """Agent 상태 정보"""
        return self.graph.agent_nodes.get_agent_health()
    
    def get_all_agents_info(self) -> List[Dict[str, Any]]:
        """모든 Agent 정보 조회"""
        return self.graph.agent_nodes.get_all_agents_info() 