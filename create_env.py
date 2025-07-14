#!/usr/bin/env python3
"""
.env 파일 생성 스크립트
"""

import os
from pathlib import Path

def create_env_file():
    """프로젝트 루트에 .env 파일 생성"""
    
    # 프로젝트 루트 경로
    project_root = Path(__file__).parent
    
    # .env 파일 경로
    env_file = project_root / ".env"
    
    # .env 파일이 이미 존재하는지 확인
    if env_file.exists():
        print(f"⚠️  .env 파일이 이미 존재합니다: {env_file}")
        print("기존 파일을 백업하고 새로 생성하시겠습니까? (y/N): ", end="")
        response = input().strip().lower()
        if response != 'y':
            print("취소되었습니다.")
            return
    
    # .env 파일 내용
    env_content = """# ===============================
# NaruTalk AI 챗봇 환경 설정
# ===============================

# OpenAI API 설정
OPENAI_API_KEY=sk-your-openai-api-key-here

# HuggingFace 설정 (선택사항)
HUGGINGFACE_TOKEN=your-huggingface-token-here

# 애플리케이션 설정
DEBUG=true
APP_NAME=NaruTalk AI 챗봇

# 데이터베이스 설정
CHROMA_DB_PATH=database/chroma_db
SQLITE_DB_PATH=database/relationdb

# LangGraph 설정
LANGGRAPH_DEBUG=true

# API 설정
API_V1_PREFIX=/api/v1
"""
    
    try:
        # .env 파일 생성
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print(f"✅ .env 파일이 생성되었습니다: {env_file}")
        print("\n📝 다음 단계:")
        print("1. .env 파일을 열어서 OPENAI_API_KEY를 실제 키로 변경하세요")
        print("2. 서버를 다시 시작하세요")
        print("\n⚠️  주의: .env 파일은 .gitignore에 포함되어 있어야 합니다!")
        
    except Exception as e:
        print(f"❌ .env 파일 생성 실패: {str(e)}")

if __name__ == "__main__":
    create_env_file() 