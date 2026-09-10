from extensions import db

# 등급(권한) 값 — 인가(Authorization) 테스트용
# 0 = 일반(최초 가입 기본값) · 1 = 골드(중간 관리자) · 2 = 관리자
ROLE_NORMAL = 0
ROLE_GOLD = 1
ROLE_ADMIN = 2
ROLE_NAMES = {ROLE_NORMAL: '일반', ROLE_GOLD: '골드', ROLE_ADMIN: '관리자'}


class User(db.Model):
  __tablename__ = 'users'

  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  password = db.Column(db.String(255), nullable=False)   # 해시만 저장(평문 금지)
  # 등급: 0=일반, 1=골드, 2=관리자. 회원가입 시 항상 0(일반)으로 시작한다.
  role = db.Column(db.Integer, nullable=False, default=ROLE_NORMAL)

  def role_name(self):
    return ROLE_NAMES.get(self.role, '알수없음')

  def to_dict(self):
    return {
        'id': self.id,
        'username': self.username,
        'role': self.role,
        'role_name': self.role_name(),
    }

  def __repr__(self):
    return f'<User {self.username} role={self.role}>'
