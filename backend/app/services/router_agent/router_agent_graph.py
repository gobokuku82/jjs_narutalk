"""
Router Agent Graph Module

라우팅 로직 및 그래프 관리 기능
"""

import logging
from typing import Dict, List, Any, Optional
from .router_agent_tool import RouterAgentTool
from .router_agent_nodes import RouterAgentNodes

logger = logging.getLogger(__name__)

class RouterAgentGraph:
    """라우팅 그래프 관리 및 메인 로직"""
    
    def __init__(self):
        self.tool_caller = RouterAgentTool()
        self.agent_nodes = RouterAgentNodes()
        
        logger.info("Router Agent Graph 초기화 완료")
    
    async def route_request(self, message: str, user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """
        메인 라우팅 로직 - 사용자 요청을 분석하고 적절한 Agent로 라우팅
        """
        try:
            logger.info(f"Router Agent Graph 요청 처리: {message[:50]}...")
            
            # 1. Tool Calling으로 적절한 Agent 선택
            tool_result = await self.tool_caller.call_tool(message)
            
            if "error" in tool_result:
                return {
                    "error": tool_result["error"],
                    "response": "시스템 오류가 발생했습니다. OpenAI API 키를 확인해주세요.",
                    "agent": "error",
                    "routing_confidence": 0.0
                }
            
            # 2. Tool Call 결과 처리
            if tool_result["tool_call"]:
                # 특정 Agent로 라우팅
                function_name = tool_result["tool_call"]["function_name"]
                function_args = tool_result["tool_call"]["function_args"]
                confidence = tool_result["tool_call"]["confidence"]
                
                logger.info(f"Router Graph 선택: {function_name}")
                
                # 3. 선택된 Agent 실행
                agent_result = await self.agent_nodes.execute_agent(
                    function_name, function_args, message
                )
                
                return {
                    "agent": function_name,
                    "arguments": function_args,
                    "response": agent_result.get("response", ""),
                    "sources": agent_result.get("sources", []),
                    "metadata": agent_result.get("metadata", {}),
                    "user_id": user_id,
                    "session_id": session_id,
                    "routing_confidence": confidence
                }
            
            else:
                # 일반 대화 응답
                general_response = tool_result["general_response"]
                confidence = tool_result.get("confidence", 0.5)
                
                logger.info("Router Graph: 일반 응답 생성")
                
                return {
                    "agent": "general_chat",
                    "response": general_response,
                    "sources": [],
                    "metadata": {"type": "general_response"},
                    "user_id": user_id,
                    "session_id": session_id,
                    "routing_confidence": confidence
                }
                
        except Exception as e:
            logger.error(f"Router Agent Graph 처리 실패: {str(e)}")
            return {
                "error": str(e),
                "response": f"라우팅 처리 중 오류가 발생했습니다: {str(e)}",
                "agent": "error",
                "routing_confidence": 0.0
            }
    
    async def route_batch_requests(self, messages: List[str], user_id: str = None) -> List[Dict[str, Any]]:
        """배치 요청 라우팅"""
        results = []
        
        for message in messages:
            result = await self.route_request(message, user_id)
            results.append(result)
        
        return results
    
    async def route_with_fallback(self, message: str, primary_agent: str = None, user_id: str = None) -> Dict[str, Any]:
        """폴백이 있는 라우팅"""
        try:
            # 1차: 지정된 Agent로 시도
            if primary_agent:
                try:
                    result = await self.agent_nodes.execute_agent_direct(
                        primary_agent, {"query": message}, message
                    )
                    if result and result.get("response"):
                        return {
                            "agent": primary_agent,
                            "response": result.get("response", ""),
                            "sources": result.get("sources", []),
                            "metadata": result.get("metadata", {}),
                            "user_id": user_id,
                            "routing_confidence": 0.8,
                            "fallback_used": False
                        }
                except Exception as e:
                    logger.warning(f"1차 Agent {primary_agent} 실행 실패: {str(e)}")
            
            # 2차: 일반 라우팅
            return await self.route_request(message, user_id)
            
        except Exception as e:
            logger.error(f"폴백 라우팅 실패: {str(e)}")
            return {
                "error": str(e),
                "response": f"라우팅 처리 중 오류가 발생했습니다: {str(e)}",
                "agent": "error",
                "routing_confidence": 0.0
            }
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """라우팅 통계 정보"""
        tool_stats = self.tool_caller.get_tool_stats()
        node_stats = self.agent_nodes.get_node_stats()
        
        return {
            "graph_name": "RouterAgentGraph",
            "tool_caller": tool_stats,
            "agent_nodes": node_stats,
            "total_components": 2,
            "status": "active"
        }
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """사용 가능한 Agent 목록 반환"""
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
    
    def validate_routing(self, message: str) -> Dict[str, Any]:
        """라우팅 유효성 검증"""
        try:
            # 메시지 길이 검증
            if len(message) < 1:
                return {"valid": False, "error": "메시지가 너무 짧습니다."}
            
            if len(message) > 1000:
                return {"valid": False, "error": "메시지가 너무 깁니다."}
            
            # 특수 문자 검증
            if not message.strip():
                return {"valid": False, "error": "빈 메시지입니다."}
            
            # Tool Calling 준비 상태 확인
            if not self.tool_caller.is_initialized():
                return {"valid": False, "error": "Tool Calling이 초기화되지 않았습니다."}
            
            return {"valid": True, "message": "라우팅 준비 완료"}
            
        except Exception as e:
            return {"valid": False, "error": f"검증 중 오류: {str(e)}"}
    
    def get_graph_info(self) -> Dict[str, Any]:
        """그래프 정보"""
        return {
            "graph_type": "RouterAgentGraph",
            "components": {
                "tool_caller": "RouterAgentTool",
                "agent_nodes": "RouterAgentNodes"
            },
            "routing_method": "OpenAI Tool Calling",
            "supported_agents": 4,
            "fallback_support": True,
            "batch_processing": True
        } 