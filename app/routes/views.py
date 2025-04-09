from flask import Blueprint, render_template, redirect, url_for, session

views_bp = Blueprint('views', __name__)

@views_bp.route('/front_for_pro', methods=['GET'])
def front_for_pro():
    """
    프론트엔드 개발자용 대시보드 API
    ---
    tags:
      - Views
    summary: 프론트엔드 개발자를 위한 대시보드 페이지 반환
    description: 
      사용자가 로그인한 경우 대시보드 페이지 (front_for_pro.html)을 반환합니다.
      로그인하지 않은 경우 로그인 페이지로 이동됩니다.
    responses:
      200:
        description: 대시보드 HTML 페이지 반환
      302:
        description: 로그인되지 않은 경우 로그인 페이지로 리다이렉트
    """
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('front_for_pro.html')


@views_bp.route('/admin', methods=['GET'])
def admin():
    """
    관리자 대시보드 API
    ---
    tags:
      - Views
    summary: 관리자 대시보드 페이지 반환
    description: 
      사용자가 로그인한 경우 관리자 대시보드 (admin.html)을 반환합니다.  
      로그인하지 않은 경우 로그인 페이지로 이동됩니다.
    responses:
      200:
        description: 관리자 대시보드 HTML 페이지 반환
      302:
        description: 로그인되지 않은 경우 로그인 페이지로 리다이렉트
    """
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('admin.html')