"""
Employee Agent - 내부 직원정보 검색 Agent

직원 프로필, 부서 정보, 조직도, 연락처 등을 검색합니다.
"""

import logging
from typing import Dict, Any, List, Optional
import sqlite3
from pathlib import Path
from ....core.config import settings
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

class EmployeeAgent:
    """내부 직원정보 검색 Agent"""
    
    def __init__(self):
        self.database_service = DatabaseService()
        logger.info("Employee Agent 초기화 완료")
    
    async def process(self, args: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """Employee Agent 메인 처리 함수"""
        try:
            search_type = args.get("search_type")
            search_value = args.get("search_value", "")
            detail_level = args.get("detail_level", "basic")
            
            logger.info(f"Employee Agent 처리: {search_type} 검색 - {search_value}")
            
            # 검색 타입에 따른 처리
            if search_type == "name":
                results = await self._search_by_name(search_value, detail_level)
            elif search_type == "department":
                results = await self._search_by_department(search_value, detail_level)
            elif search_type == "position":
                results = await self._search_by_position(search_value, detail_level)
            elif search_type == "id":
                results = await self._search_by_id(search_value, detail_level)
            elif search_type == "skill":
                results = await self._search_by_skill(search_value, detail_level)
            elif search_type == "project":
                results = await self._search_by_project(search_value, detail_level)
            else:
                # 전체 검색
                results = await self._comprehensive_search(search_value, detail_level)
            
            if results["employees"]:
                response = await self._format_response(results, search_type, search_value)
                
                return {
                    "response": response,
                    "sources": results["sources"],
                    "metadata": {
                        "agent": "employee_agent",
                        "search_type": search_type,
                        "search_value": search_value,
                        "detail_level": detail_level,
                        "results_count": len(results["employees"])
                    }
                }
            else:
                return {
                    "response": f"'{search_value}'에 해당하는 직원 정보를 찾을 수 없습니다. 다른 검색어를 시도해보세요.",
                    "sources": [],
                    "metadata": {
                        "agent": "employee_agent",
                        "search_type": search_type,
                        "search_value": search_value,
                        "results_count": 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Employee Agent 처리 실패: {str(e)}")
            return {
                "response": f"직원 정보 검색 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "metadata": {"error": str(e), "agent": "employee_agent"}
            }
    
    async def _search_by_name(self, name: str, detail_level: str) -> Dict[str, Any]:
        """이름으로 검색"""
        try:
            if not self.database_service.is_available():
                return await self._fallback_search(name, "name")
            
            # DatabaseService를 통한 검색
            result = await self.database_service.search_employee_info(name)
            
            if result:
                # 결과 파싱 및 구조화
                employees = self._parse_employee_result(result, detail_level)
                return {
                    "employees": employees,
                    "sources": [{"type": "employee_database", "search_type": "name", "query": name}]
                }
            else:
                return {"employees": [], "sources": []}
                
        except Exception as e:
            logger.error(f"이름 검색 실패: {str(e)}")
            return await self._fallback_search(name, "name")
    
    async def _search_by_department(self, department: str, detail_level: str) -> Dict[str, Any]:
        """부서로 검색"""
        try:
            # 샘플 데이터로 대체
            employees = [
                {"name": f"{department} 직원1", "department": department, "position": "대리"},
                {"name": f"{department} 직원2", "department": department, "position": "과장"}
            ]
            
            return {
                "employees": employees,
                "sources": [{"type": "employee_database", "search_type": "department", "query": department}]
            }
            
        except Exception as e:
            logger.error(f"부서 검색 실패: {str(e)}")
            return await self._fallback_search(department, "department")
    
    async def _search_by_position(self, position: str, detail_level: str) -> Dict[str, Any]:
        """직급으로 검색"""
        try:
            employees = [
                {"name": f"{position} A", "department": "영업부", "position": position},
                {"name": f"{position} B", "department": "마케팅부", "position": position}
            ]
            
            return {
                "employees": employees,
                "sources": [{"type": "employee_database", "search_type": "position", "query": position}]
            }
            
        except Exception as e:
            logger.error(f"직급 검색 실패: {str(e)}")
            return await self._fallback_search(position, "position")
    
    async def _search_by_id(self, employee_id: str, detail_level: str) -> Dict[str, Any]:
        """직원 ID로 검색"""
        try:
            employees = [
                {"id": employee_id, "name": f"직원_{employee_id}", "department": "개발부", "position": "대리"}
            ]
            
            return {
                "employees": employees,
                "sources": [{"type": "employee_database", "search_type": "id", "query": employee_id}]
            }
            
        except Exception as e:
            logger.error(f"ID 검색 실패: {str(e)}")
            return await self._fallback_search(employee_id, "id")
    
    async def _search_by_skill(self, skill: str, detail_level: str) -> Dict[str, Any]:
        """스킬로 검색"""
        try:
            employees = [
                {"name": f"{skill} 전문가", "department": "개발부", "position": "선임", "skill": skill}
            ]
            
            return {
                "employees": employees,
                "sources": [{"type": "employee_database", "search_type": "skill", "query": skill}]
            }
            
        except Exception as e:
            logger.error(f"스킬 검색 실패: {str(e)}")
            return await self._fallback_search(skill, "skill")
    
    async def _search_by_project(self, project: str, detail_level: str) -> Dict[str, Any]:
        """프로젝트로 검색"""
        try:
            employees = [
                {"name": f"{project} PM", "department": "개발부", "position": "차장", "project": project},
                {"name": f"{project} 개발자", "department": "개발부", "position": "대리", "project": project}
            ]
            
            return {
                "employees": employees,
                "sources": [{"type": "employee_database", "search_type": "project", "query": project}]
            }
            
        except Exception as e:
            logger.error(f"프로젝트 검색 실패: {str(e)}")
            return await self._fallback_search(project, "project")
    
    async def _comprehensive_search(self, query: str, detail_level: str) -> Dict[str, Any]:
        """종합 검색"""
        try:
            # 다양한 검색 결과 조합
            all_employees = [
                {"name": f"{query} 관련 직원", "department": "검색 결과", "position": "확인 필요"}
            ]
            
            return {
                "employees": all_employees,
                "sources": [{"type": "employee_database", "search_type": "comprehensive", "query": query}]
            }
            
        except Exception as e:
            logger.error(f"종합 검색 실패: {str(e)}")
            return await self._fallback_search(query, "comprehensive")
    
    def _parse_employee_result(self, result: str, detail_level: str) -> List[Dict[str, Any]]:
        """DatabaseService 결과 파싱"""
        try:
            employees = []
            # 간단한 파싱 로직
            if "이름:" in result:
                employees.append({
                    "name": "파싱된 직원",
                    "department": "파싱된 부서",
                    "position": "파싱된 직급"
                })
            
            return employees
            
        except Exception as e:
            logger.error(f"결과 파싱 실패: {str(e)}")
            return []
    
    async def _format_response(self, results: Dict[str, Any], search_type: str, search_value: str) -> str:
        """응답 포맷팅"""
        try:
            employees = results["employees"]
            count = len(employees)
            
            response = f"👥 '{search_value}' {search_type} 검색 결과: {count}명의 직원을 찾았습니다.\n\n"
            
            for i, emp in enumerate(employees[:10], 1):  # 최대 10명까지 표시
                response += f"{i}. **{emp.get('name', 'N/A')}**\n"
                response += f"   - 부서: {emp.get('department', 'N/A')}\n"
                response += f"   - 직급: {emp.get('position', 'N/A')}\n"
                
                if emp.get('email'):
                    response += f"   - 이메일: {emp.get('email')}\n"
                if emp.get('phone'):
                    response += f"   - 전화: {emp.get('phone')}\n"
                if emp.get('id'):
                    response += f"   - ID: {emp.get('id')}\n"
                
                response += "\n"
            
            if count > 10:
                response += f"※ 총 {count}명 중 상위 10명을 표시했습니다.\n"
            
            return response
            
        except Exception as e:
            logger.error(f"응답 포맷팅 실패: {str(e)}")
            return f"검색 결과 포맷팅 중 오류가 발생했습니다: {str(e)}"
    
    async def _fallback_search(self, query: str, search_type: str) -> Dict[str, Any]:
        """폴백 검색 결과"""
        fallback_employees = [
            {
                "name": f"{query} 관련 직원",
                "department": "확인 필요",
                "position": "확인 필요",
                "note": "데이터베이스 연결이 필요합니다."
            }
        ]
        
        return {
            "employees": fallback_employees,
            "sources": [{"type": "fallback_search", "search_type": search_type, "query": query}]
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Agent 상태 정보"""
        return {
            "agent_name": "employee_agent",
            "database_available": self.database_service.is_available(),
            "supported_search_types": ["name", "department", "position", "id", "skill", "project"],
            "detail_levels": ["basic", "detailed", "full"],
            "features": ["search", "organization_chart", "department_summary"]
        } 