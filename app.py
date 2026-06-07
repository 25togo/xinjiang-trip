import streamlit as st
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

st.set_page_config(
    page_title="2026 南疆 14 天行程",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.data_loader import load_itinerary, load_documents

itin = load_itinerary()
docs = load_documents()
trip = itin["trip"]

_sd = trip["start_date"]
start_date = _sd if isinstance(_sd, date) else date.fromisoformat(_sd)
today = date.today()
days_to_go = (start_date - today).days

st.title("🏔️ 2026 南疆 14 天行程")
st.caption(f"{trip['route_type']} ｜ 兩人 ｜ {trip['vehicle']}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("出發日", trip["start_date"])
c2.metric("距出發", f"{days_to_go} 天")
c3.metric("總天數", "14")
c4.metric("路線", "經典大環＋獨庫")

st.markdown("---")
st.subheader("快速導覽")

cols = st.columns(3)
nav = [
    ("📅 行程總覽", "從喀什到塔縣（含盤龍古道）、和田、庫車、獨庫公路 14 天"),
    ("🗺️ 互動地圖", "所有景點/住宿一鍵丟到高德 APP"),
    ("📍 每日詳情", "每天的時程、餐廳、住宿、注意事項"),
    ("📋 證件倒數", "台胞證、邊防證、保險，含申辦倒數"),
    ("🎒 打包清單", "8 月新疆 70+ 項打包必備"),
    ("💰 預算記帳", "預算規劃 + 兩人均攤即時記帳"),
    ("📞 緊急聯絡", "包車師傅、海基會、保險、機場電話"),
    ("📥 離線匯出", "匯出單頁 HTML 給手機，新疆離線可看"),
    ("🛒 Ctrip 比價", "對比攜程套裝/包車/跟團行情"),
]
for i, (label, desc) in enumerate(nav):
    with cols[i % 3]:
        with st.container(border=True):
            st.markdown(f"**{label}**")
            st.caption(desc)

st.markdown("---")

# 急件提醒
must_docs = [d for d in docs["documents"] if d["required"] and d["deadline_days_before"] > 0]
urgent = [
    d for d in must_docs
    if (start_date - today).days < d["deadline_days_before"] + 14
]
if urgent:
    st.warning("⏰ **接下來 2 週內該動的證件/準備：**")
    for d in urgent:
        deadline = start_date.toordinal() - d["deadline_days_before"]
        days_left = deadline - today.toordinal()
        st.markdown(
            f"- **{d['name']}**：建議 {(date.fromordinal(deadline)).isoformat()} 前完成"
            f"（剩 {days_left} 天） — {d['apply_location']}"
        )

st.markdown("---")
st.caption(
    "💡 提示：在新疆 Streamlit 會被牆，記得出發前到「📥 離線匯出」下載 HTML 存手機。"
)
