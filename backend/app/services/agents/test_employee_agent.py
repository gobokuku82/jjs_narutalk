#!/usr/bin/env python3
"""
직원 실적 분석 에이전트 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from employee_agent import EmployeePerformanceAgent

def test_employee_agent():
    """LangGraph 기반 직원 실적 분석 에이전트를 테스트합니다."""
    
    print("=== LangGraph 기반 직원 실적 분석 에이전트 테스트 ===")
    
    # 에이전트 초기화
    agent = EmployeePerformanceAgent()
    
    try:
        # LangGraph를 사용하여 분석 실행
        print("\n1. LangGraph 워크플로우 실행 중...")
        result = agent.run_analysis()
        
        if result.get("error"):
            print(f"❌ 오류 발생: {result['error']}")
            return
        
        print("✅ LangGraph 워크플로우 실행 완료")
        
        # 분석 결과 확인
        analysis_result = result.get("analysis_result")
        if analysis_result:
            print(f"\n2. 분석 결과:")
            print(f"   - 분석 기간: {analysis_result.get('period', 'N/A')}")
            print(f"   - 총 실적: {analysis_result.get('total_performance', 0):,.0f}원")
            print(f"   - 총 목표: {analysis_result.get('total_target', 0):,.0f}원")
            print(f"   - 달성률: {analysis_result.get('achievement_rate', 0):.1f}%")
            print(f"   - 분석된 품목 수: {len(analysis_result.get('employee_analysis', []))}")
        
        # 보고서 확인
        report = result.get("report")
        if report:
            print(f"\n3. LLM 생성 보고서:")
            print("=" * 50)
            print(report[:500] + "..." if len(report) > 500 else report)
            print("=" * 50)
            
            # Word 문서로 저장
            print("\n4. Word 문서 저장 중...")
            save_result = agent.save_report_to_docx(report, "최수아_실적분석보고서.docx")
            print(f"   {save_result}")
        
        print("\n✅ 모든 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_employee_agent() 