import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
from datetime import date
from utils.data_loader import load_ctrip_refs
from utils.storage import load_json, append_ctrip, delete_ctrip
from utils.currency import fmt_twd, rmb_to_twd

st.set_page_config(page_title="Ctrip 比價", page_icon="🛒", layout="wide")
st.title("Ctrip（攜程）比價")
st.caption("找包車、跟團、住宿時對攜程套裝產品比價。攜程 90% 大陸用戶在用，價格基準。")

refs = load_ctrip_refs()

tab_search, tab_pricing, tab_compare = st.tabs(["🔍 攜程搜尋捷徑", "💵 行情參考", "📋 我的比價清單"])

with tab_search:
    st.subheader("攜程搜尋捷徑")
    st.caption("點下面任一連結直接跳到攜程對應頁。海外 IP 也能瀏覽，下單需大陸帳號或微信支付。")
    for s in refs["search_shortcuts"]:
        with st.container(border=True):
            cols = st.columns([3, 2])
            cols[0].markdown(f"**{s['label']}**  \n_{s['note']}_")
            cols[1].link_button("前往攜程 →", s["url"], use_container_width=True)

    st.markdown("---")
    st.markdown("**自訂搜尋**")
    keyword = st.text_input("關鍵字", value="南疆 15 日 包車")
    st.link_button(
        f"在攜程搜尋「{keyword}」",
        f"https://you.ctrip.com/searchsite/all/{keyword.replace(' ', '%20')}.html",
        use_container_width=True,
    )

with tab_pricing:
    st.subheader("典型行情區間（暑期）")
    pricing = refs["typical_pricing"]
    for k, v in pricing.items():
        with st.container(border=True):
            st.markdown(f"### {v['label']}")
            cols = st.columns(3)
            if "per_person_twd" in v:
                cols[0].metric("人均 TWD", v["per_person_twd"])
            if "total_rmb" in v:
                cols[0].metric("總價 RMB", v["total_rmb"])
                cols[1].metric("≈ TWD", v.get("twd_equivalent", "—"))
            if "rmb" in v:
                cols[0].metric("RMB", v["rmb"])
            cols[2].caption(v["note"])

with tab_compare:
    st.subheader("我的比價清單")
    st.caption("貼任何看到的攜程套裝/包車產品，記下你想對比的方案。")

    with st.form("add_comparison", clear_on_submit=True):
        c1, c2 = st.columns(2)
        vendor = c1.text_input("供應商", value="攜程", placeholder="攜程／飛豬／馬蜂窩")
        product = c2.text_input("產品名稱", placeholder="ex. 南疆 15 日包車（喀什-塔縣-和田-庫車）")

        c3, c4, c5 = st.columns(3)
        price_twd = c3.number_input("價格 TWD（兩人合計）", min_value=0, step=1000)
        contact = c4.text_input("聯絡方式", placeholder="客服 LINE/電話/微信")
        url = c5.text_input("產品連結", placeholder="https://...")

        c6, c7 = st.columns(2)
        pros = c6.text_area("優點", height=80, placeholder="ex. 含住宿、含早餐、4 星酒店")
        cons = c7.text_area("缺點", height=80, placeholder="ex. 強制購物、行程趕、不含機票")

        submit = st.form_submit_button("➕ 加入比價清單", use_container_width=True, type="primary")
        if submit and product:
            append_ctrip({
                "vendor": vendor,
                "product_name": product,
                "price_twd": price_twd,
                "contact": contact,
                "url": url,
                "pros": pros,
                "cons": cons,
            })
            st.toast("已加入比價清單", icon="✅")
            st.rerun()

    st.markdown("---")
    items = load_json("ctrip_comparisons.json", default=[])
    if not items:
        st.info("還沒加任何方案。在攜程找到合適的套裝就貼進來。")
    else:
        for it in sorted(items, key=lambda x: x.get("price_twd", 0)):
            with st.container(border=True):
                cols = st.columns([3, 1, 1, 1])
                cols[0].markdown(f"**{it['product_name']}**  \n_{it.get('vendor', '?')}_")
                cols[1].metric("TWD", fmt_twd(it.get("price_twd", 0)))
                cols[2].metric("人均", fmt_twd(it.get("price_twd", 0) / 2))
                if cols[3].button("🗑", key=f"del_ctrip_{it['id']}"):
                    delete_ctrip(it["id"])
                    st.rerun()
                if it.get("url"):
                    st.caption(f"🔗 [{it['url'][:60]}...]({it['url']})")
                if it.get("pros") or it.get("cons"):
                    p_cols = st.columns(2)
                    if it.get("pros"):
                        p_cols[0].success(f"優點：{it['pros']}")
                    if it.get("cons"):
                        p_cols[1].error(f"缺點：{it['cons']}")
                if it.get("contact"):
                    st.caption(f"📞 {it['contact']}")

        st.markdown("---")
        st.markdown("**對照我的預算**")
        my_budget_twd = 200700  # 從 budget.yaml 推
        cheapest = min(items, key=lambda x: x.get("price_twd", 999999))
        st.info(
            f"目前比價最便宜：{cheapest['product_name']} = {fmt_twd(cheapest['price_twd'])}  \n"
            f"我自己估算總預算：{fmt_twd(my_budget_twd)}  \n"
            f"差額：{fmt_twd(my_budget_twd - cheapest['price_twd'])}"
        )
