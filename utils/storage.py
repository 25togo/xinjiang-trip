"""本地 JSON 持久化（記帳資料、Ctrip 比價）。

Streamlit Cloud 重啟會清空，正式上線建議改 Google Sheets。
本地開發＋出發前規劃階段用 JSON 即可。
"""
from pathlib import Path
import json
from datetime import datetime
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
USER_DATA_DIR = BASE_DIR / "data_user"
USER_DATA_DIR.mkdir(exist_ok=True)


def _path(filename: str) -> Path:
    return USER_DATA_DIR / filename


def load_json(filename: str, default: Any = None) -> Any:
    path = _path(filename)
    if not path.exists():
        return default if default is not None else []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data: Any) -> None:
    path = _path(filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def append_expense(record: dict) -> list:
    expenses = load_json("expenses.json", default=[])
    record["id"] = len(expenses) + 1
    record["created_at"] = datetime.now().isoformat(timespec="seconds")
    expenses.append(record)
    save_json("expenses.json", expenses)
    return expenses


def delete_expense(expense_id: int) -> list:
    expenses = load_json("expenses.json", default=[])
    expenses = [e for e in expenses if e.get("id") != expense_id]
    save_json("expenses.json", expenses)
    return expenses


def append_budget_item(record: dict) -> list:
    items = load_json("budget_plan.json", default=[])
    record["id"] = len(items) + 1
    record["created_at"] = datetime.now().isoformat(timespec="seconds")
    items.append(record)
    save_json("budget_plan.json", items)
    return items


def delete_budget_item(item_id: int) -> list:
    items = load_json("budget_plan.json", default=[])
    items = [e for e in items if e.get("id") != item_id]
    save_json("budget_plan.json", items)
    return items


def append_ctrip(record: dict) -> list:
    items = load_json("ctrip_comparisons.json", default=[])
    record["id"] = len(items) + 1
    record["saved_at"] = datetime.now().isoformat(timespec="seconds")
    items.append(record)
    save_json("ctrip_comparisons.json", items)
    return items


def delete_ctrip(item_id: int) -> list:
    items = load_json("ctrip_comparisons.json", default=[])
    items = [e for e in items if e.get("id") != item_id]
    save_json("ctrip_comparisons.json", items)
    return items
