"""
cli.py — 커맨드라인에서 바로 쓰는 stopcord 인터페이스.

사용 예:
    stopcord status
    stopcord kill --reason "긴급 점검"
    stopcord resume
    stopcord approvals list
    stopcord approvals request "결제수단 연결" --category payment
    stopcord budget status
    stopcord budget log "도메인 등록" 12000
"""
import argparse
import sys

from .guard import Guard
from .approvals import ApprovalQueue
from .budget import BudgetTracker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stopcord", description="당기면 즉시 멈춘다 — AI 에이전트 안전장치 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="킬스위치 상태 확인")

    kill_p = sub.add_parser("kill", help="킬스위치 활성화(즉시 중단)")
    kill_p.add_argument("--reason", default="", help="중단 사유")

    sub.add_parser("resume", help="킬스위치 해제(재개)")

    approvals_p = sub.add_parser("approvals", help="승인 대기열 조작")
    approvals_sub = approvals_p.add_subparsers(dest="approvals_command", required=True)
    approvals_sub.add_parser("list", help="대기 중인 승인 목록")
    req_p = approvals_sub.add_parser("request", help="승인 요청 등록")
    req_p.add_argument("description", help="작업 설명")
    req_p.add_argument("--category", default="기타")
    resolve_p = approvals_sub.add_parser("resolve", help="승인 요청을 승인/거부 처리")
    resolve_p.add_argument("id", help="승인 항목 ID")
    resolve_p.add_argument("--approved", required=True, choices=["true", "false"], help="승인(true) 또는 거부(false)")
    resolve_p.add_argument("--note", default="", help="처리 메모")

    deadman_p = sub.add_parser("deadman", help="데드맨스위치 확인")
    deadman_sub = deadman_p.add_subparsers(dest="deadman_command", required=True)
    deadman_check_p = deadman_sub.add_parser("check", help="마지막 응답 시각 기준으로 데드맨스위치 상태 판정")
    deadman_check_p.add_argument("last_response_at", help="마지막 사람 응답 시각 (ISO 8601, 예: 2026-07-25T10:00:00+09:00)")
    deadman_check_p.add_argument("--warn-hours", type=float, default=24, help="경고 임계값 (시간, 기본 24)")
    deadman_check_p.add_argument("--kill-hours", type=float, default=36, help="자동정지 임계값 (시간, 기본 36)")

    budget_p = sub.add_parser("budget", help="예산 조회/기록")
    budget_sub = budget_p.add_subparsers(dest="budget_command", required=True)
    budget_sub.add_parser("status", help="현재 예산 상태")
    log_p = budget_sub.add_parser("log", help="지출 기록")
    log_p.add_argument("item", help="지출 항목명")
    log_p.add_argument("amount", type=float, help="지출 금액")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    guard = Guard()

    if args.command == "status":
        print(guard.status())
    elif args.command == "kill":
        print(guard.activate_kill(reason=args.reason))
    elif args.command == "resume":
        print(guard.deactivate_kill())
    elif args.command == "approvals":
        queue = ApprovalQueue()
        if args.approvals_command == "list":
            pending = queue.list_pending()
            if not pending:
                print("승인 대기 중인 항목 없음")
            for entry in pending:
                print(f"[{entry['id']}] ({entry['category']}) {entry['description']} — {entry['requested_at']}")
        elif args.approvals_command == "request":
            entry_id = queue.request(args.description, category=args.category)
            print(f"승인 요청 등록됨 (id={entry_id})")
        elif args.approvals_command == "resolve":
            approved = args.approved == "true"
            ok = queue.resolve(args.id, approved=approved, note=args.note)
            if ok:
                print(f"승인 처리 완료 (id={args.id}, approved={approved})")
            else:
                print(f"해당 ID를 찾을 수 없음: {args.id}")
    elif args.command == "deadman":
        from .deadman import DeadmanSwitch
        ds = DeadmanSwitch(guard=guard, warn_hours=args.warn_hours, kill_hours=args.kill_hours)
        from datetime import datetime as _dt
        last = _dt.fromisoformat(args.last_response_at)
        result = ds.check(last)
        print(f"action={result.action}, elapsed={result.elapsed_hours:.1f}h")
        print(result.message)
    elif args.command == "budget":
        tracker = BudgetTracker(hardcap=300000, daily_warn=15000)
        if args.budget_command == "status":
            print(tracker.status())
        elif args.budget_command == "log":
            print(tracker.log_spend(args.item, args.amount))

    return 0


if __name__ == "__main__":
    sys.exit(main())
