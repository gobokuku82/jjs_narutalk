"""
Client Analysis Agent
client_data.db에서 고객 데이터 분석 및 고객 정보를 조회하는 Agent
"""

import logging
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from openai import OpenAI
from ...core.config import settings

logger = logging.getLogger(__name__)

class ClientAnalysisAgent:
    """고객 분석 Agent"""
    
    def __init__(self):
        self.openai_client = None
        try:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
        
        logger.info("Client Analysis Agent 초기화 완료")
    
    async def process(self, function_args: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """
        고객 분석 처리
        
        Args:
            function_args: OpenAI function calling에서 전달된 인자
            original_message: 원본 사용자 메시지
            
        Returns:
            처리 결과 딕셔너리
        """
        try:
            analysis_type = function_args.get("analysis_type", "profile")
            client_id = function_args.get("client_id", None)
            time_period = function_args.get("time_period", None)
            
            logger.info(f"고객 분석 시작: {analysis_type}, 고객ID: {client_id}, 기간: {time_period}")
            
            # 1. 고객 데이터 분석 수행
            analysis_data = await self._perform_client_analysis(analysis_type, client_id, time_period)
            
            # 2. 분석 결과가 있으면 OpenAI로 응답 생성
            if analysis_data:
                response = await self._generate_analysis_response(analysis_data, original_message, analysis_type, client_id, time_period)
                
                return {
                    "response": response,
                    "sources": analysis_data,
                    "metadata": {
                        "agent": "client_analysis_agent",
                        "analysis_type": analysis_type,
                        "client_id": client_id,
                        "time_period": time_period,
                        "data_points": len(analysis_data)
                    }
                }
            else:
                return {
                    "response": f"{self._get_analysis_type_korean(analysis_type)} 분석을 위한 데이터를 찾을 수 없습니다. 고객 데이터베이스가 구성되지 않았거나 해당 기간의 데이터가 없을 수 있습니다.",
                    "sources": [],
                    "metadata": {
                        "agent": "client_analysis_agent",
                        "analysis_type": analysis_type,
                        "client_id": client_id,
                        "data_points": 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Client Analysis Agent 처리 실패: {str(e)}")
            return {
                "response": f"고객 분석 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "metadata": {
                    "agent": "client_analysis_agent",
                    "error": str(e)
                }
            }
    
    async def _perform_client_analysis(self, analysis_type: str, client_id: str = None, time_period: str = None) -> List[Dict[str, Any]]:
        """
        고객 분석 수행
        """
        try:
            # 데이터베이스 경로 설정
            db_path = f"{settings.sqlite_db_path}/client_data.db"
            
            # 분석 타입에 따른 데이터 수집
            if analysis_type == "profile":
                return await self._get_client_profiles(db_path, client_id)
            elif analysis_type == "transaction":
                return await self._get_transaction_analysis(db_path, client_id, time_period)
            elif analysis_type == "sales":
                return await self._get_sales_analysis(db_path, client_id, time_period)
            elif analysis_type == "segment":
                return await self._get_segment_analysis(db_path, time_period)
            else:
                logger.warning(f"알 수 없는 분석 타입: {analysis_type}")
                return []
                
        except Exception as e:
            logger.error(f"고객 분석 수행 실패: {str(e)}")
            # 데이터베이스가 없는 경우 샘플 데이터 반환
            return await self._generate_sample_data(analysis_type, client_id, time_period)
    
    async def _get_client_profiles(self, db_path: str, client_id: str = None) -> List[Dict[str, Any]]:
        """
        고객 프로필 조회
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if client_id:
                cursor.execute("SELECT * FROM clients WHERE client_id = ?", (client_id,))
            else:
                cursor.execute("SELECT * FROM clients LIMIT 10")
            
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            
            results = []
            for row in rows:
                client_data = dict(zip(column_names, row))
                results.append({
                    "type": "client_profile",
                    "data": client_data,
                    "source": "client_data.db"
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"고객 프로필 조회 실패: {str(e)}")
            return []
    
    async def _get_transaction_analysis(self, db_path: str, client_id: str = None, time_period: str = None) -> List[Dict[str, Any]]:
        """
        거래 이력 분석
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 기간 필터링
            date_filter = self._parse_time_period(time_period)
            
            if client_id:
                if date_filter:
                    cursor.execute("""
                        SELECT * FROM transactions 
                        WHERE client_id = ? AND transaction_date >= ? 
                        ORDER BY transaction_date DESC
                    """, (client_id, date_filter))
                else:
                    cursor.execute("""
                        SELECT * FROM transactions 
                        WHERE client_id = ? 
                        ORDER BY transaction_date DESC LIMIT 50
                    """, (client_id,))
            else:
                if date_filter:
                    cursor.execute("""
                        SELECT client_id, COUNT(*) as transaction_count, 
                               SUM(amount) as total_amount, AVG(amount) as avg_amount
                        FROM transactions 
                        WHERE transaction_date >= ?
                        GROUP BY client_id
                        ORDER BY total_amount DESC LIMIT 20
                    """, (date_filter,))
                else:
                    cursor.execute("""
                        SELECT client_id, COUNT(*) as transaction_count, 
                               SUM(amount) as total_amount, AVG(amount) as avg_amount
                        FROM transactions 
                        GROUP BY client_id
                        ORDER BY total_amount DESC LIMIT 20
                    """)
            
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            
            results = []
            for row in rows:
                transaction_data = dict(zip(column_names, row))
                results.append({
                    "type": "transaction_analysis",
                    "data": transaction_data,
                    "source": "client_data.db"
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"거래 분석 실패: {str(e)}")
            return []
    
    async def _get_sales_analysis(self, db_path: str, client_id: str = None, time_period: str = None) -> List[Dict[str, Any]]:
        """
        매출 분석
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            date_filter = self._parse_time_period(time_period)
            
            # 월별 매출 분석
            if date_filter:
                cursor.execute("""
                    SELECT 
                        strftime('%Y-%m', transaction_date) as month,
                        COUNT(*) as transaction_count,
                        SUM(amount) as total_sales,
                        AVG(amount) as avg_transaction
                    FROM transactions 
                    WHERE transaction_date >= ?
                    GROUP BY strftime('%Y-%m', transaction_date)
                    ORDER BY month DESC
                """, (date_filter,))
            else:
                cursor.execute("""
                    SELECT 
                        strftime('%Y-%m', transaction_date) as month,
                        COUNT(*) as transaction_count,
                        SUM(amount) as total_sales,
                        AVG(amount) as avg_transaction
                    FROM transactions 
                    GROUP BY strftime('%Y-%m', transaction_date)
                    ORDER BY month DESC LIMIT 12
                """)
            
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            
            results = []
            for row in rows:
                sales_data = dict(zip(column_names, row))
                results.append({
                    "type": "sales_analysis",
                    "data": sales_data,
                    "source": "client_data.db"
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"매출 분석 실패: {str(e)}")
            return []
    
    async def _get_segment_analysis(self, db_path: str, time_period: str = None) -> List[Dict[str, Any]]:
        """
        고객 세그먼트 분석
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 고객 세그먼트별 분석 (예: 매출 구간별)
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN total_amount >= 10000000 THEN 'VIP'
                        WHEN total_amount >= 5000000 THEN 'Gold'
                        WHEN total_amount >= 1000000 THEN 'Silver'
                        ELSE 'Bronze'
                    END as segment,
                    COUNT(*) as client_count,
                    AVG(total_amount) as avg_amount,
                    SUM(total_amount) as segment_total
                FROM (
                    SELECT client_id, SUM(amount) as total_amount
                    FROM transactions
                    GROUP BY client_id
                ) client_totals
                GROUP BY segment
                ORDER BY segment_total DESC
            """)
            
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            
            results = []
            for row in rows:
                segment_data = dict(zip(column_names, row))
                results.append({
                    "type": "segment_analysis",
                    "data": segment_data,
                    "source": "client_data.db"
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"세그먼트 분석 실패: {str(e)}")
            return []
    
    async def _generate_sample_data(self, analysis_type: str, client_id: str = None, time_period: str = None) -> List[Dict[str, Any]]:
        """
        데이터베이스가 없는 경우 샘플 데이터 생성
        """
        sample_data = []
        
        if analysis_type == "profile":
            sample_data = [
                {
                    "type": "sample_profile",
                    "data": {
                        "client_id": client_id or "C001",
                        "name": "샘플 고객",
                        "type": "기업",
                        "registration_date": "2023-01-15",
                        "status": "활성"
                    },
                    "source": "sample_data"
                }
            ]
        elif analysis_type == "sales":
            sample_data = [
                {
                    "type": "sample_sales",
                    "data": {
                        "period": time_period or "2024년",
                        "total_sales": "500,000,000원",
                        "transaction_count": 1250,
                        "avg_transaction": "400,000원"
                    },
                    "source": "sample_data"
                }
            ]
        
        return sample_data
    
    def _parse_time_period(self, time_period: str) -> str:
        """
        시간 기간 문자열을 DB 날짜 형식으로 변환
        """
        if not time_period:
            return None
        
        try:
            # "2024-01 ~ 2024-12" 형식 처리
            if "~" in time_period:
                start_date = time_period.split("~")[0].strip()
                return f"{start_date}-01"
            
            # "2024" 형식 처리
            if len(time_period) == 4:
                return f"{time_period}-01-01"
            
            # "2024-01" 형식 처리
            if len(time_period) == 7:
                return f"{time_period}-01"
            
            return time_period
            
        except Exception:
            return None
    
    def _get_analysis_type_korean(self, analysis_type: str) -> str:
        """
        분석 타입을 한국어로 변환
        """
        korean_mapping = {
            "profile": "고객 프로필",
            "transaction": "거래 이력",
            "sales": "매출",
            "segment": "고객 세그먼트"
        }
        return korean_mapping.get(analysis_type, analysis_type)
    
    async def _generate_analysis_response(self, analysis_data: List[Dict[str, Any]], original_message: str, analysis_type: str, client_id: str = None, time_period: str = None) -> str:
        """
        분석 결과를 바탕으로 OpenAI로 응답 생성
        """
        if not self.openai_client:
            return "OpenAI 서비스에 연결할 수 없어 분석 결과만 제공합니다:\n\n" + self._format_analysis_data(analysis_data)
        
        try:
            # 분석 데이터 포맷팅
            analysis_text = self._format_analysis_data_for_prompt(analysis_data)
            
            # OpenAI 프롬프트 생성
            prompt = f"""다음은 고객 데이터 분석 결과입니다:

분석 유형: {self._get_analysis_type_korean(analysis_type)}
고객 ID: {client_id or '전체'}
분석 기간: {time_period or '전체 기간'}

분석 데이터:
{analysis_text}

사용자 질문: {original_message}

위 분석 결과를 바탕으로 사용자의 질문에 대해 전문적이고 도움이 되는 답변을 제공해주세요.

답변 조건:
1. 한국어로 답변하세요
2. 데이터 기반의 구체적인 인사이트를 제공하세요
3. 수치가 있는 경우 명확하게 표시하세요
4. 비즈니스 관점에서 의미 있는 해석을 제공하세요
5. 추가 분석이나 개선 방향을 제안하세요"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"고객 분석 응답 생성 실패: {str(e)}")
            return f"응답 생성 중 오류가 발생했습니다. 분석 결과:\n\n{self._format_analysis_data(analysis_data)}"
    
    def _format_analysis_data(self, analysis_data: List[Dict[str, Any]]) -> str:
        """
        분석 데이터를 사용자용 텍스트로 포맷팅
        """
        if not analysis_data:
            return "분석 데이터가 없습니다."
        
        formatted_data = []
        for i, data in enumerate(analysis_data, 1):
            data_type = data.get("type", "unknown")
            data_content = data.get("data", {})
            
            formatted_data.append(f"📊 {data_type} {i}:\n{self._format_single_data(data_content)}")
        
        return "\n\n".join(formatted_data)
    
    def _format_analysis_data_for_prompt(self, analysis_data: List[Dict[str, Any]]) -> str:
        """
        분석 데이터를 OpenAI 프롬프트용으로 포맷팅
        """
        formatted_data = []
        for data in analysis_data:
            data_content = data.get("data", {})
            formatted_data.append(str(data_content))
        
        return "\n".join(formatted_data)
    
    def _format_single_data(self, data_content: Dict[str, Any]) -> str:
        """
        단일 데이터 포맷팅
        """
        formatted_lines = []
        for key, value in data_content.items():
            if value:
                korean_key = self._translate_field_name(key)
                formatted_lines.append(f"  {korean_key}: {value}")
        
        return "\n".join(formatted_lines)
    
    def _translate_field_name(self, field_name: str) -> str:
        """
        필드명을 한국어로 번역
        """
        translations = {
            "client_id": "고객 ID",
            "name": "고객명",
            "type": "고객 유형",
            "registration_date": "등록일",
            "status": "상태",
            "transaction_count": "거래 건수",
            "total_amount": "총 금액",
            "avg_amount": "평균 금액",
            "month": "월",
            "total_sales": "총 매출",
            "avg_transaction": "평균 거래액",
            "segment": "고객 세그먼트",
            "client_count": "고객 수",
            "segment_total": "세그먼트 총액",
            "period": "기간"
        }
        
        return translations.get(field_name.lower(), field_name) 