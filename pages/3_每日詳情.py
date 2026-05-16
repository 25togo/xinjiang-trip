import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from utils.data_loader import load_itinerary, load_places
from utils.amap import amap_marker_url

st.set_page_config(page_title="每日詳情", page_icon="📍", layout="wide")
st.title("每日詳情")

itin = load_itinerary()
places = load_places()
place_by_name = {p["name"]: p for p in places["places"]}

day_labels = [f"Day {d['day']} - {d['date']} {d['city_from']}→{d['city_to']}" for d in itin["days"]]
sel = st.selectbox("選擇日期", day_labels, index=0)
day_idx = day_labels.index(sel)
d = itin["days"][day_idx]

st.header(f"Day {d['day']} ｜ {d['date']}")
st.subheader(f"{d['city_from']} → {d['city_to']}")

# 今日封面圖：優先取 day.cover_place_id 指定的，沒指定就抓第一個有圖的
_today_places = [p for p in places["places"] if d["day"] in p["day"]]
_cover_id = d.get("cover_place_id")
_cover = None
if _cover_id:
    _cover = next((p for p in places["places"] if p.get("id") == _cover_id and p.get("image_url", "").strip()), None)
if not _cover:
    _cover = next((p for p in _today_places if p.get("image_url", "").strip()), None)
if _cover:
    st.image(_cover["image_url"], caption=f"📷 {_cover['name']}", use_container_width=True)

cols = st.columns(4)
cols[0].metric("海拔", f"{d['altitude_m']} m")
cols[1].metric("里程", f"{d['distance_km']} km")
cols[2].metric("車程", f"{d['drive_hours']} h")
cols[3].metric("住宿", d["overnight"])

st.caption(f"🚗 {d['transport']}")

st.markdown("### 今日重點")
for h in d["highlights"]:
    st.markdown(f"- {h}")

if d.get("notes"):
    st.warning(f"💡 {d['notes']}")

st.markdown("---")
st.markdown("### 今日地點（含高德 APP 一鍵開啟）")

today_places = [p for p in places["places"] if d["day"] in p["day"]]
if not today_places:
    st.caption("此日無預設地點，可在 places.yaml 加入")
else:
    for p in today_places:
        with st.container(border=True):
            img = p.get("image_url", "").strip()
            if img:
                cols = st.columns([1, 2, 1])
                cols[0].image(img, use_container_width=True)
                cols[1].markdown(f"**{p['name']}** ({p['type']})  \n{p.get('note', '')}")
                cols[2].link_button(
                    "📍 高德 APP",
                    amap_marker_url(p["lat"], p["lng"], p["name"]),
                    use_container_width=True,
                )
            else:
                cols = st.columns([3, 1])
                cols[0].markdown(f"**{p['name']}** ({p['type']})  \n{p.get('note', '')}")
                cols[1].link_button(
                    "📍 高德 APP",
                    amap_marker_url(p["lat"], p["lng"], p["name"]),
                    use_container_width=True,
                )

# 推薦住宿/餐廳（根據今日城市）
st.markdown("---")
st.markdown("### 今日住宿與餐廳建議")

today_hotels = [h for h in places.get("hotels", []) if h["city"] in (d["city_to"], d["overnight"])]
today_food = [r for r in places.get("restaurants", []) if r["city"] in (d["city_to"], d["overnight"])]

if today_hotels:
    st.markdown("**🏨 推薦住宿**")
    for h in today_hotels:
        st.markdown(f"- **{h['name']}** ｜ RMB {h['price_rmb']}／晚 ｜ {h['note']}")

if today_food:
    st.markdown("**🍽️ 推薦餐廳**")
    for r in today_food:
        st.markdown(f"- **{r['name']}**（{r['type']}）— {r['note']}")

# 上下一天導航
st.markdown("---")
nav_cols = st.columns(3)
if day_idx > 0:
    nav_cols[0].caption(f"← 前一天：{itin['days'][day_idx-1]['city_to']}")
nav_cols[1].caption(f"目前：Day {d['day']}")
if day_idx < len(itin["days"]) - 1:
    nav_cols[2].caption(f"後一天：{itin['days'][day_idx+1]['city_to']} →")
