"""統一編輯頁 — 按 Day 分組，可加/刪/改景點。改完自動同步到 GitHub。"""
import sys
import re
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import yaml
from utils.github_sync import is_configured, show_setup_instructions, get_file, update_file, upload_image, list_recent_commits

st.set_page_config(page_title="編輯日程", page_icon="✏️", layout="wide")
st.title("✏️ 編輯日程")
st.caption("按天編輯：選 Day → 加/改/刪景點 → 自動同步")

if not is_configured():
    show_setup_instructions()
    st.stop()


def show_save_result(result: dict, label: str):
    """儲存後寫入 session_state，rerun 後在頁首 banner 顯示憑證。"""
    if "save_log" not in st.session_state:
        st.session_state["save_log"] = []
    st.session_state["save_log"].insert(0, {
        "label": label,
        "commit_sha": result.get("commit_sha", ""),
        "commit_url": result.get("commit_url", ""),
        "verified": result.get("verified"),
    })
    st.session_state["save_log"] = st.session_state["save_log"][:10]
    st.rerun()


# ===== 頁首：上次儲存結果 banner（rerun 後也看得到）=====
if st.session_state.get("save_log"):
    last = st.session_state["save_log"][0]
    if last.get("verified"):
        st.success(
            f"✅ 上一次儲存：「{last['label']}」已寫進 GitHub — commit "
            f"[`{last['commit_sha']}`]({last['commit_url']})（按連結可直接看到 diff）"
        )
    else:
        st.error(
            f"⚠️ 上一次儲存「{last['label']}」verify 失敗 — "
            f"請打開 [{last['commit_sha']}]({last['commit_url']}) 人工確認"
        )

# ---------- 讀資料 ----------
try:
    places_content, places_sha = get_file("data/places.yaml")
    itin_content, itin_sha = get_file("data/itinerary.yaml")
    places_data = yaml.safe_load(places_content)
    itin = yaml.safe_load(itin_content)
except Exception as e:
    st.error(f"讀取失敗：{e}")
    st.stop()


def save_places(message: str):
    new_yaml = yaml.safe_dump(places_data, allow_unicode=True, sort_keys=False, default_flow_style=False)
    return update_file("data/places.yaml", new_yaml, message, places_sha)


def save_itin(message: str):
    new_yaml = yaml.safe_dump(itin, allow_unicode=True, sort_keys=False, default_flow_style=False)
    return update_file("data/itinerary.yaml", new_yaml, message, itin_sha)


def parse_coords(s: str) -> tuple[float, float] | None:
    """解析座標：'37.778, 75.230' 或 Google Maps URL。"""
    s = s.strip()
    if not s:
        return None
    # 純座標格式：「lat, lng」
    m = re.match(r"^\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*$", s)
    if m:
        return float(m.group(1)), float(m.group(2))
    # Google Maps URL: ...@LAT,LNG,...
    m = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", s)
    if m:
        return float(m.group(1)), float(m.group(2))
    # Google Maps URL: ?q=LAT,LNG
    m = re.search(r"q=(-?\d+\.\d+),(-?\d+\.\d+)", s)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None


# ---------- 選 Day ----------
day_options = [d["day"] for d in itin["days"]]
day_labels = {d["day"]: f"Day {d['day']} - {d['date']} {d['city_from']}→{d['city_to']}" for d in itin["days"]}
selected_day = st.selectbox(
    "📅 選日期",
    day_options,
    format_func=lambda x: day_labels[x],
    key="day_picker",
)

current_day_data = next(d for d in itin["days"] if d["day"] == selected_day)

# ---------- Day-level：備註、封面景點 ----------
with st.expander(f"📝 Day {selected_day} 的備註與封面", expanded=False):
    today_places_for_cover = [p for p in places_data["places"] if selected_day in p.get("day", [])]
    cover_opts = [""] + [p["id"] for p in today_places_for_cover]
    cover_labels = {"": "（自動選第一個有圖的）"}
    for p in today_places_for_cover:
        cover_labels[p["id"]] = f"{p['name']} {'✓' if p.get('image_url') else '✗ 沒圖'}"
    current_cover = current_day_data.get("cover_place_id", "") or ""
    if current_cover not in cover_opts:
        current_cover = ""

    with st.form(f"day_meta_{selected_day}"):
        new_cover = st.selectbox(
            "封面景點（顯示在「每日詳情」最上方那張大圖）",
            cover_opts,
            index=cover_opts.index(current_cover),
            format_func=lambda x: cover_labels.get(x, x),
        )
        new_notes = st.text_area("備註/提醒", value=current_day_data.get("notes", ""), height=100)
        new_overnight = st.text_input("住宿", value=current_day_data.get("overnight", ""))
        if new_cover:
            preview = next((p for p in places_data["places"] if p["id"] == new_cover), None)
            if preview and preview.get("image_url"):
                st.image(preview["image_url"], caption=f"預覽：{preview['name']}", use_container_width=True)

        if st.form_submit_button("💾 儲存 Day 資料", type="primary"):
            current_day_data["cover_place_id"] = new_cover or None
            current_day_data["notes"] = new_notes
            current_day_data["overnight"] = new_overnight
            try:
                result = save_itin(f"edit(UI): Day {selected_day} 備註/封面")
                show_save_result(result, f"Day {selected_day} 備註/封面")
            except Exception as e:
                st.error(f"❌ 儲存失敗（GitHub 沒收到）：{e}")

st.markdown("---")

# ---------- 列出這天的景點 ----------
today_places = [p for p in places_data["places"] if selected_day in p.get("day", [])]
st.markdown(f"### 📍 Day {selected_day} 的景點（{len(today_places)} 個）")

if not today_places:
    st.info("這天還沒有景點。下面可以新增。")

for idx, p in enumerate(today_places):
    with st.expander(f"📍 {p['name']}", expanded=False):
        if p.get("image_url"):
            st.image(p["image_url"], use_container_width=True)

        # 換圖區（form 外，因為 file_uploader 不能在 form 中觸發上傳）
        st.markdown("**🖼️ 換圖**")
        col1, col2 = st.columns(2)
        with col1:
            pasted = st.text_input(f"貼圖片網址", value=p.get("image_url", ""), key=f"img_url_{p['id']}")
        with col2:
            uploaded = st.file_uploader(
                "或上傳照片",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"upload_{p['id']}",
            )
            if uploaded is not None:
                if st.button(f"📤 上傳到 GitHub", key=f"upload_btn_{p['id']}"):
                    try:
                        ext = uploaded.name.split(".")[-1].lower()
                        filename = f"{p['id']}.{ext}"
                        raw_url = upload_image(uploaded.getvalue(), filename, f"feat: 上傳 {p['name']} 圖")
                        st.session_state[f"img_url_{p['id']}"] = raw_url
                        st.success(f"✅ 上傳成功，按下「儲存景點」把網址寫入")
                        st.rerun()
                    except Exception as e:
                        st.error(f"上傳失敗：{e}")

        st.markdown("---")
        with st.form(f"edit_place_{p['id']}"):
            new_name = st.text_input("名稱", value=p["name"], key=f"name_{p['id']}")
            new_note = st.text_area("說明", value=p.get("note", ""), height=80, key=f"note_{p['id']}")
            new_type = st.selectbox(
                "類型",
                ["city", "attraction", "bazaar", "border", "checkpoint", "memorial", "route", "food", "airport"],
                index=["city", "attraction", "bazaar", "border", "checkpoint", "memorial", "route", "food", "airport"].index(p.get("type", "attraction")) if p.get("type") in ["city", "attraction", "bazaar", "border", "checkpoint", "memorial", "route", "food", "airport"] else 1,
                key=f"type_{p['id']}",
            )
            new_days = st.multiselect(
                "出現在哪幾天",
                day_options,
                default=p.get("day", []),
                key=f"days_{p['id']}",
                help="取消勾選某天 = 從那天移除這景點",
            )

            cc1, cc2, cc3 = st.columns([1, 1, 1])
            save_btn = cc1.form_submit_button("💾 儲存", type="primary", use_container_width=True)
            remove_day_btn = cc2.form_submit_button(f"🚫 從 Day {selected_day} 移除", use_container_width=True)
            delete_btn = cc3.form_submit_button("🗑 整個刪除", use_container_width=True)

            if save_btn:
                p["name"] = new_name
                p["note"] = new_note
                p["type"] = new_type
                p["day"] = sorted(new_days)
                p["image_url"] = pasted
                try:
                    result = save_places(f"edit(UI): {p['name']} 景點修改")
                    show_save_result(result, f"{p['name']} 景點修改")
                except Exception as e:
                    st.error(f"❌ 儲存失敗（GitHub 沒收到）：{e}")

            if remove_day_btn:
                p["day"] = [d for d in p.get("day", []) if d != selected_day]
                try:
                    result = save_places(f"edit(UI): {p['name']} 從 Day {selected_day} 移除")
                    show_save_result(result, f"{p['name']} 從 Day {selected_day} 移除")
                except Exception as e:
                    st.error(f"❌ 儲存失敗（GitHub 沒收到）：{e}")

            if delete_btn:
                places_data["places"] = [x for x in places_data["places"] if x["id"] != p["id"]]
                try:
                    result = save_places(f"edit(UI): 刪除景點 {p['name']}")
                    show_save_result(result, f"刪除 {p['name']}")
                except Exception as e:
                    st.error(f"❌ 刪除失敗（GitHub 沒收到）：{e}")

# ---------- 新增景點 ----------
st.markdown("---")
st.markdown(f"### ➕ 在 Day {selected_day} 新增景點")

with st.form("add_new_place"):
    new_name = st.text_input("名稱（必填）", placeholder="例：紅其拉甫口岸")
    new_type = st.selectbox(
        "類型",
        ["attraction", "city", "bazaar", "border", "checkpoint", "memorial", "route", "food", "airport"],
        index=0,
    )
    new_note = st.text_area("說明（選填）", height=80, placeholder="例：中巴邊境海拔 4733m")

    coords_input = st.text_input(
        "座標（選填）",
        placeholder="貼 Google Maps URL 或「緯度,經度」例：37.778, 75.230",
        help="不填會用 0,0（之後可在地圖上拖）",
    )

    new_days_add = st.multiselect(
        "出現在哪幾天",
        day_options,
        default=[selected_day],
        help="可以同時加到多天（例如同一個地點 Day 4、Day 5 都會去）",
    )

    new_img_url = st.text_input("圖片網址（選填）", placeholder="貼任何網址，或之後再上傳")

    add_btn = st.form_submit_button("➕ 加入", type="primary", use_container_width=True)

    if add_btn:
        if not new_name:
            st.error("名稱必填")
        else:
            coords = parse_coords(coords_input) if coords_input else (0.0, 0.0)
            if coords is None:
                st.error("座標格式錯誤，請貼「lat, lng」或 Google Maps URL")
            else:
                # 生成唯一 id
                base_id = re.sub(r"[^a-zA-Z0-9]", "_", new_name.lower())[:30] or f"place_{uuid.uuid4().hex[:6]}"
                new_id = base_id
                existing_ids = {p["id"] for p in places_data["places"]}
                suffix = 1
                while new_id in existing_ids:
                    suffix += 1
                    new_id = f"{base_id}_{suffix}"

                new_place = {
                    "id": new_id,
                    "name": new_name,
                    "type": new_type,
                    "lat": round(coords[0], 4),
                    "lng": round(coords[1], 4),
                    "day": sorted(new_days_add),
                    "note": new_note,
                    "image_url": new_img_url,
                }
                places_data["places"].append(new_place)

                try:
                    result = save_places(f"add(UI): 新增景點 {new_name}")
                    show_save_result(result, f"新增 {new_name} 到 Day {', '.join(str(d) for d in new_days_add)}")
                except Exception as e:
                    st.error(f"❌ 新增失敗（GitHub 沒收到）：{e}")

# ---------- 最近儲存記錄（從 GitHub 真實讀回，不靠 session_state） ----------
st.markdown("---")
st.markdown("### 📜 最近儲存記錄（從 GitHub 真實讀回）")
st.caption("這裡顯示的是 GitHub 真的收到的 commit，按下儲存後就會多一筆。沒看到就是沒存進去。")
try:
    commits = list_recent_commits(limit=8)
    if not commits:
        st.info("還沒有任何 commit。")
    else:
        for c in commits:
            badge = "🟢" if c["message"].startswith(("edit(UI)", "add(UI)")) else "⚪"
            st.markdown(
                f"{badge} `{c['sha']}` · {c['date']} · [{c['message']}]({c['html_url']}) · {c['author']}"
            )
except Exception as e:
    st.error(f"讀取 commit 列表失敗：{e}")
