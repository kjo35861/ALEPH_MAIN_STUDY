"""
alert_sender.py
로그인 경보 데이터를 n8n Webhook으로 전송하는 스크립트

security_events 테이블 컬럼과 매칭되는 필드를 함께 보낸다:
  student, src_ip, level, rule, fail_count, decision, severity, reason
※ decision / severity / reason 은 n8n의 Code 노드가 계산하므로
   여기서는 판정에 필요한 원본 값(ip, level, rule, fail_count)만 보내면 된다.
"""

import json
import urllib.request
import urllib.error

# ── 설정값 (상수로 모아둠) ────────────────────────────────
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")  # 본인 n8n Webhook 주소로 변경
STUDENT_NAME = "김준오"  # 본인 식별자 (채점 증적)
TIMEOUT_SEC = 5

# ── 전송할 경보 목록 ──────────────────────────────────────
# level >= 10  → deny 로 판정될 예정
# level < 10   → allow 로 판정될 예정
ALERTS = [
    {
        "ip": "1.2.3.114",
        "level": 10,
        "rule": "5712",
        "fail_count": 8,
    },
    {
        "ip": "192.168.0.10",
        "level": 3,
        "rule": "5501",
        "fail_count": 1,
    },
]


def build_payload():
    """n8n으로 보낼 JSON payload 구성"""
    return {
        "student": STUDENT_NAME,
        "alerts": ALERTS,
    }


def send_alert(payload):
    """n8n Webhook으로 POST 전송. 실패해도 프로그램이 죽지 않는다."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        N8N_WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as res:
            status = res.status
            body = res.read().decode("utf-8", errors="ignore")
            print(f"[n8n] POST {N8N_WEBHOOK_URL} -> {status}")
            if body:
                print(f"[n8n] response body: {body}")
    except urllib.error.HTTPError as e:
        # n8n이 응답은 했지만 에러 상태 코드를 준 경우
        print(f"[오류] n8n이 HTTP {e.code} 응답: {e.reason}")
    except urllib.error.URLError as e:
        # n8n 서버 자체가 꺼져있거나 연결이 안 되는 경우
        print(f"[오류] n8n에 연결할 수 없습니다: {e.reason}")
    except Exception as e:
        # 그 외 예상하지 못한 오류
        print(f"[오류] 알 수 없는 예외 발생: {e}")


def main():
    payload = build_payload()
    print("[전송할 데이터]")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    send_alert(payload)


if __name__ == "__main__":
    main()
