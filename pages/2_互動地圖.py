import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import folium
from streamlit_folium import st_folium
from utils.data_loader import load_places, load_itinerary
from utils.amap import amap_marker_url, amap_navigation_url

st.set_page_config(page_title="互動地圖", page_icon="🗺️", layout="wide")
st.title("互動地圖")

st.caption(
    "中國地區用 OSM 磚塊（不需翻牆）。點任一地點可一鍵丟到高德地圖 APP（手機）。"
)

with st.expander("💡 為什麼這趟要『喀什進、烏魯木齊出』？", expanded=False):
    st.markdown(
        """
        **獨庫公路是線性單向**，南端在庫車、北端在獨山子（離烏市 250km）。
        走完獨庫公路全段，車自然就到烏魯木齊那邊了。

        如果硬要回喀什：
        - 烏市→喀什走南疆全境 1500 km，多 2 天車程
        - 或烏市→喀什飛回去（多 RMB 1500 + 一天）

        買 **開口票**（Multi-City：台北→喀什、烏市→台北）最順。
        下面地圖：
        - **藍實線** = 實際走的路徑（不回頭）
        - **灰虛線** = 如果硬要喀什折返會多走的回頭路（白費 2 天）
        - **紅色 ✈️** = 喀什機場（進）和烏市機場（出）
        """
    )

places_data = load_places()
itin = load_itinerary()

type_filter = st.multiselect(
    "篩選類型",
    ["city", "attraction", "bazaar", "border", "checkpoint", "memorial", "route", "food"],
    default=["city", "attraction", "bazaar", "border"],
)

day_filter = st.slider("第幾天", 1, 15, (1, 15))

filtered = [
    p for p in places_data["places"]
    if p["type"] in type_filter
    and any(day_filter[0] <= d <= day_filter[1] for d in p["day"])
]

st.caption(f"目前顯示 {len(filtered)} 個地點")

if filtered:
    avg_lat = sum(p["lat"] for p in filtered) / len(filtered)
    avg_lng = sum(p["lng"] for p in filtered) / len(filtered)
else:
    avg_lat, avg_lng = 39.5, 80.0

m = folium.Map(
    location=[avg_lat, avg_lng],
    zoom_start=6,
    tiles="OpenStreetMap",
)

color_by_type = {
    "city": "blue", "attraction": "green", "bazaar": "purple",
    "border": "red", "checkpoint": "orange", "memorial": "gray",
    "route": "darkblue", "food": "pink",
}

# 加路線（按 day 順序連接城市）
route_pts = []
for d in itin["days"]:
    target_city = d["city_to"]
    for p in places_data["places"]:
        if p["type"] == "city" and target_city in p["name"]:
            route_pts.append([p["lat"], p["lng"]])
            break

if len(route_pts) >= 2:
    folium.PolyLine(
        route_pts, color="#1a4d6e", weight=4, opacity=0.85,
        tooltip="實際路線：喀什→塔縣→和田→阿克蘇→庫車→獨庫公路→烏市",
    ).add_to(m)

# 假設要喀什折返的虛線（從烏市穿沙漠回喀什 1500km）
kashgar_pt = [39.467663, 75.989138]
urumqi_pt = [43.825592, 87.616848]
folium.PolyLine(
    [urumqi_pt, [42, 81], [40, 78], kashgar_pt],
    color="#888", weight=2, opacity=0.5, dash_array="6,10",
    tooltip="× 假設要喀什折返會多走 1500km / 2 天車程（不推薦）",
).add_to(m)

# 機場標記
folium.Marker(
    kashgar_pt,
    popup="✈️ 喀什機場 KHG（進）",
    tooltip="喀什機場 KHG（進）",
    icon=folium.Icon(color="red", icon="plane", prefix="fa"),
).add_to(m)
folium.Marker(
    urumqi_pt,
    popup="✈️ 烏魯木齊機場 URC（出）",
    tooltip="烏魯木齊機場 URC（出）",
    icon=folium.Icon(color="red", icon="plane", prefix="fa"),
).add_to(m)

for p in filtered:
    days_str = ", ".join(f"Day {d}" for d in p["day"])
    amap_link = amap_marker_url(p["lat"], p["lng"], p["name"])
    nav_link = amap_navigation_url(p["lat"], p["lng"], p["name"])
    popup_html = f"""
    <div style="font-family:sans-serif;font-size:13px;min-width:200px;">
      <b>{p['name']}</b><br>
      <span style="color:#666">{days_str}</span><br>
      {p.get('note', '')}<br>
      <br>
      <a href="{amap_link}" target="_blank">📍 高德 APP 開啟</a><br>
      <a href="{nav_link}" target="_blank">🧭 高德導航</a>
    </div>
    """
    folium.Marker(
        [p["lat"], p["lng"]],
        popup=folium.Popup(popup_html, max_width=260),
        tooltip=p["name"],
        icon=folium.Icon(color=color_by_type.get(p["type"], "gray"), icon="info-sign"),
    ).add_to(m)

st_folium(m, height=560, use_container_width=True, returned_objects=[])

st.markdown("---")
st.subheader("地點清單（含高德 APP 連結）")

for p in filtered:
    days_str = ", ".join(f"Day {d}" for d in p["day"])
    cols = st.columns([3, 2, 2, 2])
    cols[0].markdown(f"**{p['name']}**  \n{p.get('note', '')}")
    cols[1].caption(f"{days_str} ｜ {p['type']}")
    cols[2].link_button(
        "📍 高德標點",
        amap_marker_url(p["lat"], p["lng"], p["name"]),
        use_container_width=True,
    )
    cols[3].link_button(
        "🧭 導航",
        amap_navigation_url(p["lat"], p["lng"], p["name"]),
        use_container_width=True,
    )
