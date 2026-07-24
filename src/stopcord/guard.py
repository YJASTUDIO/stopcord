"""
guard.py — 킬스위치 및 되돌릴 수 없는 작업 감지

원본: ~/.hermes/guard/base.py (헤르메스 CEO 프로젝트에서 실전 사용 중인 로직)
이 패키지에서는 파일 경로를 설정 가능하게 일반화했다.
"""
import os
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_STATE_DIR = Path(os.environ.get("STOPCORD_STATE_DIR", "~/.stopcord")).expanduser()

IRREVERSIBLE_KEYWORDS = [
    "payment", "publish", "hire", "delete", "config_change",
    "결제", "발행", "채용", "삭제", "설정변경",
]


class Guard:
    def __init__(self, state_dir: Path | str | None = None):
        self.state_dir = Path(state_dir).expanduser() if state_dir else DEFAULT_STATE_DIR
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.kill_file = self.state_dir / ".killswitch"

    def is_killed(self) -> bool:
        return self.kill_file.exists()

    def activate_kill(self, reason: str = "") -> str:
        with open(self.kill_file, "w") as f:
            f.write(f"Killed at {datetime.now(timezone.utc).isoformat()}\n")
            if reason:
                f.write(f"Reason: {reason}\n")
        return "킬스위치 활성화됨. 모든 자동화가 중단됩니다."

    def deactivate_kill(self) -> str:
        if self.kill_file.exists():
            self.kill_file.unlink()
            return "킬스위치 해제됨. 정상 운영을 재개합니다."
        return "이미 정상 운영 중입니다."

    def status(self) -> str:
        return "중단됨" if self.is_killed() else "정상 운영중"

    def needs_approval(self, action_description: str) -> bool:
        lowered = action_description.lower()
        return any(keyword in lowered for keyword in IRREVERSIBLE_KEYWORDS)
