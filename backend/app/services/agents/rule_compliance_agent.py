"""
Rule Compliance Agent
규정 및 컴플라이언스 분석을 담당하는 Agent
현재는 rule DB 미구현으로 기본 규정 체크 기능 제공
"""

import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
from ...core.config import settings

logger = logging.getLogger(__name__)

class RuleComplianceAgent:
    """규정 컴플라이언스 분석 Agent"""
    
    def __init__(self):
        self.openai_client = None
        try:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
        
        # 기본 규정 규칙 (데이터베이스 대신 임시 사용)
        self.basic_rules = {
            "ethics": [
                "이해상충 금지 - 개인적 이익과 회사 이익이 상충하는 행위 금지",
                "선물 및 접대 제한 - 업무 관련 선물 및 접대는 사회 통념상 적정 수준 내",
                "정보 보안 - 회사 기밀 정보의 외부 유출 금지",
                "공정 거래 - 불공정한 거래 행위 및 담합 금지"
            ],
            "finance": [
                "예산 승인 절차 - 일정 금액 이상 지출 시 사전 승인 필요",
                "영수증 보관 - 모든 비용 지출에 대한 영수증 보관 의무",
                "회계 투명성 - 정확한 회계 기록 작성 및 허위 기재 금지",
                "자금 운용 - 회사 자금의 개인적 사용 금지"
            ],
            "hr": [
                "근무 시간 준수 - 정규 근무 시간 및 휴가 규정 준수",
                "차별 금지 - 성별, 나이, 종교 등에 의한 차별 금지",
                "괴롭힘 방지 - 직장 내 괴롭힘 및 성희롱 금지",
                "개인정보 보호 - 직원 개인정보의 적절한 관리 및 보호"
            ],
            "safety": [
                "안전 수칙 준수 - 작업장 안전 수칙 및 보호장비 착용 의무",
                "사고 보고 - 안전사고 발생 시 즉시 보고 의무",
                "위험물 관리 - 위험물질의 적절한 보관 및 처리",
                "비상 대응 - 비상상황 발생 시 대응 절차 숙지"
            ],
            "general": [
                "법령 준수 - 관련 법령 및 규정 준수",
                "문서 관리 - 업무 관련 문서의 적절한 작성 및 보관",
                "보고 의무 - 업무상 중요 사항의 적시 보고",
                "협력 의무 - 동료 및 상급자와의 원활한 협력"
            ]
        }
        
        logger.info("Rule Compliance Agent 초기화 완료")
    
    async def process(self, function_args: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """
        규정 준수 분석 처리
        
        Args:
            function_args: OpenAI function calling에서 전달된 인자
            original_message: 원본 사용자 메시지
            
        Returns:
            처리 결과 딕셔너리
        """
        try:
            content = function_args.get("content", "")
            rule_category = function_args.get("rule_category", "general")
            
            logger.info(f"규정 준수 분석 시작: 카테고리={rule_category}")
            
            # 1. 관련 규정 검색
            relevant_rules = self._get_relevant_rules(content, rule_category)
            
            # 2. 컴플라이언스 분석 수행
            compliance_analysis = await self._analyze_compliance(content, relevant_rules, original_message, rule_category)
            
            return {
                "response": compliance_analysis["response"],
                "sources": compliance_analysis["sources"],
                "metadata": {
                    "agent": "rule_compliance_agent",
                    "rule_category": rule_category,
                    "rules_checked": len(relevant_rules),
                    "compliance_status": compliance_analysis["status"],
                    "risk_level": compliance_analysis["risk_level"]
                }
            }
                
        except Exception as e:
            logger.error(f"Rule Compliance Agent 처리 실패: {str(e)}")
            return {
                "response": f"규정 준수 분석 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "metadata": {
                    "agent": "rule_compliance_agent",
                    "error": str(e)
                }
            }
    
    def _get_relevant_rules(self, content: str, rule_category: str) -> List[str]:
        """
        관련 규정 검색
        """
        try:
            # 지정된 카테고리의 규정 가져오기
            category_rules = self.basic_rules.get(rule_category, [])
            
            # 전체 검색인 경우 모든 카테고리에서 관련 규정 검색
            if rule_category == "general" or not category_rules:
                all_rules = []
                for category, rules in self.basic_rules.items():
                    all_rules.extend(rules)
                
                # 키워드 기반으로 관련성 높은 규정 필터링
                relevant_rules = self._filter_relevant_rules(content, all_rules)
                return relevant_rules[:5]  # 상위 5개만 반환
            
            return category_rules
            
        except Exception as e:
            logger.error(f"관련 규정 검색 실패: {str(e)}")
            return []
    
    def _filter_relevant_rules(self, content: str, all_rules: List[str]) -> List[str]:
        """
        키워드 기반으로 관련성 높은 규정 필터링
        """
        content_lower = content.lower()
        relevant_rules = []
        
        # 키워드 매칭 점수 계산
        for rule in all_rules:
            rule_lower = rule.lower()
            score = 0
            
            # 공통 키워드 체크
            keywords = ["금지", "의무", "승인", "보고", "관리", "준수", "제한", "보호"]
            for keyword in keywords:
                if keyword in content_lower and keyword in rule_lower:
                    score += 1
            
            # 특정 업무 키워드 체크
            business_keywords = ["비용", "지출", "문서", "정보", "직원", "고객", "거래", "계약"]
            for keyword in business_keywords:
                if keyword in content_lower and keyword in rule_lower:
                    score += 2
            
            if score > 0:
                relevant_rules.append((rule, score))
        
        # 점수 순으로 정렬하여 반환
        relevant_rules.sort(key=lambda x: x[1], reverse=True)
        return [rule for rule, score in relevant_rules]
    
    async def _analyze_compliance(self, content: str, relevant_rules: List[str], original_message: str, rule_category: str) -> Dict[str, Any]:
        """
        컴플라이언스 분석 수행
        """
        if not self.openai_client:
            return {
                "response": f"OpenAI 서비스에 연결할 수 없어 기본 규정만 제공합니다:\n\n{self._format_rules(relevant_rules)}",
                "sources": [{"type": "basic_rules", "rules": relevant_rules}],
                "status": "unknown",
                "risk_level": "medium"
            }
        
        try:
            # 규정 텍스트 포맷팅
            rules_text = "\n".join([f"- {rule}" for rule in relevant_rules])
            
            # OpenAI 프롬프트 생성
            prompt = f"""다음은 규정 준수 분석 요청입니다:

분석 대상: {content}

적용 가능한 규정:
{rules_text}

규정 카테고리: {self._get_category_korean(rule_category)}

사용자 요청: {original_message}

위 내용을 분석하여 다음 사항을 제공해주세요:

1. 규정 위반 여부 판단
2. 위반 가능성이 있는 부분 구체적 지적
3. 준수해야 할 규정 설명
4. 개선 방안 또는 대안 제시
5. 리스크 수준 평가 (높음/보통/낮음)

답변 조건:
- 한국어로 답변하세요
- 객관적이고 전문적으로 분석하세요
- 구체적인 근거를 제시하세요
- 실무에 도움이 되는 조언을 포함하세요
- 명확하고 이해하기 쉽게 설명하세요"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # 객관적 분석을 위해 낮은 temperature
                max_tokens=1200
            )
            
            analysis_response = response.choices[0].message.content
            
            # 리스크 수준 추출 (간단한 키워드 분석)
            risk_level = self._extract_risk_level(analysis_response)
            compliance_status = self._extract_compliance_status(analysis_response)
            
            return {
                "response": analysis_response,
                "sources": [
                    {
                        "type": "compliance_rules",
                        "category": rule_category,
                        "rules": relevant_rules,
                        "source": "rule_compliance_agent"
                    }
                ],
                "status": compliance_status,
                "risk_level": risk_level
            }
            
        except Exception as e:
            logger.error(f"컴플라이언스 분석 실패: {str(e)}")
            return {
                "response": f"분석 중 오류가 발생했습니다. 관련 규정:\n\n{self._format_rules(relevant_rules)}",
                "sources": [{"type": "basic_rules", "rules": relevant_rules}],
                "status": "error",
                "risk_level": "unknown"
            }
    
    def _extract_risk_level(self, analysis_text: str) -> str:
        """
        분석 결과에서 리스크 수준 추출
        """
        analysis_lower = analysis_text.lower()
        
        if any(keyword in analysis_lower for keyword in ["높음", "high", "위험", "심각", "중대"]):
            return "high"
        elif any(keyword in analysis_lower for keyword in ["낮음", "low", "안전", "양호"]):
            return "low"
        else:
            return "medium"
    
    def _extract_compliance_status(self, analysis_text: str) -> str:
        """
        분석 결과에서 준수 상태 추출
        """
        analysis_lower = analysis_text.lower()
        
        if any(keyword in analysis_lower for keyword in ["위반", "문제", "부적절", "금지"]):
            return "violation"
        elif any(keyword in analysis_lower for keyword in ["준수", "적절", "문제없음", "양호"]):
            return "compliant"
        else:
            return "review_needed"
    
    def _get_category_korean(self, rule_category: str) -> str:
        """
        규정 카테고리를 한국어로 변환
        """
        korean_mapping = {
            "ethics": "윤리 규정",
            "finance": "재무 규정",
            "hr": "인사 규정",
            "safety": "안전 규정",
            "general": "일반 규정"
        }
        return korean_mapping.get(rule_category, rule_category)
    
    def _format_rules(self, rules: List[str]) -> str:
        """
        규정 목록을 텍스트로 포맷팅
        """
        if not rules:
            return "적용 가능한 규정이 없습니다."
        
        formatted_rules = []
        for i, rule in enumerate(rules, 1):
            formatted_rules.append(f"{i}. {rule}")
        
        return "\n".join(formatted_rules)
    
    async def get_all_rules_by_category(self, category: str = None) -> Dict[str, Any]:
        """
        카테고리별 전체 규정 조회 (관리용)
        """
        try:
            if category and category in self.basic_rules:
                return {
                    "category": category,
                    "rules": self.basic_rules[category],
                    "count": len(self.basic_rules[category])
                }
            else:
                return {
                    "all_categories": self.basic_rules,
                    "total_rules": sum(len(rules) for rules in self.basic_rules.values())
                }
        except Exception as e:
            logger.error(f"규정 조회 실패: {str(e)}")
            return {"error": str(e)}
    
    async def add_custom_rule(self, category: str, rule: str) -> bool:
        """
        사용자 정의 규정 추가 (확장 기능)
        """
        try:
            if category not in self.basic_rules:
                self.basic_rules[category] = []
            
            if rule not in self.basic_rules[category]:
                self.basic_rules[category].append(rule)
                logger.info(f"새 규정 추가: {category} - {rule}")
                return True
            
            return False  # 이미 존재하는 규정
            
        except Exception as e:
            logger.error(f"규정 추가 실패: {str(e)}")
            return False 