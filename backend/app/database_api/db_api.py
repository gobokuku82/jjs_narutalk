from fastapi import FastAPI, UploadFile, File, Form
from .services import s3_service, postgres_service
from .schemas.document import DocumentMeta

app = FastAPI()

@app.get("/ping")
def ping():
    return {"message": "pong"}

# 1. 문서 업로드
@app.post("/upload-document/")
def upload_document(file: UploadFile = File(...), title: str = Form(...), description: str = Form("")):
    # 1. S3에 파일 업로드
    s3_url = s3_service.upload_file(file)
    # 2. PostgreSQL에 메타데이터 저장
    meta = DocumentMeta(title=title, description=description, s3_url=s3_url)
    postgres_service.save_metadata(meta)
    return {"message": "Document uploaded", "s3_url": s3_url}

# 2. 문서-키워드 매핑
@app.post("/map-keywords/")
def map_keywords(document_id: int, keywords: List[str]):
    # TODO: 키워드-문서 매핑 저장 (PostgreSQL)
    return {"message": "Keywords mapped"}

# 3. 테이블 데이터 적재
@app.post("/upload-table/")
def upload_table(file: UploadFile = File(...)):
    # TODO: 테이블 데이터 파싱 및 PostgreSQL 저장
    return {"message": "Table data uploaded"}

# 4. 문서 청크/임베딩 및 매핑
@app.post("/chunk-embed/")
def chunk_and_embed(document_id: int):
    # TODO: 문서 청크 분할, 임베딩 생성, 매핑 정보 저장
    return {"message": "Document chunked and embedded"}

# 5. 쿼리로 청크 검색
@app.post("/search-chunks/")
def search_chunks(query: str):
    # TODO: 쿼리 임베딩, OpenSearch에서 유사 청크 검색
    return {"chunks": []}

# 6. 청크의 원본 문서 반환
@app.get("/chunk-original/")
def get_chunk_original(chunk_id: int):
    # TODO: 청크-문서 매핑 정보로 원본 문서 반환
    return {"document": {}}

# 7. 키워드로 문서 검색
@app.get("/search-by-keyword/")
def search_by_keyword(keyword: str):
    # TODO: 키워드-문서 매핑 테이블에서 문서 검색
    return {"documents": []}

# 8. 문서 요약
@app.post("/summarize/")
def summarize(document_ids: List[int]):
    # TODO: 문서/청크 내용 요약
    return {"summary": "요약 결과"}

# 9. 관리자용 pgAdmin/Opensearch Dashboards 안내
@app.get("/admin/pgadmin-url/")
def get_pgadmin_url():
    # TODO: 관리자 인증 후 URL 안내
    return {"url": "http://localhost:5050"}

@app.get("/admin/opensearch-dashboards-url/")
def get_opensearch_dashboards_url():
    # TODO: 관리자 인증 후 URL 안내
    return {"url": "http://localhost:5601"} 