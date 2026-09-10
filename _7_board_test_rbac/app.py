"""엔트리포인트 — 앱 팩토리(create_app) 패턴.

구조
  config.py       설정(.env 로딩)
  extensions.py   db · jwt 인스턴스
  models/         User · Post · SecurityEvent
  controllers/    page · auth · post · security · public (블루프린트)
  templates/      화면 (partials/_nav.html = 공통 반응형 헤더)

실행:  python app.py   →  http://localhost:5000
"""
from flask import Flask

from config import Config
from controllers import all_blueprints
from extensions import db, jwt


def create_app(config_class=Config):
  app = Flask(__name__)
  app.config.from_object(config_class)

  # 확장 초기화
  db.init_app(app)
  jwt.init_app(app)

  # 컨트롤러(블루프린트) 등록
  for bp in all_blueprints:
    app.register_blueprint(bp)

  # 테이블 생성 (models 를 import 한 뒤여야 한다 — controllers 가 이미 import 함)
  with app.app_context():
    db.create_all()

    # db.create_all() 은 '없는 테이블'만 만들고 기존 테이블은 건드리지 않는다.
    # 이미 users 테이블이 있던 사람(role 컬럼이 없는 상태)을 위한 간단 마이그레이션.
    # 컬럼이 이미 있으면 그냥 실패하고 무시된다(학습용 프로젝트라 마이그레이션 도구 없이 처리).
    from sqlalchemy import text
    try:
      db.session.execute(
          text('ALTER TABLE users ADD COLUMN role INT NOT NULL DEFAULT 0'))
      db.session.commit()
    except Exception:
      db.session.rollback()

  return app


app = create_app()


if __name__ == '__main__':
  # host='0.0.0.0' 이면 같은 공유기의 다른 기기에서도 접속 가능.
  # 도커 안 n8n 에서는 http://host.docker.internal:5000 으로 부른다.
  app.run(debug=True, host='0.0.0.0', port=5000)
