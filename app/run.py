from app import create_app
import os

try:
    PORT = int(os.getenv("PORT", "10000"))
except ValueError:
    # 환경 변수가 유효하지 않을 경우 기본값 사용
    PORT = 10000

app = create_app()

if __name__ == '__main__':
    print(f"서버가 http://0.0.0.0:{PORT} 에서 실행됩니다.")
    app.run(host="0.0.0.0", port=PORT)