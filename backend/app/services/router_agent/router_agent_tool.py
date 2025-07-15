"""
Router Agent Tool Calling Module

OpenAI GPT-4o Tool Calling을 사용한 Agent 라우팅 기능
JSON 스키마 기반 에이전트 정의
"""

import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
from ...core.config import settings
from .schema_loader import AgentSchemaLoader

logger = logging.getLogger(__name__)

class RouterAgentTool:
    """Tool Calling 기반 라우팅 기능 (JSON 스키마 기반)"""
    
    def __init__(self):
        self.openai_client = None
        self.schema_loader = None
        
        # OpenAI 클라이언트 초기화
        self._initialize_openai_client()
        
        # JSON 스키마 로더 초기화
        self._initialize_schema_loader()
    
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
    
    def _initialize_schema_loader(self):
        """JSON 스키마 로더 초기화"""
        try:
            self.schema_loader = AgentSchemaLoader()
            logger.info("JSON 스키마 로더 초기화 완료")
        except Exception as e:
            logger.error(f"JSON 스키마 로더 초기화 실패: {str(e)}")
            self.schema_loader = None
    
    async def call_tool(self, message: str) -> Dict[str, Any]:
        """OpenAI Tool Calling 실행"""
        if not self.openai_client:
            return self._get_fallback_response(message, "OpenAI 클라이언트가 초기화되지 않았습니다.")
        
        try:
            logger.info(f"Tool Calling 실행: {message[:50]}...")
            
            # JSON 스키마에서 함수 정의와 설정 가져오기
            if not self.schema_loader:
                return self._get_fallback_response(message, "JSON 스키마 로더가 초기화되지 않았습니다.")
            
            function_definitions = self.schema_loader.get_function_definitions()
            system_prompt = self.schema_loader.get_system_prompt()
            settings_data = self.schema_loader.get_settings()
            
            if not function_definitions:
                return self._get_fallback_response(message, "함수 정의를 로드할 수 없습니다.")
            
            logger.info(f"Tool Calling 설정: 함수 {len(function_definitions)}개, 모델 {settings_data.get('model', 'gpt-4o')}")
            
            # OpenAI Tool Calling 요청
            response = self.openai_client.chat.completions.create(
                model=settings_data.get("model", "gpt-4o"),
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user", 
                        "content": message
                    }
                ],
                tools=function_definitions,
                tool_choice=settings_data.get("tool_choice", "auto"),
                temperature=settings_data.get("temperature", 0.1)
            )
            
            logger.info(f"OpenAI 응답 받음: {len(response.choices)} choices")
            
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
            return self._get_fallback_response(message, f"Tool Calling 오류: {str(e)}")
    
    def _get_fallback_response(self, message: str, error_msg: str) -> Dict[str, Any]:
        """Fallback 응답 생성 - 키워드 기반 라우팅"""
        logger.warning(f"Fallback 라우팅 사용: {error_msg}")
        
        # 간단한 키워드 기반 라우팅
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ["직원", "인사", "연락처", "조직", "부서"]):
            return {
                "tool_call": {
                    "function_name": "employee_agent",
                    "function_args": {"search_type": "name", "search_value": message},
                    "confidence": 0.7
                },
                "general_response": None
            }
        elif any(keyword in message_lower for keyword in ["문서", "정책", "규정", "검색", "찾기"]):
            return {
                "tool_call": {
                    "function_name": "db_agent", 
                    "function_args": {"query": message, "search_type": "semantic"},
                    "confidence": 0.7
                },
                "general_response": None
            }
        elif any(keyword in message_lower for keyword in ["거래처", "고객", "분석", "매출", "비즈니스"]):
            return {
                "tool_call": {
                    "function_name": "client_agent",
                    "function_args": {"analysis_type": "profile"},
                    "confidence": 0.7
                },
                "general_response": None
            }
        elif any(keyword in message_lower for keyword in ["컴플라이언스", "위반", "규정", "생성", "문서생성"]):
            return {
                "tool_call": {
                    "function_name": "docs_agent",
                    "function_args": {"task_type": "compliance_check", "content": message},
                    "confidence": 0.7
                },
                "general_response": None
            }
        else:
            # 일반 대화
            return {
                "tool_call": None,
                "general_response": f"'{message}'에 대한 질문을 처리하기 위해서는 더 구체적인 정보가 필요합니다. 직원 정보, 문서 검색, 거래처 분석, 컴플라이언스 검토 중 어떤 도움이 필요하신지 알려주세요.",
                "confidence": 0.3
            }
    
    def get_agent_functions(self) -> List[Dict[str, Any]]:
        """Agent 함수 목록 반환 (JSON 스키마 기반)"""
        if self.schema_loader:
            return self.schema_loader.get_function_definitions()
        return []
    
    def is_initialized(self) -> bool:
        """초기화 상태 확인"""
        return self.openai_client is not None
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """Tool Calling 통계 정보 (JSON 스키마 기반)"""
        if not self.schema_loader:
            return {
                "tool_name": "RouterAgentTool",
                "total_functions": 0,
                "available_functions": [],
                "initialized": False,
                "error": "JSON 스키마 로더가 초기화되지 않음"
            }
        
        schema_stats = self.schema_loader.get_schema_stats()
        function_definitions = self.schema_loader.get_function_definitions()
        
        return {
            "tool_name": "RouterAgentTool (JSON Schema)",
            "total_functions": schema_stats["total_functions"],
            "available_functions": [func["function"]["name"] for func in function_definitions],
            "initialized": self.is_initialized() and self.schema_loader is not None,
            "openai_model": self.schema_loader.get_settings().get("model", "gpt-4o"),
            "schema_loaded": schema_stats["schema_loaded"],
            "schema_path": schema_stats["schema_path"]
        } 