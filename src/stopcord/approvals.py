"""
approvals.py — 승인 대기열

되돌릴 수 없는/고비용 작업을 사람이 승인하기 전까지 큐에 쌓아두는 모듈.
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .guard import DEFAULT_STATE_DIR


class ApprovalQueue:
    def __init__(self, state_dir: Optional[Path] = None):
        self.state_dir = Path(state_dir).expanduser() if state_dir else DEFAULT_STATE_DIR
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.file = self.state_dir / "approvals.json"
        if not self.file.exists():
            self._write({"pending": [], "resolved": []})

    def _read(self) -> dict:
        return json.loads(self.file.read_text())

    def _write(self, data: dict) -> None:
        self.file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def request(self, description: str, category: str = "기타") -> str:
        data = self._read()
        entry = {
            "id": uuid.uuid4().hex[:8],
            "description": description,
            "category": category,
            "requested_at": datetime.now(timezone.utc).isoformat(),
        }
        data["pending"].append(entry)
        self._write(data)
        return entry["id"]

    def list_pending(self) -> list:
        return self._read()["pending"]

    def resolve(self, entry_id: str, approved: bool, note: str = "") -> bool:
        data = self._read()
        for i, entry in enumerate(data["pending"]):
            if entry["id"] == entry_id:
                entry["resolved_at"] = datetime.now(timezone.utc).isoformat()
                entry["approved"] = approved
                entry["note"] = note
                data["resolved"].append(entry)
                data["pending"].pop(i)
                self._write(data)
                return True
        return False
