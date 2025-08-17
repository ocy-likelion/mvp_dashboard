from app import create_app
from app.config import PORT
from flask_cors import CORS

app = create_app()
CORS(
    app,
    resources={
        r"/*": {
            "origins": ["https://lion-helper-v2.vercel.app"],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type"],
        }
    },
)

if __name__ == "__main__":
    print(f"서버가 http://0.0.0.0:{PORT} 에서 실행됩니다.")
    app.run(host="0.0.0.0", port=PORT)
