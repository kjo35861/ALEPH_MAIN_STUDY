"""회원가입 / 로그인."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
  data = request.get_json(silent=True) or {}
  if not data.get('username') or not data.get('password'):
    return jsonify({'msg': 'username, password 는 필수입니다.'}), 400
  if User.query.filter_by(username=data['username']).first():
    return jsonify({'msg': '이미 존재하는 사용자입니다.'}), 400

  # 회원가입은 항상 일반(role=0) 등급으로 생성한다. 등급 승격은 관리자 페이지에서만 가능.
  user = User(username=data['username'],
              password=generate_password_hash(data['password']),
              role=0)
  db.session.add(user)
  db.session.commit()
  return jsonify({'msg': '회원가입 성공'}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
  data = request.get_json(silent=True) or {}
  user = User.query.filter_by(username=data.get('username')).first()
  if not user or not check_password_hash(user.password, data.get('password', '')):
    return jsonify({'msg': '아이디 또는 비밀번호가 잘못되었습니다.'}), 401

  # role을 JWT 클레임에 심어서, 보호된 API마다 DB를 다시 조회하지 않아도
  # 토큰만으로 등급을 확인할 수 있게 한다(rbac.py 의 role_required 가 이 값을 읽음).
  token = create_access_token(
      identity=str(user.id),
      additional_claims={'role': user.role, 'username': user.username},
  )
  return jsonify(access_token=token, username=user.username,
                 role=user.role, role_name=user.role_name())
