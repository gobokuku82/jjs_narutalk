"""
ChromaDB Agent
임베딩 기반 문서 검색 및 질문답변을 담당하는 Agent
KURE-V1 임베딩 모델과 BGE-reranker 사용
"""

import logging
from typing import Dict, List, Any, Optional
from ..embedding_service import EmbeddingService
from openai import OpenAI
from ...core.config import settings

logger = logging.getLogger(__name__)

class ChromaDBAgent:
    """ChromaDB 기반 문서 검색 Agent"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.openai_client = None
        try:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
        
        logger.info("ChromaDB Agent 초기화 완료")
    
    async def process(self, function_args: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """
        문서 검색 및 질문답변 처리
        
        Args:
            function_args: OpenAI function calling에서 전달된 인자
            original_message: 원본 사용자 메시지
            
        Returns:
            처리 결과 딕셔너리
        """
        try:
            query = function_args.get("query", original_message)
            document_type = function_args.get("document_type", "general")
            
            logger.info(f"ChromaDB 검색 시작: {query}, 타입: {document_type}")
            
            # 1. 임베딩 검색 수행
            search_results = await self._search_documents(query, document_type)
            
            # 2. 검색 결과가 있으면 OpenAI로 답변 생성
            if search_results:
                response = await self._generate_answer(query, search_results, original_message)
                
                return {
                    "response": response,
                    "sources": search_results,
                    "metadata": {
                        "agent": "chroma_db_agent",
                        "document_type": document_type,
                        "documents_found": len(search_results),
                        "search_query": query
                    }
                }
            else:
                return {
                    "response": f"'{query}'에 대한 관련 문서를 찾을 수 없습니다. 다른 검색어로 시도해보시거나 더 구체적인 질문을 해주세요.",
                    "sources": [],
                    "metadata": {
                        "agent": "chroma_db_agent",
                        "document_type": document_type,
                        "documents_found": 0,
                        "search_query": query
                    }
                }
                
        except Exception as e:
            logger.error(f"ChromaDB Agent 처리 실패: {str(e)}")
            return {
                "response": f"문서 검색 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "metadata": {
                    "agent": "chroma_db_agent",
                    "error": str(e)
                }
            }
    
    async def _search_documents(self, query: str, document_type: str = "general") -> List[Dict[str, Any]]:
        """
        ChromaDB에서 문서 검색
        """
        try:
            # 임베딩 서비스를 통한 유사도 검색
            if hasattr(self.embedding_service, 'search_similar_documents'):
                results = await self.embedding_service.search_similar_documents(
                    query=query,
                    limit=5
                )
                
                # 문서 타입 필터링 (필요시)
                if document_type != "general":
                    filtered_results = []
                    for result in results:
                        doc_content = result.get("document", "").lower()
                        if self._matches_document_type(doc_content, document_type):
                            filtered_results.append(result)
                    return filtered_results[:3]  # 상위 3개만 반환
                
                return results[:3]  # 상위 3개만 반환
            else:
                logger.warning("임베딩 서비스에 search_similar_documents 메소드가 없습니다")
                return []
                
        except Exception as e:
            logger.error(f"문서 검색 실패: {str(e)}")
            return []
    
    def _matches_document_type(self, content: str, document_type: str) -> bool:
        """
        문서 내용이 지정된 타입과 일치하는지 확인
        """
        type_keywords = {
            "policy": ["정책", "방침", "policy", "규칙"],
            "manual": ["매뉴얼", "안내서", "manual", "가이드", "사용법"],
            "regulation": ["규정", "규칙", "regulation", "법규", "준수사항"],
            "general": []  # 모든 문서
        }
        
        keywords = type_keywords.get(document_type, [])
        if not keywords:  # general 타입
            return True
            
        return any(keyword in content for keyword in keywords)
    
    async def _generate_answer(self, query: str, search_results: List[Dict[str, Any]], original_message: str) -> str:
        """
        검색 결과를 바탕으로 OpenAI로 답변 생성
        """
        if not self.openai_client:
            return "OpenAI 서비스에 연결할 수 없어 검색 결과만 제공합니다:\n\n" + self._format_search_results(search_results)
        
        try:
            # 검색된 문서 내용 조합
            context_documents = []
            for i, result in enumerate(search_results, 1):
                doc_content = result.get("document", "내용 없음")
                doc_source = result.get("source", f"문서 {i}")
                context_documents.append(f"[문서 {i}: {doc_source}]\n{doc_content}")
            
            context_text = "\n\n".join(context_documents)
            
            # OpenAI 프롬프트 생성
            prompt = f"""다음은 사용자 질문과 관련된 문서들입니다:

{context_text}

사용자 질문: {original_message}

위 문서들을 바탕으로 사용자의 질문에 대해 정확하고 도움이 되는 답변을 제공해주세요.

답변 조건:
1. 한국어로 답변하세요
2. 제공된 문서의 내용을 기반으로 답변하세요
3. 문서에 없는 내용은 추측하지 마세요
4. 구체적이고 실용적인 정보를 제공하세요
5. 필요시 어떤 문서에서 가져온 정보인지 언급하세요"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"답변 생성 실패: {str(e)}")
            return f"답변 생성 중 오류가 발생했습니다. 검색 결과:\n\n{self._format_search_results(search_results)}"
    
    def _format_search_results(self, search_results: List[Dict[str, Any]]) -> str:
        """
        검색 결과를 텍스트로 포맷팅
        """
        if not search_results:
            return "검색 결과가 없습니다."
        
        formatted_results = []
        for i, result in enumerate(search_results, 1):
            doc_content = result.get("document", "내용 없음")
            doc_source = result.get("source", f"문서 {i}")
            score = result.get("score", 0.0)
            
            formatted_results.append(f"📄 {doc_source} (유사도: {score:.2f})\n{doc_content[:200]}...")
        
        return "\n\n".join(formatted_results) 