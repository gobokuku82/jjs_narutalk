#!/usr/bin/env python3
"""
스트리밍 API 테스트 스크립트
"""

import requests
import json
import time

def test_streaming_api():
    """스트리밍 API 테스트"""
    try:
        print("🔄 스트리밍 API 테스트 시작...")
        
        data = {
            "message": "3~6월 실적 패턴 분석해줘",
            "session_id": "test_stream_session",
            "user_id": "test_user"
        }
        
        print(f"📤 요청 데이터: {json.dumps(data, ensure_ascii=False)}")
        
        # 스트리밍 요청
        response = requests.post(
            "http://localhost:8000/api/v1/tool-calling/chat/stream",
            json=data,
            stream=True,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📥 응답 상태: {response.status_code}")
        print(f"📥 응답 헤더: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"❌ 오류 응답: {response.text}")
            return False
        
        print("📡 스트리밍 데이터 수신 중...")
        
        # 스트리밍 데이터 읽기
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                print(f"📨 원본 라인: {line_str}")
                
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # 'data: ' 제거
                    
                    if data_str == '[DONE]':
                        print("✅ 스트리밍 완료")
                        break
                    
                    try:
                        data_obj = json.loads(data_str)
                        print(f"📋 파싱된 데이터: {json.dumps(data_obj, ensure_ascii=False, indent=2)}")
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON 파싱 오류: {e}, 데이터: {data_str}")
        
        return True
        
    except Exception as e:
        print(f"❌ 스트리밍 API 테스트 실패: {e}")
        return False

def test_regular_api():
    """일반 API 테스트"""
    try:
        print("\n🔄 일반 API 테스트 시작...")
        
        data = {
            "message": "3~6월 실적 패턴 분석해줘",
            "session_id": "test_regular_session",
            "user_id": "test_user"
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/tool-calling/chat",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📥 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📋 응답 데이터: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"❌ 오류 응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 일반 API 테스트 실패: {e}")
        return False

def main():
    print("🚀 API 테스트 시작\n")
    
    print("1. 스트리밍 API 테스트")
    streaming_ok = test_streaming_api()
    print()
    
    print("2. 일반 API 테스트")
    regular_ok = test_regular_api()
    print()
    
    print("📋 테스트 결과:")
    print(f"스트리밍 API: {'✅' if streaming_ok else '❌'}")
    print(f"일반 API: {'✅' if regular_ok else '❌'}")

if __name__ == "__main__":
    main() 