from flask import Blueprint, render_template, redirect, url_for, session

views_bp = Blueprint("views", __name__)


@views_bp.route("/front_for_pro", methods=["GET"])
def front_for_pro():
    """
    프론트엔드 개발자용 대시보드 API
    ---
    tags:
      - Views
    summary: 프론트엔드 개발자를 위한 대시보드 페이지 반환
    description: |
      사용자가 로그인한 경우 대시보드 페이지 (front_for_pro.html)을 반환합니다.
      로그인하지 않은 경우 로그인 페이지로 이동됩니다.
      
      ### 사용 예시
      ```javascript
      // 브라우저에서 직접 접근
      window.location.href = '/front_for_pro';
      
      // 또는 fetch로 HTML 내용 가져오기
      const response = await fetch('/front_for_pro', {
        method: 'GET',
        credentials: 'include'
      });
      
      if (response.redirected) {
        // 로그인 페이지로 리다이렉트된 경우
        window.location.href = response.url;
      } else {
        const html = await response.text();
        document.body.innerHTML = html;
      }
      ```
    responses:
      200:
        description: 대시보드 HTML 페이지 반환
        schema:
          type: string
          format: html
        examples:
          text/html:
            summary: 대시보드 HTML 페이지
            value: |
              <!DOCTYPE html>
              <html>
              <head>
                <title>업무 관리 대시보드</title>
              </head>
              <body>
                <h1>업무 관리 대시보드</h1>
                <!-- 대시보드 내용 -->
              </body>
              </html>
      302:
        description: 로그인되지 않은 경우 로그인 페이지로 리다이렉트
        headers:
          Location:
            description: 리다이렉트 URL
            schema:
              type: string
              example: "/login"
    """
    if "user" not in session:
        return redirect(url_for("auth.login"))
    return render_template("front_for_pro.html")


@views_bp.route("/admin", methods=["GET"])
def admin():
    """
    관리자 대시보드 API
    ---
    tags:
      - Views
    summary: 관리자 대시보드 페이지 반환
    description: |
      사용자가 로그인한 경우 관리자 대시보드 (admin.html)을 반환합니다.
      로그인하지 않은 경우 로그인 페이지로 이동됩니다.
      
      ### 사용 예시
      ```javascript
      // 브라우저에서 직접 접근
      window.location.href = '/admin';
      
      // 또는 fetch로 HTML 내용 가져오기
      const response = await fetch('/admin', {
        method: 'GET',
        credentials: 'include'
      });
      
      if (response.redirected) {
        // 로그인 페이지로 리다이렉트된 경우
        window.location.href = response.url;
      } else {
        const html = await response.text();
        document.body.innerHTML = html;
      }
      ```
    responses:
      200:
        description: 관리자 대시보드 HTML 페이지 반환
        schema:
          type: string
          format: html
        examples:
          text/html:
            summary: 관리자 대시보드 HTML 페이지
            value: |
              <!DOCTYPE html>
              <html>
              <head>
                <title>관리자 대시보드</title>
              </head>
              <body>
                <h1>관리자 대시보드</h1>
                <!-- 관리자 대시보드 내용 -->
              </body>
              </html>
      302:
        description: 로그인되지 않은 경우 로그인 페이지로 리다이렉트
        headers:
          Location:
            description: 리다이렉트 URL
            schema:
              type: string
              example: "/login"
    """
    if "user" not in session:
        return redirect(url_for("auth.login"))
    return render_template("admin.html")
