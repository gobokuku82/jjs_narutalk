#!/usr/bin/env python3
"""
NaruTalk AI 시스템 디버깅 스크립트
"""

import os
import sys
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment():
    """환경 설정 확인"""
    print("🔍 환경 설정 확인 중...")
    
    # .env 파일 확인
    project_root = Path(__file__).parent
    env_file = project_root / ".env"
    
    print(f"📁 프로젝트 루트: {project_root}")
    print(f"📄 .env 파일: {env_file}")
    print(f"✅ .env 파일 존재: {env_file.exists()}")
    
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "OPENAI_API_KEY" in content:
                print("✅ .env 파일에 OPENAI_API_KEY 설정됨")
            else:
                print("❌ .env 파일에 OPENAI_API_KEY 없음")
    
    # 환경변수 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"✅ OPENAI_API_KEY 환경변수: {api_key[:10]}...")
    else:
        print("❌ OPENAI_API_KEY 환경변수 없음")

def check_dependencies():
    """의존성 확인"""
    print("\n🔍 의존성 확인 중...")
    
    required_packages = [
        "fastapi",
        "uvicorn", 
        "openai",
        "langgraph",
        "chromadb",
        "pydantic",
        "python-dotenv"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: 설치됨")
        except ImportError:
            print(f"❌ {package}: 설치되지 않음")

def check_file_structure():
    """파일 구조 확인"""
    print("\n🔍 파일 구조 확인 중...")
    
    project_root = Path(__file__).parent
    required_files = [
        "backend/main.py",
        "backend/app/core/config.py",
        "backend/app/services/router_agent/router_agent.py",
        "backend/app/services/router_agent/agent_schemas.json",
        "frontend/index.html",
        "frontend/script.js",
        "frontend/style.css"
    ]
    
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")

def check_agent_files():
    """Agent 파일 확인"""
    print("\n🔍 Agent 파일 확인 중...")
    
    project_root = Path(__file__).parent
    agent_files = [
        "backend/app/services/agents/db_agent.py",
        "backend/app/services/agents/docs_agent.py", 
        "backend/app/services/agents/employee_agent.py",
        "backend/app/services/agents/client_agent.py"
    ]
    
    for agent_file in agent_files:
        full_path = project_root / agent_file
        if full_path.exists():
            print(f"✅ {agent_file}")
        else:
            print(f"❌ {agent_file}")

def test_imports():
    """모듈 import 테스트"""
    print("\n🔍 모듈 import 테스트 중...")
    
    try:
        # 백엔드 모듈 import 테스트
        sys.path.append(str(Path(__file__).parent / "backend"))
        
        from app.core.config import settings
        print("✅ config.py import 성공")
        
        from app.services.router_agent.router_agent import RouterAgent
        print("✅ router_agent.py import 성공")
        
        from app.services.router_agent.schema_loader import AgentSchemaLoader
        print("✅ schema_loader.py import 성공")
        
        # 스키마 로더 테스트
        schema_loader = AgentSchemaLoader()
        print("✅ AgentSchemaLoader 초기화 성공")
        
        functions = schema_loader.get_function_definitions()
        print(f"✅ 함수 정의 로드: {len(functions)}개")
        
    except Exception as e:
        print(f"❌ import 실패: {str(e)}")

def main():
    """메인 디버깅 함수"""
    print("🚀 NaruTalk AI 시스템 디버깅 시작\n")
    
    check_environment()
    check_dependencies()
    check_file_structure()
    check_agent_files()
    test_imports()
    
    print("\n📋 디버깅 완료!")
    print("\n💡 다음 단계:")
    print("1. .env 파일에 OPENAI_API_KEY 설정")
    print("2. pip install -r requirements.txt")
    print("3. python debug_server.py (포트 8001)")
    print("4. 브라우저에서 http://localhost:8001 접속")

if __name__ == "__main__":
    main() 