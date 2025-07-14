"""
State Manager 기반 채팅 API 엔드포인트
LangGraph StateGraph와 Session Management를 통한 상태 관리
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, AsyncGenerator
import logging
import json
import asyncio

# State Management 시스템 import
from ...services.state_management import StateManager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 전역 State Manager 인스턴스
state_manager = StateManager()

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
class ChatResponse(BaseModel):
    response: str
    agent: str
    arguments: Dict[str, Any]
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    session_id: str
    error: Optional[str] = None

@router.post("/chat/stream")
async def state_managed_chat_stream(request: ChatMessage):
    """
    State Manager를 통한 스트리밍 채팅
    
    Features:
    - LangGraph StateGraph 기반 대화 흐름
    - 세션별 대화 기록 관리
    - 컨텍스트 유지 및 상태 지속성
    """
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            logger.info(f"State managed chat stream: {request.message}")
            
            # 시작 메시지
            yield f"data: {json.dumps({'type': 'start', 'message': 'State Manager 초기화 중...', 'stage': 'initialize'})}\n\n"
            await asyncio.sleep(0.1)
            
            # 세션 확인/생성
            yield f"data: {json.dumps({'type': 'session', 'message': '세션 확인 중...', 'stage': 'session_check'})}\n\n"
            await asyncio.sleep(0.2)
            
            # StateGraph 처리 시작
            yield f"data: {json.dumps({'type': 'processing', 'message': 'LangGraph StateGraph 실행 중...', 'stage': 'state_graph'})}\n\n"
            await asyncio.sleep(0.3)
            
            # State Manager를 통해 메시지 처리
            result = await state_manager.process_message(
                message=request.message,
                session_id=request.session_id,
                user_id=request.user_id
            )
            
            if result.get('error'):
                yield f"data: {json.dumps({'type': 'error', 'message': result['error']})}\n\n"
                return
            
            # 에이전트 정보 전송
            agent_name = result.get('agent', 'unknown')
            yield f"data: {json.dumps({'type': 'agent_info', 'agent': agent_name, 'message': f'{agent_name} 에이전트가 처리했습니다', 'stage': 'agent_complete'})}\n\n"
            await asyncio.sleep(0.2)
            
            # 응답을 단어별로 스트리밍
            response_text = result.get('response', '')
            words = response_text.split()
            current_text = ""
            
            for i, word in enumerate(words):
                current_text += word + " "
                
                yield f"data: {json.dumps({'type': 'content', 'content': current_text.strip(), 'is_final': i == len(words) - 1})}\n\n"
                await asyncio.sleep(0.05)
            
            # 최종 메타데이터 전송
            final_data = {
                'type': 'complete',
                'agent': result.get('agent', 'unknown'),
                'sources': result.get('sources', []),
                'metadata': result.get('metadata', {}),
                'session_id': result.get('session_id'),
                'stage': 'complete'
            }
            
            yield f"data: {json.dumps(final_data)}\n\n"
            yield f"data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"State managed chat stream error: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'스트리밍 처리 중 오류: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )

@router.post("/chat", response_model=ChatResponse)
async def state_managed_chat(request: ChatMessage):
    """
    State Manager를 통한 일반 채팅
    
    Features:
    - LangGraph StateGraph 기반 처리
    - 대화 기록 자동 저장
    - 세션별 컨텍스트 유지
    - 4개 전문 Agent 자동 라우팅
    """
    try:
        logger.info(f"State managed chat request: {request.message}")
        
        # State Manager를 통해 메시지 처리
        result = await state_manager.process_message(
            message=request.message,
            session_id=request.session_id,
            user_id=request.user_id
        )
        
        logger.info(f"State managed chat response - Agent: {result.get('agent', 'unknown')}, Session: {result.get('session_id')}")
        
        return ChatResponse(
            response=result.get("response", ""),
            agent=result.get("agent", "unknown"),
            arguments=result.get("arguments", {}),
            sources=result.get("sources", []),
            metadata=result.get("metadata", {}),
            session_id=result.get("session_id", ""),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"State managed chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"State managed chat failed: {str(e)}"
        )

@router.get("/conversation/history/{session_id}")
async def get_conversation_history(session_id: str, limit: int = 20):
    """
    대화 기록 조회
    """
    try:
        history = state_manager.get_conversation_history(session_id, limit)
        return {
            "session_id": session_id,
            "messages": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Get conversation history error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversation history: {str(e)}"
        )

@router.get("/session/stats/{session_id}")
async def get_session_stats(session_id: str):
    """
    세션 통계 조회
    """
    try:
        stats = state_manager.get_session_stats(session_id)
        return {
            "session_id": session_id,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Get session stats error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session stats: {str(e)}"
        )

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    세션 삭제
    """
    try:
        state_manager.delete_session(session_id)
        return {
            "message": f"Session {session_id} deleted successfully"
        }
    except Exception as e:
        logger.error(f"Delete session error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )

@router.post("/session/cleanup")
async def cleanup_sessions():
    """
    비활성 세션 정리
    """
    try:
        state_manager.cleanup_sessions()
        return {
            "message": "Session cleanup completed"
        }
    except Exception as e:
        logger.error(f"Session cleanup error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup sessions: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    State Manager 상태 확인
    """
    try:
        # 세션 통계 가져오기
        session_stats = state_manager.session_manager.get_session_stats()
        
        return {
            "status": "healthy",
            "system": "state_managed_chat",
            "features": [
                "LangGraph StateGraph",
                "Session Management", 
                "Conversation History",
                "Context Preservation",
                "4-Agent Routing System"
            ],
            "session_stats": session_stats,
            "agents": [
                "chroma_db_agent - 문서 검색 및 질문답변",
                "employee_db_agent - 직원 정보 검색",
                "client_analysis_agent - 고객 데이터 분석",
                "rule_compliance_agent - 규정 준수 분석"
            ]
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "error",
            "system": "state_managed_chat",
            "error": str(e)
        }

# Legacy API 호환성을 위한 엔드포인트들
@router.get("/tools")
async def get_available_tools():
    """
    사용 가능한 도구들의 목록 반환 (Legacy 호환성)
    """
    return {
        "message": "현재 시스템은 LangGraph StateGraph 기반으로 변경되었습니다.",
        "new_system": "state_managed_chat",
        "agents": [
            {
                "name": "chroma_db_agent",
                "description": "ChromaDB 문서 검색 및 질문답변",
                "capabilities": ["문서 검색", "정책 질의", "규정 확인"]
            },
            {
                "name": "employee_db_agent", 
                "description": "직원 정보 및 조직 관리",
                "capabilities": ["직원 검색", "조직도 확인", "연락처 조회"]
            },
            {
                "name": "client_analysis_agent",
                "description": "고객 데이터 분석 및 보고",
                "capabilities": ["고객 분석", "매출 분석", "거래 현황"]
            },
            {
                "name": "rule_compliance_agent",
                "description": "규정 준수 및 컴플라이언스 분석", 
                "capabilities": ["규정 검토", "위험 분석", "준수성 확인"]
            }
        ]
    }

@router.post("/test-tool")
async def test_tool_legacy(tool_name: str, tool_args: Dict[str, Any]):
    """
    도구 테스트 (Legacy 호환성)
    """
    return {
        "message": "Legacy tool testing is no longer supported",
        "recommendation": "Use /chat endpoint with StateManager for proper agent routing",
        "tool_name": tool_name,
        "args": tool_args
    } 