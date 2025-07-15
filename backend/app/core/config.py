from pydantic_settings import BaseSettings
from typing import Optional, ClassVar, List
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트에서 찾기)
project_root = Path(__file__).parent.parent.parent.parent
env_file = project_root / ".env"

# 디버깅을 위한 로그
print(f"🔍 .env 파일 경로: {env_file}")
print(f"🔍 .env 파일 존재: {env_file.exists()}")

if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ .env 파일 로드 완료: {env_file}")
else:
    # .env 파일이 없으면 현재 디렉토리에서 찾기
    load_dotenv()
    print("⚠️  프로젝트 루트에 .env 파일이 없어 현재 디렉토리에서 로드 시도")

# 환경변수 디버깅
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"✅ OPENAI_API_KEY 로드됨: {api_key[:10]}...")
else:
    print("❌ OPENAI_API_KEY 로드 실패")

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    app_name: str = "NaruTalk AI 챗봇"
    debug: bool = True
    
    # 프로젝트 루트 경로
    project_root: ClassVar[Path] = Path(__file__).parent.parent.parent.parent
    
    # OpenAI 설정
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 1000
    openai_timeout: int = 30
    
    # HuggingFace 설정
    huggingface_token: Optional[str] = os.getenv("HUGGINGFACE_TOKEN")
    
    # 허깅페이스 모델 ID (로컬 모델 대신 사용)
    embedding_model_id: str = "nlpai-lab/KURE-v1"  # 한국어 특화 임베딩 모델
    reranker_model_id: str = "dragonkue/bge-reranker-v2-m3-ko"  # 한국어 특화 리랭커 모델
    
    # 모델 사용 방식 설정
    use_huggingface_models: bool = True  # 허깅페이스 모델 사용 여부
    
    # 모델 경로 (호환성 유지용 - 허깅페이스 모델 사용 시 무시됨)
    embedding_model_path: str = str(project_root / "models" / "KURE-V1")
    reranker_model_path: str = str(project_root / "models" / "bge-reranker-v2-m3-ko")
    
    # 데이터베이스 설정 (절대 경로)
    chroma_db_path: str = str(project_root / "database" / "chroma_db")
    sqlite_db_path: str = str(project_root / "database" / "relationdb")
    
    # 랭그래프 설정
    langgraph_debug: bool = True
    
    # 라우터 시스템 설정
    available_routers: List[str] = [
        "qa_router",
        "document_search_router", 
        "employee_info_router",
        "general_chat_router",
        "analysis_router",
        "report_generator_router"
    ]
    
    router_confidence_threshold: float = 0.5
    max_router_switches: int = 5
    
    # API 설정
    api_v1_prefix: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 추가 필드 무시

# 설정 인스턴스 생성
settings = Settings() 