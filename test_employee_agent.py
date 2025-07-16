#!/usr/bin/env python3
"""
직원 실적 분석 에이전트 테스트 스크립트
"""

import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.services.agents.employee_agent import run_employee_analysis

def test_employee_analysis():
    """직원 실적 분석 테스트"""
    print("=== 직원 실적 분석 에이전트 테스트 ===\n")
    
    # 테스트 케이스들
    test_cases = [
        {
            "query": "종합 실적 분석해줘",
            "start_month": "202312",
            "end_month": "202403",
            "description": "종합 실적 분석 (보고서 생성 포함)"
        },
        {
            "query": "담당자별 달성률 분석해줘",
            "start_month": "202312",
            "end_month": "202403",
            "description": "담당자별 목표 달성률 분석"
        },
        {
            "query": "실적 변화 분석해줘",
            "start_month": "202312",
            "end_month": "202403",
            "description": "최수아 담당자의 병원별/품목별 실적 급증/감소 분석"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"테스트 {i}: {test_case['description']}")
        print(f"쿼리: {test_case['query']}")
        print(f"기간: {test_case['start_month']} ~ {test_case['end_month']}")
        print("-" * 50)
        
        try:
            result = run_employee_analysis(
                user_query=test_case['query'],
                start_month=test_case['start_month'],
                end_month=test_case['end_month']
            )
            
            if "comprehensive_report" in result:
                print("✅ 종합 분석 완료")
                print(f"보고서 파일: {result.get('saved_filename', '저장 실패')}")
                print("\n보고서 미리보기 (처음 500자):")
                report = result.get("comprehensive_report", "")
                print(report[:500] + "..." if len(report) > 500 else report)
            else:
                print("✅ 분석 완료")
                analysis_result = result.get("result", "결과 없음")
                print("\n분석 결과:")
                print(analysis_result[:500] + "..." if len(analysis_result) > 500 else analysis_result)
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    test_employee_analysis() 