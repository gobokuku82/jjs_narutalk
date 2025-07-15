import openai
from typing import Optional, Dict, Any
import pandas as pd
import os

EXCEL_PATH = r'C:/FINAL_PROJECT/jjs_narutalk/data/Docs/DATABASE/총정리/내부규정/좋은제약_실적자료_최수아.xlsx'

class EmployeePerformanceAgent:
    """
    직원 실적 분석 에이전트 (엑셀 파일에서 실적 데이터 읽기)
    - 직원 모드: 기간별 실적 데이터 조회, LLM 요약, 보고서 저장 및 반환
    - 관리자 모드: 직원별 저장된 분석 보고서 조회
    """
    def __init__(self, openai_api_key=None):
        self.db_service = HybridDBService()
        self.llm_service = LLMService(openai_api_key)
        self.report_store = ReportStoreService()

    async def analyze_performance(self, employee_id, year, month, product=None):
        # 1. 실적 데이터 조회 (엑셀에서)
        current_data = self.db_service.get_employee_monthly_performance(employee_id, year, month, product)
        prev_year, prev_month = self._get_prev_year_month(year, month)
        prev_data = self.db_service.get_employee_monthly_performance(employee_id, prev_year, prev_month, product)

        # 2. 증감률 계산 (타입 안전성 보장)
        current_sales = float(current_data.get('total_sales', 0)) if current_data else 0.0
        prev_sales = float(prev_data.get('total_sales', 0)) if prev_data else 0.0
        if prev_sales > 0:
            change_rate = (current_sales - prev_sales) / prev_sales * 100
        else:
            change_rate = 0.0 if current_sales == 0 else 100.0

        # 3. LLM 요약 보고서 생성
        summary = await self.llm_service.summarize_performance({
            'current_month': {'year': year, 'month': month, 'total_sales': current_sales},
            'prev_month': {'year': prev_year, 'month': prev_month, 'total_sales': prev_sales},
            'change_rate': change_rate
        })

        # 4. 보고서 저장 
        report_id = self.report_store.save_report(employee_id, year, month, summary, current_sales, prev_sales, change_rate)

        # 5. 결과 반환
        return {
            'employee_id': employee_id,
            'year': year,
            'month': month,
            'product': product,
            'current_sales': current_sales,
            'prev_sales': prev_sales,
            'change_rate': change_rate,
            'summary': summary,
            'report_id': report_id
        }

    def get_reports_for_admin(self, employee_id=None):
        return self.report_store.get_reports(employee_id)

    def _get_prev_year_month(self, year, month):
        if month == 1:
            return year - 1, 12
        else:
            return year, month - 1

class HybridDBService:
    def __init__(self):
        # 엑셀 파일을 미리 읽어둠 (메모리 캐싱)
        self.df = None
        if os.path.exists(EXCEL_PATH):
            self.df = pd.read_excel(EXCEL_PATH)

    def get_employee_monthly_performance(self, employee_id, year, month, product=None) -> Optional[Dict[str, Any]]:
        # 엑셀 파일에서 실적 데이터 추출
        if self.df is None:
            return None
        # 월 컬럼명 생성 (예: 202405)
        month_col = f"{year}{month:02d}"
        # 필터링: 담당자, (옵션) 품목
        df = self.df
        df_filtered = df[df['담당자'] == employee_id]
        if product:
            df_filtered = df_filtered[df_filtered['품목'] == product]
        if df_filtered.empty:
            return None
        # 여러 행이 있을 수 있으니 합산
        total_sales = df_filtered[month_col].fillna(0).sum()
        return {
            'employee_id': employee_id,
            'year': year,
            'month': month,
            'total_sales': float(total_sales),
            'sales_count': int(len(df_filtered))
        }

class LLMService:
    def __init__(self, api_key=None):
        self.api_key = api_key or "YOUR_OPENAI_API_KEY"

    async def summarize_performance(self, perf_data):
        current = perf_data.get('current_month', {}) or {}
        prev = perf_data.get('prev_month', {}) or {}
        current_year = current.get('year', 0)
        current_month = current.get('month', 0)
        current_sales = float(current.get('total_sales', 0) or 0.0)
        prev_year = prev.get('year', 0)
        prev_month = prev.get('month', 0)
        prev_sales = float(prev.get('total_sales', 0) or 0.0)
        change_rate = float(perf_data.get('change_rate', 0) or 0.0)
        prompt = (
            f"아래는 직원의 월간 실적 데이터입니다.\n"
            f"- 이번 달 실적: {current_sales}원\n"
            f"- 전월 실적: {prev_sales}원\n"
            f"- 전월 대비 증감률: {change_rate:.2f}%\n"
            "이 데이터를 바탕으로, "
            "1) 실적의 주요 특징(증가/감소 원인, 특이사항)\n"
            "2) 개선점 또는 칭찬할 점\n"
            "3) 다음 달을 위한 간단한 제안\n"
            "을 포함한 5~6줄 내외의 요약 보고서를 작성해줘."
        )
        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content
        return content

class ReportStoreService:
    def __init__(self):
        self._reports = []  # 메모리 mock 저장소

    def save_report(self, employee_id, year, month, summary, current_sales, prev_sales, change_rate):
        report_id = len(self._reports) + 1
        report = {
            'report_id': report_id,
            'employee_id': employee_id,
            'year': year,
            'month': month,
            'summary': summary,
            'current_sales': current_sales,
            'prev_sales': prev_sales,
            'change_rate': change_rate
        }
        self._reports.append(report)
        return report_id

    def get_reports(self, employee_id=None):
        if employee_id:
            return [r for r in self._reports if r['employee_id'] == employee_id]
        return self._reports 