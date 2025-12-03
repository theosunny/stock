import numpy as np

def _ma(values, n):
    if len(values) < n:
        return None
    return float(np.mean(values[-n:]))

def analyze_market(market, index_sh, index_cy):
    sh_close = [float(x.get("close", x.get("收盘", 0))) for x in index_sh]
    cy_close = [float(x.get("close", x.get("收盘", 0))) for x in index_cy]
    sh_ma20 = _ma(sh_close, 20)
    sh_ma60 = _ma(sh_close, 60)
    cy_ma20 = _ma(cy_close, 20)
    cy_ma60 = _ma(cy_close, 60)
    up = market["market_info"]["up"]
    down = market["market_info"]["down"]
    zt = market["market_info"]["zt"]
    dt = market["market_info"]["dt"]
    amount = market["market_info"]["amount"]
    trend_ok = sh_ma20 and sh_ma60 and cy_ma20 and cy_ma60 and sh_ma20 >= sh_ma60 and cy_ma20 >= cy_ma60
    sentiment_ok = up > down and zt >= 30 and dt <= 5
    amount_ok = amount > 5e11
    level = "绿灯" if trend_ok and sentiment_ok and amount_ok else ("黄灯" if up >= down else "红灯")
    conclusion = "可提升仓位，积极操作" if level == "绿灯" else ("可中等仓位，快进快出" if level == "黄灯" else "空仓或极轻仓，保命第一")
    return {"评级": level, "指数": {"sh_ma20": sh_ma20, "sh_ma60": sh_ma60, "cy_ma20": cy_ma20, "cy_ma60": cy_ma60}, "量能": amount, "情绪": {"up": up, "down": down, "zt": zt, "dt": dt}, "结论": conclusion}

def analyze_board(code, concepts, market):
    strength = "一般" if len(concepts) <= 1 else ("强" if len(concepts) >= 3 else "一般")
    ladder = "不完整" if len(concepts) == 0 else "一般"
    continuity = "存疑" if len(concepts) <= 1 else "持续"
    kind = "主线板块" if strength == "强" and continuity == "持续" else ("支线轮动" if strength == "一般" else "一日游板块")
    advice = "重点参与，选择前排龙头" if kind == "主线板块" else ("只能套利，不可恋战" if kind == "支线轮动" else "坚决回避")
    return {"板块": concepts, "强度": strength, "持续性": continuity, "梯队": ladder, "结论": {"类别": kind, "建议": advice}}

def analyze_stock(code, spot, kline, concepts):
    closes = [float(x.get("收盘", x.get("close", 0))) for x in kline]
    vols = [float(x.get("成交量", x.get("volume", 0))) for x in kline]
    ma20 = _ma(closes, 20)
    ma60 = _ma(closes, 60)
    vol_ma20 = _ma(vols, 20)
    breakout = False
    if len(closes) >= 2:
        breakout = closes[-1] > max(closes[-5:])
    vol_ok = False
    if len(vols) >= 2 and vol_ma20:
        vol_ok = vols[-1] >= 1.2 * vol_ma20
    pct = spot.get("涨跌幅", 0) or 0
    role = "龙二" if pct >= 5 else ("跟风" if pct >= 2 else "待观察")
    plan = {}
    if breakout and vol_ok:
        plan["次日开盘"] = "高开可能性较高"
        plan["市场信号"] = "量价齐升"
        plan["操作策略"] = {"激进型": "集合竞价高开且量能充足，轻仓介入", "稳健型": "开盘后分时线不回补缺口或回踩分时均线后拉起时加仓"}
        plan["预期管理"] = {"符合/超预期": "强势确认，资金认可", "低于预期": "坚决放弃"}
    else:
        plan["次日开盘"] = "平开或低开概率较高"
        plan["市场信号"] = "强势未确认"
        plan["操作策略"] = {"激进型": "不介入", "稳健型": "取消关注"}
        plan["预期管理"] = {"符合/超预期": "跟踪但谨慎", "低于预期": "坚决放弃"}
    risk = {"止损": "买入价下方-5%"}
    return {
        "individual": {"代码": code, "名称": spot.get("名称", code), "最新价": spot.get("最新价", None), "涨跌幅": spot.get("涨跌幅", None), "概念": concepts, "MA20": ma20, "MA60": ma60, "突破": breakout, "放量": vol_ok},
        "base_info": {},
        "latest_buy": {},
        "stock_data_flow": {},
        "stock_min": {},
        "stock_share": {},
        "stock_min_flow": {},
        "计划": plan,
        "风险": risk,
    }
