import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

APP_ENV = os.getenv("APP_ENV", "test")  # 기본값은 test

if APP_ENV == "prod":
    # 실제 서비스용 PostgreSQL (docker-compose 환경에 맞게 수정)
    SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"
else:
    # 항상 database_api 폴더 하위에 users.db 생성
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'users.db')}"

print(f"✅ DB 연결 타입: {APP_ENV} ({SQLALCHEMY_DATABASE_URL})")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if APP_ENV != "prod" else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base() 