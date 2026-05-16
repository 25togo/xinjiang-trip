import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from utils.data_loader import load_packing
from utils.storage import load_json, save_json

st.set_page_config(page_title="打包清單", page_icon="🎒", layout="wide")
st.title("打包清單")
st.caption("勾選已準備好的，會自動存。出發前一天再掃一遍。")

packing = load_packing()
checked = load_json("packed.json", default={})

# 統計
all_items = [(c["name"], i) for c in packing["categories"] for i in c["items"]]
total = len(all_items)
must_count = sum(1 for _, i in all_items if i.get("must"))
checked_count = sum(1 for k, v in checked.items() if v)
must_checked = sum(
    1 for cname, item in all_items
    if item.get("must") and checked.get(f"{cname}_{item['item']}", False)
)

c1, c2, c3 = st.columns(3)
c1.metric("總項目", total, help=f"必備 {must_count} 項")
c2.metric("已備齊", f"{checked_count} / {total}")
c3.metric("必備備齊", f"{must_checked} / {must_count}",
          delta="✅ 全好" if must_checked == must_count else "⚠️ 還有缺")

st.progress(checked_count / total if total else 0)

st.markdown("---")

show_only_unchecked = st.toggle("只顯示尚未備齊的", value=False)

dirty = False
for cat in packing["categories"]:
    cat_items = cat["items"]
    cat_keys = [f"{cat['name']}_{i['item']}" for i in cat_items]
    cat_done = sum(1 for k in cat_keys if checked.get(k))

    with st.expander(f"**{cat['name']}** ({cat_done}/{len(cat_items)})", expanded=True):
        for i in cat_items:
            key = f"{cat['name']}_{i['item']}"
            current = checked.get(key, False)
            if show_only_unchecked and current:
                continue
            label_parts = [i["item"]]
            if i.get("qty", 1) > 1:
                label_parts.append(f"× {i['qty']}")
            if i.get("must"):
                label_parts.append("🔴")
            if i.get("note"):
                label_parts.append(f"_{i['note']}_")
            label = " ".join(label_parts)
            new_val = st.checkbox(label, value=current, key=f"chk_{key}")
            if new_val != current:
                checked[key] = new_val
                dirty = True

if dirty:
    save_json("packed.json", checked)
    st.toast("已存", icon="💾")
