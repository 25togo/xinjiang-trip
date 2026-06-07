import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
from datetime import date
from utils.data_loader import load_budget
from utils.currency import rmb_to_twd, twd_to_rmb, fmt_twd, fmt_rmb
from utils.storage import load_json, append_expense, delete_expense, append_budget_item, delete_budget_item

st.set_page_config(page_title="預算與記帳", page_icon="💰", layout="wide")
st.title("預算與記帳")

budget = load_budget()
rate = budget["currency"]["rmb_to_twd"]

tab_budget, tab_log, tab_split = st.tabs(["📊 預算規劃", "✍️ 即時記帳", "🤝 兩人均攤"])

with tab_budget:
    st.subheader("預算規劃")
    st.caption(f"匯率參考：1 RMB = {rate} TWD")

    with st.form("add_budget", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        item_name = c1.text_input("項目", placeholder="ex. 機票、住宿、包車")
        amount_twd = c2.number_input("金額 (TWD)", min_value=0, step=1000, value=0)
        category = c3.selectbox("類別", ["交通", "住宿", "餐飲", "門票", "採購", "雜支", "其他"])
        note = st.text_input("備註", placeholder="ex. 兩人來回，東方航空")
        add_btn = st.form_submit_button("➕ 新增", use_container_width=True, type="primary")
        if add_btn and item_name and amount_twd > 0:
            append_budget_item({
                "name": item_name,
                "amount_twd": amount_twd,
                "amount_rmb": twd_to_rmb(amount_twd, rate),
                "category": category,
                "note": note,
            })
            st.toast(f"已加入「{item_name}」", icon="💾")
            st.rerun()

    st.markdown("---")
    plan_items = load_json("budget_plan.json", default=[])

    if not plan_items:
        st.info("還沒有項目。用上方表單新增。")
    else:
        total_twd = 0
        for item in plan_items:
            with st.container(border=True):
                cols = st.columns([3, 2, 2, 3, 1])
                cols[0].markdown(f"**{item['name']}**")
                cols[1].markdown(f"NT$ {item['amount_twd']:,}")
                cols[2].caption(f"≈ ¥{item['amount_rmb']:,.0f}")
                cols[3].caption(item.get("note", "") or "—")
                if cols[4].button("🗑", key=f"del_b_{item['id']}"):
                    delete_budget_item(item["id"])
                    st.rerun()
            total_twd += item["amount_twd"]

        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("兩人合計", fmt_twd(total_twd))
        c2.metric("人均", fmt_twd(total_twd / 2))
        c3.metric("人均 RMB", fmt_rmb(twd_to_rmb(total_twd / 2, rate)))

with tab_log:
    st.subheader("即時記帳")
    st.caption("出發後在新疆隨時記。手機點下方表單就能加。")

    # 新增表單
    with st.form("add_expense", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        d = c1.date_input("日期", value=date.today())
        amount_rmb = c2.number_input("金額 (RMB)", min_value=0.0, step=10.0, value=0.0)
        category = c3.selectbox("類別", [
            "餐飲", "住宿", "交通", "門票", "包車", "採購", "雜支"
        ])

        c4, c5, c6 = st.columns(3)
        payer = c4.selectbox("付款人", ["我", "朋友", "公帳"])
        sharing = c5.selectbox("分攤方式", ["均攤", "我獨享", "朋友獨享"])
        note = c6.text_input("備註", placeholder="ex. 喀什大巴扎午餐")

        submitted = st.form_submit_button("➕ 新增", use_container_width=True, type="primary")
        if submitted and amount_rmb > 0:
            append_expense({
                "date": d.isoformat(),
                "amount_rmb": amount_rmb,
                "amount_twd": rmb_to_twd(amount_rmb, rate),
                "category": category,
                "payer": payer,
                "sharing": sharing,
                "note": note,
            })
            st.toast(f"已記 ¥{amount_rmb}", icon="💾")
            st.rerun()

    # 顯示
    st.markdown("---")
    expenses = load_json("expenses.json", default=[])
    if not expenses:
        st.info("還沒有記帳。出發後開始記。")
    else:
        # 按日期反序
        expenses_sorted = sorted(expenses, key=lambda e: e["date"], reverse=True)

        # 篩選
        col_a, col_b = st.columns(2)
        cat_filter = col_a.multiselect(
            "類別篩選",
            ["餐飲", "住宿", "交通", "門票", "包車", "採購", "雜支"],
            default=[],
        )
        if cat_filter:
            expenses_sorted = [e for e in expenses_sorted if e["category"] in cat_filter]

        for e in expenses_sorted:
            with st.container(border=True):
                cols = st.columns([1, 1, 1, 1, 2, 1])
                cols[0].caption(e["date"])
                cols[1].markdown(f"**{fmt_rmb(e['amount_rmb'])}**")
                cols[2].caption(f"≈ {fmt_twd(e['amount_twd'])}")
                cols[3].caption(f"{e['category']} ｜ {e['payer']}付")
                cols[4].caption(e.get("note", "") or "—")
                if cols[5].button("🗑", key=f"del_{e['id']}"):
                    delete_expense(e["id"])
                    st.rerun()

        # 統計
        st.markdown("---")
        total_rmb = sum(e["amount_rmb"] for e in expenses)
        total_twd = sum(e["amount_twd"] for e in expenses)
        c1, c2, c3 = st.columns(3)
        c1.metric("已花費 RMB", fmt_rmb(total_rmb))
        c2.metric("≈ TWD", fmt_twd(total_twd))
        c3.metric("人均", fmt_twd(total_twd / 2))

with tab_split:
    st.subheader("兩人均攤結算")
    expenses = load_json("expenses.json", default=[])
    if not expenses:
        st.info("還沒有記帳。")
    else:
        # 計算每人實付 vs 應付
        my_paid = 0
        friend_paid = 0
        my_share = 0
        friend_share = 0

        for e in expenses:
            amount = e["amount_rmb"]
            payer = e["payer"]
            sharing = e["sharing"]

            if payer == "我":
                my_paid += amount
            elif payer == "朋友":
                friend_paid += amount
            else:
                my_paid += amount / 2
                friend_paid += amount / 2

            if sharing == "均攤":
                my_share += amount / 2
                friend_share += amount / 2
            elif sharing == "我獨享":
                my_share += amount
            elif sharing == "朋友獨享":
                friend_share += amount

        balance_me = my_paid - my_share

        c1, c2, c3 = st.columns(3)
        c1.metric("我實付 (RMB)", fmt_rmb(my_paid))
        c2.metric("我應付 (RMB)", fmt_rmb(my_share))
        if balance_me > 0:
            c3.metric("結算", f"朋友欠我 {fmt_rmb(balance_me)}",
                      delta=f"≈ {fmt_twd(rmb_to_twd(balance_me, rate))}")
        elif balance_me < 0:
            c3.metric("結算", f"我欠朋友 {fmt_rmb(abs(balance_me))}",
                      delta=f"≈ {fmt_twd(rmb_to_twd(abs(balance_me), rate))}",
                      delta_color="inverse")
        else:
            c3.metric("結算", "兩不相欠")

        st.markdown("---")
        st.markdown("**雙方付款金額**")
        c4, c5 = st.columns(2)
        c4.metric("我", fmt_rmb(my_paid))
        c5.metric("朋友", fmt_rmb(friend_paid))
