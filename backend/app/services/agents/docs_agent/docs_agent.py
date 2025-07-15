"""
Docs Agent - 문서 자동생성 및 규정 위반 검색 Agent

문서 생성, 컴플라이언스 검토, 규정 위반 분석을 처리합니다.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from ....core.config import settings
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class DocsAgent:
    """문서 자동생성 및 규정 위반 검색 Agent"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.openai_client = None
        
        # OpenAI 클라이언트 초기화
        try:
            if settings.openai_api_key:
                self.openai_client = OpenAI(api_key=settings.openai_api_key)
                logger.info("Docs Agent OpenAI 클라이언트 초기화 성공")
        except Exception as e:
            logger.warning(f"Docs Agent OpenAI 클라이언트 초기화 실패: {str(e)}")
        
        # 문서 템플릿 정의
        self.document_templates = {
            "report": {
                "name": "보고서",
                "structure": ["제목", "개요", "현황 분석", "문제점", "개선방안", "결론"],
                "format": "공식 보고서 형식"
            },
            "memo": {
                "name": "메모",
                "structure": ["제목", "배경", "주요 내용", "조치사항"],
                "format": "간결한 메모 형식"
            },
            "proposal": {
                "name": "제안서",
                "structure": ["제안 제목", "제안 배경", "제안 내용", "기대효과", "추진계획"],
                "format": "제안서 형식"
            },
            "analysis": {
                "name": "분석서",
                "structure": ["분석 대상", "분석 방법", "분석 결과", "시사점", "권고사항"],
                "format": "분석 보고서 형식"
            }
        }
        
        # 규정 카테고리 정의
        self.regulation_categories = {
            "ethics": "윤리 및 행동강령",
            "finance": "재무 및 회계 규정",
            "hr": "인사 및 노무 규정",
            "safety": "안전 및 보건 규정",
            "general": "일반 운영 규정"
        }
    
    async def process(self, args: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """Docs Agent 메인 처리 함수"""
        try:
            task_type = args.get("task_type")
            content = args.get("content", original_message)
            
            logger.info(f"Docs Agent 처리: {task_type} - {content[:50]}...")
            
            if task_type == "generate_document":
                return await self._generate_document(args, content)
            elif task_type == "compliance_check":
                return await self._compliance_check(args, content)
            elif task_type == "regulation_violation":
                return await self._regulation_violation_check(args, content)
            else:
                return {
                    "response": f"지원하지 않는 작업 타입입니다: {task_type}",
                    "sources": [],
                    "metadata": {"error": "unsupported_task_type", "agent": "docs_agent"}
                }
                
        except Exception as e:
            logger.error(f"Docs Agent 처리 실패: {str(e)}")
            return {
                "response": f"문서 처리 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "metadata": {"error": str(e), "agent": "docs_agent"}
            }
    
    async def _generate_document(self, args: Dict[str, Any], content: str) -> Dict[str, Any]:
        """문서 자동 생성"""
        try:
            document_template = args.get("document_template", "report")
            template_info = self.document_templates.get(document_template, self.document_templates["report"])
            
            if not self.openai_client:
                return await self._fallback_document_generation(content, template_info)
            
            # OpenAI를 사용한 문서 생성
            system_prompt = f"""당신은 전문적인 문서 작성 AI입니다.
            
요청된 문서 타입: {template_info['name']}
문서 구조: {' → '.join(template_info['structure'])}
형식: {template_info['format']}

한국어로 전문적이고 체계적인 문서를 작성해주세요.
각 섹션을 명확히 구분하고, 내용은 구체적이고 실용적으로 작성해주세요."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"다음 내용을 바탕으로 {template_info['name']}를 작성해주세요:\n\n{content}"}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            generated_document = response.choices[0].message.content
            
            # 메타데이터 생성
            metadata = {
                "agent": "docs_agent",
                "task_type": "generate_document",
                "document_type": document_template,
                "template_structure": template_info['structure'],
                "generated_at": datetime.now().isoformat(),
                "word_count": len(generated_document.split())
            }
            
            return {
                "response": f"📄 {template_info['name']} 생성이 완료되었습니다.\n\n{generated_document}",
                "sources": [{"type": "generated_document", "template": document_template}],
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"문서 생성 실패: {str(e)}")
            return await self._fallback_document_generation(content, template_info)
    
    async def _compliance_check(self, args: Dict[str, Any], content: str) -> Dict[str, Any]:
        """컴플라이언스 검토"""
        try:
            regulation_category = args.get("regulation_category", "general")
            category_name = self.regulation_categories.get(regulation_category, "일반 규정")
            
            if not self.openai_client:
                return await self._fallback_compliance_check(content, category_name)
            
            # OpenAI를 사용한 컴플라이언스 검토
            system_prompt = f"""당신은 기업 컴플라이언스 전문가입니다.
            
검토 대상 규정 카테고리: {category_name}

다음 내용을 검토하여:
1. 잠재적 위험 요소 식별
2. 규정 준수 여부 판단
3. 개선 권고사항 제시
4. 위험도 평가 (높음/중간/낮음)

한국의 기업 법규와 일반적인 컴플라이언스 기준을 바탕으로 분석해주세요."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"다음 내용에 대한 컴플라이언스 검토를 해주세요:\n\n{content}"}
                ],
                temperature=0.3,  # 일관된 분석을 위해 낮은 temperature
                max_tokens=1500
            )
            
            compliance_analysis = response.choices[0].message.content
            
            # 위험도 추출 (간단한 키워드 기반)
            risk_level = "중간"
            if any(keyword in compliance_analysis.lower() for keyword in ["높음", "심각", "위험", "위반"]):
                risk_level = "높음"
            elif any(keyword in compliance_analysis.lower() for keyword in ["낮음", "문제없음", "적절"]):
                risk_level = "낮음"
            
            metadata = {
                "agent": "docs_agent",
                "task_type": "compliance_check",
                "regulation_category": regulation_category,
                "risk_level": risk_level,
                "analyzed_at": datetime.now().isoformat()
            }
            
            return {
                "response": f"🔍 {category_name} 컴플라이언스 검토 결과\n\n{compliance_analysis}",
                "sources": [{"type": "compliance_analysis", "category": regulation_category, "risk_level": risk_level}],
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"컴플라이언스 검토 실패: {str(e)}")
            return await self._fallback_compliance_check(content, category_name)
    
    async def _regulation_violation_check(self, args: Dict[str, Any], content: str) -> Dict[str, Any]:
        """규정 위반 검색 및 분석"""
        try:
            regulation_category = args.get("regulation_category", "general")
            category_name = self.regulation_categories.get(regulation_category, "일반 규정")
            
            # 임베딩을 사용한 유사한 위반 사례 검색
            violation_results = await self._search_violation_cases(content, regulation_category)
            
            if not self.openai_client:
                return await self._fallback_violation_check(content, category_name, violation_results)
            
            # OpenAI를 사용한 위반 분석
            system_prompt = f"""당신은 규정 위반 분석 전문가입니다.
            
분석 대상 규정: {category_name}

다음을 수행해주세요:
1. 구체적인 위반 내용 식별
2. 관련 규정 조항 참조
3. 위반 심각도 평가
4. 시정 조치 방안 제시
5. 재발 방지 대책 권고

객관적이고 전문적인 분석을 제공해주세요."""

            context = f"검토 대상:\n{content}\n\n"
            if violation_results:
                context += f"유사 사례:\n{chr(10).join([case['content'][:200] + '...' for case in violation_results[:3]])}"

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            violation_analysis = response.choices[0].message.content
            
            # 위반 심각도 추출
            severity = "중간"
            if any(keyword in violation_analysis.lower() for keyword in ["심각", "중대", "엄중"]):
                severity = "높음"
            elif any(keyword in violation_analysis.lower() for keyword in ["경미", "가벼운", "낮음"]):
                severity = "낮음"
            
            metadata = {
                "agent": "docs_agent",
                "task_type": "regulation_violation",
                "regulation_category": regulation_category,
                "severity": severity,
                "similar_cases_found": len(violation_results),
                "analyzed_at": datetime.now().isoformat()
            }
            
            return {
                "response": f"⚠️ {category_name} 위반 분석 결과\n\n{violation_analysis}",
                "sources": violation_results + [{"type": "violation_analysis", "category": regulation_category, "severity": severity}],
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"규정 위반 검색 실패: {str(e)}")
            return await self._fallback_violation_check(content, category_name, [])
    
    async def _search_violation_cases(self, content: str, category: str) -> List[Dict[str, Any]]:
        """유사한 위반 사례 검색"""
        try:
            if not self.embedding_service.is_available():
                return []
            
            # 간단한 위반 사례 데이터베이스 (실제로는 ChromaDB나 별도 DB에서 조회)
            sample_cases = [
                {
                    "content": f"{category} 관련 위반 사례: 규정을 준수하지 않은 경우입니다.",
                    "metadata": {"category": category, "type": "violation_case"},
                    "score": 0.7,
                    "source": "violation_database"
                }
            ]
            
            return sample_cases
            
        except Exception as e:
            logger.error(f"위반 사례 검색 실패: {str(e)}")
            return []
    
    async def _fallback_document_generation(self, content: str, template_info: Dict) -> Dict[str, Any]:
        """폴백 문서 생성"""
        fallback_doc = f"""📄 {template_info['name']} (기본 템플릿)

요청 내용: {content}

구조:
{chr(10).join([f"{i+1}. {section}" for i, section in enumerate(template_info['structure'])])}

※ 더 상세한 문서 생성을 위해서는 OpenAI API 키를 설정해주세요."""

        return {
            "response": fallback_doc,
            "sources": [{"type": "fallback_document", "template": template_info['name']}],
            "metadata": {"agent": "docs_agent", "mode": "fallback"}
        }
    
    async def _fallback_compliance_check(self, content: str, category_name: str) -> Dict[str, Any]:
        """폴백 컴플라이언스 검토"""
        fallback_analysis = f"""🔍 {category_name} 기본 컴플라이언스 체크

검토 대상: {content[:200]}...

기본 검토 항목:
1. 법적 준수 사항 확인 필요
2. 내부 규정 검토 필요
3. 윤리적 측면 고려 필요
4. 리스크 평가 권장

※ 상세한 분석을 위해서는 OpenAI API 키를 설정해주세요."""

        return {
            "response": fallback_analysis,
            "sources": [{"type": "fallback_compliance", "category": category_name}],
            "metadata": {"agent": "docs_agent", "mode": "fallback", "risk_level": "검토 필요"}
        }
    
    async def _fallback_violation_check(self, content: str, category_name: str, violation_results: List) -> Dict[str, Any]:
        """폴백 위반 검토"""
        fallback_analysis = f"""⚠️ {category_name} 기본 위반 검토

검토 대상: {content[:200]}...

기본 검토 결과:
1. 규정 준수 여부 확인 필요
2. 잠재적 위험 요소 검토 필요
3. 전문가 상담 권장

※ 정확한 위반 분석을 위해서는 OpenAI API 키를 설정해주세요."""

        return {
            "response": fallback_analysis,
            "sources": violation_results + [{"type": "fallback_violation", "category": category_name}],
            "metadata": {"agent": "docs_agent", "mode": "fallback", "severity": "검토 필요"}
        }
    
    def get_available_templates(self) -> Dict[str, Any]:
        """사용 가능한 문서 템플릿 목록"""
        return {
            "templates": self.document_templates,
            "categories": self.regulation_categories
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Agent 상태 정보"""
        return {
            "agent_name": "docs_agent",
            "openai_available": self.openai_client is not None,
            "embedding_available": self.embedding_service.is_available(),
            "supported_tasks": ["generate_document", "compliance_check", "regulation_violation"],
            "document_templates": list(self.document_templates.keys()),
            "regulation_categories": list(self.regulation_categories.keys())
        } 