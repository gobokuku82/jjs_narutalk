"""
Employee Agent Database Service

직원 정보 검색을 위한 데이터베이스 서비스
"""

import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from ....core.config import settings

# pandas 선택적 임포트
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

logger = logging.getLogger(__name__)

class DatabaseService:
    """직원 정보 데이터베이스 서비스"""
    
    def __init__(self):
        self.db_path = Path(settings.sqlite_db_path) / "employee_data.db"
        self.excel_path = Path(settings.project_root) / "database" / "raw_data" / "내부자료"
        logger.info("Employee DatabaseService 초기화 완료")
    
    def search_employee(self, search_type: str, search_value: str) -> List[Dict[str, Any]]:
        """직원 검색"""
        try:
            # Excel 파일에서 직원 정보 검색
            excel_files = [
                "좋은제약_인사자료.xlsx",
                "좋은제약_직원평가.xlsx"
            ]
            
            results = []
            
            for excel_file in excel_files:
                file_path = self.excel_path / excel_file
                if file_path.exists():
                    if HAS_PANDAS:
                        try:
                            df = pd.read_excel(file_path)
                            
                            # 검색 타입에 따른 필터링
                            if search_type == "name" and search_value:
                                # 이름으로 검색
                                mask = df.astype(str).apply(lambda x: x.str.contains(search_value, case=False, na=False)).any(axis=1)
                                filtered_df = df[mask]
                                
                                if not filtered_df.empty:
                                    for _, row in filtered_df.iterrows():
                                        results.append({
                                            "source": excel_file,
                                            "data": row.to_dict(),
                                            "match_type": "name_search"
                                        })
                            
                        except Exception as e:
                            logger.warning(f"Excel 파일 {excel_file} 읽기 실패: {str(e)}")
                    else:
                        # pandas 없이 기본 응답
                        results.append({
                            "source": excel_file,
                            "data": {
                                "message": f"파일 {excel_file}이 존재하지만 pandas가 설치되지 않아 읽을 수 없습니다.",
                                "file_path": str(file_path),
                                "search_value": search_value
                            },
                            "match_type": "pandas_not_available"
                        })
            
            if not results:
                # 기본 응답
                results = [{
                    "source": "system",
                    "data": {
                        "message": f"'{search_value}'에 대한 직원 정보를 찾을 수 없습니다.",
                        "suggestion": "정확한 이름이나 직원 ID를 입력해주세요."
                    },
                    "match_type": "no_match"
                }]
            
            return results
            
        except Exception as e:
            logger.error(f"직원 검색 실패: {str(e)}")
            return [{
                "source": "error",
                "data": {"error": str(e)},
                "match_type": "error"
            }]
    
    def get_department_info(self) -> List[Dict[str, Any]]:
        """부서 정보 조회"""
        try:
            # 조직도 파일에서 부서 정보 추출
            org_file = self.excel_path / "좋은제약_인사도.docx"
            
            if org_file.exists():
                return [{
                    "source": "좋은제약_인사도.docx",
                    "data": {
                        "message": "조직도 정보가 있습니다.",
                        "file_path": str(org_file)
                    },
                    "match_type": "organization_chart"
                }]
            else:
                return [{
                    "source": "system",
                    "data": {
                        "message": "조직도 파일을 찾을 수 없습니다.",
                        "available_files": list(self.excel_path.glob("*.xlsx"))
                    },
                    "match_type": "file_not_found"
                }]
                
        except Exception as e:
            logger.error(f"부서 정보 조회 실패: {str(e)}")
            return [{
                "source": "error", 
                "data": {"error": str(e)},
                "match_type": "error"
            }] 