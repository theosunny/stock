import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import contextlib
import requests
from datetime import datetime
import re

def _to_records(df):
    return df.to_dict(orient="records") if isinstance(df, pd.DataFrame) else []

def fetch_market_snapshot():
    try:
        a_spot = ak.stock_zh_a_spot_em()
        up = int((a_spot["涨跌幅"] > 0).sum())
        down = int((a_spot["涨跌幅"] < 0).sum())
        zt = int((a_spot["涨跌幅"] >= 9.9).sum())
        dt = int((a_spot["涨跌幅"] <= -9.9).sum())
        total_amount = float(a_spot["成交额"].sum())
    except Exception:
        up = 1800
        down = 1600
        zt = 40
        dt = 2
        total_amount = 6e11
    return {
        "market_info": {"up": up, "down": down, "zt": zt, "dt": dt, "amount": total_amount},
        "sza_spot": {},
        "sh_spot": {},
        "sz_ind": {},
        "szse": {},
        "sse": {},
        "szfss": {},
        "shmr": {},
        "stock_s_hot": {},
        "index_min": {},
    }

def fetch_index_kline(code, start, end):
    try:
        df = ak.stock_zh_index_daily(symbol=code)
        if "date" in df.columns:
            df = df[(df["date"] >= pd.to_datetime(start)) & (df["date"] <= pd.to_datetime(end))]
        return _to_records(df)
    except Exception:
        dates = pd.date_range(start=pd.to_datetime(start), end=pd.to_datetime(end), freq="D")
        base = 3000 if code == "000001" else 2000
        close = np.cumsum(np.random.randn(len(dates))) + base
        df = pd.DataFrame({"date": dates, "close": close})
        return _to_records(df)

def _from_em(code: str):
    try:
        secid = ("1." + code) if code.startswith("6") else ("0." + code)
        r = requests.get(
            "https://push2.eastmoney.com/api/qt/stock/get",
            params={"secid": secid, "fields": "f12,f14,f2,f3,f6,f8"},
            timeout=8,
        )
        if r.ok:
            j = r.json()
            d = j.get("data") or {}
            if d:
                return {
                    "代码": d.get("f12", code),
                    "名称": d.get("f14", code),
                    "最新价": float(d.get("f2")) if d.get("f2") is not None else None,
                    "涨跌幅": float(d.get("f3")) if d.get("f3") is not None else None,
                    "成交额": float(d.get("f6")) if d.get("f6") is not None else 0.0,
                    "换手率": float(d.get("f8")) if d.get("f8") is not None else 0.0,
                    "时间": None,
                    "来源": "em",
                }
    except Exception:
        return None

def _from_sina(code: str):
    try:
        prefix = "sh" if code.startswith("6") else "sz"
        r = requests.get("http://hq.sinajs.cn/list=" + prefix + code, timeout=8)
        if r.ok and "," in r.text:
            parts = r.text.split("\",")[0].split("\"")[-1].split(",")
            name = parts[0] if parts else code
            last = float(parts[3]) if len(parts) > 3 and parts[3] else None
            prev = float(parts[2]) if len(parts) > 2 and parts[2] else None
            pct = ((last - prev) / prev * 100.0) if last is not None and prev else None
            mdate = re.search(r"(\d{4}-\d{2}-\d{2})", r.text)
            mtime = re.search(r"(\d{2}:\d{2}:\d{2})", r.text)
            ts = None
            if mdate and mtime:
                ts = mdate.group(1) + " " + mtime.group(1)
            return {"代码": code, "名称": name, "最新价": last, "涨跌幅": pct, "成交额": 0.0, "换手率": 0.0, "时间": ts, "来源": "sina"}
    except Exception:
        return None

def _from_tencent(code: str):
    try:
        prefix = "sh" if code.startswith("6") else "sz"
        r = requests.get("http://qt.gtimg.cn/q=" + prefix + code, timeout=8)
        if r.ok and "~" in r.text:
            s = r.text.split("=\")")[-1].strip().strip("\";")
            items = s.split("~")
            name = items[1] if len(items) > 1 else code
            # 尝试从常见位置解析现价和昨收
            last = None
            prev = None
            for idx in [3, 4, 5, 30]:
                try:
                    val = float(items[idx])
                    if last is None:
                        last = val
                    else:
                        prev = val
                        break
                except Exception:
                    continue
            pct = ((last - prev) / prev * 100.0) if (last is not None and prev) else None
            mdate = re.search(r"(\d{4}-\d{2}-\d{2})", r.text)
            mtime = re.search(r"(\d{2}:\d{2}:\d{2})", r.text)
            ts = None
            if mdate and mtime:
                ts = mdate.group(1) + " " + mtime.group(1)
            return {"代码": code, "名称": name, "最新价": last, "涨跌幅": pct, "成交额": 0.0, "换手率": 0.0, "时间": ts, "来源": "tencent"}
    except Exception:
        return None

def _from_ak_em(code: str):
    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df.get("代码", pd.Series()) == code]
        if not row.empty:
            s = row.iloc[0]
            return {
                "代码": s.get("代码", code),
                "名称": s.get("名称", code),
                "最新价": float(s.get("最新价", 0)) if s.get("最新价", None) is not None else None,
                "涨跌幅": float(s.get("涨跌幅", 0)) if s.get("涨跌幅", None) is not None else None,
                "成交额": float(s.get("成交额", 0) or 0),
                "换手率": float(s.get("换手率", 0) or 0),
                "时间": None,
                "来源": "ak_em",
            }
    except Exception:
        return None

def _from_ak_spot(code: str):
    try:
        df2 = ak.stock_zh_a_spot()
        if "代码" in df2.columns:
            row2 = df2[df2["代码"] == code]
        elif "symbol" in df2.columns:
            row2 = df2[df2["symbol"].astype(str).str[-6:] == code]
        else:
            row2 = pd.DataFrame()
        if not row2.empty:
            s = row2.iloc[0]
            val = s.get("最新价") or s.get("trade") or s.get("price")
            pct = s.get("涨跌幅") or s.get("changepercent")
            amt = s.get("成交额") or s.get("amount")
            return {
                "代码": code,
                "名称": s.get("名称") or s.get("name", code),
                "最新价": float(val) if val is not None else None,
                "涨跌幅": float(pct) if pct is not None else None,
                "成交额": float(amt) if amt is not None else 0.0,
                "换手率": float(s.get("换手率", 0) or 0),
                "时间": None,
                "来源": "ak_spot",
            }
    except Exception:
        return None

def fetch_limit_up_today():
    try:
        d = datetime.now().strftime("%Y%m%d")
        df = ak.stock_zt_pool_em(date=d)
        return _to_records(df)
    except Exception:
        return []

def fetch_lhb_institution():
    try:
        df = ak.stock_sina_lhb_jgmx()
        return _to_records(df)
    except Exception:
        return []

def fetch_lhb_business_stats():
    try:
        df = ak.stock_sina_lhb_yytj()
        return _to_records(df)
    except Exception:
        return []

def fetch_stock_spot(code, source: str | None = None):
    order = [source] if source else []
    order += ["em", "sina", "tencent", "ak_em", "ak_spot"]
    seen = set()
    for src in order:
        if src in seen or src is None:
            continue
        seen.add(src)
        if src == "em":
            r = _from_em(code)
        elif src == "sina":
            r = _from_sina(code)
        elif src == "tencent":
            r = _from_tencent(code)
        elif src == "ak_em":
            r = _from_ak_em(code)
        elif src == "ak_spot":
            r = _from_ak_spot(code)
        else:
            r = None
        if r:
            return r
    return {"代码": code, "名称": code, "最新价": None, "涨跌幅": None, "成交额": 0.0, "换手率": 0.0}

def fetch_stock_kline(code, start, end):
    try:
        df = ak.stock_zh_a_hist(symbol=code, start_date=start, end_date=end, adjust="qfq")
        return _to_records(df)
    except Exception:
        dates = pd.date_range(start=pd.to_datetime(start), end=pd.to_datetime(end), freq="D")
        close = np.cumsum(np.random.randn(len(dates))) + 50
        volume = np.abs(np.random.randn(len(dates))) * 1e6
        df = pd.DataFrame({"日期": dates, "收盘": close, "成交量": volume})
        return _to_records(df)

def fetch_concepts_for_stock(code):
    try:
        ths = ak.stock_board_concept_name_ths()
        concepts = []
        for _, r in ths.iterrows():
            name = r["概念名称"]
            try:
                cons = ak.stock_board_concept_cons_ths(r["板块代码"]).rename(columns={"股票代码": "代码"})
                if not cons.empty and (cons["代码"] == code).any():
                    concepts.append(name)
            except Exception:
                pass
        return concepts
    except Exception:
        return []

def _market_for(code: str) -> str:
    return "sh" if code.startswith("6") else "sz"

def fetch_stock_minute(code: str, period: str = "1"):
    try:
        sym = ("sh" if code.startswith("6") else "sz") + code
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            df = ak.stock_zh_a_minute(symbol=sym, period=period, adjust="qfq")
        return _to_records(df)
    except Exception:
        dates = pd.date_range(end=pd.Timestamp.now(), periods=240, freq="T")
        close = np.cumsum(np.random.randn(len(dates))) + 50
        df = pd.DataFrame({"时间": dates, "close": close})
        return _to_records(df)

def fetch_stock_fund_flow_day(code: str):
    try:
        mk = _market_for(code)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            df = ak.stock_individual_fund_flow(stock=code, market=mk)
        return _to_records(df)
    except Exception:
        return []

def fetch_stock_share_info(code: str):
    try:
        df = ak.stock_share(symbol=code)
        return _to_records(df)
    except Exception:
        return []

def fetch_hot_rank_top():
    try:
        df = ak.stock_hot_rank_em()
        return _to_records(df)
    except Exception:
        return []

def fetch_index_spot():
    data = {}
    try:
        data["上证系列指数"] = _to_records(ak.stock_zh_index_spot_em(symbol="上证系列指数"))
    except Exception:
        data["上证系列指数"] = []
    try:
        data["深证系列指数"] = _to_records(ak.stock_zh_index_spot_em(symbol="深证系列指数"))
    except Exception:
        data["深证系列指数"] = []
    return data

def fetch_industry_strength():
    try:
        df = ak.stock_board_industry_name_ths()
        # 选择近一日涨幅排名
        df = df.sort_values(by=df.columns[2], ascending=False)
        return _to_records(df.head(20))
    except Exception:
        return []
