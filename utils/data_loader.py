from pathlib import Path
from datetime import date, datetime
import yaml
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
USER_DATA_DIR = BASE_DIR / "data_user"
USER_DATA_DIR.mkdir(exist_ok=True)


def _stringify_dates(obj):
    """遞迴把 datetime.date 轉成 ISO 字串，避免 streamlit metric 等元件爆掉。"""
    if isinstance(obj, dict):
        return {k: _stringify_dates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_stringify_dates(v) for v in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()[:10] if isinstance(obj, date) and not isinstance(obj, datetime) else obj.isoformat()
    return obj


@st.cache_data
def load_yaml(filename: str) -> dict:
    path = DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return _stringify_dates(yaml.safe_load(f))


def load_itinerary():
    return load_yaml("itinerary.yaml")


def load_places():
    return load_yaml("places.yaml")


def load_documents():
    return load_yaml("documents.yaml")


def load_packing():
    return load_yaml("packing.yaml")


def load_budget():
    return load_yaml("budget.yaml")


def load_contacts():
    return load_yaml("contacts.yaml")


def load_ctrip_refs():
    return load_yaml("ctrip_refs.yaml")
