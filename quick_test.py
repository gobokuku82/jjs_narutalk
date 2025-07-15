#!/usr/bin/env python3
import requests
import json

def test_api():
    print("🔍 API 엔드포인트 빠른 테스트")
    
    # 1. 기본 엔드포인트 확인
    try:
        response = requests.get("http://localhost:8000/api/v1/health")
        print(f"✅ /api/v1/health: {response.status_code}")
        if response.status_code == 200:
            print(f"   응답: {response.json()}")
    except Exception as e:
        print(f"❌ /api/v1/health 실패: {e}")
    
    # 2. tool-calling 헬스체크
    try:
        response = requests.get("http://localhost:8000/api/v1/tool-calling/health")
        print(f"✅ /api/v1/tool-calling/health: {response.status_code}")
        if response.status_code == 200:
            print(f"   응답: {response.json()}")
    except Exception as e:
        print(f"❌ /api/v1/tool-calling/health 실패: {e}")
    
    # 3. 채팅 엔드포인트 테스트
    try:
        data = {"message": "안녕하세요", "session_id": "test123"}
        response = requests.post("http://localhost:8000/api/v1/tool-calling/chat", json=data)
        print(f"✅ /api/v1/tool-calling/chat: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   응답: {result.get('response', 'No response')[:50]}...")
        else:
            print(f"   오류: {response.text}")
    except Exception as e:
        print(f"❌ /api/v1/tool-calling/chat 실패: {e}")

if __name__ == "__main__":
    test_api() 