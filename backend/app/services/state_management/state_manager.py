"""
State Manager

LangGraph StateGraph 기반 대화 상태 관리자
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state_schema import ConversationState, MessageState, MessageRole, AgentType
from .session_manager import SessionManager
from ..main_agent_router import MainAgentRouter

logger = logging.getLogger(__name__)

class StateManager:
    """LangGraph 기반 상태 관리자"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.agent_router = MainAgentRouter()
        
        # LangGraph StateGraph 생성
        self.workflow = self._create_workflow()
        
        # Checkpoint saver 설정 (메모리 기반 상태 지속성)
        # 참고: LangGraph 0.5.2에서는 SqliteSaver 대신 MemorySaver 사용
        self.checkpointer = MemorySaver()
        
        # 컴파일된 앱
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
        
        logger.info("StateManager 초기화 완료")
    
    def _create_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 생성"""
        
        # StateGraph 생성
        workflow = StateGraph(ConversationState)
        
        # 노드 추가
        workflow.add_node("process_user_input", self._process_user_input)
        workflow.add_node("route_to_agent", self._route_to_agent)
        workflow.add_node("execute_agent", self._execute_agent)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("save_state", self._save_state)
        
        # 엣지 추가 (노드 간 흐름 정의)
        workflow.set_entry_point("process_user_input")
        
        workflow.add_edge("process_user_input", "route_to_agent")
        workflow.add_edge("route_to_agent", "execute_agent")
        workflow.add_edge("execute_agent", "generate_response")
        workflow.add_edge("generate_response", "save_state")
        workflow.add_edge("save_state", END)
        
        return workflow
    
    async def _process_user_input(self, state: ConversationState) -> ConversationState:
        """사용자 입력 처리"""
        try:
            session_id = state["session_id"]
            current_message = state["current_message"]
            
            logger.info(f"사용자 입력 처리: {session_id} - {current_message[:50]}...")
            
            # 사용자 메시지를 상태에 추가
            user_message = MessageState(
                role=MessageRole.USER,
                content=current_message,
                timestamp=datetime.now()
            )
            
            state["messages"].append(user_message)
            
            # 대화 컨텍스트 로드
            context_messages = self.session_manager.get_conversation_context(session_id, 10)
            if context_messages and len(context_messages) > len(state["messages"]):
                # 메모리 상태가 DB보다 적으면 최근 메시지로 업데이트
                state["messages"] = context_messages[-20:]  # 최근 20개 메시지 유지
            
            state["should_continue"] = True
            state["error_message"] = None
            
            return state
            
        except Exception as e:
            logger.error(f"사용자 입력 처리 실패: {str(e)}")
            state["should_continue"] = False
            state["error_message"] = f"입력 처리 중 오류: {str(e)}"
            return state
    
    async def _route_to_agent(self, state: ConversationState) -> ConversationState:
        """에이전트 라우팅"""
        try:
            session_id = state["session_id"]
            current_message = state["current_message"]
            
            logger.info(f"에이전트 라우팅: {session_id}")
            
            # MainAgentRouter를 통해 에이전트 선택
            routing_result = await self.agent_router.route_message(
                message=current_message,
                session_id=session_id,
                user_id=state["user_id"]
            )
            
            if routing_result.get("error"):
                state["error_message"] = routing_result["error"]
                state["should_continue"] = False
                return state
            
            # 라우팅 결과를 상태에 저장
            agent_name = routing_result.get("agent", "unknown")
            
            # AgentType enum으로 변환
            agent_type_map = {
                "chroma_db_agent": AgentType.CHROMA_DB,
                "employee_db_agent": AgentType.EMPLOYEE_DB,
                "client_analysis_agent": AgentType.CLIENT_ANALYSIS,
                "rule_compliance_agent": AgentType.RULE_COMPLIANCE
            }
            
            state["current_agent"] = agent_type_map.get(agent_name)
            state["agent_arguments"] = routing_result.get("arguments", {})
            state["sources"] = routing_result.get("sources", [])
            
            # 라우팅 기록 추가
            route_info = {
                "timestamp": datetime.now().isoformat(),
                "agent": agent_name,
                "arguments": state["agent_arguments"],
                "confidence": 1.0  # MainAgentRouter에서는 신뢰도 점수가 없음
            }
            state["route_history"].append(route_info)
            state["route_confidence"] = 1.0
            
            logger.info(f"라우팅 완료: {agent_name}")
            return state
            
        except Exception as e:
            logger.error(f"에이전트 라우팅 실패: {str(e)}")
            state["error_message"] = f"라우팅 실패: {str(e)}"
            state["should_continue"] = False
            return state
    
    async def _execute_agent(self, state: ConversationState) -> ConversationState:
        """에이전트 실행"""
        try:
            session_id = state["session_id"]
            current_agent = state["current_agent"]
            
            if not current_agent:
                state["error_message"] = "실행할 에이전트가 선택되지 않았습니다."
                state["should_continue"] = False
                return state
            
            logger.info(f"에이전트 실행: {current_agent.value}")
            
            # 에이전트 실행 (MainAgentRouter에서 이미 처리됨)
            # 여기서는 추가적인 처리나 상태 업데이트만 수행
            
            # 컨텍스트 정보 추가
            recent_messages = state["messages"][-5:]  # 최근 5개 메시지
            context_summary = self._create_context_summary(recent_messages)
            
            state["conversation_metadata"]["context_summary"] = context_summary
            state["conversation_metadata"]["agent_execution_time"] = datetime.now().isoformat()
            
            return state
            
        except Exception as e:
            logger.error(f"에이전트 실행 실패: {str(e)}")
            state["error_message"] = f"에이전트 실행 실패: {str(e)}"
            state["should_continue"] = False
            return state
    
    async def _generate_response(self, state: ConversationState) -> ConversationState:
        """최종 응답 생성"""
        try:
            session_id = state["session_id"]
            current_message = state["current_message"]
            
            logger.info(f"응답 생성: {session_id}")
            
            # MainAgentRouter에서 이미 응답이 생성됨
            # 여기서는 이미 생성된 응답을 사용하거나 추가 처리 수행
            
            # 만약 아직 응답이 없다면 기본 응답 생성
            if not state["last_agent_response"]:
                # MainAgentRouter를 통해 다시 처리
                routing_result = await self.agent_router.route_message(
                    message=current_message,
                    session_id=session_id,
                    user_id=state["user_id"]
                )
                
                response_text = routing_result.get("response", "죄송합니다. 응답을 생성할 수 없습니다.")
                state["last_agent_response"] = response_text
                state["sources"] = routing_result.get("sources", [])
            
            # 어시스턴트 메시지 생성
            assistant_message = MessageState(
                role=MessageRole.ASSISTANT,
                content=state["last_agent_response"],
                timestamp=datetime.now(),
                agent_type=state["current_agent"],
                metadata={
                    "sources": state["sources"],
                    "agent_arguments": state["agent_arguments"]
                }
            )
            
            state["messages"].append(assistant_message)
            
            # 메타데이터 업데이트
            state["conversation_metadata"]["response_generated_at"] = datetime.now().isoformat()
            state["conversation_metadata"]["total_messages"] = len(state["messages"])
            
            return state
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {str(e)}")
            state["error_message"] = f"응답 생성 실패: {str(e)}"
            state["last_agent_response"] = "죄송합니다. 응답 생성 중 오류가 발생했습니다."
            return state
    
    async def _save_state(self, state: ConversationState) -> ConversationState:
        """상태 저장"""
        try:
            session_id = state["session_id"]
            
            logger.debug(f"상태 저장: {session_id}")
            
            # 세션 상태 업데이트
            self.session_manager.update_state(session_id, state)
            
            # 새로운 메시지가 있으면 데이터베이스에 저장
            if len(state["messages"]) >= 2:
                # 마지막 사용자 메시지와 어시스턴트 메시지 저장
                for message in state["messages"][-2:]:
                    if message.timestamp > datetime.now().replace(second=datetime.now().second-10):
                        # 최근 10초 이내의 메시지만 저장 (중복 방지)
                        self.session_manager.conversation_store.save_message(session_id, message)
            
            state["conversation_metadata"]["state_saved_at"] = datetime.now().isoformat()
            state["should_continue"] = False  # 처리 완료
            
            return state
            
        except Exception as e:
            logger.error(f"상태 저장 실패: {str(e)}")
            state["error_message"] = f"상태 저장 실패: {str(e)}"
            return state
    
    def _create_context_summary(self, messages: List[MessageState]) -> str:
        """컨텍스트 요약 생성"""
        try:
            if not messages:
                return "대화 기록 없음"
            
            summary_parts = []
            for msg in messages:
                role_label = "사용자" if msg.role == MessageRole.USER else "AI"
                content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                summary_parts.append(f"{role_label}: {content_preview}")
            
            return " | ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"컨텍스트 요약 생성 실패: {str(e)}")
            return "컨텍스트 요약 생성 실패"
    
    async def process_message(self, message: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """메시지 처리 (메인 진입점)"""
        try:
            # 세션 확보
            session_id = self.session_manager.get_or_create_session(session_id, user_id)
            
            # 초기 상태 생성
            state = self.session_manager.get_state(session_id)
            if not state:
                from .state_schema import create_initial_state
                state = create_initial_state(session_id, user_id, message)
                self.session_manager.update_state(session_id, state)
            else:
                state["current_message"] = message
            
            # 스레드 설정 (LangGraph checkpointing)
            thread_config = {"configurable": {"thread_id": session_id}}
            
            # StateGraph 실행
            result = await self.app.ainvoke(state, config=thread_config)
            
            # 결과 반환
            return {
                "response": result["last_agent_response"],
                "agent": result["current_agent"].value if result["current_agent"] else "unknown",
                "sources": result["sources"],
                "metadata": result["conversation_metadata"],
                "session_id": session_id,
                "error": result.get("error_message")
            }
            
        except Exception as e:
            logger.error(f"메시지 처리 실패: {str(e)}")
            return {
                "response": f"메시지 처리 중 오류가 발생했습니다: {str(e)}",
                "agent": "error",
                "sources": [],
                "metadata": {},
                "session_id": session_id,
                "error": str(e)
            }
    
    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """대화 기록 조회"""
        try:
            messages = self.session_manager.get_conversation_context(session_id, limit)
            return [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "agent_type": msg.agent_type.value if msg.agent_type else None,
                    "metadata": msg.metadata
                }
                for msg in messages
            ]
        except Exception as e:
            logger.error(f"대화 기록 조회 실패: {str(e)}")
            return []
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """세션 통계"""
        try:
            return self.session_manager.get_conversation_summary(session_id)
        except Exception as e:
            logger.error(f"세션 통계 조회 실패: {str(e)}")
            return {}
    
    def cleanup_sessions(self):
        """세션 정리"""
        try:
            self.session_manager.cleanup_inactive_sessions()
        except Exception as e:
            logger.error(f"세션 정리 실패: {str(e)}")
    
    def delete_session(self, session_id: str):
        """세션 삭제"""
        try:
            self.session_manager.delete_session(session_id)
        except Exception as e:
            logger.error(f"세션 삭제 실패: {str(e)}") 