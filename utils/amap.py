from urllib.parse import quote


def amap_marker_url(lat: float, lng: float, name: str) -> str:
    """產生高德地圖網頁版標記 URL，手機點下去會嘗試開啟高德 APP。"""
    name_q = quote(name)
    return (
        f"https://uri.amap.com/marker?position={lng},{lat}"
        f"&name={name_q}&src=chubbydoo&coordinate=wgs84&callnative=1"
    )


def amap_navigation_url(lat: float, lng: float, name: str) -> str:
    """產生高德地圖導航 URL（從當前位置導航到目的地）。"""
    name_q = quote(name)
    return (
        f"https://uri.amap.com/navigation?to={lng},{lat},{name_q}"
        f"&mode=car&policy=1&src=chubbydoo&coordinate=wgs84&callnative=1"
    )


def amap_route_url(points: list, name: str = "南疆行程") -> str:
    """多點路徑 URL（高德最多支援 16 個途經點）。"""
    if len(points) < 2:
        return ""
    origin = points[0]
    destination = points[-1]
    waypoints = points[1:-1]
    name_q = quote(name)
    via_str = ""
    if waypoints:
        via_pairs = [f"{p['lng']},{p['lat']}" for p in waypoints[:16]]
        via_str = "&waypoints=" + ";".join(via_pairs)
    return (
        f"https://uri.amap.com/navigation"
        f"?from={origin['lng']},{origin['lat']},{quote(origin['name'])}"
        f"&to={destination['lng']},{destination['lat']},{quote(destination['name'])}"
        f"{via_str}&mode=car&src=chubbydoo&coordinate=wgs84&callnative=1"
    )


def baidu_marker_url(lat: float, lng: float, name: str) -> str:
    """備用：百度地圖 URL（部分高德開不到時可用）。"""
    name_q = quote(name)
    return (
        f"https://api.map.baidu.com/marker?location={lat},{lng}"
        f"&title={name_q}&content=南疆行程&output=html&src=chubbydoo"
    )
