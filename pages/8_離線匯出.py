import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from datetime import date
from utils.exporter import render_html

st.set_page_config(page_title="離線匯出", page_icon="📥", layout="wide")
st.title("離線匯出（HTML 單頁）")

st.markdown(
    """
    Streamlit Cloud 在中國會被牆。匯出 **單頁 HTML**：
    - 下載到手機
    - 用 Safari/Chrome 打開
    - **存成書籤** 或 **加到主畫面**
    - 沒網也能看行程、證件、打包、預算、緊急聯絡

    限制：離線版只是「快照」，記帳跟勾選會看不到。記帳要在當地用紙本／Splitwise／拍照備存。
    """
)

st.markdown("---")
html = render_html()

c1, c2 = st.columns([1, 2])
filename = c1.text_input("檔名", value=f"南疆15天_{date.today().isoformat()}.html")
c2.metric("檔案大小", f"{len(html.encode('utf-8')) / 1024:.1f} KB")

st.download_button(
    "📥 下載 HTML 離線版",
    data=html.encode("utf-8"),
    file_name=filename,
    mime="text/html",
    use_container_width=True,
    type="primary",
)

with st.expander("👀 預覽（前 200 行）"):
    preview_lines = html.split("\n")[:200]
    st.code("\n".join(preview_lines), language="html")

st.markdown("---")
st.subheader("帶到新疆的建議流程")
st.markdown(
    """
    1. **出發前一週**：在這頁下載 HTML 存到手機 Files / iCloud Drive
    2. **同步到雲端硬碟**（Google Drive / iCloud / OneDrive）一份備份
    3. **設成手機首頁書籤**：Safari/Chrome 打開 HTML → 分享 → 加到主畫面
    4. **VPN 備案**：出發前裝好 ExpressVPN / Astrill，萬一要更新行程
    5. **離線高德地圖**：在台灣高德 APP 內預先下載新疆全域離線地圖（700MB）
    """
)
