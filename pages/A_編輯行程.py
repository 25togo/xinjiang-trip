import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import yaml
from utils.github_sync import is_configured, show_setup_instructions, get_file, update_file

st.set_page_config(page_title="編輯行程", page_icon="✏️", layout="wide")
st.title("✏️ 編輯行程")
st.caption("改完按儲存會自動同步到 GitHub，1-2 分鐘後線上版自動更新")

if not is_configured():
    show_setup_instructions()
    st.stop()

# 讀取最新版本（同時讀 places 給封面選擇器用）
try:
    content, sha = get_file("data/itinerary.yaml")
    itin = yaml.safe_load(content)
    places_content, _ = get_file("data/places.yaml")
    places_data = yaml.safe_load(places_content)
except Exception as e:
    st.error(f"讀取失敗：{e}")
    st.stop()

day_labels = [f"Day {d['day']} - {d['date']} {d['city_from']}→{d['city_to']}" for d in itin["days"]]
sel = st.selectbox("選擇日期", day_labels)
day_idx = day_labels.index(sel)
d = itin["days"][day_idx]

with st.form("edit_day"):
    c1, c2, c3 = st.columns(3)
    new_date = c1.text_input("日期 (YYYY-MM-DD)", value=str(d.get("date", "")))
    new_from = c2.text_input("起", value=d.get("city_from", ""))
    new_to = c3.text_input("迄", value=d.get("city_to", ""))

    new_transport = st.text_input("交通", value=d.get("transport", ""))

    c4, c5, c6, c7 = st.columns(4)
    new_alt = c4.number_input("海拔 (m)", value=int(d.get("altitude_m", 0)), step=100)
    new_km = c5.number_input("里程 (km)", value=int(d.get("distance_km", 0)), step=10)
    new_hours = c6.number_input("車程 (h)", value=float(d.get("drive_hours", 0)), step=0.5)
    new_overnight = c7.text_input("住宿", value=d.get("overnight", ""))

    new_highlights = st.text_area(
        "今日重點（每行一個 bullet）",
        value="\n".join(d.get("highlights", [])),
        height=180,
        help="一行寫一個重點，會自動轉成 bullet list",
    )

    new_notes = st.text_area("備註／提醒", value=d.get("notes", ""), height=80)

    st.markdown("---")
    st.markdown("**📷 今日封面照片** — 選哪個景點的照片當這天的首圖")
    today_places = [p for p in places_data.get("places", []) if d["day"] in p.get("day", [])]
    cover_options = [("", "（自動選第一個有圖的）")] + [(p["id"], f"{p['name']} {'✓ 有圖' if p.get('image_url') else '✗ 沒圖'}") for p in today_places]
    cover_ids = [o[0] for o in cover_options]
    cover_labels = {o[0]: o[1] for o in cover_options}
    current_cover = d.get("cover_place_id", "")
    if current_cover not in cover_ids:
        current_cover = ""
    new_cover_id = st.selectbox(
        "封面景點",
        cover_ids,
        index=cover_ids.index(current_cover),
        format_func=lambda x: cover_labels.get(x, x),
    )
    # 預覽
    if new_cover_id:
        preview_place = next((p for p in places_data["places"] if p["id"] == new_cover_id), None)
        if preview_place and preview_place.get("image_url"):
            st.image(preview_place["image_url"], caption=f"預覽：{preview_place['name']}", use_container_width=True)

    submitted = st.form_submit_button("💾 儲存到 GitHub", type="primary", use_container_width=True)

if submitted:
    d["date"] = new_date
    d["city_from"] = new_from
    d["city_to"] = new_to
    d["transport"] = new_transport
    d["altitude_m"] = int(new_alt)
    d["distance_km"] = int(new_km)
    d["drive_hours"] = float(new_hours)
    d["overnight"] = new_overnight
    d["highlights"] = [h.strip() for h in new_highlights.split("\n") if h.strip()]
    d["notes"] = new_notes
    d["cover_place_id"] = new_cover_id or None

    new_yaml = yaml.safe_dump(itin, allow_unicode=True, sort_keys=False, default_flow_style=False)

    try:
        commit_url = update_file(
            "data/itinerary.yaml",
            new_yaml,
            f"edit(UI): Day {d['day']} {d['city_from']}→{d['city_to']} 修改",
            sha,
        )
        st.success("✅ 已儲存！1-2 分鐘後線上版自動更新。")
        if commit_url:
            st.link_button("查看 commit", commit_url)
        st.balloons()
    except Exception as e:
        st.error(f"儲存失敗：{e}")
