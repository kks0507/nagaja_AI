# nagaza_ai 🍽️🎬🏨

## Description
Google의 Gemini API를 활용하여 웹 스크래핑한 식당, 호텔, 영화에 대한 리뷰에 대해 감정을 분석하고 전반적인 총평을 제공하는 프로그램입니다. (리뷰에 대한 감정 점수는 Hugging Face transformers의 감정분석 파이프라인을 활용하였고, 리뷰에 대한 총평 생성은 Gemini API를 활용했습니다.)

## Installation and Execution

### Requirements
프로그램을 실행하기 위해 필요한 라이브러리들이 `requirements.txt` 파일에 명시되어 있습니다. 다음 명령어를 사용하여 필요한 라이브러리를 설치하세요:

```bash
pip install -r requirements.txt
```

`requirements.txt` 파일에는 다음 라이브러리들이 포함되어 있습니다:
- mysql-connector-python
- transformers
- beautifulsoup4
- requests
- selenium
- webdriver-manager

### Environment Variables
Google Gemini API를 사용하기 위해 환경 변수를 설정해야 합니다. 아래 명령어를 통해 API 키를 설정하세요:

```bash
export GEMINI_API_KEY=your_gemini_api_key
```

### Run the Program
프로그램을 실행하여 웹 스크래핑과 리뷰 감정 분석을 수행하려면, 아래 명령어로 각각의 스크립트를 실행하세요:

#### 식당 리뷰 분석
```bash
python restaurant.py
```

#### 호텔 리뷰 분석
```bash
python hotel.py
```

#### 영화 리뷰 분석
```bash
python movie2.py
```

## Code Explanation

### 주요 함수: `gemini.py`
```python
import google.generativeai as genai

def analyze_review(review):
    chat_session = model.start_chat(
        history=[{"role": "user", "parts": [review]}]
    )
    response = chat_session.send_message("Analyze this review")
    return response.text
```
이 함수는 Google Gemini API를 호출하여 리뷰 감정 분석을 수행하고, 분석된 결과를 반환합니다.

### 주요 함수: `restaurant.py`
```python
def restaurant(query):
    url = f'https://search.naver.com/search.naver?query={query}'
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    titles = soup.find_all("span", class_="place_bluelink TYaxT")
    return titles
```
이 함수는 웹에서 식당 정보를 스크래핑하여 반환합니다.

### 주요 함수: `hotel.py`
```python
def scrapHotel():
    # 웹에서 호텔 정보를 스크래핑하고, 감정 분석 후 결과를 DB에 저장
    combined_review, emotion_rating = aggregate_reviews(review_list)
    insert_hotel_data(hotel_data)
```
호텔 정보를 스크래핑하고 감정 분석을 통해 종합 리뷰를 생성합니다.

### 주요 함수: `movie2.py`
```python
def get_movie_reviews_selenium(movie_url):
    driver.get(movie_url)
    reviews = driver.find_elements(By.CLASS_NAME, 'box-comment')
    return reviews
```
Selenium을 이용해 영화 리뷰를 스크래핑하는 함수입니다.

## Contributor
- kks0507 (movie2.py, gemini.py, geminihot.py, geminimv.py)
- jhed0613 (restaurant.py)
- Hoyeon9 (hotel.py)

## License
This project is licensed under the MIT License.

## Repository
코드 및 프로젝트의 최신 업데이트는 [여기](https://github.com/kks0507/nagaja_ai.git)에서 확인할 수 있습니다.
