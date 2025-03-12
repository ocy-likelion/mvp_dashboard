import os
from app import create_app

# Flask 애플리케이션 생성
app = create_app()

# 서버 실행
if __name__ == '__main__':
    port = int(os.getenv("PORT", 10000))  # 기본 포트 10000
    app.run(host="0.0.0.0", port=port)