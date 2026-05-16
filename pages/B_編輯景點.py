import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import yaml
from utils.github_sync import is_configured, show_setup_instructions, get_file, update_file, upload_image

st.set_page_config(page_title="編輯景點", page_icon="🖼️", layout="wide")
st.title("🖼️ 編輯景點與圖片")
st.caption("改完按儲存會自動同步到 GitHub。圖片可貼 URL 或直接上傳手機照片。")

if not is_configured():
    show_setup_instructions()
    st.stop()

try:
    content, sha = get_file("data/places.yaml")
    data = yaml.safe_load(content)
except Exception as e:
    st.error(f"讀取失敗：{e}")
    st.stop()

places = data.get("places", [])
place_labels = [f"{p['id']} ｜ {p['name']}" for p in places]
sel = st.selectbox("選景點", place_labels)
place_idx = place_labels.index(sel)
p = places[place_idx]

# 預覽現有圖
if p.get("image_url", "").strip():
    st.image(p["image_url"], caption=f"📷 目前的 {p['name']}", use_container_width=True)
else:
    st.info(f"{p['name']} 目前沒有圖片")

st.markdown("---")

# 圖片更新區（兩種方式）
st.subheader("🖼️ 更新圖片")
img_method = st.radio("選一種", ["貼網址 URL", "上傳手機照片"], horizontal=True)

new_image_url = p.get("image_url", "")
if img_method == "貼網址 URL":
    pasted_url = st.text_input("圖片網址（任何網路圖都可）", value=p.get("image_url", ""))
    new_image_url = pasted_url.strip()
    if pasted_url:
        try:
            st.image(pasted_url, caption="預覽", use_container_width=True)
        except Exception:
            st.warning("圖片載入失敗，網址可能有問題")
else:
    uploaded = st.file_uploader(
        "選張照片（jpg/png）",
        type=["jpg", "jpeg", "png", "webp"],
        help="檔案會上傳到 GitHub repo 的 images/places/ 資料夾",
    )
    if uploaded is not None:
        st.image(uploaded, caption="即將上傳", use_container_width=True)
        if st.button("📤 上傳到 GitHub", type="secondary"):
            ext = uploaded.name.split(".")[-1].lower()
            filename = f"{p['id']}.{ext}"
            try:
                raw_url = upload_image(uploaded.getvalue(), filename, f"feat: 上傳 {p['name']} 圖")
                st.session_state[f"uploaded_url_{p['id']}"] = raw_url
                st.success(f"✅ 上傳成功！URL：`{raw_url}`")
                st.info("⬇️ 拉到下面按「儲存景點變更」把這個 URL 寫進景點資料")
            except Exception as e:
                st.error(f"上傳失敗：{e}")

    # 顯示剛上傳的 URL（如果有）
    if f"uploaded_url_{p['id']}" in st.session_state:
        new_image_url = st.session_state[f"uploaded_url_{p['id']}"]

st.markdown("---")

# 其他欄位
st.subheader("📝 景點資料")
with st.form("edit_place"):
    new_name = st.text_input("名稱", value=p.get("name", ""))
    new_type = st.selectbox(
        "類型",
        ["city", "attraction", "bazaar", "border", "checkpoint", "memorial", "route", "food", "airport"],
        index=["city", "attraction", "bazaar", "border", "checkpoint", "memorial", "route", "food", "airport"].index(p.get("type", "attraction")) if p.get("type") in ["city", "attraction", "bazaar", "border", "checkpoint", "memorial", "route", "food", "airport"] else 1,
    )
    c1, c2 = st.columns(2)
    new_lat = c1.number_input("緯度 (lat)", value=float(p.get("lat", 0)), format="%.4f")
    new_lng = c2.number_input("經度 (lng)", value=float(p.get("lng", 0)), format="%.4f")

    days_str = ",".join(str(x) for x in p.get("day", []))
    new_days_str = st.text_input("對應 Day（用逗號分隔）", value=days_str, help="例：4,5 = 第 4、5 天會出現")

    new_note = st.text_area("說明", value=p.get("note", ""), height=80)
    final_image_url = st.text_input(
        "圖片 URL（會自動帶上面選的）",
        value=new_image_url,
        help="如果剛上傳照片，這裡會自動填好",
    )

    submitted = st.form_submit_button("💾 儲存景點變更", type="primary", use_container_width=True)

if submitted:
    try:
        day_list = [int(x.strip()) for x in new_days_str.split(",") if x.strip()]
    except ValueError:
        st.error("Day 欄位請用「逗號分隔的數字」，例如 4,5")
        st.stop()

    p["name"] = new_name
    p["type"] = new_type
    p["lat"] = round(float(new_lat), 4)
    p["lng"] = round(float(new_lng), 4)
    p["day"] = day_list
    p["note"] = new_note
    p["image_url"] = final_image_url.strip()

    new_yaml = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)

    try:
        commit_url = update_file(
            "data/places.yaml",
            new_yaml,
            f"edit(UI): {p['name']} 景點修改",
            sha,
        )
        # 清除上傳暫存
        st.session_state.pop(f"uploaded_url_{p['id']}", None)
        st.success("✅ 已儲存！1-2 分鐘後線上版自動更新。")
        if commit_url:
            st.link_button("查看 commit", commit_url)
        st.balloons()
    except Exception as e:
        st.error(f"儲存失敗：{e}")
