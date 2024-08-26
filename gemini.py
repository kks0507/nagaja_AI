import os
import mysql.connector
import google.generativeai as genai

# Google Gemini API 키 설정 (실제 API 키로 교체해야 합니다)
api_key = "YOUR_GEMINI_KEY"  # 여기에 실제 제미나이 API 키를 입력하세요
genai.configure(api_key=api_key)

# Google Gemini 모델 설정
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction=(
        "너는 입력된 댓글의 감정을 분석해서 긍정적인 부분과 부정적인 부분을 나누어 350자 이내로 총평해주는 AI야.\n\n"
        "### 출력 예시\n총평:\n댓글은 범죄도시 4편에 대한 긍정적, 부정적 평가가 혼재되어 있습니다. "
        "특히 장이수 캐릭터에 대한 호평이 많지만, 영화 내용, 빌런 캐릭터, 팀워크 등에 대한 비판도 존재합니다. "
        "긍정적인 부분은 주로 배우들의 연기력과 영화가 주는 재미에 대한 것들이고, 부정적인 부분은 내용의 반복성, "
        "캐릭터 매력 부족 등에 대한 것들입니다.\n전반적으로 범죄도시 4편은 호불호가 갈리는 영화라는 것을 알 수 있습니다."
    ),
)

# 리뷰 데이터를 분석하는 함수
def analyze_review(review):
    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [review],
            },
        ]
    )
    response = chat_session.send_message("Analyze this review")
    return response.text

# 분석된 요약을 DB에 업데이트하는 함수
def update_review_summary_in_db(review_summary, restaurant_id):
    update_query = """
    UPDATE restaurant
    SET review_summary = %s
    WHERE id = %s
    """
    insert_into_db(update_query, (review_summary, restaurant_id))

# 전체 리뷰 데이터를 처리하는 함수
def process_reviews():
    # MariaDB에 연결
    db = mysql.connector.connect(
        host="127.0.0.1",
        user="boot",  # Docker MariaDB 사용자 이름
        password="boot",  # Docker MariaDB 사용자 비밀번호
        database="boot_db"  # 사용할 데이터베이스 이름
    )
    cursor = db.cursor()

    # RESTAURANT 테이블에서 리뷰를 가져옴
    cursor.execute("SELECT id, reviews FROM restaurant")
    restaurants = cursor.fetchall()

    for restaurant in restaurants:
        restaurant_id, reviews = restaurant
        if reviews:
            # 리뷰를 Google Gemini API로 분석
            review_summary = analyze_review(reviews)
            # 분석 결과를 DB에 업데이트
            update_review_summary_in_db(review_summary, restaurant_id)

    cursor.close()
    db.close()

# 데이터베이스에 삽입하는 함수 (기존 코드 재사용)
def insert_into_db(query, data):
    try:
        db = mysql.connector.connect(
            host="127.0.0.1",
            user="boot",  # Docker MariaDB 사용자 이름
            password="boot",  # Docker MariaDB 사용자 비밀번호
            database="boot_db"  # 사용할 데이터베이스 이름
        )
        cursor = db.cursor()
        cursor.execute(query, data)
        db.commit()
        print("Data updated successfully")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

# 실행
process_reviews()


