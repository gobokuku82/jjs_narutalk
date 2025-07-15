#!/usr/bin/env python3
"""
API 엔드포인트 테스트 스크립트
"""

import requests
import json

def test_endpoint(url, method="GET", data=None):
    """엔드포인트 테스트"""
    try:
        print(f"\n🔍 테스트: {method} {url}")
        
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        print(f"✅ 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                print(f"📄 응답 타입: {type(json_data)}")
                if isinstance(json_data, dict) and len(json_data) < 10:
                    print(f"📄 응답 내용: {json_data}")
                else:
                    print(f"📄 응답 키: {list(json_data.keys()) if isinstance(json_data, dict) else '문자열 응답'}")
            except:
                print(f"📄 응답 내용 (텍스트): {response.text[:200]}...")
        else:
            print(f"❌ 오류: {response.text}")
            
    except Exception as e:
        print(f"❌ 요청 실패: {str(e)}")

def main():
    base_url = "http://localhost:8000"
    
    print("🚀 NaruTalk API 엔드포인트 테스트")
    print("=" * 50)
    
    # 기본 엔드포인트들
    test_endpoint(f"{base_url}/")
    test_endpoint(f"{base_url}/docs")
    test_endpoint(f"{base_url}/api/v1/health")
    test_endpoint(f"{base_url}/api/v1/system/info")
    
    # Tool Calling 관련 엔드포인트들
    test_endpoint(f"{base_url}/api/v1/tool-calling/health")
    test_endpoint(f"{base_url}/api/v1/tool-calling/agents")
    
    # 채팅 엔드포인트 (POST)
    chat_data = {
        "message": "안녕하세요! 테스트 메시지입니다.",
        "session_id": "test_session_123"
    }
    
    test_endpoint(f"{base_url}/api/v1/tool-calling/chat", "POST", chat_data)
    
    # 스트리밍 엔드포인트 (POST) - 일부만 확인
    print(f"\n🔍 스트리밍 테스트: POST {base_url}/api/v1/tool-calling/chat/stream")
    try:
        response = requests.post(
            f"{base_url}/api/v1/tool-calling/chat/stream", 
            json=chat_data, 
            stream=True,
            timeout=10
        )
        print(f"✅ 스트리밍 상태 코드: {response.status_code}")
        print(f"📄 응답 헤더: {dict(response.headers)}")
        
        # 첫 번째 청크만 확인
        if response.status_code == 200:
            for i, chunk in enumerate(response.iter_content(chunk_size=1024, decode_unicode=True)):
                if chunk:
                    print(f"📄 청크 {i+1}: {chunk[:100]}...")
                if i >= 2:  # 처음 3개 청크만 확인
                    break
        
    except Exception as e:
        print(f"❌ 스트리밍 요청 실패: {str(e)}")

if __name__ == "__main__":
    main() 