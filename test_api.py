#!/usr/bin/env python3
"""
API 테스트 스크립트
"""

import requests
import json

def test_health():
    """헬스 체크 테스트"""
    try:
        response = requests.get("http://localhost:8000/api/v1/health")
        print(f"헬스 체크 상태: {response.status_code}")
        print(f"응답: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"헬스 체크 실패: {e}")
        return False

def test_system_info():
    """시스템 정보 테스트"""
    try:
        response = requests.get("http://localhost:8000/api/v1/system/info")
        print(f"시스템 정보 상태: {response.status_code}")
        print(f"응답: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"시스템 정보 실패: {e}")
        return False

def test_chat():
    """채팅 API 테스트"""
    try:
        data = {
            "message": "안녕하세요",
            "session_id": "test_session",
            "user_id": "test_user"
        }
        response = requests.post("http://localhost:8000/api/v1/tool-calling/chat", json=data)
        print(f"채팅 API 상태: {response.status_code}")
        print(f"응답: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"채팅 API 실패: {e}")
        return False

def main():
    print("🚀 API 테스트 시작\n")
    
    print("1. 헬스 체크 테스트")
    health_ok = test_health()
    print()
    
    print("2. 시스템 정보 테스트")
    system_ok = test_system_info()
    print()
    
    print("3. 채팅 API 테스트")
    chat_ok = test_chat()
    print()
    
    print("📋 테스트 결과:")
    print(f"헬스 체크: {'✅' if health_ok else '❌'}")
    print(f"시스템 정보: {'✅' if system_ok else '❌'}")
    print(f"채팅 API: {'✅' if chat_ok else '❌'}")

if __name__ == "__main__":
    main() 