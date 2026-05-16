# 2026 南疆 15 天行程系統

兩人自由行包車版。Streamlit 規劃用 + 一鍵匯出 HTML 帶到當地離線使用。

## 啟動

```bash
cd xinjiang_trip
pip install -r requirements.txt
streamlit run app.py
```

預設 `http://localhost:8501`，免登入直接用。

## 結構

- `app.py` — 主入口，總覽
- `pages/1-9_xxx.py` — 9 個分頁
- `data/*.yaml` — 行程、地點、證件、打包、預算、聯絡、Ctrip 參考
- `utils/` — 高德 deep link、匯率、本地存檔、HTML 匯出
- `data_user/` — 記帳、Ctrip 比價、打包勾選的本地持久化（gitignored）

## 在新疆使用

Streamlit Cloud 域名在 GFW 內連不上。流程：

1. 出發前在 `📥 離線匯出` 頁下載 HTML
2. 存到手機 Files / iCloud Drive
3. Safari/Chrome 打開 → 加到主畫面
4. 沒網也能看行程、證件、打包、預算、緊急聯絡

地圖 / 即時記帳要用：
- 高德地圖 APP（出發前下載新疆離線地圖）
- 紙本記帳或 Splitwise（離線可用）

## 部署到 Streamlit Cloud

Push 到 GitHub 後在 Streamlit Cloud 設定：
- Main file: `xinjiang_trip/app.py`
- Python version: 3.11
- Branch: `main`
