#!/usr/bin/env python3
"""
백엔드 스트리밍 API 단독 테스트 (sequential thinking 1단계)
"""
import requests
import json

def test_stream():
    url = "http://localhost:8000/api/v1/tool-calling/chat/stream"
    payload = {
        "message": "미라클신경과 실적분석해줘",
        "session_id": "test_seq_stream",
        "user_id": "test_user"
    }
    print(f"[요청] {url}")
    print(f"[Payload] {json.dumps(payload, ensure_ascii=False)}")
    resp = requests.post(url, json=payload, stream=True)
    print(f"[응답코드] {resp.status_code}")
    print(f"[응답헤더] {dict(resp.headers)}")
    print("[스트리밍 데이터]")
    for line in resp.iter_lines():
        if line:
            print(line.decode('utf-8'))
    print("[테스트 종료]")

if __name__ == "__main__":
    test_stream() 