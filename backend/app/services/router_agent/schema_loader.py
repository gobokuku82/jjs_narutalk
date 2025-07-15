"""
Agent Schema Loader

JSON 스키마 기반 에이전트 정의 로더
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from ...core.config import settings

logger = logging.getLogger(__name__)

class AgentSchemaLoader:
    """JSON 스키마 기반 에이전트 정의 로더"""
    
    def __init__(self, schema_path: str = None):
        """
        Agent Schema Loader 초기화
        
        Args:
            schema_path: JSON 스키마 파일 경로 (기본값: agent_schemas.json)
        """
        self.schema_path = schema_path or "agent_schemas.json"
        self.schema_data = None
        self.agents = {}
        self.function_definitions = []
        
        # 스키마 로드
        self._load_schema()
    
    def _load_schema(self):
        """JSON 스키마 파일 로드"""
        try:
            # 현재 파일 기준 상대 경로로 스키마 파일 찾기
            current_dir = Path(__file__).parent
            schema_file = current_dir / self.schema_path
            
            if not schema_file.exists():
                logger.error(f"스키마 파일을 찾을 수 없습니다: {schema_file}")
                return
            
            with open(schema_file, 'r', encoding='utf-8') as f:
                self.schema_data = json.load(f)
            
            # 에이전트 정보 추출
            self.agents = self.schema_data.get("agents", {})
            
            # 함수 정의 추출
            self.function_definitions = []
            for agent_name, agent_config in self.agents.items():
                if "function_definition" in agent_config:
                    self.function_definitions.append(agent_config["function_definition"])
            
            logger.info(f"Agent 스키마 로드 완료: {len(self.agents)}개 에이전트, {len(self.function_definitions)}개 함수")
            
        except Exception as e:
            logger.error(f"스키마 로드 실패: {str(e)}")
            self.schema_data = {}
            self.agents = {}
            self.function_definitions = []
    
    def get_agent_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """특정 에이전트 설정 조회"""
        return self.agents.get(agent_name)
    
    def get_all_agents(self) -> Dict[str, Any]:
        """모든 에이전트 설정 조회"""
        return self.agents
    
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """모든 함수 정의 조회"""
        return self.function_definitions
    
    def get_agent_function_definition(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """특정 에이전트의 함수 정의 조회"""
        agent_config = self.get_agent_config(agent_name)
        if agent_config and "function_definition" in agent_config:
            return agent_config["function_definition"]
        return None
    
    def get_agent_default_args(self, agent_name: str) -> Dict[str, Any]:
        """특정 에이전트의 기본 인수 조회"""
        agent_config = self.get_agent_config(agent_name)
        if agent_config and "default_args" in agent_config:
            return agent_config["default_args"]
        return {}
    
    def get_system_prompt(self) -> str:
        """시스템 프롬프트 조회"""
        return self.schema_data.get("system_prompt", "")
    
    def get_settings(self) -> Dict[str, Any]:
        """설정 조회"""
        return self.schema_data.get("settings", {})
    
    def validate_agent(self, agent_name: str) -> Dict[str, Any]:
        """에이전트 설정 유효성 검증"""
        try:
            if agent_name not in self.agents:
                return {"valid": False, "error": f"알 수 없는 에이전트: {agent_name}"}
            
            agent_config = self.agents[agent_name]
            
            # 필수 필드 검증
            required_fields = ["name", "description", "module_path", "class_name", "capabilities"]
            for field in required_fields:
                if field not in agent_config:
                    return {"valid": False, "error": f"필수 필드 누락: {field}"}
            
            # 함수 정의 검증
            if "function_definition" not in agent_config:
                return {"valid": False, "error": "함수 정의가 없습니다."}
            
            function_def = agent_config["function_definition"]
            if "function" not in function_def:
                return {"valid": False, "error": "함수 정의가 올바르지 않습니다."}
            
            return {"valid": True, "message": f"에이전트 {agent_name} 검증 완료"}
            
        except Exception as e:
            return {"valid": False, "error": f"검증 중 오류: {str(e)}"}
    
    def get_agent_info(self, agent_name: str) -> Dict[str, Any]:
        """에이전트 정보 조회"""
        agent_config = self.get_agent_config(agent_name)
        if not agent_config:
            return {"error": f"알 수 없는 에이전트: {agent_name}"}
        
        return {
            "name": agent_config.get("name", ""),
            "description": agent_config.get("description", ""),
            "capabilities": agent_config.get("capabilities", []),
            "module_path": agent_config.get("module_path", ""),
            "class_name": agent_config.get("class_name", ""),
            "has_function_definition": "function_definition" in agent_config,
            "has_default_args": "default_args" in agent_config
        }
    
    def get_all_agents_info(self) -> List[Dict[str, Any]]:
        """모든 에이전트 정보 조회"""
        agents_info = []
        
        for agent_name in self.agents:
            agent_info = self.get_agent_info(agent_name)
            agent_info["agent_name"] = agent_name
            agents_info.append(agent_info)
        
        return agents_info
    
    def reload_schema(self):
        """스키마 재로드"""
        logger.info("스키마 재로드 중...")
        self._load_schema()
    
    def get_schema_stats(self) -> Dict[str, Any]:
        """스키마 통계 정보"""
        return {
            "total_agents": len(self.agents),
            "total_functions": len(self.function_definitions),
            "schema_loaded": self.schema_data is not None,
            "schema_path": str(Path(__file__).parent / self.schema_path)
        } 