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
    from app.routes.notifications import notifications_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(notices_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(issues_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(training_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(notifications_bp)

    # 시스템 상태 확인 라우트
    @app.route("/healthcheck", methods=["GET"])
    def healthcheck():
        """
        시스템 상태 확인 API
        ---
        tags:
          - System
        summary: 시스템 상태 확인
        description: |
          API 서버의 상태를 확인합니다.
          
          ### 사용 예시
          ```javascript
          const response = await fetch('/healthcheck', {
            method: 'GET'
          });
          
          const result = await response.json();
          console.log(result);
          ```
        responses:
          200:
            description: 시스템 정상 동작
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                message:
                  type: string
                  example: "Service is running!"
                data:
                  type: object
                  properties:
                    status:
                      type: string
                      example: "ok"
                status_code:
                  type: integer
                  example: 200
            examples:
              application/json:
                summary: 시스템 상태 확인 성공 응답
                value:
                  success: true
                  message: "Service is running!"
                  data:
                    status: "ok"
                  status_code: 200
        """
        return json_response(
            data={"status": "ok"}, message="Service is running!", status_code=200
        )

    # 루트 경로
    @app.route("/", methods=["GET"])
    def index():
        """
        API 서버 루트 경로
        ---
        tags:
          - System
        summary: API 서버 정보 조회
        description: |
          API 서버의 기본 정보를 조회합니다.
          
          ### 사용 예시
          ```javascript
          const response = await fetch('/', {
            method: 'GET'
          });
          
          const result = await response.json();
          console.log(result);
          ```
        responses:
          200:
            description: API 서버 정보 반환
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                message:
                  type: string
                  example: "API 서버가 정상적으로 실행 중입니다."
                data:
                  type: object
                  properties:
                    status:
                      type: string
                      example: "ok"
                    version:
                      type: string
                      example: "1.0.0"
                status_code:
                  type: integer
                  example: 200
            examples:
              application/json:
                summary: API 서버 정보 조회 성공 응답
                value:
                  success: true
                  message: "API 서버가 정상적으로 실행 중입니다."
                  data:
                    status: "ok"
                    version: "1.0.0"
                  status_code: 200
        """
        return json_response(
            data={
                "status": "ok",
                "version": "1.0.0",
            },
            message="API 서버가 정상적으로 실행 중입니다.",
            status_code=200,
        )
