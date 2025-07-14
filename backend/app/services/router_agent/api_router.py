"""
Router Agent API Router

OpenAI GPT-4o Tool Calling 기반 Router Agent의 FastAPI 엔드포인트
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import logging
import uuid
from datetime import datetime
import asyncio

from .router_agent import RouterAgent

logger = logging.getLogger(__name__)

# Router Agent 인스턴스
router_agent = RouterAgent()

# FastAPI 라우터
router = APIRouter()

# 요청/응답 모델
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    agent: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    session_id: str
    user_id: Optional[str]
    routing_confidence: float
    timestamp: str

class AgentInfo(BaseModel):
    name: str
    description: str
    capabilities: List[str]

class RouterStats(BaseModel):
    router_name: str
    openai_model: str
    total_agents: int
    available_agents: List[str]
    initialized: bool

# 메인 채팅 엔드포인트
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """메인 채팅 엔드포인트 - Router Agent를 통한 자동 라우팅"""
    try:
        # 세션 ID 생성 (없는 경우)
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"채팅 요청 처리: session_id={session_id}, message={request.message[:50]}...")
        
        # Router Agent로 요청 라우팅
        result = await router_agent.route_request(
            message=request.message,
            user_id=request.user_id,
            session_id=session_id
        )
        
        # 오류 처리
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # 응답 생성
        response = ChatResponse(
            response=result.get("response", ""),
            agent=result.get("agent", "unknown"),
            sources=result.get("sources", []),
            metadata=result.get("metadata", {}),
            session_id=session_id,
            user_id=request.user_id,
            routing_confidence=result.get("routing_confidence", 0.0),
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"채팅 응답 완료: agent={response.agent}, confidence={response.routing_confidence}")
        return response
        
    except Exception as e:
        logger.error(f"채팅 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류가 발생했습니다: {str(e)}")

# 스트리밍 채팅 엔드포인트
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """스트리밍 채팅 엔드포인트"""
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"스트리밍 채팅 요청: session_id={session_id}")
        
        # Router Agent로 요청 라우팅
        result = await router_agent.route_request(
            message=request.message,
            user_id=request.user_id,
            session_id=session_id
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # 스트리밍 응답 생성
        async def generate_stream():
            # 초기 정보 전송
            yield f"data: {json.dumps({'type': 'start', 'session_id': session_id, 'agent': result.get('agent', 'unknown')})}\n\n"
            
            # 응답 텍스트를 단어 단위로 스트리밍
            response_text = result.get("response", "")
            words = response_text.split()
            
            for i, word in enumerate(words):
                yield f"data: {json.dumps({'type': 'token', 'word': word, 'index': i})}\n\n"
                await asyncio.sleep(0.05)  # 자연스러운 타이핑 효과
            
            # 최종 메타데이터 전송
            final_data = {
                'type': 'end',
                'session_id': session_id,
                'agent': result.get('agent', 'unknown'),
                'sources': result.get('sources', []),
                'metadata': result.get('metadata', {}),
                'routing_confidence': result.get('routing_confidence', 0.0)
            }
            yield f"data: {json.dumps(final_data)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except Exception as e:
        logger.error(f"스트리밍 채팅 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"스트리밍 처리 중 오류가 발생했습니다: {str(e)}")

# 사용 가능한 Agent 목록
@router.get("/agents", response_model=List[AgentInfo])
async def get_agents():
    """사용 가능한 Agent 목록 조회"""
    try:
        agents = router_agent.get_available_agents()
        return [AgentInfo(**agent) for agent in agents]
    except Exception as e:
        logger.error(f"Agent 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent 목록 조회 중 오류가 발생했습니다: {str(e)}")

# Router Agent 통계
@router.get("/stats", response_model=RouterStats)
async def get_router_stats():
    """Router Agent 통계 정보"""
    try:
        stats = router_agent.get_router_stats()
        return RouterStats(**stats)
    except Exception as e:
        logger.error(f"Router 통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}")

# 헬스 체크
@router.get("/health")
async def health_check():
    """Router Agent 헬스 체크"""
    try:
        stats = router_agent.get_router_stats()
        
        return {
            "status": "healthy" if stats["initialized"] else "degraded",
            "router_agent": "RouterAgent",
            "openai_model": stats["openai_model"],
            "total_agents": stats["total_agents"],
            "initialized": stats["initialized"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"헬스 체크 실패: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# 세션 관리 엔드포인트들 (기본 구현)
@router.get("/conversation/history/{session_id}")
async def get_conversation_history(session_id: str):
    """대화 기록 조회 (기본 구현)"""
    return {
        "session_id": session_id,
        "message": "대화 기록 기능은 현재 구현 중입니다.",
        "history": []
    }

@router.get("/session/stats/{session_id}")
async def get_session_stats(session_id: str):
    """세션 통계 조회 (기본 구현)"""
    return {
        "session_id": session_id,
        "message": "세션 통계 기능은 현재 구현 중입니다.",
        "stats": {}
    }

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제 (기본 구현)"""
    return {
        "session_id": session_id,
        "message": "세션 삭제 기능은 현재 구현 중입니다.",
        "deleted": True
    }

@router.post("/session/cleanup")
async def cleanup_sessions():
    """세션 정리 (기본 구현)"""
    return {
        "message": "세션 정리 기능은 현재 구현 중입니다.",
        "cleaned_sessions": 0
    } 