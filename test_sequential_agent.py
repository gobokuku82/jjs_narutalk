#!/usr/bin/env python3
"""
Agent 인스턴스 생성 및 process 메서드 단독 테스트 (sequential thinking 2단계)
"""
import sys
import os
import asyncio

# 상대경로 import 문제 해결
sys.path.insert(0, os.path.abspath('./backend/app'))

from services.agents.client_agent.client_agent import ClientAgent
from services.agents.db_agent.db_agent import DBAgent
from services.agents.docs_agent.docs_agent import DocsAgent
from services.agents.employee_agent.employee_agent import EmployeeAgent

async def test_agent(agent_class, agent_name, args, message):
    print(f"\n[테스트] {agent_name}")
    try:
        agent = agent_class()
        print(f"- 인스턴스 생성 성공: {agent}")
        result = await agent.process(args, message)
        print(f"- process 결과: {result}")
    except Exception as e:
        print(f"- 오류 발생: {e}")

async def main():
    await test_agent(ClientAgent, 'client_agent', {"analysis_type": "profile"}, "미라클신경과 실적분석해줘")
    await test_agent(DBAgent, 'db_agent', {"query": "미라클신경과 실적분석"}, "미라클신경과 실적분석해줘")
    await test_agent(DocsAgent, 'docs_agent', {"task_type": "generate_document", "content": "미라클신경과 실적분석"}, "미라클신경과 실적분석해줘")
    await test_agent(EmployeeAgent, 'employee_agent', {"search_type": "name", "search_value": "미라클신경과"}, "미라클신경과 실적분석해줘")

if __name__ == "__main__":
    asyncio.run(main()) 