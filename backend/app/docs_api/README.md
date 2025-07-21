# 문서 자동 작성 API 시스템

업무용 문서를 자동으로 분류하고 초안을 작성해주는 FastAPI 기반 시스템입니다.

## 시스템 구조

```
docs_api/
├── main.py              # FastAPI 서버 (통합)
├── classify_docs.py     # 문서 분류 에이전트
├── write_docs.py        # 문서 작성 에이전트
├── test_api.py          # API 테스트 파일
└── README.md           # 본 파일
```

## 파일 설명

### `main.py`
- **역할**: FastAPI 웹 서버의 메인 진입점
- **기능**: 
  - API 엔드포인트 정의 (`/api/docs/classify`, `/api/docs/write`)
  - 요청/응답 모델 정의 (Pydantic BaseModel)
  - 에이전트 인스턴스 생성 및 실행
  - 예외 처리 및 HTTP 응답 관리
- **실행**: `python main.py`로 서버 시작

### `classify_docs.py`
- **역할**: 문서 분류 전용 에이전트
- **기능**:
  - 사용자 입력 분석 ("영업방문 결과보고서를 작성해줘")
  - 문서 타입 자동 분류 (3가지 문서 타입 지원)
  - 해당 문서 타입의 템플릿 내용 반환
  - LangGraph StateGraph를 이용한 워크플로우 관리
- **주요 클래스**: `DocumentClassifyAgent`

### `write_docs.py`
- **역할**: 문서 초안 작성 전용 에이전트
- **기능**:
  - 사용자 입력을 구조화된 JSON 데이터로 변환
  - 문서 타입별 필드 매핑 (영업방문 결과보고서: 14개 필드)
  - 내부 규정 위반 검사 (Tool Calling 활용)
  - 파싱 실패 시 자동 재시도 (최대 3회)
  - 격식 있는 보고서 어투로 자동 변환
- **주요 클래스**: `DocumentDraftAgent`

### `test_api.py`
- **역할**: API 테스트 스크립트
- **기능**:
  - 전체 워크플로우 테스트 (분류 → 작성)
  - 실제 데이터로 API 동작 검증
  - 요청/응답 로그 출력
- **사용법**: `python test_api.py`
- **테스트 시나리오**: 영업방문 결과보고서 작성 과정

## API 엔드포인트

### 1. 문서 분류 API (`/api/docs/classify`)

**기능**: 사용자 요청을 분석하여 문서 타입을 분류하고 템플릿 제공

**입력**:
```json
{
  "user_input": "영업방문 결과보고서를 작성해줘"
}
```

**출력**:
```json
{
  "success": true,
  "state": {
    "messages": [...],
    "doc_type": "영업방문 결과보고서",
    "template_content": "영업방문 결과보고서 작성을 위해 다음 정보를 입력해주세요:\n【기본 정보】\n- 방문 제목:\n- Client(고객사명):\n...",
    "filled_data": null,
    "violation": null,
    "final_doc": null,
    "retry_count": 0,
    "restart_classification": null,
    "classification_retry_count": 0
  },
  "error": null
}
```

### 2. 문서 작성 API (`/api/docs/write`)

**기능**: 분류된 문서 타입과 사용자 입력을 기반으로 구조화된 문서 데이터 생성

**입력**:
```json
{
  "state": {
    "doc_type": "영업방문 결과보고서",
    "template_content": "...",
    ...
  },
  "user_input": "고객은 아이유이비인후과, 담당자와 방문자는 손현성, 방문자 소속은 좋은제약이야. 연락처는 010-3752-5265이고..."
}
```

**출력**:
```json
{
  "success": true,
  "filled_data": {
    "방문제목": "",
    "고객사명": "아이유이비인후과",
    "담당자": "손현성",
    "방문Site": "",
    "담당자소속": "",
    "연락처": "010-3752-5265",
    "영업제공자": "",
    "방문자": "손현성",
    "방문자소속": "좋은제약",
    "고객사개요": "최근 오픈한 이비인후과입니다",
    "프로젝트개요": "신약 거래처 확보",
    "방문및협의내용": "25년 7월 16일 방문하여 새로운 신약 소개 및 가격과 로얄티를 소개하였습니다",
    "향후계획및일정": "25년 7월 18일 방문하여 가격 협상 및 로얄티 협상을 진행할 예정입니다",
    "협조사항및공유사항": ""
  },
  "error": null
}
```

## 지원 문서 타입

### 1. 영업방문 결과보고서
- **필드**: 방문제목, 고객사명, 담당자, 방문Site, 담당자소속, 연락처, 영업제공자, 방문자, 방문자소속, 고객사개요, 프로젝트개요, 방문및협의내용, 향후계획및일정, 협조사항및공유사항

### 2. 제품설명회 시행 신청서
- **필드**: 구분단일복수, 일시, 제품명, PM참석, 장소, 참석인원, 제품설명회시행목적, 제품설명회주요내용, 직원팀명이름, 의료기관명이름

### 3. 제품설명회 시행 결과보고서
- **필드**: 구분단일복수, 일시, 제품명, PM참석, 장소, 참석인원, 제품설명회시행목적, 제품설명회주요내용, 직원팀명이름, 의료기관명이름, 금액, 메뉴, 주류, 일인금액

## 에이전트 상세

### DocumentClassifyAgent (`classify_docs.py`)
- **역할**: 사용자 요청을 분석하여 문서 타입 분류
- **기술**: LangGraph StateGraph, OpenAI GPT-4o-mini
- **처리 과정**: 
  1. 사용자 입력 분석
  2. 문서 타입 분류
  3. 해당 타입의 템플릿 내용 반환

### DocumentDraftAgent (`write_docs.py`)
- **역할**: 사용자 입력을 구조화된 문서 데이터로 변환
- **기술**: LangGraph StateGraph, OpenAI GPT-4o-mini, Tool Calling
- **처리 과정**:
  1. 사용자 입력 파싱 (JSON 구조화)
  2. 내부 규정 위반 검사
  3. 구조화된 데이터 반환
  4. 실패 시 재시도 (최대 3회)

## 실행 방법

### 1. 서버 시작
```bash
python main.py
```
서버는 `http://localhost:8000`에서 실행됩니다.

### 2. API 테스트
```bash
python test_api.py
```

### 3. 직접 요청 예시
```bash
# 1단계: 문서 분류
curl -X POST "http://localhost:8000/api/docs/classify" \
     -H "Content-Type: application/json" \
     -d '{"user_input": "영업방문 결과보고서를 작성해줘"}'

# 2단계: 문서 작성 (분류 결과의 state 사용)
curl -X POST "http://localhost:8000/api/docs/write" \
     -H "Content-Type: application/json" \
     -d '{"state": {...}, "user_input": "고객은 아이유이비인후과..."}'
```

## 기술 스택

- **웹 프레임워크**: FastAPI
- **AI 모델**: OpenAI GPT-4o-mini
- **워크플로우**: LangGraph StateGraph
- **언어**: Python
- **환경 관리**: python-dotenv

## 환경 설정

`.env` 파일에 OpenAI API 키를 설정해야 합니다:
```
OPENAI_API_KEY=your_api_key_here
```

## 주요 특징

- 🤖 **AI 기반 문서 분류 및 작성**
- 📋 **구조화된 JSON 출력**
- 🔍 **내부 규정 자동 검토**
- 🔄 **자동 재시도 메커니즘**
- 📄 **다양한 문서 유형 지원**
- 🚀 **REST API 인터페이스**