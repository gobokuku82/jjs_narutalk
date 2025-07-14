"""
State Schema 정의

LangGraph StateGraph에서 사용할 상태 구조를 정의합니다.
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

class MessageRole(Enum):
    """메시지 역할 정의"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class AgentType(Enum):
    """에이전트 타입 정의"""
    CHROMA_DB = "chroma_db_agent"
    EMPLOYEE_DB = "employee_db_agent"
    CLIENT_ANALYSIS = "client_analysis_agent"
    RULE_COMPLIANCE = "rule_compliance_agent"

@dataclass
class MessageState:
    """개별 메시지 상태"""
    role: MessageRole
    content: str
    timestamp: datetime
    agent_type: Optional[AgentType] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = asdict(self)
        result["role"] = self.role.value
        result["timestamp"] = self.timestamp.isoformat()
        if self.agent_type:
            result["agent_type"] = self.agent_type.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageState":
        """딕셔너리에서 생성"""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            agent_type=AgentType(data["agent_type"]) if data.get("agent_type") else None,
            metadata=data.get("metadata")
        )

class ConversationState(TypedDict):
    """LangGraph에서 사용할 대화 상태"""
    
    # 기본 정보
    session_id: str
    user_id: Optional[str]
    current_message: str
    
    # 대화 기록
    messages: List[MessageState]
    
    # 컨텍스트 정보
    current_agent: Optional[AgentType]
    agent_arguments: Dict[str, Any]
    last_agent_response: str
    
    # 메타데이터
    conversation_metadata: Dict[str, Any]
    sources: List[Dict[str, Any]]
    
    # 상태 제어
    should_continue: bool
    error_message: Optional[str]
    
    # 라우팅 정보
    route_confidence: float
    route_history: List[Dict[str, Any]]

@dataclass
class SessionInfo:
    """세션 정보"""
    session_id: str
    user_id: Optional[str]
    created_at: datetime
    last_activity: datetime
    message_count: int
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": self.message_count,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionInfo":
        """딕셔너리에서 생성"""
        return cls(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            message_count=data["message_count"],
            metadata=data.get("metadata", {})
        )

def create_initial_state(session_id: str, user_id: Optional[str] = None, message: str = "") -> ConversationState:
    """초기 상태 생성"""
    return ConversationState(
        session_id=session_id,
        user_id=user_id,
        current_message=message,
        messages=[],
        current_agent=None,
        agent_arguments={},
        last_agent_response="",
        conversation_metadata={},
        sources=[],
        should_continue=True,
        error_message=None,
        route_confidence=0.0,
        route_history=[]
    ) 