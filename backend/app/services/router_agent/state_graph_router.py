"""
StateGraph Router Agent

LangGraph StateGraph 기반 상태 관리가 포함된 Router Agent
"""

import logging
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
import uuid

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .router_agent_tool import RouterAgentTool
from .router_agent_nodes import RouterAgentNodes

logger = logging.getLogger(__name__)

# StateGraph에서 사용할 상태 정의
class RouterState(TypedDict):
    """Router Agent 상태"""
    # 기본 정보
    session_id: str
    user_id: Optional[str]
    current_message: str
    
    # 대화 기록
    conversation_history: List[Dict[str, Any]]
    
    # 라우팅 정보
    selected_agent: Optional[str]
    agent_arguments: Dict[str, Any]
    routing_confidence: float
    
    # 실행 결과
    agent_response: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    
    # 상태 제어
    should_continue: bool
    error_message: Optional[str]
    
    # 메타데이터
    timestamp: str
    execution_steps: List[str]

class StateGraphRouter:
    """LangGraph StateGraph 기반 Router Agent"""
    
    def __init__(self):
        self.tool_caller = RouterAgentTool()
        self.agent_nodes = RouterAgentNodes()
        
        # StateGraph 생성
        self.workflow = self._create_workflow()
        
        # Checkpoint saver 설정
        self.checkpointer = MemorySaver()
        
        # 컴파일된 앱
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
        
        logger.info("StateGraph Router 초기화 완료")
    
    def _create_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 생성"""
        
        # StateGraph 생성
        workflow = StateGraph(RouterState)
        
        # 노드 추가
        workflow.add_node("initialize_state", self._initialize_state)
        workflow.add_node("process_user_input", self._process_user_input)
        workflow.add_node("route_to_agent", self._route_to_agent)
        workflow.add_node("execute_agent", self._execute_agent)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("save_conversation", self._save_conversation)
        
        # 엣지 추가 (노드 간 흐름 정의)
        workflow.set_entry_point("initialize_state")
        
        workflow.add_edge("initialize_state", "process_user_input")
        workflow.add_edge("process_user_input", "route_to_agent")
        workflow.add_edge("route_to_agent", "execute_agent")
        workflow.add_edge("execute_agent", "generate_response")
        workflow.add_edge("generate_response", "save_conversation")
        workflow.add_edge("save_conversation", END)
        
        return workflow
    
    async def _initialize_state(self, state: RouterState) -> RouterState:
        """상태 초기화"""
        try:
            session_id = state.get("session_id") or str(uuid.uuid4())
            
            # 초기 상태 설정
            state.update({
                "session_id": session_id,
                "conversation_history": state.get("conversation_history", []),
                "selected_agent": None,
                "agent_arguments": {},
                "routing_confidence": 0.0,
                "agent_response": "",
                "sources": [],
                "metadata": {},
                "should_continue": True,
                "error_message": None,
                "timestamp": datetime.now().isoformat(),
                "execution_steps": ["initialized"]
            })
            
            logger.info(f"상태 초기화 완료: {session_id}")
            return state
            
        except Exception as e:
            logger.error(f"상태 초기화 실패: {str(e)}")
            state["should_continue"] = False
            state["error_message"] = f"상태 초기화 실패: {str(e)}"
            return state
    
    async def _process_user_input(self, state: RouterState) -> RouterState:
        """사용자 입력 처리"""
        try:
            current_message = state["current_message"]
            session_id = state["session_id"]
            
            logger.info(f"사용자 입력 처리: {session_id} - {current_message[:50]}...")
            
            # 사용자 메시지를 대화 기록에 추가
            user_message = {
                "role": "user",
                "content": current_message,
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id
            }
            
            state["conversation_history"].append(user_message)
            state["execution_steps"].append("user_input_processed")
            
            return state
            
        except Exception as e:
            logger.error(f"사용자 입력 처리 실패: {str(e)}")
            state["should_continue"] = False
            state["error_message"] = f"입력 처리 실패: {str(e)}"
            return state
    
    async def _route_to_agent(self, state: RouterState) -> RouterState:
        """에이전트 라우팅"""
        try:
            current_message = state["current_message"]
            
            logger.info(f"에이전트 라우팅: {state['session_id']}")
            
            # Tool Calling으로 적절한 Agent 선택
            tool_result = await self.tool_caller.call_tool(current_message)
            
            if "error" in tool_result:
                state["error_message"] = tool_result["error"]
                state["should_continue"] = False
                return state
            
            # Tool Call 결과 처리
            if tool_result["tool_call"]:
                function_name = tool_result["tool_call"]["function_name"]
                function_args = tool_result["tool_call"]["function_args"]
                confidence = tool_result["tool_call"]["confidence"]
                
                state.update({
                    "selected_agent": function_name,
                    "agent_arguments": function_args,
                    "routing_confidence": confidence
                })
                
                logger.info(f"라우팅 완료: {function_name}")
            else:
                # 일반 대화 응답
                state.update({
                    "selected_agent": "general_chat",
                    "agent_response": tool_result["general_response"],
                    "routing_confidence": tool_result.get("confidence", 0.5)
                })
            
            state["execution_steps"].append("agent_routed")
            return state
            
        except Exception as e:
            logger.error(f"에이전트 라우팅 실패: {str(e)}")
            state["error_message"] = f"라우팅 실패: {str(e)}"
            state["should_continue"] = False
            return state
    
    async def _execute_agent(self, state: RouterState) -> RouterState:
        """에이전트 실행"""
        try:
            selected_agent = state["selected_agent"]
            agent_arguments = state["agent_arguments"]
            current_message = state["current_message"]
            
            if not selected_agent or selected_agent == "general_chat":
                # 일반 대화는 이미 응답이 있음
                state["execution_steps"].append("agent_executed")
                return state
            
            logger.info(f"에이전트 실행: {selected_agent}")
            
            # Agent 실행
            agent_result = await self.agent_nodes.execute_agent(
                selected_agent, agent_arguments, current_message
            )
            
            # 결과를 상태에 저장
            state.update({
                "agent_response": agent_result.get("response", ""),
                "sources": agent_result.get("sources", []),
                "metadata": agent_result.get("metadata", {})
            })
            
            state["execution_steps"].append("agent_executed")
            return state
            
        except Exception as e:
            logger.error(f"에이전트 실행 실패: {str(e)}")
            state["error_message"] = f"에이전트 실행 실패: {str(e)}"
            state["should_continue"] = False
            return state
    
    async def _generate_response(self, state: RouterState) -> RouterState:
        """최종 응답 생성"""
        try:
            session_id = state["session_id"]
            
            logger.info(f"응답 생성: {session_id}")
            
            # Assistant 응답을 대화 기록에 추가
            assistant_message = {
                "role": "assistant",
                "content": state["agent_response"],
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "agent": state["selected_agent"],
                "sources": state["sources"],
                "metadata": state["metadata"]
            }
            
            state["conversation_history"].append(assistant_message)
            state["execution_steps"].append("response_generated")
            
            return state
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {str(e)}")
            state["error_message"] = f"응답 생성 실패: {str(e)}"
            state["should_continue"] = False
            return state
    
    async def _save_conversation(self, state: RouterState) -> RouterState:
        """대화 저장"""
        try:
            session_id = state["session_id"]
            
            # 여기서 실제 DB 저장 로직을 구현할 수 있음
            # 현재는 메모리에만 저장됨 (LangGraph MemorySaver)
            
            logger.info(f"대화 저장 완료: {session_id}")
            state["execution_steps"].append("conversation_saved")
            
            return state
            
        except Exception as e:
            logger.error(f"대화 저장 실패: {str(e)}")
            # 저장 실패해도 응답은 반환
            return state
    
    async def route_request(self, message: str, user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """메인 라우팅 함수"""
        try:
            # 초기 상태 생성
            initial_state = RouterState(
                session_id=session_id or str(uuid.uuid4()),
                user_id=user_id,
                current_message=message,
                conversation_history=[],
                selected_agent=None,
                agent_arguments={},
                routing_confidence=0.0,
                agent_response="",
                sources=[],
                metadata={},
                should_continue=True,
                error_message=None,
                timestamp=datetime.now().isoformat(),
                execution_steps=[]
            )
            
            # StateGraph 실행
            result = await self.app.ainvoke(initial_state)
            
            # 결과 반환
            return {
                "response": result["agent_response"],
                "agent": result["selected_agent"],
                "sources": result["sources"],
                "metadata": result["metadata"],
                "session_id": result["session_id"],
                "user_id": result["user_id"],
                "routing_confidence": result["routing_confidence"],
                "conversation_history": result["conversation_history"],
                "execution_steps": result["execution_steps"]
            }
            
        except Exception as e:
            logger.error(f"StateGraph 라우팅 실패: {str(e)}")
            return {
                "error": str(e),
                "response": f"라우팅 처리 중 오류가 발생했습니다: {str(e)}",
                "agent": "error",
                "routing_confidence": 0.0
            }
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """대화 기록 조회"""
        try:
            # LangGraph checkpoint에서 세션 정보 조회
            # 실제로는 DB나 파일 시스템에서 조회해야 함
            return []
        except Exception as e:
            logger.error(f"대화 기록 조회 실패: {str(e)}")
            return []
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """세션 통계 조회"""
        try:
            # 세션별 통계 정보 반환
            return {
                "session_id": session_id,
                "message_count": 0,
                "agent_usage": {},
                "last_activity": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"세션 통계 조회 실패: {str(e)}")
            return {} 