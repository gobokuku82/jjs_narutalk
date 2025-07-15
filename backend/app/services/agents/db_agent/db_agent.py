"""
DB Agent - 내부 벡터 검색 Agent

ChromaDB를 사용한 문서 검색, 정책 검색, 지식베이스 질문답변을 처리합니다.
"""

import logging
from typing import Dict, Any, List, Optional
import chromadb
from pathlib import Path
from ....core.config import settings
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class DBAgent:
    """내부 벡터 검색 Agent"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.chroma_client = None
        self.collection = None
        
        # ChromaDB 초기화
        try:
            self._initialize_chroma_db()
        except Exception as e:
            logger.warning(f"ChromaDB 초기화 실패: {str(e)}")
    
    def _initialize_chroma_db(self):
        """ChromaDB 초기화"""
        try:
            chroma_path = Path(settings.chroma_db_path)
            chroma_path.mkdir(parents=True, exist_ok=True)
            
            # ChromaDB 클라이언트 생성
            self.chroma_client = chromadb.PersistentClient(path=str(chroma_path))
            
            # 컬렉션 가져오기 또는 생성
            try:
                self.collection = self.chroma_client.get_collection("documents")
                logger.info("기존 ChromaDB 컬렉션 로드 완료")
            except:
                self.collection = self.chroma_client.create_collection("documents")
                logger.info("새로운 ChromaDB 컬렉션 생성 완료")
                
        except Exception as e:
            logger.error(f"ChromaDB 초기화 실패: {str(e)}")
            raise
    
    async def process(self, args: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """DB Agent 메인 처리 함수"""
        try:
            query = args.get("query", original_message)
            search_type = args.get("search_type", "semantic")
            document_type = args.get("document_type", "general")
            
            logger.info(f"DB Agent 처리: {search_type} 검색 - {query[:50]}...")
            
            # 검색 실행
            if search_type == "semantic":
                results = await self._semantic_search(query, document_type)
            elif search_type == "keyword":
                results = await self._keyword_search(query, document_type)
            elif search_type == "hybrid":
                results = await self._hybrid_search(query, document_type)
            else:
                results = await self._semantic_search(query, document_type)
            
            if results:
                # 검색 결과를 기반으로 응답 생성
                response = await self._generate_response(query, results)
                
                return {
                    "response": response,
                    "sources": results,
                    "metadata": {
                        "agent": "db_agent",
                        "search_type": search_type,
                        "document_type": document_type,
                        "results_count": len(results)
                    }
                }
            else:
                return {
                    "response": f"'{query}'와 관련된 문서를 찾을 수 없습니다. 다른 키워드로 검색해보시거나 더 구체적인 질문을 해주세요.",
                    "sources": [],
                    "metadata": {
                        "agent": "db_agent",
                        "search_type": search_type,
                        "document_type": document_type,
                        "results_count": 0
                    }
                }
                
        except Exception as e:
            logger.error(f"DB Agent 처리 실패: {str(e)}")
            return {
                "response": f"문서 검색 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "metadata": {"error": str(e), "agent": "db_agent"}
            }
    
    async def _semantic_search(self, query: str, document_type: str) -> List[Dict[str, Any]]:
        """의미 기반 검색"""
        try:
            if not self.collection or not self.embedding_service.is_available():
                return await self._fallback_search(query)
            
            # 쿼리 임베딩 생성
            query_embedding = await self.embedding_service.embed_text(query)
            if not query_embedding:
                return await self._fallback_search(query)
            
            # ChromaDB에서 검색
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                where={"type": document_type} if document_type != "general" else None
            )
            
            # 결과 포맷팅
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0] if results["metadatas"] else [{}] * len(results["documents"][0]),
                    results["distances"][0] if results["distances"] else [0.0] * len(results["documents"][0])
                )):
                    formatted_results.append({
                        "content": doc,
                        "metadata": metadata,
                        "score": 1.0 - distance,  # 유사도 점수로 변환
                        "rank": i + 1,
                        "source": "chromadb_semantic_search"
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"의미 검색 실패: {str(e)}")
            return await self._fallback_search(query)
    
    async def _keyword_search(self, query: str, document_type: str) -> List[Dict[str, Any]]:
        """키워드 기반 검색"""
        try:
            if not self.collection:
                return await self._fallback_search(query)
            
            # 키워드 검색 (where 조건 사용)
            results = self.collection.query(
                query_texts=[query],
                n_results=5,
                where={"type": document_type} if document_type != "general" else None
            )
            
            # 결과 포맷팅
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0] if results["metadatas"] else [{}] * len(results["documents"][0]),
                    results["distances"][0] if results["distances"] else [0.0] * len(results["documents"][0])
                )):
                    formatted_results.append({
                        "content": doc,
                        "metadata": metadata,
                        "score": 1.0 - distance,
                        "rank": i + 1,
                        "source": "chromadb_keyword_search"
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"키워드 검색 실패: {str(e)}")
            return await self._fallback_search(query)
    
    async def _hybrid_search(self, query: str, document_type: str) -> List[Dict[str, Any]]:
        """하이브리드 검색 (의미 + 키워드)"""
        try:
            # 의미 검색과 키워드 검색 결과를 결합
            semantic_results = await self._semantic_search(query, document_type)
            keyword_results = await self._keyword_search(query, document_type)
            
            # 중복 제거 및 점수 조합
            combined_results = {}
            
            # 의미 검색 결과 추가 (가중치 0.7)
            for result in semantic_results:
                doc_id = result["content"][:100]  # 문서 일부를 ID로 사용
                combined_results[doc_id] = {
                    **result,
                    "score": result["score"] * 0.7,
                    "source": "hybrid_semantic"
                }
            
            # 키워드 검색 결과 추가 (가중치 0.3)
            for result in keyword_results:
                doc_id = result["content"][:100]
                if doc_id in combined_results:
                    # 기존 결과와 점수 결합
                    combined_results[doc_id]["score"] += result["score"] * 0.3
                    combined_results[doc_id]["source"] = "hybrid_combined"
                else:
                    combined_results[doc_id] = {
                        **result,
                        "score": result["score"] * 0.3,
                        "source": "hybrid_keyword"
                    }
            
            # 점수 순으로 정렬
            final_results = sorted(combined_results.values(), key=lambda x: x["score"], reverse=True)
            
            # 순위 재설정
            for i, result in enumerate(final_results[:5]):
                result["rank"] = i + 1
            
            return final_results[:5]
            
        except Exception as e:
            logger.error(f"하이브리드 검색 실패: {str(e)}")
            return await self._fallback_search(query)
    
    async def _fallback_search(self, query: str) -> List[Dict[str, Any]]:
        """폴백 검색 결과"""
        fallback_docs = [
            {
                "content": f"'{query}'와 관련된 기본 문서입니다. 더 구체적인 검색을 위해 ChromaDB를 설정해주세요.",
                "metadata": {"type": "fallback", "query": query},
                "score": 0.5,
                "rank": 1,
                "source": "fallback_search"
            }
        ]
        return fallback_docs
    
    async def _generate_response(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """검색 결과를 기반으로 응답 생성"""
        try:
            if not search_results:
                return f"'{query}'와 관련된 문서를 찾을 수 없습니다."
            
            # 상위 3개 결과 사용
            top_results = search_results[:3]
            
            # 검색 결과 요약
            context = "\n\n".join([
                f"문서 {i+1}: {result['content'][:300]}..."
                for i, result in enumerate(top_results)
            ])
            
            # 간단한 응답 생성 (추후 OpenAI API로 개선 가능)
            response = f"""'{query}'에 대한 검색 결과입니다.

총 {len(search_results)}개의 관련 문서를 찾았습니다.

주요 내용:
{context}

더 자세한 정보가 필요하시면 구체적인 질문을 해주세요."""

            return response
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {str(e)}")
            return f"검색 결과를 처리하는 중 오류가 발생했습니다: {str(e)}"
    
    def get_collection_info(self) -> Dict[str, Any]:
        """컬렉션 정보 반환"""
        try:
            if not self.collection:
                return {"error": "컬렉션이 초기화되지 않았습니다."}
            
            count = self.collection.count()
            return {
                "collection_name": "documents",
                "document_count": count,
                "status": "active" if count > 0 else "empty"
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def add_document(self, content: str, metadata: Dict[str, Any] = None) -> bool:
        """문서 추가"""
        try:
            if not self.collection or not self.embedding_service.is_available():
                return False
            
            # 문서 임베딩 생성
            embedding = await self.embedding_service.embed_text(content)
            if not embedding:
                return False
            
            # ChromaDB에 추가
            doc_id = f"doc_{hash(content)}"
            self.collection.add(
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata or {}],
                ids=[doc_id]
            )
            
            logger.info(f"문서 추가 완료: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"문서 추가 실패: {str(e)}")
            return False 