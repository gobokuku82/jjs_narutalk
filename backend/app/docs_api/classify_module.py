from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from classify_docs import DocumentClassifyAgent
from write_docs import DocumentDraftAgent

class ClassifyRequest(BaseModel):
    user_input: str

class ClassifyResponse(BaseModel):
    success: bool
    state: Optional[Dict[str, Any]]
    error: Optional[str]

class WriteRequest(BaseModel):
    state: Dict[str, Any]
    user_input: str

class WriteResponse(BaseModel):
    success: bool
    filled_data: Optional[Dict[str, Any]]
    error: Optional[str]

router = APIRouter()

@router.post("/classify", response_model=ClassifyResponse)
async def classify_document(request: ClassifyRequest):
    try:
        agent = DocumentClassifyAgent()
        result = agent.run(request.user_input)
        
        if result:
            return ClassifyResponse(
                success=True,
                state=dict(result),
                error=None
            )
        else:
            return ClassifyResponse(
                success=False,
                state=None,
                error="문서 분류에 실패했습니다."
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분류 처리 중 오류가 발생했습니다: {str(e)}")

@router.post("/write", response_model=WriteResponse)
async def write_document(request: WriteRequest):
    try:
        agent = DocumentDraftAgent()
        result = agent.run_with_state(request.state, request.user_input)
        
        if result:
            return WriteResponse(
                success=True,
                filled_data=result,
                error=None
            )
        else:
            return WriteResponse(
                success=False,
                filled_data=None,
                error="문서 초안 작성에 실패했습니다."
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 작성 처리 중 오류가 발생했습니다: {str(e)}")