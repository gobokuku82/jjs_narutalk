"""
API 라우터 모듈

모든 API 엔드포인트 라우터들을 포함합니다.
"""

from .fastapi_router_tool_calling import router as tool_calling_router
# from .fastapi_router_simple import router as simple_router  # 삭제됨
# from .fastapi_router_document import router as document_router  # 현재 비활성화됨

__all__ = [
    "tool_calling_router",
    # "simple_router",  # 삭제됨
    # "document_router"  # 현재 비활성화됨
] 