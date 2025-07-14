"""
Router Agent

OpenAI GPT-4o Tool Calling을 사용하여 4개의 전문 Agent로 라우팅하는 메인 라우터
"""

import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
from ...core.config import settings

logger = logging.getLogger(__name__)

class RouterAgent:
    """메인 Router Agent - OpenAI Tool Calling 기반"""
    
    def __init__(self):
        self.openai_client = None
        
        # API 키 확인 및 디버깅
        api_key = settings.openai_api_key
        logger.info(f"🔍 Router Agent 초기화 - API 키: {api_key[:10] if api_key else 'None'}...")
        
        if not api_key:
            logger.error("OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
            return
            
        try:
            self.openai_client = OpenAI(api_key=api_key)
            logger.info("Router Agent OpenAI 클라이언트 초기화 성공")
        except Exception as e:
            logger.error(f"Router Agent OpenAI 클라이언트 초기화 실패: {str(e)}")
            
        # 4개의 전문 Agent 정의 (Tool Calling Functions)
        self.agent_functions = [
            {
                "type": "function",
                "function": {
                    "name": "db_agent",
                    "description": "내부 벡터 검색 Agent. ChromaDB를 사용한 문서 검색, 정책 검색, 지식베이스 질문답변을 처리합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "검색할 질문이나 키워드"
                            },
                            "search_type": {
                                "type": "string",
                                "enum": ["semantic", "keyword", "hybrid"],
                                "description": "검색 타입 (의미 검색, 키워드 검색, 하이브리드)"
                            },
                            "document_type": {
                                "type": "string",
                                "enum": ["policy", "manual", "regulation", "general"],
                                "description": "문서 타입"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "docs_agent",
                    "description": "문서 자동생성 및 규정 위반 검색 Agent. 문서 생성, 컴플라이언스 검토, 규정 위반 분석을 처리합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_type": {
                                "type": "string",
                                "enum": ["generate_document", "compliance_check", "regulation_violation"],
                                "description": "작업 타입"
                            },
                            "content": {
                                "type": "string",
                                "description": "처리할 내용이나 생성할 문서 요구사항"
                            },
                            "document_template": {
                                "type": "string",
                                "enum": ["report", "memo", "proposal", "analysis"],
                                "description": "문서 템플릿 타입"
                            },
                            "regulation_category": {
                                "type": "string",
                                "enum": ["ethics", "finance", "hr", "safety", "general"],
                                "description": "규정 카테고리"
                            }
                        },
                        "required": ["task_type", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "employee_agent",
                    "description": "내부 직원정보 검색 Agent. 직원 프로필, 부서 정보, 조직도, 연락처 등을 검색합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_type": {
                                "type": "string",
                                "enum": ["name", "department", "position", "id", "skill", "project"],
                                "description": "검색 유형"
                            },
                            "search_value": {
                                "type": "string",
                                "description": "검색할 값 (이름, 부서명, 직급, ID 등)"
                            },
                            "detail_level": {
                                "type": "string",
                                "enum": ["basic", "detailed", "full"],
                                "description": "정보 상세 레벨"
                            }
                        },
                        "required": ["search_type", "search_value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "client_agent",
                    "description": "거래처 분석 Agent. 고객 데이터 분석, 거래 이력, 매출 분석, 비즈니스 인사이트를 제공합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "analysis_type": {
                                "type": "string",
                                "enum": ["profile", "transaction", "sales", "trend", "risk", "opportunity"],
                                "description": "분석 유형"
                            },
                            "client_id": {
                                "type": "string",
                                "description": "고객 ID (선택사항)"
                            },
                            "time_period": {
                                "type": "string",
                                "description": "분석 기간 (예: 2024-01 ~ 2024-12)"
                            },
                            "metrics": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "분석할 지표들"
                            }
                        },
                        "required": ["analysis_type"]
                    }
                }
            }
        ]
        
        logger.info("Router Agent 초기화 완료 - 4개 전문 Agent 등록")
    
    async def route_request(self, message: str, user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """
        사용자 요청을 분석하고 적절한 Agent로 라우팅
        """
        if not self.openai_client:
            return {
                "error": "Router Agent가 초기화되지 않았습니다.",
                "response": "시스템 오류가 발생했습니다. OpenAI API 키를 확인해주세요."
            }
        
        try:
            logger.info(f"Router Agent 요청 처리: {message[:50]}...")
            
            # 1. OpenAI Tool Calling으로 적절한 Agent 선택
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 NaruTalk AI 챗봇의 메인 라우터입니다. 
                        사용자의 요청을 분석하고 가장 적절한 전문 Agent를 선택해야 합니다.

                        Agent 선택 가이드:
                        1. db_agent: 문서 검색, 정책 문의, 지식베이스 질문답변, 벡터 검색
                        2. docs_agent: 문서 자동생성, 규정 위반 검색, 컴플라이언스 검토
                        3. employee_agent: 직원 정보 검색, 조직도, 연락처, 부서 정보
                        4. client_agent: 거래처 분석, 고객 데이터, 매출 분석, 비즈니스 인사이트

                        사용자의 질문을 분석하고 적절한 함수를 호출하세요.
                        질문의 의도를 정확히 파악하여 최적의 Agent를 선택하는 것이 중요합니다."""
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                tools=self.agent_functions,
                tool_choice="auto",
                temperature=0.1  # 일관된 라우팅을 위해 낮은 temperature 사용
            )
            
            # 2. Tool Call 결과 확인
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"Router Agent 선택: {function_name}")
                
                # 3. 선택된 Agent 실행
                result = await self._execute_agent(function_name, function_args, message)
                
                return {
                    "agent": function_name,
                    "arguments": function_args,
                    "response": result.get("response", ""),
                    "sources": result.get("sources", []),
                    "metadata": result.get("metadata", {}),
                    "user_id": user_id,
                    "session_id": session_id,
                    "routing_confidence": 1.0
                }
            
            else:
                # Tool Call이 없는 경우 일반 응답
                general_response = response.choices[0].message.content
                logger.info("Router Agent: 일반 응답 생성")
                
                return {
                    "agent": "general_chat",
                    "response": general_response,
                    "sources": [],
                    "metadata": {"type": "general_response"},
                    "user_id": user_id,
                    "session_id": session_id,
                    "routing_confidence": 0.5
                }
                
        except Exception as e:
            logger.error(f"Router Agent 처리 실패: {str(e)}")
            return {
                "error": str(e),
                "response": f"라우팅 처리 중 오류가 발생했습니다: {str(e)}",
                "agent": "error",
                "routing_confidence": 0.0
            }
    
    async def _execute_agent(self, agent_name: str, function_args: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """
        선택된 Agent 실행
        """
        try:
            logger.info(f"Agent 실행: {agent_name}")
            
            if agent_name == "db_agent":
                from ..agents.db_agent import DBAgent
                agent = DBAgent()
                return await agent.process(function_args, original_message)
                
            elif agent_name == "docs_agent":
                from ..agents.docs_agent import DocsAgent
                agent = DocsAgent()
                return await agent.process(function_args, original_message)
                
            elif agent_name == "employee_agent":
                from ..agents.employee_agent import EmployeeAgent
                agent = EmployeeAgent()
                return await agent.process(function_args, original_message)
                
            elif agent_name == "client_agent":
                from ..agents.client_agent import ClientAgent
                agent = ClientAgent()
                return await agent.process(function_args, original_message)
            
            else:
                return {
                    "response": f"알 수 없는 Agent: {agent_name}",
                    "sources": [],
                    "metadata": {"error": "unknown_agent"}
                }
                
        except ImportError as e:
            logger.warning(f"Agent {agent_name} 미구현: {str(e)}")
            return {
                "response": f"{agent_name}는 현재 구현 중입니다. 곧 서비스를 제공할 예정입니다.",
                "sources": [],
                "metadata": {"status": "under_development", "agent": agent_name}
            }
        except Exception as e:
            logger.error(f"Agent {agent_name} 실행 실패: {str(e)}")
            return {
                "response": f"Agent 실행 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "metadata": {"error": str(e), "agent": agent_name}
            }
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """사용 가능한 Agent 목록 반환"""
        return [
            {
                "name": "db_agent",
                "description": "내부 벡터 검색 Agent",
                "capabilities": ["문서 검색", "정책 검색", "지식베이스 QA", "벡터 검색"]
            },
            {
                "name": "docs_agent", 
                "description": "문서 자동생성 및 규정 위반 검색 Agent",
                "capabilities": ["문서 생성", "컴플라이언스 검토", "규정 위반 분석", "문서 템플릿"]
            },
            {
                "name": "employee_agent",
                "description": "내부 직원정보 검색 Agent", 
                "capabilities": ["직원 검색", "조직도", "연락처", "부서 정보"]
            },
            {
                "name": "client_agent",
                "description": "거래처 분석 Agent",
                "capabilities": ["고객 분석", "거래 이력", "매출 분석", "비즈니스 인사이트"]
            }
        ]
    
    def get_router_stats(self) -> Dict[str, Any]:
        """Router Agent 통계 정보"""
        return {
            "router_name": "RouterAgent",
            "openai_model": "gpt-4o",
            "total_agents": len(self.agent_functions),
            "available_agents": [func["function"]["name"] for func in self.agent_functions],
            "initialized": self.openai_client is not None
        } 