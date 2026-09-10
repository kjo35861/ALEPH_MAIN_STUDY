"""등급(권한) 기반 접근 제어(RBAC) 데코레이터.

JWT 안에 들어있는 role 클레임(로그인 시 심어둠)을 확인해서
필요 등급 미만이면 403 예외 응답을 준다.

사용법:
  @role_required(ROLE_GOLD)   # 골드 이상만 통과
  def some_view(): ...
"""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request

from models.user import ROLE_NAMES


def role_required(min_role):
  def decorator(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
      # 1) 로그인(JWT) 자체가 안 되어 있으면 401
      verify_jwt_in_request()
      claims = get_jwt()
      current_role = claims.get('role', 0)

      # 2) 로그인은 했지만 등급이 모자라면 403 (예외 화면용 정보 포함)
      if current_role < min_role:
        return jsonify({
            'msg': '접근 권한이 없습니다.',
            'required_role': min_role,
            'required_role_name': ROLE_NAMES.get(min_role, '?'),
            'current_role': current_role,
            'current_role_name': ROLE_NAMES.get(current_role, '?'),
        }), 403

      return fn(*args, **kwargs)
    return wrapper
  return decorator
