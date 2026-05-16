import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
from utils.data_loader import load_itinerary
from utils.amap import amap_marker_url

st.set_page_config(page_title="行程總覽", page_icon="📅", layout="wide")
st.title("行程總覽")

itin = load_itinerary()
trip = itin["trip"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("出發日", trip["start_date"])
col2.metric("返程日", trip["end_date"])
col3.metric("天數", "15")
col4.metric("人數", trip["travelers"])

st.caption(f"路線：{trip['route_type']} ｜ 移動方式：{trip['vehicle']}")

st.markdown("---")
st.subheader("15 天一覽")

rows = []
for d in itin["days"]:
    rows.append({
        "Day": d["day"],
        "日期": d["date"],
        "起": d["city_from"],
        "迄": d["city_to"],
        "交通": d["transport"],
        "里程 (km)": d["distance_km"],
        "車程 (h)": d["drive_hours"],
        "海拔 (m)": d["altitude_m"],
        "住宿": d["overnight"],
    })

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("每日重點")

for d in itin["days"]:
    with st.expander(f"Day {d['day']} ｜ {d['date']} ｜ {d['city_from']} → {d['city_to']}"):
        meta_cols = st.columns(4)
        meta_cols[0].caption(f"📍 海拔 {d['altitude_m']} m")
        meta_cols[1].caption(f"🚗 {d['distance_km']} km / {d['drive_hours']} h")
        meta_cols[2].caption(f"🏨 {d['overnight']}")
        meta_cols[3].caption(f"✈️ {d['transport']}")

        st.markdown("**今日重點**")
        for h in d["highlights"]:
            st.markdown(f"- {h}")

        if d.get("notes"):
            st.info(d["notes"])

st.markdown("---")
st.subheader("關鍵指標")

total_km = sum(d["distance_km"] for d in itin["days"])
total_drive = sum(d["drive_hours"] for d in itin["days"])
max_alt = max(d["altitude_m"] for d in itin["days"])
max_alt_day = next(d for d in itin["days"] if d["altitude_m"] == max_alt)

c1, c2, c3, c4 = st.columns(4)
c1.metric("總里程", f"{total_km:,} km")
c2.metric("總車程", f"{total_drive} 小時")
c3.metric("最高海拔", f"{max_alt} m", help=f"{max_alt_day['date']} {max_alt_day['city_to']}")
c4.metric("跨越城市", "8")

st.warning("⚠️ Day 5 紅其拉甫 4733m，當天車上備好氧氣瓶。Day 14 車程 10 小時，建議清晨 6 點出發。")
