#!/usr/bin/env python3
"""
디버깅용 테스트 서버
"""

import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from typing import Optional, Dict, Any

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="NaruTalk Debug Server")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "ok", "message": "Debug server is running"}

@app.post("/api/v1/tool-calling/chat")
async def debug_chat(request: ChatRequest):
    """디버깅용 채팅 엔드포인트"""
    try:
        logger.info(f"채팅 요청 받음: {request.message}")
        
        # 간단한 응답 반환
        return {
            "response": f"디버그 응답: {request.message}",
            "agent": "debug_agent",
            "sources": [],
            "metadata": {"debug": True},
            "session_id": request.session_id or "debug_session",
            "routing_confidence": 1.0,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"채팅 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/tool-calling/chat/stream")
async def debug_chat_stream(request: ChatRequest):
    """디버깅용 스트리밍 채팅 엔드포인트"""
    import json
    
    async def generate_stream():
        try:
            logger.info(f"스트리밍 요청 받음: {request.message}")
            
            # 시작 신호
            yield f"data: {json.dumps({'type': 'start', 'session_id': request.session_id or 'debug_session'})}\n\n"
            
            # 처리 중 신호
            yield f"data: {json.dumps({'type': 'agent_selection', 'message': '디버그 Agent 선택 중...'})}\n\n"
            
            # 응답 생성
            response_text = f"디버그 스트리밍 응답: {request.message}"
            words = response_text.split()
            
            for i, word in enumerate(words):
                yield f"data: {json.dumps({'type': 'content', 'content': ' '.join(words[:i+1]), 'is_final': False})}\n\n"
                await asyncio.sleep(0.1)
            
            # 완료 신호
            yield f"data: {json.dumps({'type': 'complete', 'content': response_text, 'agent': 'debug_agent'})}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"스트리밍 오류: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="debug") 