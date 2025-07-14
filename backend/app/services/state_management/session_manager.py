"""
Session Manager

세션별 상태 관리 및 대화 컨텍스트 유지
"""

import uuid
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from .state_schema import ConversationState, MessageState, SessionInfo, MessageRole, AgentType, create_initial_state
from .conversation_store import ConversationStore

logger = logging.getLogger(__name__)

class SessionManager:
    """세션 관리자"""
    
    def __init__(self):
        self.conversation_store = ConversationStore()
        # 메모리 캐시 (활성 세션)
        self._active_sessions: Dict[str, ConversationState] = {}
        # 세션 타임아웃 (30분)
        self.session_timeout = timedelta(minutes=30)
        logger.info("SessionManager 초기화 완료")
    
    def create_session(self, user_id: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        """새 세션 생성"""
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        
        try:
            # 데이터베이스에 세션 정보 저장
            session_info = self.conversation_store.create_session(
                session_id=session_id,
                user_id=user_id,
                metadata=metadata
            )
            
            # 메모리에 초기 상태 생성
            initial_state = create_initial_state(session_id, user_id)
            self._active_sessions[session_id] = initial_state
            
            logger.info(f"새 세션 생성: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"세션 생성 실패: {str(e)}")
            raise
    
    def get_or_create_session(self, session_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
        """세션 조회 또는 생성"""
        if session_id:
            # 기존 세션 확인
            if self.session_exists(session_id):
                return session_id
            else:
                # 데이터베이스에서 세션 복원 시도
                if self._restore_session(session_id):
                    return session_id
        
        # 새 세션 생성
        return self.create_session(user_id)
    
    def session_exists(self, session_id: str) -> bool:
        """세션 존재 여부 확인"""
        return session_id in self._active_sessions
    
    def _restore_session(self, session_id: str) -> bool:
        """데이터베이스에서 세션 복원"""
        try:
            # 세션 정보 조회
            session_info = self.conversation_store.get_session(session_id)
            if not session_info:
                return False
            
            # 대화 기록 조회
            messages = self.conversation_store.get_recent_context(session_id, 20)
            
            # 상태 복원
            state = create_initial_state(session_id, session_info.user_id)
            state["messages"] = messages
            
            # 마지막 메시지에서 컨텍스트 복원
            if messages:
                last_message = messages[-1]
                if last_message.role == MessageRole.ASSISTANT and last_message.agent_type:
                    state["current_agent"] = last_message.agent_type
                    state["last_agent_response"] = last_message.content
            
            self._active_sessions[session_id] = state
            logger.info(f"세션 복원: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"세션 복원 실패 {session_id}: {str(e)}")
            return False
    
    def get_state(self, session_id: str) -> Optional[ConversationState]:
        """세션 상태 조회"""
        return self._active_sessions.get(session_id)
    
    def update_state(self, session_id: str, state: ConversationState):
        """세션 상태 업데이트"""
        self._active_sessions[session_id] = state
    
    def add_message(self, session_id: str, role: MessageRole, content: str, agent_type: Optional[AgentType] = None, metadata: Optional[Dict] = None):
        """메시지 추가"""
        try:
            # 메시지 생성
            message = MessageState(
                role=role,
                content=content,
                timestamp=datetime.now(),
                agent_type=agent_type,
                metadata=metadata
            )
            
            # 상태 업데이트
            if session_id in self._active_sessions:
                self._active_sessions[session_id]["messages"].append(message)
                
                # 최근 메시지만 유지 (메모리 절약)
                if len(self._active_sessions[session_id]["messages"]) > 50:
                    self._active_sessions[session_id]["messages"] = self._active_sessions[session_id]["messages"][-30:]
            
            # 데이터베이스에 저장
            self.conversation_store.save_message(session_id, message)
            
            logger.debug(f"메시지 추가: {session_id} - {role.value}")
            
        except Exception as e:
            logger.error(f"메시지 추가 실패: {str(e)}")
    
    def get_conversation_context(self, session_id: str, max_messages: int = 10) -> List[MessageState]:
        """대화 컨텍스트 조회"""
        try:
            if session_id in self._active_sessions:
                messages = self._active_sessions[session_id]["messages"]
                return messages[-max_messages:] if messages else []
            
            # 메모리에 없으면 데이터베이스에서 조회
            return self.conversation_store.get_recent_context(session_id, max_messages)
            
        except Exception as e:
            logger.error(f"컨텍스트 조회 실패: {str(e)}")
            return []
    
    def get_conversation_summary(self, session_id: str) -> Dict:
        """대화 요약 정보"""
        try:
            messages = self.get_conversation_context(session_id, 50)
            
            # 통계 계산
            user_messages = [m for m in messages if m.role == MessageRole.USER]
            assistant_messages = [m for m in messages if m.role == MessageRole.ASSISTANT]
            
            # 사용된 에이전트 분석
            agents_used = {}
            for msg in assistant_messages:
                if msg.agent_type:
                    agent_name = msg.agent_type.value
                    agents_used[agent_name] = agents_used.get(agent_name, 0) + 1
            
            return {
                "total_messages": len(messages),
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "agents_used": agents_used,
                "last_activity": messages[-1].timestamp if messages else None
            }
            
        except Exception as e:
            logger.error(f"대화 요약 실패: {str(e)}")
            return {}
    
    def clear_session(self, session_id: str):
        """세션 정리 (메모리에서만)"""
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
            logger.info(f"세션 메모리 정리: {session_id}")
    
    def delete_session(self, session_id: str):
        """세션 완전 삭제"""
        try:
            # 메모리에서 제거
            self.clear_session(session_id)
            
            # 데이터베이스에서 삭제
            self.conversation_store.delete_session(session_id)
            
            logger.info(f"세션 삭제: {session_id}")
            
        except Exception as e:
            logger.error(f"세션 삭제 실패: {str(e)}")
    
    def cleanup_inactive_sessions(self):
        """비활성 세션 정리"""
        try:
            current_time = datetime.now()
            sessions_to_remove = []
            
            for session_id, state in self._active_sessions.items():
                # 마지막 활동 시간 확인
                if state["messages"]:
                    last_activity = state["messages"][-1].timestamp
                    if current_time - last_activity > self.session_timeout:
                        sessions_to_remove.append(session_id)
            
            # 비활성 세션 제거
            for session_id in sessions_to_remove:
                self.clear_session(session_id)
            
            if sessions_to_remove:
                logger.info(f"비활성 세션 정리: {len(sessions_to_remove)}개")
            
        except Exception as e:
            logger.error(f"세션 정리 실패: {str(e)}")
    
    def get_session_info(self, session_id: str) -> Optional[SessionInfo]:
        """세션 정보 조회"""
        return self.conversation_store.get_session(session_id)
    
    def get_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """사용자별 세션 목록"""
        return self.conversation_store.get_user_sessions(user_id)
    
    def get_active_sessions_count(self) -> int:
        """활성 세션 수"""
        return len(self._active_sessions)
    
    def get_session_stats(self) -> Dict:
        """세션 통계"""
        return {
            "active_sessions": len(self._active_sessions),
            "session_timeout_minutes": self.session_timeout.total_seconds() / 60,
            "sessions": [
                {
                    "session_id": session_id,
                    "message_count": len(state["messages"]),
                    "current_agent": state["current_agent"].value if state["current_agent"] else None
                }
                for session_id, state in self._active_sessions.items()
            ]
        } 