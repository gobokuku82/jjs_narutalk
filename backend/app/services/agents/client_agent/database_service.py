"""
Client Agent Database Service

거래처 분석을 위한 데이터베이스 서비스
"""

import logging
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
    """거래처 데이터베이스 서비스"""
    
    def __init__(self):
        self.excel_path = Path(settings.project_root) / "database" / "raw_data" / "내부자료"
        logger.info("Client DatabaseService 초기화 완료")
    
    def get_client_data(self) -> List[Dict[str, Any]]:
        """거래처 데이터 조회"""
        try:
            # 거래처 관련 파일들
            client_files = [
                "좋은제약_거래처정보.xlsx",
                "좋은제약_실적자료_최수아.xlsx"
            ]
            
            results = []
            
            for client_file in client_files:
                file_path = self.excel_path / client_file
                if file_path.exists():
                    if HAS_PANDAS:
                        try:
                            df = pd.read_excel(file_path)
                            results.append({
                                "source": client_file,
                                "data": df.head().to_dict('records'),  # 상위 5개 레코드
                                "total_records": len(df),
                                "columns": list(df.columns)
                            })
                        except Exception as e:
                            logger.warning(f"Excel 파일 {client_file} 읽기 실패: {str(e)}")
                    else:
                        # pandas 없이 기본 응답
                        results.append({
                            "source": client_file,
                            "data": {
                                "message": f"파일 {client_file}이 존재하지만 pandas가 설치되지 않아 읽을 수 없습니다.",
                                "file_path": str(file_path)
                            },
                            "match_type": "pandas_not_available"
                        })
            
            if not results:
                results = [{
                    "source": "system",
                    "data": {
                        "message": "거래처 데이터 파일을 찾을 수 없습니다.",
                        "available_files": list(self.excel_path.glob("*.xlsx"))
                    },
                    "match_type": "file_not_found"
                }]
            
            return results
            
        except Exception as e:
            logger.error(f"거래처 데이터 조회 실패: {str(e)}")
            return [{
                "source": "error",
                "data": {"error": str(e)},
                "match_type": "error"
            }]
    
    def analyze_performance(self, time_period: str = None) -> Dict[str, Any]:
        """성과 분석"""
        try:
            return {
                "analysis_type": "performance",
                "time_period": time_period or "2024년",
                "summary": "거래처 성과 분석 결과입니다.",
                "metrics": {
                    "total_clients": "분석 중",
                    "revenue_growth": "분석 중",
                    "top_clients": "분석 중"
                }
            }
        except Exception as e:
            logger.error(f"성과 분석 실패: {str(e)}")
            return {"error": str(e)} 