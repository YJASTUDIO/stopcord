"""
budget.py — 예산 하드캡 추적
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .guard import DEFAULT_STATE_DIR


class BudgetTracker:
    def __init__(self, hardcap: float, daily_warn: float, state_dir: Optional[Path] = None, currency: str = "KRW"):
        self.state_dir = Path(state_dir).expanduser() if state_dir else DEFAULT_STATE_DIR
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.file = self.state_dir / "budget.json"
        self.currency = currency
        if not self.file.exists():
            self._write({
                "month": datetime.now(timezone.utc).strftime("%Y-%m"),
                "hardcap": hardcap,
                "daily_warn": daily_warn,
                "total_spent_this_month": 0,
                "entries": [],
            })

    def _read(self) -> dict:
        return json.loads(self.file.read_text())

    def _write(self, data: dict) -> None:
        self.file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def log_spend(self, item: str, amount: float) -> dict:
        data = self._read()
        data["entries"].append({
            "date": datetime.now(timezone.utc).isoformat(),
            "item": item,
            "amount": amount,
        })
        data["total_spent_this_month"] += amount
        self._write(data)
        return self.status()

    def status(self) -> dict:
        data = self._read()
        over_hardcap = data["total_spent_this_month"] >= data["hardcap"]
        return {
            "total_spent_this_month": data["total_spent_this_month"],
            "hardcap": data["hardcap"],
            "over_hardcap": over_hardcap,
            "currency": self.currency,
        }
