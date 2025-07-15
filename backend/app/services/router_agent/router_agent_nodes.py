"""
Router Agent Nodes Module

Agent 노드 정의 및 실행 관리
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class RouterAgentNodes:
    """Agent 노드 관리 및 실행"""
    
    def __init__(self):
        self.agent_instances = {}
        self.agent_status = {}
        
        # Agent 노드 정의
        self.agent_definitions = {
            "db_agent": {
                "name": "DB Agent",
                "description": "내부 벡터 검색 Agent",
                "module_path": "..agents.db_agent",
                "class_name": "DBAgent",
                "capabilities": ["문서 검색", "정책 검색", "지식베이스 QA", "벡터 검색"]
            },
            "docs_agent": {
                "name": "Docs Agent",
                "description": "문서 자동생성 및 규정 위반 검색 Agent",
                "module_path": "..agents.docs_agent",
                "class_name": "DocsAgent",
                "capabilities": ["문서 생성", "컴플라이언스 검토", "규정 위반 분석", "문서 템플릿"]
            },
            "employee_agent": {
                "name": "Employee Agent",
                "description": "내부 직원정보 검색 Agent",
                "module_path": "..agents.employee_agent",
                "class_name": "EmployeeAgent",
                "capabilities": ["직원 검색", "조직도", "연락처", "부서 정보"]
            },
            "client_agent": {
                "name": "Client Agent",
                "description": "거래처 분석 Agent",
                "module_path": "..agents.client_agent",
                "class_name": "ClientAgent",
                "capabilities": ["고객 분석", "거래 이력", "매출 분석", "비즈니스 인사이트"]
            }
        }
        
        logger.info("Router Agent Nodes 초기화 완료")
    
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
        """직접 Agent 실행 (폴백용)"""
        try:
            logger.info(f"Agent 직접 실행: {agent_name}")
            
            # 기본 인수 설정
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
            
            # Agent 정의 확인
            if agent_name not in self.agent_definitions:
                logger.error(f"알 수 없는 Agent: {agent_name}")
                return None
            
            agent_def = self.agent_definitions[agent_name]
            
            # 동적 import 및 인스턴스 생성
            if agent_name == "db_agent":
                from ..agents.db_agent import DBAgent
                agent_instance = DBAgent()
                
            elif agent_name == "docs_agent":
                from ..agents.docs_agent import DocsAgent
                agent_instance = DocsAgent()
                
            elif agent_name == "employee_agent":
                from ..agents.employee_agent import EmployeeAgent
                agent_instance = EmployeeAgent()
                
            elif agent_name == "client_agent":
                from ..agents.client_agent import ClientAgent
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
        """특정 Agent 정보 조회"""
        if agent_name not in self.agent_definitions:
            return {"error": f"알 수 없는 Agent: {agent_name}"}
        
        agent_def = self.agent_definitions[agent_name]
        status = self.agent_status.get(agent_name, {})
        
        return {
            "name": agent_def["name"],
            "description": agent_def["description"],
            "capabilities": agent_def["capabilities"],
            "status": status,
            "initialized": agent_name in self.agent_instances
        }
    
    def get_all_agents_info(self) -> List[Dict[str, Any]]:
        """모든 Agent 정보 조회"""
        agents_info = []
        
        for agent_name in self.agent_definitions:
            agent_info = self.get_agent_info(agent_name)
            agents_info.append(agent_info)
        
        return agents_info
    
    def get_node_stats(self) -> Dict[str, Any]:
        """노드 통계 정보"""
        total_agents = len(self.agent_definitions)
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
            "node_name": "RouterAgentNodes",
            "total_agents": total_agents,
            "initialized_agents": initialized_agents,
            "initialization_rate": initialized_agents / total_agents if total_agents > 0 else 0,
            "execution_stats": execution_stats,
            "status": "active"
        }
    
    def validate_agent(self, agent_name: str) -> Dict[str, Any]:
        """Agent 유효성 검증"""
        try:
            if agent_name not in self.agent_definitions:
                return {"valid": False, "error": f"알 수 없는 Agent: {agent_name}"}
            
            agent_def = self.agent_definitions[agent_name]
            
            # 기본 검증
            if not agent_def.get("name"):
                return {"valid": False, "error": "Agent 이름이 정의되지 않았습니다."}
            
            if not agent_def.get("module_path"):
                return {"valid": False, "error": "Agent 모듈 경로가 정의되지 않았습니다."}
            
            if not agent_def.get("class_name"):
                return {"valid": False, "error": "Agent 클래스 이름이 정의되지 않았습니다."}
            
            # 인스턴스 생성 가능성 검증
            try:
                # 동적 import 테스트
                if agent_name == "db_agent":
                    from ..agents.db_agent import DBAgent
                elif agent_name == "docs_agent":
                    from ..agents.docs_agent import DocsAgent
                elif agent_name == "employee_agent":
                    from ..agents.employee_agent import EmployeeAgent
                elif agent_name == "client_agent":
                    from ..agents.client_agent import ClientAgent
                
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
        """Agent 상태 정보"""
        health_status = {}
        
        for agent_name in self.agent_definitions:
            status = self.agent_status.get(agent_name, {})
            health_status[agent_name] = {
                "initialized": agent_name in self.agent_instances,
                "execution_count": status.get("execution_count", 0),
                "last_execution": status.get("last_execution", "never"),
                "status": "healthy" if agent_name in self.agent_instances else "not_initialized"
            }
        
        return {
            "total_agents": len(self.agent_definitions),
            "healthy_agents": len([s for s in health_status.values() if s["status"] == "healthy"]),
            "agent_status": health_status
        } 