import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://cysss:QJxyP6VuLMAZykzMyeRtO3QJUGMf0aWA@dpg-cuim9pogph6c73acoj0g-a/mvp_dashboard')
    SWAGGER = {
        'title': "업무 관리 대시보드 API",
        'uiversion': 3,
        'specs_route': "/apidocs/"
    } 