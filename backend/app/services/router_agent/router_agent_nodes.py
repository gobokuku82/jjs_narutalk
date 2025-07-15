"""
Router Agent Nodes Module

Agent 노드 정의 및 실행 관리 (JSON 스키마 기반)
"""

import logging
from typing import Dict, List, Any, Optional
from .schema_loader import AgentSchemaLoader

logger = logging.getLogger(__name__)

class RouterAgentNodes:
    """Agent 노드 관리 및 실행 (JSON 스키마 기반)"""
    
    def __init__(self):
        self.agent_instances = {}
        self.agent_status = {}
        self.schema_loader = None
        
        # JSON 스키마 로더 초기화
        self._initialize_schema_loader()
        
        logger.info("Router Agent Nodes 초기화 완료")
    
    def _initialize_schema_loader(self):
        """JSON 스키마 로더 초기화"""
        try:
            self.schema_loader = AgentSchemaLoader()
            logger.info("JSON 스키마 로더 초기화 완료")
        except Exception as e:
            logger.error(f"JSON 스키마 로더 초기화 실패: {str(e)}")
            self.schema_loader = None
    
    async def execute_agent(self, agent_name: str, function_args: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """
        선택된 Agent 실행
        """
        try:
            logger.info(f"Agent 노드 실행: {agent_name}")
            
            # Agent 인스턴스 가져오기 또는 생성
            agent_instance = await self._get_agent_instance(agent_name)
            
            if not agent_instance:
                return {
                    "response": f"Agent {agent_name}를 초기화할 수 없습니다.",
                    "sources": [],
                    "metadata": {"error": "agent_initialization_failed", "agent": agent_name}
                }
            
            # Agent 실행
            result = await agent_instance.process(function_args, original_message)
            
            # 실행 상태 업데이트
            self.agent_status[agent_name] = {
                "last_execution": "success",
                "execution_count": self.agent_status.get(agent_name, {}).get("execution_count", 0) + 1
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Agent {agent_name} 실행 실패: {str(e)}")
            
            # 실행 상태 업데이트
            self.agent_status[agent_name] = {
                "last_execution": "failed",
                "error": str(e),
                "execution_count": self.agent_status.get(agent_name, {}).get("execution_count", 0) + 1
            }
            
            return {
                "response": f"Agent 실행 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "metadata": {"error": str(e), "agent": agent_name}
            }
    
    async def execute_agent_direct(self, agent_name: str, args: Dict[str, Any], message: str) -> Dict[str, Any]:
        """직접 Agent 실행 (폴백용) - JSON 스키마 기반"""
        try:
            logger.info(f"Agent 직접 실행: {agent_name}")
            
            # JSON 스키마에서 기본 인수 가져오기
            if self.schema_loader:
                default_args = self.schema_loader.get_agent_default_args(agent_name)
                # 기본 인수와 메시지 결합
                if agent_name == "db_agent":
                    args = {**default_args, "query": message}
                elif agent_name == "docs_agent":
                    args = {**default_args, "content": message}
                elif agent_name == "employee_agent":
                    args = {**default_args, "search_value": message}
                elif agent_name == "client_agent":
                    args = {**default_args}
            else:
                # 폴백: 하드코딩된 기본값
                if agent_name == "db_agent":
                    args = {"query": message, "search_type": "semantic", "document_type": "general"}
                elif agent_name == "docs_agent":
                    args = {"task_type": "generate_document", "content": message}
                elif agent_name == "employee_agent":
                    args = {"search_type": "name", "search_value": message}
                elif agent_name == "client_agent":
                    args = {"analysis_type": "profile"}
            
            return await self.execute_agent(agent_name, args, message)
            
        except Exception as e:
            logger.error(f"Agent 직접 실행 실패: {str(e)}")
            return {
                "response": f"Agent 직접 실행 중 오류: {str(e)}",
                "sources": [],
                "metadata": {"error": str(e), "agent": agent_name}
            }
    
    async def _get_agent_instance(self, agent_name: str):
        """Agent 인스턴스 가져오기 또는 생성"""
        try:
            # 이미 생성된 인스턴스가 있으면 반환
            if agent_name in self.agent_instances:
                return self.agent_instances[agent_name]
            
            # JSON 스키마에서 Agent 정의 확인
            if not self.schema_loader:
                logger.error("JSON 스키마 로더가 초기화되지 않았습니다.")
                return None
            
            agent_config = self.schema_loader.get_agent_config(agent_name)
            if not agent_config:
                logger.error(f"알 수 없는 Agent: {agent_name}")
                return None
            
            # 동적 import 및 인스턴스 생성
            if agent_name == "db_agent":
                from ..agents.db_agent.db_agent import DBAgent
                agent_instance = DBAgent()
                
            elif agent_name == "docs_agent":
                from ..agents.docs_agent.docs_agent import DocsAgent
                agent_instance = DocsAgent()
                
            elif agent_name == "employee_agent":
                from ..agents.employee_agent.employee_agent import EmployeeAgent
                agent_instance = EmployeeAgent()
                
            elif agent_name == "client_agent":
                from ..agents.client_agent.client_agent import ClientAgent
                agent_instance = ClientAgent()
            
            else:
                logger.error(f"지원하지 않는 Agent: {agent_name}")
                return None
            
            # 인스턴스 캐시에 저장
            self.agent_instances[agent_name] = agent_instance
            
            # 상태 초기화
            self.agent_status[agent_name] = {
                "initialized": True,
                "execution_count": 0,
                "last_execution": None
            }
            
            logger.info(f"Agent 인스턴스 생성 완료: {agent_name}")
            return agent_instance
            
        except ImportError as e:
            logger.warning(f"Agent {agent_name} 미구현: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Agent 인스턴스 생성 실패: {str(e)}")
            return None
    
    def get_agent_info(self, agent_name: str) -> Dict[str, Any]:
        """특정 Agent 정보 조회 (JSON 스키마 기반)"""
        if not self.schema_loader:
            return {"error": "JSON 스키마 로더가 초기화되지 않았습니다."}
        
        agent_info = self.schema_loader.get_agent_info(agent_name)
        if "error" in agent_info:
            return agent_info
        
        status = self.agent_status.get(agent_name, {})
        
        return {
            **agent_info,
            "status": status,
            "initialized": agent_name in self.agent_instances
        }
    
    def get_all_agents_info(self) -> List[Dict[str, Any]]:
        """모든 Agent 정보 조회 (JSON 스키마 기반)"""
        if not self.schema_loader:
            return [{"error": "JSON 스키마 로더가 초기화되지 않았습니다."}]
        
        return self.schema_loader.get_all_agents_info()
    
    def get_node_stats(self) -> Dict[str, Any]:
        """노드 통계 정보 (JSON 스키마 기반)"""
        if not self.schema_loader:
            return {
                "node_name": "RouterAgentNodes",
                "total_agents": 0,
                "initialized_agents": 0,
                "initialization_rate": 0,
                "execution_stats": {},
                "status": "error",
                "error": "JSON 스키마 로더가 초기화되지 않음"
            }
        
        schema_stats = self.schema_loader.get_schema_stats()
        total_agents = schema_stats["total_agents"]
        initialized_agents = len(self.agent_instances)
        
        # 실행 통계
        execution_stats = {}
        for agent_name, status in self.agent_status.items():
            execution_stats[agent_name] = {
                "execution_count": status.get("execution_count", 0),
                "last_execution": status.get("last_execution", "never"),
                "initialized": agent_name in self.agent_instances
            }
        
        return {
            "node_name": "RouterAgentNodes (JSON Schema)",
            "total_agents": total_agents,
            "initialized_agents": initialized_agents,
            "initialization_rate": initialized_agents / total_agents if total_agents > 0 else 0,
            "execution_stats": execution_stats,
            "status": "active",
            "schema_loaded": schema_stats["schema_loaded"]
        }
    
    def validate_agent(self, agent_name: str) -> Dict[str, Any]:
        """Agent 유효성 검증 (JSON 스키마 기반)"""
        try:
            if not self.schema_loader:
                return {"valid": False, "error": "JSON 스키마 로더가 초기화되지 않았습니다."}
            
            # JSON 스키마 기반 검증
            validation_result = self.schema_loader.validate_agent(agent_name)
            if not validation_result["valid"]:
                return validation_result
            
            # 인스턴스 생성 가능성 검증
            try:
                # 동적 import 테스트
                if agent_name == "db_agent":
                    from ..agents.db_agent.db_agent import DBAgent
                elif agent_name == "docs_agent":
                    from ..agents.docs_agent.docs_agent import DocsAgent
                elif agent_name == "employee_agent":
                    from ..agents.employee_agent.employee_agent import EmployeeAgent
                elif agent_name == "client_agent":
                    from ..agents.client_agent.client_agent import ClientAgent
                
                return {"valid": True, "message": f"Agent {agent_name} 검증 완료"}
                
            except ImportError as e:
                return {"valid": False, "error": f"Agent 모듈 import 실패: {str(e)}"}
            
        except Exception as e:
            return {"valid": False, "error": f"검증 중 오류: {str(e)}"}
    
    def clear_agent_cache(self, agent_name: str = None):
        """Agent 캐시 정리"""
        if agent_name:
            if agent_name in self.agent_instances:
                del self.agent_instances[agent_name]
                logger.info(f"Agent 캐시 정리: {agent_name}")
        else:
            self.agent_instances.clear()
            logger.info("모든 Agent 캐시 정리")
    
    def get_agent_health(self) -> Dict[str, Any]:
        """Agent 상태 정보 (JSON 스키마 기반)"""
        if not self.schema_loader:
            return {
                "total_agents": 0,
                "healthy_agents": 0,
                "agent_status": {},
                "error": "JSON 스키마 로더가 초기화되지 않음"
            }
        
        schema_stats = self.schema_loader.get_schema_stats()
        health_status = {}
        
        for agent_name in self.schema_loader.get_all_agents():
            status = self.agent_status.get(agent_name, {})
            health_status[agent_name] = {
                "initialized": agent_name in self.agent_instances,
                "execution_count": status.get("execution_count", 0),
                "last_execution": status.get("last_execution", "never"),
                "status": "healthy" if agent_name in self.agent_instances else "not_initialized"
            }
        
        return {
            "total_agents": schema_stats["total_agents"],
            "healthy_agents": len([s for s in health_status.values() if s["status"] == "healthy"]),
            "agent_status": health_status,
            "schema_loaded": schema_stats["schema_loaded"]
        } 