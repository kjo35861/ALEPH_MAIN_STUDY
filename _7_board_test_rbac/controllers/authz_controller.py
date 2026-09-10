"""등급(RBAC) 접근 제어 확인용 API.

- /api/gold/check, /api/admin/check
  : 각 페이지(gold.html, admin.html)가 로드되자마자 호출해서
    통과(200)/거부(403) 여부로 '접근 시도 결과 화면'을 그려준다.
- /api/admin/users*
  : 관리자 전용 — 회원 목록 조회 / 등급(role) 수정 / 삭제.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity

from extensions import db
from models import User
from models.user import ROLE_ADMIN, ROLE_GOLD
from rbac import role_required

authz_bp = Blueprint('authz', __name__, url_prefix='/api')


@authz_bp.route('/gold/check', methods=['GET'])
@role_required(ROLE_GOLD)
def gold_check():
  claims = get_jwt()
  return jsonify({'msg': '골드 등급 접근을 허용합니다.',
                  'role': claims.get('role', 0)})


@authz_bp.route('/admin/check', methods=['GET'])
@role_required(ROLE_ADMIN)
def admin_check():
  claims = get_jwt()
  return jsonify({'msg': '관리자 접근을 허용합니다.',
                  'role': claims.get('role', 0)})


@authz_bp.route('/admin/users', methods=['GET'])
@role_required(ROLE_ADMIN)
def list_users():
  """관리자 페이지: 전체 회원 목록 + 등급."""
  users = User.query.order_by(User.id).all()
  return jsonify({'users': [u.to_dict() for u in users]})


@authz_bp.route('/admin/users/<int:id>', methods=['PUT'])
@role_required(ROLE_ADMIN)
def update_user_role(id):
  """관리자 페이지: 회원 등급 수정(0/1/2)."""
  data = request.get_json(silent=True) or {}
  new_role = data.get('role')
  if new_role not in (0, 1, 2):
    return jsonify({'msg': 'role 은 0(일반)/1(골드)/2(관리자) 중 하나여야 합니다.'}), 400

  user = User.query.get_or_404(id)

  my_id = int(get_jwt_identity())
  if user.id == my_id and new_role != ROLE_ADMIN:
    # 본인이 관리자 화면에 계속 접근할 수 있도록, 스스로 강등하는 것은 막는다.
    return jsonify({'msg': '본인의 관리자 등급은 스스로 낮출 수 없습니다.'}), 400

  user.role = new_role
  db.session.commit()
  return jsonify({'msg': '등급이 수정되었습니다.', **user.to_dict()})


@authz_bp.route('/admin/users/<int:id>', methods=['DELETE'])
@role_required(ROLE_ADMIN)
def delete_user(id):
  """관리자 페이지: 회원 삭제."""
  my_id = int(get_jwt_identity())
  if id == my_id:
    return jsonify({'msg': '본인 계정은 삭제할 수 없습니다.'}), 400

  user = User.query.get_or_404(id)
  db.session.delete(user)
  db.session.commit()
  return jsonify({'msg': '삭제되었습니다.'})
