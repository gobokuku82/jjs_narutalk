#!/usr/bin/env python3
"""
더미 데이터 생성 디버깅 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from employee_agent import create_dummy_branch_targets, create_dummy_employee_performance, make_month_list

def debug_dummy_data():
    """더미 데이터 생성 디버깅"""
    print("=== 더미 데이터 생성 디버깅 ===\n")
    
    # 1. 지점별 목표 데이터 테스트
    print("1. 지점별 목표 데이터 생성:")
    try:
        branch_df = create_dummy_branch_targets()
        print(f"✅ 생성 성공: {len(branch_df)} 행")
        print(f"컬럼: {list(branch_df.columns)}")
        print(f"담당자 목록: {list(branch_df['담당자'].unique())}")
        print(f"월 목록: {list(branch_df['월'].unique())}")
        print("\n처음 3행:")
        print(branch_df.head(3))
        print()
    except Exception as e:
        print(f"❌ 오류: {e}")
        return
    
    # 2. 개인별 실적 데이터 테스트
    print("2. 개인별 실적 데이터 생성:")
    try:
        performance_df = create_dummy_employee_performance()
        print(f"✅ 생성 성공: {len(performance_df)} 행")
        print(f"컬럼: {list(performance_df.columns)}")
        print(f"병원 목록: {list(performance_df['병원명'].unique())}")
        print(f"품목 목록: {list(performance_df['품목명'].unique())}")
        print(f"월 목록: {list(performance_df['월'].unique())}")
        print("\n처음 3행:")
        print(performance_df.head(3))
        print()
    except Exception as e:
        print(f"❌ 오류: {e}")
        return
    
    # 3. 월 리스트 생성 테스트
    print("3. 월 리스트 생성:")
    try:
        months = make_month_list("202312", "202403")
        print(f"✅ 생성 성공: {months}")
        print()
    except Exception as e:
        print(f"❌ 오류: {e}")
        return
    
    # 4. 필터링 테스트
    print("4. 필터링 테스트:")
    try:
        months = make_month_list("202312", "202403")
        filtered_df = branch_df[branch_df['월'].isin(months)]
        print(f"✅ 필터링 성공: {len(filtered_df)} 행")
        print(f"필터링된 월: {list(filtered_df['월'].unique())}")
        print()
    except Exception as e:
        print(f"❌ 오류: {e}")
        return
    
    print("=== 모든 테스트 완료 ===")

if __name__ == "__main__":
    debug_dummy_data() 