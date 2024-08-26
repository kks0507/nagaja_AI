from transformers import pipeline
import requests
from bs4 import BeautifulSoup
import pymysql
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 감정 분석 파이프라인 로드
sentiment_pipeline = pipeline('sentiment-analysis', model="distilbert-base-uncased-finetuned-sst-2-english")

# 영화 정보를 스크래핑하는 함수
def get_movie_details(movie_url):
    response = requests.get(movie_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    title = soup.select_one('div.box-contents > div.title > strong').text.strip()
    poster_url = soup.select_one('div.box-image > a > span.thumb-image > img')['src']

    try:
        director = soup.select_one("dt:-soup-contains('감독') + dd > a").text.strip()
    except AttributeError:
        director = None
    
    try:
        actors = ", ".join([actor.text.strip() for actor in soup.select("dt:-soup-contains('배우') + dd > a")])
    except AttributeError:
        actors = None

    rating = soup.select_one('div.score > strong.percent > span').text.strip()

    return title, poster_url, director, actors, rating

# 영화 리뷰를 스크래핑하는 함수
def get_movie_reviews_selenium(movie_url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(movie_url)
    
    review_elements = driver.find_elements(By.CLASS_NAME, 'box-comment')
    reviews = [review.text.strip() for review in review_elements[:6]]  # 최대 6개 댓글만 가져옴
    
    driver.quit()
    return reviews

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

# 영화 데이터를 삽입하는 함수
def insert_movie_data(movie_data):
    insert_query = """
    INSERT INTO movie (title, poster_url, director, cast, rating, review_summary, reviews, emotion_rating)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    insert_into_db(insert_query, movie_data)

# 영화 목록 페이지에서 링크 추출 (상위 10개 영화)
def get_movie_links(movie_list_url):
    response = requests.get(movie_list_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    contents = soup.select('div.sect-movie-chart div.box-contents')
    movie_links = ["http://www.cgv.co.kr" + content.find('a')['href'] for content in contents[:10]]  # 상위 10개 영화만
    return movie_links

# 메인 스크래핑 및 데이터 처리 함수
movie_list_url = "http://www.cgv.co.kr/movies/?lt=1&ot=3"
movie_links = get_movie_links(movie_list_url)

# 스크래핑한 데이터를 분석하기 위해 사전 형태로 저장
movies_info = []

# 각 영화의 데이터를 가져오고 데이터베이스에 삽입
for link in movie_links:
    title, poster_url, director, cast, rating = get_movie_details(link)
    reviews = get_movie_reviews_selenium(link)

    if reviews:
        combined_comments, summary, emotion_rating = calculate_emotion_score(reviews)
    else:
        combined_comments, summary, emotion_rating = None, None, None

    movie_data = (
        title,
        poster_url,
        director,
        cast,
        rating,
        summary,
        combined_comments,
        emotion_rating
    )
    
    insert_movie_data(movie_data)
    movies_info.append(movie_data)

# 확인용 출력
for movie in movies_info:
    print("MOVIE {")
    print(f"    title: {movie[0]}")
    print(f"    posterUrl: {movie[1]}")
    print(f"    director: {movie[2]}")
    print(f"    cast: {movie[3]}")
    print(f"    rating: {movie[4]}")
    print(f"    reviewSummary: {movie[5]}")
    print(f"    reviews: {movie[6]}")
    print(f"    emotionRating: {movie[7]}")
    print("}")
    print("="*70)

