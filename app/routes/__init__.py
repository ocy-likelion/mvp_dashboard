from app.serializers import json_response


def register_routes(app):
    """모든 라우터를 등록하는 함수"""
    from app.routes.auth import auth_bp
    from app.routes.notices import notices_bp
    from app.routes.tasks import tasks_bp
    from app.routes.issues import issues_bp
    from app.routes.attendance import attendance_bp
    from app.routes.training import training_bp
    from app.routes.admin import admin_bp
    from app.routes.views import views_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(notices_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(issues_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(training_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(views_bp)

    # 시스템 상태 확인 라우트
    @app.route("/healthcheck", methods=["GET"])
    def healthcheck():
        return json_response(
            data={"status": "ok"}, message="Service is running!", status_code=200
        )

    # 루트 경로
    @app.route("/", methods=["GET"])
    def index():
        return json_response(
            data={
                "status": "ok",
                "version": "1.0.0",
            },
            message="API 서버가 정상적으로 실행 중입니다.",
            status_code=200,
        )
