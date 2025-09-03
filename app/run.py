from app import create_app
from app.config import PORT

app = create_app()

if __name__ == "__main__":
    print(f"서버가 http://0.0.0.0:{PORT} 에서 실행됩니다.")
    app.run(host="0.0.0.0", port=PORT)
