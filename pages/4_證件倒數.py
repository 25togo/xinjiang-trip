import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from datetime import date, timedelta
from utils.data_loader import load_itinerary, load_documents

st.set_page_config(page_title="證件倒數", page_icon="📋", layout="wide")
st.title("證件與申辦倒數")

itin = load_itinerary()
docs = load_documents()
_sd = itin["trip"]["start_date"]
start_date = _sd if isinstance(_sd, date) else date.fromisoformat(_sd)
today = date.today()
days_to_go = (start_date - today).days

c1, c2, c3 = st.columns(3)
c1.metric("出發日", start_date.isoformat())
c2.metric("今天", today.isoformat())
c3.metric("距出發", f"{days_to_go} 天",
          delta=f"{'⏰ 急' if days_to_go < 30 else '✅ 還有時間'}")

st.markdown("---")
st.subheader("申辦時程表")

ranked = sorted(
    docs["documents"],
    key=lambda d: -d["deadline_days_before"],
)

for doc in ranked:
    deadline = start_date - timedelta(days=doc["deadline_days_before"])
    days_left = (deadline - today).days
    if doc["deadline_days_before"] == 0:
        status = "🟢 落地辦"
        progress = 1.0
    elif days_left < 0:
        status = "🔴 已過建議日"
        progress = 1.0
    elif days_left < 7:
        status = "🟡 急件"
        progress = 0.85
    elif days_left < 30:
        status = "🟠 該動了"
        progress = 0.6
    else:
        status = "🟢 充裕"
        progress = 0.3

    with st.expander(
        f"{status} ｜ **{doc['name']}** ｜ "
        f"{'落地辦' if doc['deadline_days_before'] == 0 else f'建議 {deadline.isoformat()} 前完成（剩 {days_left} 天）'}",
        expanded=(doc["required"] and days_left < 30 and doc["deadline_days_before"] > 0),
    ):
        cc = st.columns([2, 1, 1, 1])
        cc[0].caption(f"辦理地點：{doc['apply_location']}")
        cc[1].caption(f"費用：NT$ {doc['cost_twd']}")
        cc[2].caption(f"工期：{doc['duration_days']} 天")
        cc[3].caption(f"必備：{'是' if doc['required'] else '否'}")

        st.progress(progress)

        if doc.get("notes"):
            st.markdown("**重點：**")
            for n in doc["notes"]:
                st.markdown(f"- {n}")

        if doc.get("checklist"):
            st.markdown("**Checklist：**")
            for i, c in enumerate(doc["checklist"]):
                st.checkbox(c, key=f"{doc['id']}_{i}")

st.markdown("---")
st.subheader("總覽表")

import pandas as pd
rows = []
for doc in ranked:
    deadline = start_date - timedelta(days=doc["deadline_days_before"])
    rows.append({
        "項目": doc["name"],
        "必備": "✓" if doc["required"] else "—",
        "建議完成日": deadline.isoformat() if doc["deadline_days_before"] > 0 else "落地辦",
        "費用 TWD": doc["cost_twd"],
        "辦理": doc["apply_location"],
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
