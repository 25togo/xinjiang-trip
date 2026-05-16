"""把所有頁面內容匯出成單頁 HTML，手機書籤打開即可離線看。"""
from datetime import date
from .data_loader import (
    load_itinerary, load_places, load_documents,
    load_packing, load_budget, load_contacts,
)
from .amap import amap_marker_url
from .currency import fmt_twd


HTML_HEAD = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>2026 南疆 15 天行程（離線版）</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, "PingFang TC", "Microsoft JhengHei", sans-serif;
    line-height: 1.6; color: #222; max-width: 760px; margin: 0 auto; padding: 16px;
    background: #fafaf7; }
  h1 { color: #1a4d6e; border-bottom: 3px solid #1a4d6e; padding-bottom: 6px; }
  h2 { color: #2d6e8e; margin-top: 32px; border-left: 6px solid #2d6e8e; padding-left: 10px; }
  h3 { color: #444; margin-top: 20px; }
  table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 14px; }
  th, td { border: 1px solid #ddd; padding: 6px 8px; text-align: left; }
  th { background: #1a4d6e; color: #fff; }
  tr:nth-child(even) td { background: #f0f0eb; }
  .day-card { border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin: 12px 0;
    background: #fff; }
  .day-header { color: #1a4d6e; font-weight: bold; font-size: 17px; margin-bottom: 6px; }
  .meta { font-size: 13px; color: #666; margin-bottom: 8px; }
  .highlight { background: #fff8dc; padding: 6px 10px; border-left: 3px solid #ff9900;
    margin: 6px 0; font-size: 14px; }
  ul { padding-left: 22px; }
  li { margin: 2px 0; }
  a { color: #1a4d6e; }
  .map-btn { display: inline-block; background: #1a4d6e; color: #fff; padding: 4px 10px;
    border-radius: 4px; text-decoration: none; font-size: 12px; margin: 2px; }
  .toc { background: #eef4f8; padding: 12px; border-radius: 8px; margin: 16px 0; }
  .toc a { display: inline-block; margin: 4px 8px; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 12px;
    background: #ff9900; color: #fff; }
</style>
</head>
<body>
"""

HTML_TAIL = """
<hr>
<p style="text-align:center; color:#888; font-size:12px;">
匯出時間 {ts} ｜ 出發 2026-08-15 ｜ 兩人 15 天
</p>
</body></html>
"""


def render_html() -> str:
    itin = load_itinerary()
    places = load_places()
    docs = load_documents()
    packing = load_packing()
    budget = load_budget()
    contacts = load_contacts()

    place_by_id = {p["id"]: p for p in places["places"]}

    parts = [HTML_HEAD]
    parts.append('<h1>2026 南疆 15 天行程（離線版）</h1>')
    parts.append(f'<p>{itin["trip"]["route_type"]} ｜ 出發 {itin["trip"]["start_date"]} ｜ 返程 {itin["trip"]["end_date"]} ｜ {itin["trip"]["travelers"]} 人</p>')

    parts.append('<div class="toc"><b>目錄</b><br>')
    for s in ["行程", "證件", "打包", "預算", "聯絡"]:
        parts.append(f'<a href="#{s}">{s}</a>')
    parts.append('</div>')

    # 行程
    parts.append('<h2 id="行程">每日行程</h2>')
    for d in itin["days"]:
        parts.append('<div class="day-card">')
        parts.append(f'<div class="day-header">Day {d["day"]} ｜ {d["date"]} ｜ {d["city_from"]} → {d["city_to"]}</div>')
        parts.append(f'<div class="meta">移動 {d["distance_km"]} km / 約 {d["drive_hours"]} 小時 ｜ 海拔 {d["altitude_m"]} m ｜ 住宿：{d["overnight"]}</div>')
        parts.append('<ul>')
        for h in d["highlights"]:
            parts.append(f'<li>{h}</li>')
        parts.append('</ul>')
        if d.get("notes"):
            parts.append(f'<div class="highlight">{d["notes"]}</div>')
        parts.append('</div>')

    # 證件
    parts.append('<h2 id="證件">證件與申辦</h2>')
    parts.append('<table><tr><th>項目</th><th>必備</th><th>提前天數</th><th>費用 TWD</th><th>備註</th></tr>')
    for doc in docs["documents"]:
        must = "是" if doc["required"] else "否"
        parts.append(
            f'<tr><td>{doc["name"]}</td><td>{must}</td>'
            f'<td>{doc["deadline_days_before"]}</td>'
            f'<td>{doc["cost_twd"]}</td>'
            f'<td>{"；".join(doc["notes"][:2])}</td></tr>'
        )
    parts.append('</table>')

    # 打包
    parts.append('<h2 id="打包">打包清單</h2>')
    for cat in packing["categories"]:
        parts.append(f'<h3>{cat["name"]}</h3><ul>')
        for item in cat["items"]:
            tag = '<span class="badge">必</span> ' if item.get("must") else ""
            qty = item.get("qty", 1)
            note = item.get("note", "") or ""
            parts.append(f'<li>{tag}{item["item"]} × {qty} <span style="color:#666;font-size:13px;">{note}</span></li>')
        parts.append('</ul>')

    # 預算
    parts.append('<h2 id="預算">預算</h2>')
    parts.append('<table><tr><th>項目</th><th>預估 TWD</th><th>說明</th></tr>')
    total = 0
    for cat in budget["categories"]:
        total += cat["estimate_twd"]
        parts.append(
            f'<tr><td>{cat["name"]}</td><td>{fmt_twd(cat["estimate_twd"])}</td>'
            f'<td>{cat["detail"]}</td></tr>'
        )
    parts.append(f'<tr><td><b>合計</b></td><td><b>{fmt_twd(total)}</b></td><td>兩人合計</td></tr>')
    parts.append('</table>')
    parts.append(f'<p><b>人均：{fmt_twd(total/2)}</b></p>')

    # 聯絡
    parts.append('<h2 id="聯絡">緊急聯絡</h2>')
    for section_key, label in [
        ("emergency", "包車與同行"),
        ("china_emergency", "中國境內緊急"),
        ("taiwan_office", "台灣海基會"),
        ("insurance_company", "保險公司"),
        ("airlines", "航空公司"),
        ("local_services", "當地服務"),
    ]:
        parts.append(f'<h3>{label}</h3><ul>')
        for c in contacts.get(section_key, []):
            phone = c.get("phone", "") or "（出發前填）"
            name = c.get("name", "") or ""
            parts.append(
                f'<li><b>{c["role"]}</b> {name} '
                f'<a href="tel:{phone}">{phone}</a> '
                f'<span style="color:#666;font-size:13px;">{c.get("note", "")}</span></li>'
            )
        parts.append('</ul>')

    parts.append(HTML_TAIL.format(ts=date.today().isoformat()))
    return "".join(parts)
