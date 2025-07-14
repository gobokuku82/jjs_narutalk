# Database API 시스템 구조 및 개발 가이드

## 1. 시스템 개요

이 시스템은 독립적이고 협업 친화적인 사용자 및 문서 관리 모듈로 설계되었습니다. FastAPI 기반으로 구축되었으며, PostgreSQL(프로덕션)과 SQLite(로컬 테스트) 환경을 지원합니다.

### 1.1 주요 특징
- **환경 기반 DB 전환**: 환경변수를 통한 PostgreSQL/SQLite 자동 전환
- **JWT 기반 인증**: 안전한 토큰 기반 인증 시스템
- **역할 기반 접근 제어**: Admin/User 역할 구분
- **독립적 모듈**: 다른 시스템과 독립적으로 운영 가능

## 2. 현재 구현된 기능

### 2.1 사용자 관리 시스템
- **사용자 등록**: 이메일/비밀번호 기반 회원가입 (관리자만 가능)
- **사용자 로그인**: JWT 토큰 발급
- **초기 관리자 생성**: 1회성 관리자 계정 생성 API (`/user/init-admin`)
- **사용자 정보 조회**: 현재 로그인한 사용자 정보 조회

### 2.2 데이터베이스 구조
```sql
-- users 테이블
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    hashed_password VARCHAR NOT NULL,
    role VARCHAR NOT NULL,  -- 'admin' or 'user'
    is_active BOOLEAN DEFAULT TRUE
);
```

### 2.3 API 엔드포인트
- `POST /user/init-admin` - 초기 관리자 생성 (인증 불필요)
- `POST /user/register` - 사용자 등록 (관리자만 가능)
- `POST /user/login` - 사용자 로그인
- `GET /user/me` - 현재 사용자 정보 조회
- `GET /ping` - 헬스체크

## 3. 테스트 방법

### 3.1 환경 설정
```bash
# 1. conda 환경 활성화
conda activate test_db

# 2. 필요한 패키지 설치
pip install -r requirements.txt

# 3. 서버 실행
cd backend/app/database_api
python -m uvicorn db_api:app --reload --port 8000
```

### 3.2 초기 관리자 생성 테스트
```bash
# 1. 초기 관리자 계정 생성
curl -X POST "http://localhost:8000/user/init-admin" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "name": "관리자",
    "password": "admin123456",
    "role": "admin"
  }'
```

### 3.3 로그인 테스트
```bash
# 2. 관리자 로그인
curl -X POST "http://localhost:8000/user/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123456&grant_type=password"
```

### 3.4 사용자 등록 테스트
```bash
# 3. 토큰을 사용하여 일반 사용자 등록
curl -X POST "http://localhost:8000/user/register" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "일반사용자",
    "password": "user123456",
    "role": "user"
  }'
```

### 3.5 사용자 정보 조회 테스트
```bash
# 4. 현재 사용자 정보 조회
curl -X GET "http://localhost:8000/user/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 4. 향후 구현해야 할 기능

### 4.1 문서 관리 시스템
- [ ] **문서 업로드**: S3 호환 스토리지에 파일 저장
- [ ] **문서 메타데이터 관리**: PostgreSQL에 문서 정보 저장
- [ ] **문서 청킹**: 대용량 문서를 청크로 분할
- [ ] **임베딩 생성**: 문서 청크의 벡터 임베딩 생성
- [ ] **검색 시스템**: 벡터 유사도 기반 문서 검색

### 4.2 키워드 관리 시스템
- [ ] **키워드-문서 매핑**: 키워드와 문서 간 관계 저장
- [ ] **키워드 검색**: 키워드 기반 문서 검색
- [ ] **키워드 자동 추출**: 문서에서 키워드 자동 추출

### 4.3 고급 기능
- [ ] **문서 요약**: AI 기반 문서 요약 기능
- [ ] **관리자 대시보드**: pgAdmin, OpenSearch Dashboards 연동
- [ ] **권한 관리**: 세분화된 접근 권한 시스템
- [ ] **감사 로그**: 사용자 활동 추적

## 5. 데이터베이스 설계 (향후 구현)

### 5.1 PostgreSQL 테이블 구조
```sql
-- documents 테이블
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT,
    s3_url VARCHAR NOT NULL,
    file_type VARCHAR,
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- keywords 테이블
CREATE TABLE keywords (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- document_keywords 테이블 (매핑)
CREATE TABLE document_keywords (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    keyword_id INTEGER REFERENCES keywords(id),
    UNIQUE(document_id, keyword_id)
);

-- document_chunks 테이블
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    chunk_index INTEGER,
    content TEXT,
    embedding_id VARCHAR,  -- OpenSearch에서의 ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 OpenSearch 인덱스 구조
```json
{
  "mappings": {
    "properties": {
      "content": {"type": "text"},
      "embedding": {"type": "dense_vector", "dims": 1536},
      "document_id": {"type": "integer"},
      "chunk_index": {"type": "integer"},
      "metadata": {"type": "object"}
    }
  }
}
```

## 6. 개발 우선순위

### Phase 1: 기본 문서 관리 (1-2주)
1. S3 서비스 구현
2. 문서 업로드 API 구현
3. 문서 메타데이터 저장
4. 기본 문서 조회 기능

### Phase 2: 검색 시스템 (2-3주)
1. 문서 청킹 로직 구현
2. 임베딩 생성 서비스 구현
3. OpenSearch 연동
4. 벡터 검색 API 구현

### Phase 3: 키워드 시스템 (1-2주)
1. 키워드 추출 로직
2. 키워드-문서 매핑
3. 키워드 검색 기능

### Phase 4: 고급 기능 (2-3주)
1. 문서 요약 기능
2. 관리자 대시보드
3. 성능 최적화
4. 보안 강화

## 7. 보안 고려사항

### 7.1 현재 구현된 보안
- [x] 비밀번호 해싱 (bcrypt)
- [x] JWT 토큰 인증
- [x] 역할 기반 접근 제어
- [x] SQL 인젝션 방지 (SQLAlchemy ORM)

### 7.2 향후 구현할 보안
- [ ] 환경변수 기반 설정 관리
- [ ] API 요청 제한 (Rate Limiting)
- [ ] CORS 설정
- [ ] 입력 데이터 검증 강화
- [ ] 로그 보안

## 8. 모니터링 및 로깅

### 8.1 현재 상태
- [x] 기본 헬스체크 엔드포인트
- [ ] 구조화된 로깅 시스템
- [ ] 성능 모니터링
- [ ] 에러 추적

### 8.2 향후 구현
- [ ] 로그 레벨 설정
- [ ] 로그 파일 관리
- [ ] 메트릭 수집
- [ ] 알림 시스템

---

**마지막 업데이트**: 2024년 12월
**버전**: 1.0.0
**상태**: 사용자 관리 시스템 완료, 문서 관리 시스템 개발 예정 