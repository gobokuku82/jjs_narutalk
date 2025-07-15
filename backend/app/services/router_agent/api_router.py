"""
Router Agent API Router

OpenAI GPT-4o Tool Calling 기반 Router Agent의 FastAPI 엔드포인트
StateGraph 옵션 지원
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
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

# Router Agent 인스턴스 (StateGraph 사용)
router_agent_state = RouterAgent(use_state_graph=True)
# Router Agent 인스턴스 (기존 방식)
router_agent_normal = RouterAgent(use_state_graph=False)

# FastAPI 라우터
router = APIRouter()

# 요청/응답 모델
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    use_state_graph: Optional[bool] = False  # StateGraph 사용 여부

class ChatResponse(BaseModel):
    response: str
    agent: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    session_id: str
    user_id: Optional[str]
    routing_confidence: float
    timestamp: str
    use_state_graph: bool
    conversation_history: Optional[List[Dict[str, Any]]] = None

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
    use_state_graph: bool

# 메인 채팅 엔드포인트
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """메인 채팅 엔드포인트 - Router Agent를 통한 자동 라우팅"""
    try:
        # StateGraph 사용 여부에 따라 Router Agent 선택
        router_agent = router_agent_state if request.use_state_graph else router_agent_normal
        
        # 세션 ID 생성 (없는 경우)
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"채팅 요청 처리: session_id={session_id}, use_state_graph={request.use_state_graph}, message={request.message[:50]}...")
        
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
            timestamp=datetime.now().isoformat(),
            use_state_graph=request.use_state_graph,
            conversation_history=result.get("conversation_history") if request.use_state_graph else None
        )
        
        logger.info(f"채팅 응답 완료: agent={response.agent}, confidence={response.routing_confidence}, state_graph={request.use_state_graph}")
        return response
        
    except Exception as e:
        logger.error(f"채팅 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류가 발생했습니다: {str(e)}")

# 스트리밍 채팅 엔드포인트
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """스트리밍 채팅 엔드포인트"""
    try:
        # StateGraph 사용 여부에 따라 Router Agent 선택
        router_agent = router_agent_state if request.use_state_graph else router_agent_normal
        
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"스트리밍 채팅 요청: session_id={session_id}, use_state_graph={request.use_state_graph}")
        
        # Router Agent로 요청 라우팅
        result = await router_agent.route_request(
            message=request.message,
            user_id=request.user_id,
            session_id=session_id
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # 스트리밍 응답 생성 (프론트엔드 형식에 맞춤)
        async def generate_stream():
            # 1. 시작 신호
            yield f"data: {json.dumps({'type': 'start', 'session_id': session_id, 'agent': result.get('agent', 'unknown'), 'use_state_graph': request.use_state_graph})}\n\n"
            
            # 2. Agent 선택 정보
            yield f"data: {json.dumps({'type': 'agent_selection', 'message': '적절한 전문 Agent를 선택하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # 3. Agent 정보
            agent_name = result.get('agent', 'unknown')
            yield f"data: {json.dumps({'type': 'agent_info', 'agent': agent_name, 'message': f'{agent_name} Agent가 처리합니다...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # 4. 응답 텍스트를 토큰 단위로 스트리밍 (한국어 친화적)
            response_text = result.get("response", "")
            words = response_text.split()
            
            for i, word in enumerate(words):
                yield f"data: {json.dumps({'type': 'token', 'word': word, 'index': i})}\n\n"
                await asyncio.sleep(0.05)  # 자연스러운 타이핑 효과
            
            # 5. 완료 정보
            complete_data = {
                'type': 'complete',
                'content': response_text,
                'agent': result.get('agent', 'unknown'),
                'sources': result.get('sources', []),
                'metadata': result.get('metadata', {}),
                'routing_confidence': result.get('routing_confidence', 0.0),
                'session_id': session_id,
                'use_state_graph': request.use_state_graph
            }
            yield f"data: {json.dumps(complete_data)}\n\n"
            
            # 6. 종료 신호 (프론트엔드가 기대하는 형식)
            yield f"data: [DONE]\n\n"
        
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
async def get_agents(use_state_graph: bool = Query(False, description="StateGraph 사용 여부")):
    """사용 가능한 Agent 목록 조회"""
    try:
        router_agent = router_agent_state if use_state_graph else router_agent_normal
        agents = router_agent.get_available_agents()
        return [AgentInfo(**agent) for agent in agents]
    except Exception as e:
        logger.error(f"Agent 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent 목록 조회 중 오류가 발생했습니다: {str(e)}")

# Router Agent 통계
@router.get("/stats", response_model=RouterStats)
async def get_router_stats(use_state_graph: bool = Query(False, description="StateGraph 사용 여부")):
    """Router Agent 통계 정보"""
    try:
        router_agent = router_agent_state if use_state_graph else router_agent_normal
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
        # 두 가지 방식 모두 체크
        stats_normal = router_agent_normal.get_router_stats()
        stats_state = router_agent_state.get_router_stats()
        
        return {
            "status": "healthy",
            "normal_router": {
                "status": "healthy" if stats_normal["initialized"] else "degraded",
                "openai_model": stats_normal["openai_model"],
                "total_agents": stats_normal["total_agents"]
            },
            "state_graph_router": {
                "status": "healthy" if stats_state["initialized"] else "degraded",
                "openai_model": stats_state["openai_model"],
                "total_agents": stats_state["total_agents"],
                "state_management": stats_state.get("state_management", "disabled")
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"헬스 체크 실패: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# 대화 기록 조회 (StateGraph 전용)
@router.get("/conversation/history/{session_id}")
async def get_conversation_history(session_id: str):
    """대화 기록 조회 (StateGraph 전용)"""
    try:
        history = router_agent_state.get_conversation_history(session_id)
        return {
            "session_id": session_id,
            "history": history,
            "message_count": len(history),
            "state_management": "enabled"
        }
    except Exception as e:
        logger.error(f"대화 기록 조회 실패: {str(e)}")
        return {
            "session_id": session_id,
            "message": "대화 기록 조회 중 오류가 발생했습니다.",
            "history": [],
            "error": str(e)
        }

# 세션 통계 조회 (StateGraph 전용)
@router.get("/session/stats/{session_id}")
async def get_session_stats(session_id: str):
    """세션 통계 조회 (StateGraph 전용)"""
    try:
        stats = router_agent_state.get_session_stats(session_id)
        return {
            "session_id": session_id,
            "stats": stats,
            "state_management": "enabled"
        }
    except Exception as e:
        logger.error(f"세션 통계 조회 실패: {str(e)}")
        return {
            "session_id": session_id,
            "message": "세션 통계 조회 중 오류가 발생했습니다.",
            "stats": {},
            "error": str(e)
        }

# 세션 삭제 (기본 구현)
@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제 (기본 구현)"""
    return {
        "session_id": session_id,
        "message": "세션 삭제 기능은 현재 구현 중입니다.",
        "deleted": True
    }

# 세션 정리 (기본 구현)
@router.post("/session/cleanup")
async def cleanup_sessions():
    """세션 정리 (기본 구현)"""
    return {
        "message": "세션 정리 기능은 현재 구현 중입니다.",
        "cleaned_sessions": 0
    } 