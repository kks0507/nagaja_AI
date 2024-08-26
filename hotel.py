from transformers import pipeline, DistilBertTokenizerFast
import requests
from bs4 import BeautifulSoup
import mysql.connector
import os
import json
import re
import math

# 감정 분석 파이프라인 로드
sentiment_pipeline = pipeline('sentiment-analysis')
tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')

# 리뷰 토큰 수 제한 함수
def truncate_review(review, max_length=512):
    tokens = tokenizer(review, truncation=True, max_length=max_length, return_tensors="pt")
    truncated_review = tokenizer.decode(tokens['input_ids'][0], skip_special_tokens=True)
    return truncated_review

# 리뷰 감정 분석 및 종합 리뷰 생성 함수
def aggregate_reviews(comments):
    all_comments = []
    scores = []
    
    for comment in comments[:5]:  # 리뷰 수를 최대 5개로 제한
        truncated_comment = truncate_review(comment)
        result = sentiment_pipeline(truncated_comment)[0]
        score = result['score']
        
        all_comments.append(truncated_comment)
        if result['label'] == 'POSITIVE':
            scores.append(score * 100)
        else:
            scores.append((1 - score) * 100)
    
    return " | ".join(all_comments), int(sum(scores) / len(scores)) if scores else "NULL"

# MariaDB에 데이터 삽입 함수
def insert_into_db(query, data):
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="boot",  # 사용자 이름
            password="boot",  # 비밀번호
            database="boot_db"  # 데이터베이스 이름
        )
        cursor = db.cursor()
        cursor.execute(query, data)
        db.commit()
        print("Data inserted successfully")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

# 호텔 데이터를 삽입하는 함수
def insert_hotel_data(hotel_data):
    insert_query = """
    INSERT INTO hotel (name, poster_url, location, detailed_url, reviews, emotion_rating)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    insert_into_db(insert_query, hotel_data)

# 호텔 정보를 스크래핑하고 DB에 저장하는 함수
def scrapHotel():
    item_limit = 10  # 호텔 수를 10개로 제한
    review_limit = 2  # 리뷰 수를 최대 5개로 제한
    review_sort_opt = 0
    review_sort = ["highRankingScore", "latest"]

    base_url = "https://www.yeogi.com/domestic-accommodations"
    req_header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
    }
    keywords = [
        "제주도"  # 제주도만 검색하도록 설정
    ]

    all_scraped_list = {}
    for keyword in keywords:
        print(f'* Scrap from "{keyword}".')
        url = base_url + "?keyword=" + keyword
        res = requests.get(url, headers=req_header, timeout=10)  # 타임아웃 설정
        if res.ok:
            soup = BeautifulSoup(res.text, "html.parser")
            json_script_page = soup.body.find('script', type='application/json', id='__NEXT_DATA__')
            if json_script_page:
                data_content = json.loads(json_script_page.string)
                total_count = data_content['props']['pageProps']['paginationInfo']['totalCount']
                total_iter = math.ceil((min(total_count, item_limit) if item_limit > 0 else total_count) / 20)
                print(f'Total results: {total_count}, Iterations needed: {total_iter}')
        else:
            print(f'*** Error: {res}')
            continue
        
        scraped_list = []
        for page in range(total_iter):
            print(f'Scraping page {page + 1} of {total_iter}')
            res = requests.get(url + "&page=" + str(page), headers=req_header, timeout=10)
            if res.ok:
                soup = BeautifulSoup(res.text, "html.parser")
                json_ld_script = soup.find('script', type='application/ld+json')
                if json_ld_script:
                    json_content = json.loads(json_ld_script.string)
                    item_list = json_content['mainEntity']['itemListElement']
                    list_from_a_page = []
                    for item in item_list:
                        accom = item['item']
                        name = accom['name']
                        address = accom['address']['addressLocality']
                        rating_val = accom['aggregateRating']
                        rating = rating_val['ratingValue'] if rating_val else '-'
                        price_str = accom['priceRange'][1:].replace(',', '')
                        price_match = re.search(r'\d+', price_str)
                        price = price_match.group() if price_match else 0
                        image_url = accom['image']
                        detailed_url = accom['url']

                        print(f'Processing hotel: {name}')

                        review_res = requests.get(detailed_url, headers=req_header, timeout=10)
                        if review_res.ok:
                            soup = BeautifulSoup(review_res.text, "html.parser")
                            json_script_page = soup.body.find('script', type='application/json', id='__NEXT_DATA__')
                            if json_script_page:
                                data_content = json.loads(json_script_page.string)
                                page_props = data_content['props']['pageProps']
                                accomId = page_props['accommodationId']
                                queries = page_props['dehydratedState']['queries']
                                total_count = queries[0]['state']['data']['body']['meta']['review']['count']
                                total_review_iter = math.ceil((min(total_count, review_limit) if review_limit > 0 else total_count) / 50)
                                print(f'Total reviews: {total_count}, Review iterations needed: {total_review_iter}')
                        
                        review_list = []
                        for review_page in range(total_review_iter):
                            review_res = requests.get(f'https://www.yeogi.com/api/gateway/content-review/v2/STAY_DOMESTIC/{accomId}/reviews?sort={review_sort[review_sort_opt]}First&page={review_page}&size={min(50, review_limit) if review_limit > 0 else 50}', headers=req_header, timeout=10)
                            if review_res.ok:
                                res = review_res.json()
                                reviews = res['data']['reviews']
                                review_list.extend([review['content'] for review in reviews])
                            else:
                                print(f'*** Error: {review_res}')
                                continue

                        combined_review, emotion_rating = aggregate_reviews(review_list)

                        list_from_a_page.append({
                            "name": name,
                            "poster_url": image_url,
                            "location": address,
                            "detailed_url": detailed_url,
                            "reviews": combined_review,  # 변경된 부분
                            "emotion_rating": emotion_rating
                        })

                        # 호텔 데이터를 MariaDB에 삽입
                        hotel_data = (
                            name,
                            image_url,
                            address,
                            detailed_url,
                            combined_review,  # 변경된 부분
                            emotion_rating
                        )
                        insert_hotel_data(hotel_data)

                    scraped_list.extend(list_from_a_page)
                else:
                    print('*** Error: json_ld for data not found')
            else:
                print(f'*** Error: {res}')
            print(f' - Page {page + 1} completed.')
        if len(scraped_list) > item_limit:
            scraped_list = scraped_list[:item_limit]
        print(f'Total hotels scraped: {len(scraped_list)}')
        all_scraped_list[keyword] = scraped_list

    # 파일로 저장하는 부분은 필요 시 주석 해제
    # file_name = os.path.basename('test.json')
    # with open(file_name, 'w', encoding='utf-8') as file:
    #     json.dump(all_scraped_list, file, ensure_ascii=False, indent=4)

scrapHotel()