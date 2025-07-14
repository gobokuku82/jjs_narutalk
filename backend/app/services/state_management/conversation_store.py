"""
Conversation Store

SQLite를 사용한 대화 기록 지속 저장소
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from ...core.config import settings
from .state_schema import MessageState, SessionInfo, MessageRole, AgentType

logger = logging.getLogger(__name__)

class ConversationStore:
    """대화 기록 저장소"""
    
    def __init__(self):
        self.db_path = Path(settings.sqlite_db_path) / "conversations.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    def _initialize_database(self):
        """데이터베이스 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 세션 테이블
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        created_at TIMESTAMP,
                        last_activity TIMESTAMP,
                        message_count INTEGER DEFAULT 0,
                        metadata TEXT
                    )
                """)
                
                # 메시지 테이블
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT,
                        role TEXT,
                        content TEXT,
                        timestamp TIMESTAMP,
                        agent_type TEXT,
                        metadata TEXT,
                        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                    )
                """)
                
                # 인덱스 생성
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
                
                conn.commit()
                logger.info("대화 기록 데이터베이스 초기화 완료")
                
        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {str(e)}")
    
    def create_session(self, session_id: str, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> SessionInfo:
        """새 세션 생성"""
        try:
            now = datetime.now()
            session_info = SessionInfo(
                session_id=session_id,
                user_id=user_id,
                created_at=now,
                last_activity=now,
                message_count=0,
                metadata=metadata or {}
            )
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO sessions 
                    (session_id, user_id, created_at, last_activity, message_count, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    session_info.session_id,
                    session_info.user_id,
                    session_info.created_at,
                    session_info.last_activity,
                    session_info.message_count,
                    json.dumps(session_info.metadata)
                ))
                conn.commit()
            
            logger.info(f"세션 생성: {session_id}")
            return session_info
            
        except Exception as e:
            logger.error(f"세션 생성 실패: {str(e)}")
            raise
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """세션 정보 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT session_id, user_id, created_at, last_activity, message_count, metadata
                    FROM sessions WHERE session_id = ?
                """, (session_id,))
                
                row = cursor.fetchone()
                if row:
                    return SessionInfo(
                        session_id=row[0],
                        user_id=row[1],
                        created_at=datetime.fromisoformat(row[2]),
                        last_activity=datetime.fromisoformat(row[3]),
                        message_count=row[4],
                        metadata=json.loads(row[5]) if row[5] else {}
                    )
                return None
                
        except Exception as e:
            logger.error(f"세션 조회 실패: {str(e)}")
            return None
    
    def update_session_activity(self, session_id: str):
        """세션 활동 시간 업데이트"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sessions 
                    SET last_activity = ?, message_count = message_count + 1
                    WHERE session_id = ?
                """, (datetime.now(), session_id))
                conn.commit()
                
        except Exception as e:
            logger.error(f"세션 활동 업데이트 실패: {str(e)}")
    
    def save_message(self, session_id: str, message: MessageState):
        """메시지 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO messages 
                    (session_id, role, content, timestamp, agent_type, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    message.role.value,
                    message.content,
                    message.timestamp,
                    message.agent_type.value if message.agent_type else None,
                    json.dumps(message.metadata) if message.metadata else None
                ))
                conn.commit()
            
            # 세션 활동 업데이트
            self.update_session_activity(session_id)
            logger.debug(f"메시지 저장: {session_id} - {message.role.value}")
            
        except Exception as e:
            logger.error(f"메시지 저장 실패: {str(e)}")
    
    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[MessageState]:
        """대화 기록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT role, content, timestamp, agent_type, metadata
                    FROM messages 
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (session_id, limit))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append(MessageState(
                        role=MessageRole(row[0]),
                        content=row[1],
                        timestamp=datetime.fromisoformat(row[2]),
                        agent_type=AgentType(row[3]) if row[3] else None,
                        metadata=json.loads(row[4]) if row[4] else None
                    ))
                
                # 시간순으로 정렬 (최신이 마지막)
                return list(reversed(messages))
                
        except Exception as e:
            logger.error(f"대화 기록 조회 실패: {str(e)}")
            return []
    
    def get_recent_context(self, session_id: str, context_length: int = 10) -> List[MessageState]:
        """최근 컨텍스트 조회"""
        try:
            return self.get_conversation_history(session_id, context_length)
        except Exception as e:
            logger.error(f"최근 컨텍스트 조회 실패: {str(e)}")
            return []
    
    def delete_session(self, session_id: str):
        """세션 및 관련 메시지 삭제"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 메시지 먼저 삭제
                cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                # 세션 삭제
                cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                conn.commit()
            
            logger.info(f"세션 삭제: {session_id}")
            
        except Exception as e:
            logger.error(f"세션 삭제 실패: {str(e)}")
    
    def get_user_sessions(self, user_id: str, limit: int = 20) -> List[SessionInfo]:
        """사용자별 세션 목록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT session_id, user_id, created_at, last_activity, message_count, metadata
                    FROM sessions 
                    WHERE user_id = ?
                    ORDER BY last_activity DESC
                    LIMIT ?
                """, (user_id, limit))
                
                sessions = []
                for row in cursor.fetchall():
                    sessions.append(SessionInfo(
                        session_id=row[0],
                        user_id=row[1],
                        created_at=datetime.fromisoformat(row[2]),
                        last_activity=datetime.fromisoformat(row[3]),
                        message_count=row[4],
                        metadata=json.loads(row[5]) if row[5] else {}
                    ))
                
                return sessions
                
        except Exception as e:
            logger.error(f"사용자 세션 조회 실패: {str(e)}")
            return []
    
    def cleanup_old_sessions(self, days_old: int = 30):
        """오래된 세션 정리"""
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 오래된 메시지 삭제
                cursor.execute("DELETE FROM messages WHERE session_id IN (SELECT session_id FROM sessions WHERE last_activity < ?)", (cutoff_date,))
                # 오래된 세션 삭제
                cursor.execute("DELETE FROM sessions WHERE last_activity < ?", (cutoff_date,))
                conn.commit()
            
            logger.info(f"{days_old}일 이전 세션 정리 완료")
            
        except Exception as e:
            logger.error(f"세션 정리 실패: {str(e)}") 