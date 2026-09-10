# 등급별 접근 제어(RBAC) — 일반 / 골드 / 관리자

목적: **접근 제어(인가) 확인용 테스트.** 로그인은 됐지만 등급이 모자란 사람이
`/gold`, `/admin` 에 들어오면 예외 화면이 뜨는지 눈으로 확인한다.

## ① 등급 값

| 값 | 이름 | 의미 |
|---|---|---|
| 0 | 일반 | 회원가입 시 기본값(최초 가입) |
| 1 | 골드 | 중간 관리자 |
| 2 | 관리자 | 전체 관리 |

`models/user.py` 의 `User.role` 컬럼 (기본값 0). `ROLE_NORMAL/ROLE_GOLD/ROLE_ADMIN` 상수도 같은 파일에 있다.

## ② 어디에 뭐가 있나

- `models/user.py` — `role` 컬럼 + `to_dict()`/`role_name()`
- `rbac.py` — `role_required(min_role)` 데코레이터. JWT의 `role` 클레임을 보고
  모자라면 **403** + `{required_role, current_role, ...}` 을 돌려준다(로그인 자체가
  안 됐으면 flask-jwt-extended 가 알아서 401).
- `controllers/auth_controller.py`
  - `POST /api/auth/register` — 항상 `role=0` 으로 가입.
  - `POST /api/auth/login` — JWT에 `role`을 심고, 응답 JSON에도 `role`/`role_name` 포함.
- `controllers/authz_controller.py`
  - `GET /api/gold/check` — 골드(1) 이상만 통과
  - `GET /api/admin/check` — 관리자(2)만 통과
  - `GET /api/admin/users` — 회원 목록(관리자)
  - `PUT /api/admin/users/<id>` — 등급 수정(관리자, 본인 강등은 막음)
  - `DELETE /api/admin/users/<id>` — 회원 삭제(관리자, 본인 삭제는 막음)
- `templates/gold.html`, `templates/admin.html` — 페이지가 뜨자마자 위 `check` API를
  호출해서, 통과면 컨텐츠를, 거부면 **예외 화면**(⛔ 접근 권한이 없습니다 + 필요/현재 등급)을 보여준다.
- `templates/partials/_nav.html` — 헤더에 `골드 전용`/`관리자` 링크를 **누구에게나** 노출한다.
  (누르는 건 자유, 통과 여부는 각 페이지가 판정 — 그래야 "허용 안 되는 접근 시도" 화면도 캡쳐할 수 있다.)
  로그인 중이면 헤더에 `아이디님 [등급배지]` 로 표시된다.

## ③ 최초 관리자 만들기 (닭이 먼저냐 달걀이 먼저냐 문제)

회원가입은 항상 일반(0)이라, 첫 관리자는 DB에서 직접 올려야 한다.

```sql
USE my_new_board_db;
UPDATE users SET role = 2 WHERE username = '내_아이디';
```

그 다음부터는 `/admin` 페이지에서 다른 회원의 등급을 화면으로 바꿀 수 있다.

## ④ 기존에 이미 만들어둔 DB라면

`db.create_all()` 은 **없는 테이블만** 만들고 기존 `users` 테이블은 건드리지 않는다.
그래서 `app.py` 의 `create_app()` 에 컬럼이 없을 때만 붙는 간단한 마이그레이션을 넣어뒀다.

```python
db.session.execute(text('ALTER TABLE users ADD COLUMN role INT NOT NULL DEFAULT 0'))
```

앱을 껐다 켜면(=`python app.py` 재실행) 자동으로 `role` 컬럼이 생긴다. 실패해도(이미 있으면)
그냥 무시하고 넘어간다.

## ⑤ 테스트 시나리오 (제출용 캡쳐 체크리스트)

1. 새 계정 가입 → 로그인 → 헤더에 `아이디님 [일반]` 뜨는지 확인
2. `/gold` 접속 → ⛔ 예외 화면(필요: 골드, 현재: 일반) 캡쳐
3. `/admin` 접속 → ⛔ 예외 화면(필요: 관리자, 현재: 일반) 캡쳐
4. DB에서 본인 계정 `role=2` 로 승격 → 재로그인 → 헤더 배지가 `[관리자]` 로 바뀌는지 확인
5. `/admin` 접속 → 통과 화면 + 회원 목록 캡쳐
6. 다른 계정 등급을 `골드`로 바꾸고 저장 → 그 계정으로 로그인해서 `/gold` 통과되는지 캡쳐
7. 관리자 화면에서 회원 삭제까지 확인 (본인 계정은 버튼이 비활성화되는지도 함께 확인)
