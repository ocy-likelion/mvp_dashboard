from app import create_app
import os

# 직접 환경 변수에서 PORT 값을 읽습니다
PORT = int(os.getenv("PORT", 10000))

app = create_app()

if __name__ == '__main__':
    print(f"서버가 http://0.0.0.0:{PORT} 에서 실행됩니다.")
    app.run(host="0.0.0.0", port=PORT)