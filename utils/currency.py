def rmb_to_twd(rmb: float, rate: float = 4.35) -> float:
    return round(rmb * rate)


def twd_to_rmb(twd: float, rate: float = 4.35) -> float:
    return round(twd / rate, 2)


def fmt_twd(amount: float) -> str:
    return f"NT$ {amount:,.0f}"


def fmt_rmb(amount: float) -> str:
    return f"¥ {amount:,.2f}"
