"""
Router Agent Tool Calling Module

OpenAI GPT-4o Tool Calling을 사용한 Agent 라우팅 기능
"""

import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
from ...core.config import settings

logger = logging.getLogger(__name__)

class RouterAgentTool:
    """Tool Calling 기반 라우팅 기능"""
    
    def __init__(self):
        self.openai_client = None
        self.agent_functions = []
        
        # OpenAI 클라이언트 초기화
        self._initialize_openai_client()
        
        # Agent 함수 정의
        self._define_agent_functions()
    
    def _initialize_openai_client(self):
        """OpenAI 클라이언트 초기화"""
        api_key = settings.openai_api_key
        logger.info(f"🔍 Router Agent Tool 초기화 - API 키: {api_key[:10] if api_key else 'None'}...")
        
        if not api_key:
            logger.error("OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
            return
            
        try:
            self.openai_client = OpenAI(api_key=api_key)
            logger.info("Router Agent Tool OpenAI 클라이언트 초기화 성공")
        except Exception as e:
            logger.error(f"Router Agent Tool OpenAI 클라이언트 초기화 실패: {str(e)}")
    
    def _define_agent_functions(self):
        """4개의 전문 Agent 함수 정의"""
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
        
        logger.info("Router Agent Tool 함수 정의 완료 - 4개 전문 Agent 등록")
    
    async def call_tool(self, message: str) -> Dict[str, Any]:
        """OpenAI Tool Calling 실행"""
        if not self.openai_client:
            return {
                "error": "OpenAI 클라이언트가 초기화되지 않았습니다.",
                "tool_call": None,
                "general_response": None
            }
        
        try:
            logger.info(f"Tool Calling 실행: {message[:50]}...")
            
            # OpenAI Tool Calling 요청
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
            
            # Tool Call 결과 확인
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"Tool Call 선택: {function_name}")
                
                return {
                    "tool_call": {
                        "function_name": function_name,
                        "function_args": function_args,
                        "confidence": 1.0
                    },
                    "general_response": None
                }
            
            else:
                # Tool Call이 없는 경우 일반 응답
                general_response = response.choices[0].message.content
                logger.info("Tool Call: 일반 응답 생성")
                
                return {
                    "tool_call": None,
                    "general_response": general_response,
                    "confidence": 0.5
                }
                
        except Exception as e:
            logger.error(f"Tool Calling 실패: {str(e)}")
            return {
                "error": str(e),
                "tool_call": None,
                "general_response": None
            }
    
    def get_agent_functions(self) -> List[Dict[str, Any]]:
        """Agent 함수 목록 반환"""
        return self.agent_functions
    
    def is_initialized(self) -> bool:
        """초기화 상태 확인"""
        return self.openai_client is not None
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """Tool Calling 통계 정보"""
        return {
            "tool_name": "RouterAgentTool",
            "openai_model": "gpt-4o",
            "total_functions": len(self.agent_functions),
            "available_functions": [func["function"]["name"] for func in self.agent_functions],
            "initialized": self.is_initialized()
        } 