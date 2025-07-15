from tools import Tools

def main():
    # Get_Keyword 인스턴스 생성
    keyword_extractor = Tools()
    
    # 사용자 입력 받기
    user_input = input("키워드를 추출할 질문을 입력하세요: ")
    
    # 키워드 추출
    keywords = keyword_extractor.get_keyword(user_input)

    # 결과 출력
    print("추출된 키워드: ", keywords)

if __name__ == "__main__":
    main()