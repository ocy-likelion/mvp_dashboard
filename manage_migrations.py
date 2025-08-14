#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 관리 스크립트
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


def run_command(command):
    """명령어 실행"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 명령어 실행 실패: {e}")
        print(f"에러 출력: {e.stderr}")
        return False


def create_migration(message):
    """새로운 마이그레이션 생성"""
    print(f"🔄 마이그레이션 생성 중: {message}")
    command = f"python -m alembic revision --autogenerate -m '{message}'"
    return run_command(command)


def upgrade_database():
    """데이터베이스 업그레이드"""
    print("🔄 데이터베이스 업그레이드 중...")
    command = "python -m alembic upgrade head"
    return run_command(command)


def downgrade_database(revision):
    """데이터베이스 다운그레이드"""
    print(f"🔄 데이터베이스 다운그레이드 중: {revision}")
    command = f"python -m alembic downgrade {revision}"
    return run_command(command)


def show_current():
    """현재 마이그레이션 상태 확인"""
    print("📊 현재 마이그레이션 상태:")
    command = "python -m alembic current"
    return run_command(command)


def show_history():
    """마이그레이션 히스토리 확인"""
    print("📋 마이그레이션 히스토리:")
    command = "python -m alembic history"
    return run_command(command)


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python manage_migrations.py create <message>  - 새 마이그레이션 생성")
        print("  python manage_migrations.py upgrade           - 데이터베이스 업그레이드")
        print("  python manage_migrations.py downgrade <rev>   - 데이터베이스 다운그레이드")
        print("  python manage_migrations.py current           - 현재 상태 확인")
        print("  python manage_migrations.py history           - 히스토리 확인")
        return

    action = sys.argv[1]

    if action == "create":
        if len(sys.argv) < 3:
            print("❌ 마이그레이션 메시지를 입력해주세요.")
            return
        message = sys.argv[2]
        create_migration(message)
    
    elif action == "upgrade":
        upgrade_database()
    
    elif action == "downgrade":
        if len(sys.argv) < 3:
            print("❌ 다운그레이드할 리비전을 입력해주세요.")
            return
        revision = sys.argv[2]
        downgrade_database(revision)
    
    elif action == "current":
        show_current()
    
    elif action == "history":
        show_history()
    
    else:
        print(f"❌ 알 수 없는 명령어: {action}")


if __name__ == "__main__":
    main()

