import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from utils.data_loader import load_contacts

st.set_page_config(page_title="緊急聯絡", page_icon="📞", layout="wide")
st.title("緊急聯絡")
st.caption("出發前把包車師傅、朋友的號碼填到 data/contacts.yaml；手機點電話可直撥。")

contacts = load_contacts()

sections = [
    ("emergency", "🚨 包車與同行（自填）", "warning"),
    ("china_emergency", "🇨🇳 中國境內緊急", "error"),
    ("taiwan_office", "🇹🇼 台灣海基會（24h）", "info"),
    ("insurance_company", "🛡️ 保險公司（24h）", "info"),
    ("airlines", "✈️ 航空公司", "info"),
    ("local_services", "🏛️ 當地服務", "info"),
]

for key, title, _ in sections:
    items = contacts.get(key, [])
    st.subheader(title)
    if not items:
        st.caption("（無）")
        continue

    for c in items:
        with st.container(border=True):
            cols = st.columns([2, 2, 2, 4])
            cols[0].markdown(f"**{c['role']}**")
            if c.get("name"):
                cols[1].caption(f"姓名：{c['name']}")
            phone = c.get("phone", "").strip()
            if phone:
                cols[2].markdown(f"📞 [{phone}](tel:{phone})")
            else:
                cols[2].caption("（出發前填）")
            wechat = c.get("wechat", "").strip()
            note = c.get("note", "")
            extra = []
            if wechat:
                extra.append(f"WeChat: {wechat}")
            if note:
                extra.append(note)
            cols[3].caption(" ｜ ".join(extra) if extra else "—")
    st.markdown("")
