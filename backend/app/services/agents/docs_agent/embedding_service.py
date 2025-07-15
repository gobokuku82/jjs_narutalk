"""
Docs Agent Embedding Service

문서 생성 및 컴플라이언스 검토를 위한 임베딩 서비스
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class EmbeddingService:
    """문서 임베딩 서비스 (기본 구현)"""
    
    def __init__(self):
        logger.info("Docs Agent EmbeddingService 초기화 완료")
    
    def embed_text(self, text: str) -> List[float]:
        """텍스트 임베딩"""
        logger.info(f"문서 텍스트 임베딩 요청: {text[:50]}...")
        return [0.0] * 768
    
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """문서 목록 임베딩"""
        return [self.embed_text(doc) for doc in documents] 