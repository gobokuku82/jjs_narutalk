"""
메인 Agent Router
OpenAI Function Calling을 사용하여 4개의 전문 Agent로 라우팅
"""

import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
from ..core.config import settings

logger = logging.getLogger(__name__)

class MainAgentRouter:
    """메인 Agent Router - OpenAI Function Calling 기반"""
    
    def __init__(self):
        self.openai_client = None
        
        # API 키 확인 및 디버깅
        api_key = settings.openai_api_key
        logger.info(f"🔍 설정에서 로드된 API 키: {api_key[:10] if api_key else 'None'}...")
        
        if not api_key:
            logger.error("OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
            logger.error("현재 settings.openai_api_key 값: None")
            return
            
        try:
            self.openai_client = OpenAI(api_key=api_key)
            logger.info("OpenAI 클라이언트 초기화 성공")
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
            
        # 4개의 전문 Agent 정의
        self.agent_functions = [
            {
                "type": "function",
                "function": {
                    "name": "chroma_db_agent",
                    "description": "ChromaDB에서 문서 검색 및 질문답변. 회사 문서, 정책, 규정, 매뉴얼 등을 검색할 때 사용합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "검색할 질문이나 키워드"
                            },
                            "document_type": {
                                "type": "string",
                                "enum": ["policy", "manual", "regulation", "general"],
                                "description": "문서 타입 (정책, 매뉴얼, 규정, 일반)"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "employee_db_agent",
                    "description": "직원 데이터베이스에서 직원 정보 검색. 직원 프로필, 부서, 연락처, 업무 이력 등을 조회할 때 사용합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_type": {
                                "type": "string",
                                "enum": ["name", "department", "position", "id"],
                                "description": "검색 유형"
                            },
                            "search_value": {
                                "type": "string",
                                "description": "검색할 값 (이름, 부서명, 직급, ID 등)"
                            }
                        },
                        "required": ["search_type", "search_value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "client_analysis_agent", 
                    "description": "고객 데이터 분석 및 고객 정보 조회. 고객 프로필, 거래 이력, 매출 분석, 고객 세그먼트 분석 등을 수행할 때 사용합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "analysis_type": {
                                "type": "string",
                                "enum": ["profile", "transaction", "sales", "segment"],
                                "description": "분석 유형"
                            },
                            "client_id": {
                                "type": "string",
                                "description": "고객 ID (선택사항)"
                            },
                            "time_period": {
                                "type": "string",
                                "description": "분석 기간 (예: 2024-01 ~ 2024-12)"
                            }
                        },
                        "required": ["analysis_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "rule_compliance_agent",
                    "description": "규정 및 컴플라이언스 분석. 입력된 문서나 행위가 회사 규정에 위반되는지 검토하고, 관련 규정 정보를 제공합니다.",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "검토할 문서 내용이나 행위 설명"
                            },
                            "rule_category": {
                                "type": "string",
                                "enum": ["ethics", "finance", "hr", "safety", "general"],
                                "description": "규정 카테고리"
                            }
                        },
                        "required": ["content"]
                    }
                }
            }
        ]
        
        logger.info("메인 Agent Router 초기화 완료")
    
    async def route_message(self, message: str, user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """
        메시지를 분석하고 적절한 Agent로 라우팅
        """
        if not self.openai_client:
            return {
                "error": "OpenAI 클라이언트가 초기화되지 않았습니다.",
                "response": "시스템 오류가 발생했습니다. OpenAI API 키를 확인해주세요."
            }
        
        try:
            # 1. OpenAI Function Calling으로 적절한 Agent 선택
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 회사의 AI 어시스턴트 라우터입니다. 
                        사용자의 요청을 분석하고 가장 적절한 전문 Agent를 선택해야 합니다.

                        Agent 선택 가이드:
                        1. chroma_db_agent: 문서 검색, 정책 문의, 매뉴얼 질문
                        2. employee_db_agent: 직원 정보, 조직도, 연락처 문의  
                        3. client_analysis_agent: 고객 정보, 매출 분석, 거래 현황
                        4. rule_compliance_agent: 규정 검토, 컴플라이언스 확인

                        사용자의 질문을 분석하고 적절한 함수를 호출하세요."""
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                tools=self.agent_functions,
                tool_choice="auto"
            )
            
            # 2. Function Call 결과 확인
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # 3. 선택된 Agent 실행
                result = await self._execute_agent(function_name, function_args, message)
                
                return {
                    "agent": function_name,
                    "arguments": function_args,
                    "response": result.get("response", ""),
                    "sources": result.get("sources", []),
                    "metadata": result.get("metadata", {}),
                    "user_id": user_id,
                    "session_id": session_id
                }
            
            else:
                # Function Call이 없는 경우 일반 응답
                return {
                    "agent": "general_chat",
                    "response": response.choices[0].message.content,
                    "sources": [],
                    "metadata": {"type": "general"},
                    "user_id": user_id,
                    "session_id": session_id
                }
                
        except Exception as e:
            logger.error(f"Agent routing 실패: {str(e)}")
            return {
                "error": str(e),
                "response": f"라우팅 처리 중 오류가 발생했습니다: {str(e)}"
            }
    
    async def _execute_agent(self, function_name: str, function_args: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """
        선택된 Agent 실행
        """
        try:
            if function_name == "chroma_db_agent":
                # ChromaDB Agent 실행 (추후 구현)
                from .agents.chroma_db_agent import ChromaDBAgent
                agent = ChromaDBAgent()
                return await agent.process(function_args, original_message)
                
            elif function_name == "employee_db_agent":
                # Employee DB Agent 실행 (추후 구현)
                from .agents.employee_db_agent import EmployeeDBAgent
                agent = EmployeeDBAgent()
                return await agent.process(function_args, original_message)
                
            elif function_name == "client_analysis_agent":
                # Client Analysis Agent 실행 (추후 구현)
                from .agents.client_analysis_agent import ClientAnalysisAgent
                agent = ClientAnalysisAgent()
                return await agent.process(function_args, original_message)
                
            elif function_name == "rule_compliance_agent":
                # Rule Compliance Agent 실행 (추후 구현)
                from .agents.rule_compliance_agent import RuleComplianceAgent
                agent = RuleComplianceAgent()
                return await agent.process(function_args, original_message)
            
            else:
                return {
                    "response": f"알 수 없는 Agent: {function_name}",
                    "sources": [],
                    "metadata": {"error": "unknown_agent"}
                }
                
        except ImportError as e:
            logger.warning(f"Agent {function_name} 미구현: {str(e)}")
            return {
                "response": f"{function_name} Agent는 현재 구현 중입니다. 곧 서비스를 제공할 예정입니다.",
                "sources": [],
                "metadata": {"status": "under_development"}
            }
        except Exception as e:
            logger.error(f"Agent {function_name} 실행 실패: {str(e)}")
            return {
                "response": f"Agent 실행 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "metadata": {"error": str(e)}
            } 