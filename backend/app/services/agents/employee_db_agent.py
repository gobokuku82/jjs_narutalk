"""
Employee DB Agent
SQLite database/relationdb/employees.db에서 직원 정보를 검색하는 Agent
"""

import logging
import sqlite3
from typing import Dict, List, Any, Optional
from ..database_service import DatabaseService
from openai import OpenAI
from ...core.config import settings

logger = logging.getLogger(__name__)

class EmployeeDBAgent:
    """직원 데이터베이스 검색 Agent"""
    
    def __init__(self):
        self.database_service = DatabaseService()
        self.openai_client = None
        try:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
        
        logger.info("Employee DB Agent 초기화 완료")
    
    async def process(self, function_args: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """
        직원 정보 검색 처리
        
        Args:
            function_args: OpenAI function calling에서 전달된 인자
            original_message: 원본 사용자 메시지
            
        Returns:
            처리 결과 딕셔너리
        """
        try:
            search_type = function_args.get("search_type", "name")
            search_value = function_args.get("search_value", "")
            
            logger.info(f"직원 정보 검색 시작: {search_type}={search_value}")
            
            # 1. 직원 정보 검색
            employee_data = await self._search_employees(search_type, search_value)
            
            # 2. 검색 결과가 있으면 OpenAI로 응답 생성
            if employee_data:
                response = await self._generate_employee_response(employee_data, original_message, search_type, search_value)
                
                return {
                    "response": response,
                    "sources": employee_data,
                    "metadata": {
                        "agent": "employee_db_agent",
                        "search_type": search_type,
                        "search_value": search_value,
                        "employees_found": len(employee_data)
                    }
                }
            else:
                return {
                    "response": f"{search_type}이(가) '{search_value}'인 직원을 찾을 수 없습니다. 정확한 {self._get_search_type_korean(search_type)}을(를) 입력해주세요.",
                    "sources": [],
                    "metadata": {
                        "agent": "employee_db_agent",
                        "search_type": search_type,
                        "search_value": search_value,
                        "employees_found": 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Employee DB Agent 처리 실패: {str(e)}")
            return {
                "response": f"직원 정보 검색 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "metadata": {
                    "agent": "employee_db_agent",
                    "error": str(e)
                }
            }
    
    async def _search_employees(self, search_type: str, search_value: str) -> List[Dict[str, Any]]:
        """
        직원 데이터베이스에서 검색
        """
        try:
            # 데이터베이스 서비스의 기존 메소드 활용
            if hasattr(self.database_service, 'search_employee_info'):
                # 기존 메소드를 search_type에 맞게 활용
                search_query = f"{search_type}:{search_value}"
                results = await self.database_service.search_employee_info(search_query)
                
                if results:
                    # 결과가 문자열이면 파싱, 리스트면 그대로 반환
                    if isinstance(results, str):
                        return [{"info": results, "source": "employees.db"}]
                    elif isinstance(results, list):
                        return results
                    else:
                        return [{"info": str(results), "source": "employees.db"}]
            
            # 직접 데이터베이스 쿼리 (기본 구현)
            return await self._direct_db_search(search_type, search_value)
            
        except Exception as e:
            logger.error(f"직원 검색 실패: {str(e)}")
            return []
    
    async def _direct_db_search(self, search_type: str, search_value: str) -> List[Dict[str, Any]]:
        """
        직접 데이터베이스 검색 (fallback)
        """
        try:
            # 데이터베이스 경로 설정
            db_path = f"{settings.sqlite_db_path}/employees.db"
            
            # SQL 쿼리 생성
            column_mapping = {
                "name": "name",
                "department": "department", 
                "position": "position",
                "id": "employee_id"
            }
            
            column = column_mapping.get(search_type, "name")
            
            # 데이터베이스 연결 및 검색
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 테이블 구조 확인 (동적)
            cursor.execute("PRAGMA table_info(employees)")
            columns_info = cursor.fetchall()
            available_columns = [col[1] for col in columns_info]
            
            if column not in available_columns:
                # 사용 가능한 컬럼에서 유사한 것 찾기
                column = self._find_similar_column(column, available_columns)
            
            # LIKE 검색으로 부분 일치 허용
            query = f"SELECT * FROM employees WHERE {column} LIKE ? LIMIT 10"
            cursor.execute(query, (f"%{search_value}%",))
            
            rows = cursor.fetchall()
            
            # 결과 포맷팅
            if rows:
                # 컬럼명 가져오기
                column_names = [description[0] for description in cursor.description]
                
                results = []
                for row in rows:
                    employee_info = dict(zip(column_names, row))
                    results.append({
                        "employee_info": employee_info,
                        "source": "employees.db"
                    })
                
                conn.close()
                return results
            
            conn.close()
            return []
            
        except Exception as e:
            logger.error(f"직접 DB 검색 실패: {str(e)}")
            return []
    
    def _find_similar_column(self, target_column: str, available_columns: List[str]) -> str:
        """
        유사한 컬럼명 찾기
        """
        column_synonyms = {
            "name": ["name", "employee_name", "full_name", "이름"],
            "department": ["department", "dept", "부서"],
            "position": ["position", "job_title", "role", "직급", "직위"],
            "id": ["id", "employee_id", "emp_id", "직원번호"]
        }
        
        for synonym_group in column_synonyms.values():
            if target_column in synonym_group:
                for col in available_columns:
                    if col.lower() in [s.lower() for s in synonym_group]:
                        return col
        
        # 기본값으로 첫 번째 컬럼 반환
        return available_columns[0] if available_columns else "id"
    
    def _get_search_type_korean(self, search_type: str) -> str:
        """
        검색 타입을 한국어로 변환
        """
        korean_mapping = {
            "name": "이름",
            "department": "부서명",
            "position": "직급",
            "id": "직원번호"
        }
        return korean_mapping.get(search_type, search_type)
    
    async def _generate_employee_response(self, employee_data: List[Dict[str, Any]], original_message: str, search_type: str, search_value: str) -> str:
        """
        검색 결과를 바탕으로 OpenAI로 응답 생성
        """
        if not self.openai_client:
            return "OpenAI 서비스에 연결할 수 없어 검색 결과만 제공합니다:\n\n" + self._format_employee_data(employee_data)
        
        try:
            # 직원 정보 포맷팅
            employee_info_text = self._format_employee_data_for_prompt(employee_data)
            
            # OpenAI 프롬프트 생성
            prompt = f"""다음은 직원 데이터베이스에서 검색한 결과입니다:

검색 조건: {self._get_search_type_korean(search_type)} = "{search_value}"

검색 결과:
{employee_info_text}

사용자 질문: {original_message}

위 정보를 바탕으로 사용자의 질문에 대해 친절하고 정확한 답변을 제공해주세요.

답변 조건:
1. 한국어로 답변하세요
2. 개인정보 보호를 위해 민감한 정보는 적절히 처리하세요
3. 검색된 직원 정보를 보기 좋게 정리해서 제공하세요
4. 직원이 여러 명인 경우 목록 형태로 표시하세요
5. 친근하고 전문적인 톤으로 답변하세요"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"직원 정보 응답 생성 실패: {str(e)}")
            return f"응답 생성 중 오류가 발생했습니다. 검색 결과:\n\n{self._format_employee_data(employee_data)}"
    
    def _format_employee_data(self, employee_data: List[Dict[str, Any]]) -> str:
        """
        직원 데이터를 사용자용 텍스트로 포맷팅
        """
        if not employee_data:
            return "검색된 직원 정보가 없습니다."
        
        formatted_data = []
        for i, data in enumerate(employee_data, 1):
            if "employee_info" in data:
                info = data["employee_info"]
                formatted_data.append(f"👤 직원 {i}:\n{self._format_single_employee(info)}")
            elif "info" in data:
                formatted_data.append(f"👤 직원 {i}:\n{data['info']}")
        
        return "\n\n".join(formatted_data)
    
    def _format_employee_data_for_prompt(self, employee_data: List[Dict[str, Any]]) -> str:
        """
        직원 데이터를 OpenAI 프롬프트용으로 포맷팅
        """
        formatted_data = []
        for data in employee_data:
            if "employee_info" in data:
                info = data["employee_info"] 
                formatted_data.append(str(info))
            elif "info" in data:
                formatted_data.append(data["info"])
        
        return "\n".join(formatted_data)
    
    def _format_single_employee(self, employee_info: Dict[str, Any]) -> str:
        """
        단일 직원 정보 포맷팅
        """
        formatted_lines = []
        for key, value in employee_info.items():
            if value:  # 값이 있는 경우만 표시
                korean_key = self._translate_column_name(key)
                formatted_lines.append(f"  {korean_key}: {value}")
        
        return "\n".join(formatted_lines)
    
    def _translate_column_name(self, column_name: str) -> str:
        """
        컬럼명을 한국어로 번역
        """
        translations = {
            "id": "직원번호",
            "employee_id": "직원번호", 
            "name": "이름",
            "employee_name": "이름",
            "department": "부서",
            "dept": "부서",
            "position": "직급",
            "job_title": "직급",
            "email": "이메일",
            "phone": "전화번호",
            "hire_date": "입사일",
            "salary": "급여",
            "manager": "상급자",
            "status": "재직상태"
        }
        
        return translations.get(column_name.lower(), column_name) 