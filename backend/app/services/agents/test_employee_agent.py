import asyncio
from employee_agent import run_performance_pipeline
from langgraph.graph import StateGraph, END
import pandas as pd
import openai
import os

if __name__ == "__main__":
    # 테스트용 직원ID, 기간 설정
    employee_id = "최수아"
    start_month = "202312"
    end_month = "202403"

    # LangGraph 파이프라인 실행 및 요약 보고서 출력
    async def main():
        summary = await run_performance_pipeline(employee_id, start_month, end_month)
        print("\n===== 요약 보고서 =====\n")
        print(summary)

    asyncio.run(main()) 