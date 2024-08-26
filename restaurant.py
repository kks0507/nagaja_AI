from transformers import pipeline
import requests
from bs4 import BeautifulSoup
import pymysql

# 감정 분석 파이프라인 로드
sentiment_pipeline = pipeline('sentiment-analysis')

# 식당 정보를 스크래핑하는 함수
def restaurant(query):
    headers = {
        'Referer': 'https://search.naver.com'
    }
    url = f'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query={query}'
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    if res.ok:
        print("ok")

    titles = soup.find_all("span", class_="place_bluelink TYaxT")
    reviews = soup.find_all("div", class_="u4vcQ")
    posters = [img.find("img")['src'] for img in soup.find_all("a", class_="place_thumb")]
    foodTypes = soup.find_all("span", class_="KCMnt")

    titles_text = [title.get_text(strip=True) for title in titles]
    reviews_text = [review.get_text(strip=True) for review in reviews]
    foodTypes_text = [foodType.get_text(strip=True) for foodType in foodTypes]

    # 스크래핑된 데이터의 개수 출력
    print(f"Titles: {len(titles_text)}")
    print(f"Posters: {len(posters)}")
    print(f"Food Types: {len(foodTypes_text)}")
    print(f"Reviews: {len(reviews_text)}")

    return titles_text, posters, foodTypes_text, reviews_text

# 감정 점수를 계산하고 리뷰를 요약하는 함수
def calculate_emotion_score(comments):
    combined_comments = " | ".join(comments)
    scores = []
    summary = " ".join(comments[:2])  # 리뷰의 요약 (첫 두 개의 리뷰를 사용)

    for comment in comments:
        result = sentiment_pipeline(comment)[0]
        if result['label'] == 'POSITIVE':
            scores.append(result['score'] * 100)
        else:
            scores.append((1 - result['score']) * 100)
    
    emotion_rating = int(sum(scores) / len(scores)) if scores else None
    
    return combined_comments, summary, emotion_rating

# MariaDB에 데이터 삽입 함수
def insert_into_db(query, data):
    try:
        conn = pymysql.connect(
            host="127.0.0.1",
            user="boot",
            password="boot",
            db="boot_db",
            charset='utf8',
            port=3306
        )
        cursor = conn.cursor()
        cursor.execute(query, data)
        conn.commit()
        print(f"Data inserted successfully: {data}")
    except pymysql.MySQLError as err:
        print(f"Error inserting data: {data}")
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 식당 데이터를 삽입하는 함수
def insert_restaurant_data(restaurant_data):
    insert_query = """
    INSERT INTO restaurant (name, poster_url, food_type, review_summary, reviews, emotion_rating)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    insert_into_db(insert_query, restaurant_data)

# 메인 스크래핑 및 데이터 처리 함수
query = "해운대맛집"
titles, posters, foodTypes, reviews = restaurant(query)

# 스크래핑한 데이터를 분석하기 위해 사전 형태로 저장
restaurants_info = []

# 각 식당의 댓글을 추가하고 데이터베이스에 삽입
for i, title in enumerate(titles):
    restaurant_data = {
        "name": title,
        "posterUrl": posters[i] if i < len(posters) else None,
        "foodType": foodTypes[i] if i < len(foodTypes) else None,
        "reviewSummary": None,
        "reviews": None,
        "emotionRating": None
    }

    comments = []
    for j in range(3):  # 각 식당당 최대 3개의 리뷰만 사용
        index = i * 3 + j
        if index < len(reviews):
            comments.append(reviews[index])
        else:
            break
    
    if comments:
        combined_comments, summary, emotion_rating = calculate_emotion_score(comments)
        restaurant_data["reviews"] = combined_comments
        restaurant_data["reviewSummary"] = summary
        restaurant_data["emotionRating"] = emotion_rating
    
    # 데이터베이스에 삽입
    restaurant_tuple = (
        restaurant_data['name'],
        restaurant_data['posterUrl'],
        restaurant_data['foodType'],
        restaurant_data['reviewSummary'],
        restaurant_data['reviews'],
        restaurant_data['emotionRating']
    )
    insert_restaurant_data(restaurant_tuple)
    restaurants_info.append(restaurant_data)

# 확인용 출력
for restaurant in restaurants_info:
    print("RESTAURANT {")
    print(f"    name: {restaurant['name']}")
    print(f"    posterUrl: {restaurant['posterUrl']}")
    print(f"    foodType: {restaurant['foodType']}")
    print(f"    reviewSummary: {restaurant['reviewSummary']}")
    print(f"    reviews: {restaurant['reviews']}")
    print(f"    emotionRating: {restaurant['emotionRating']}")
    print("}")
    print("="*70)




