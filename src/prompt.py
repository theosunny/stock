def build_system() -> str:
    return (
        "你是一名资深A股短线策略分析师，精通龙头战法与题材炒作，行事风格果断坚决，严格遵循“顺势而为”法则，核心在于精准把握市场的“势”，并据此制定切实可行的交易计划。"
    )

def build_user(data: dict) -> str:
    def dump(obj):
        return str(obj)
    def take_fields(rows, fields, limit=10):
        out = []
        try:
            for r in (rows or [])[:limit]:
                o = {}
                for f in fields:
                    if isinstance(r, dict):
                        o[f] = r.get(f)
                out.append(o)
        except Exception:
            return []
        return out
    def kline_summary(kline, close_key="收盘", vol_key="成交量"):
        try:
            last60 = kline[-60:] if kline and len(kline) > 60 else (kline or [])
            closes = [float(x.get(close_key, x.get("close", 0)) or 0) for x in last60]
            vols = [float(x.get(vol_key, x.get("volume", 0)) or 0) for x in last60]
            ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else None
            ma60 = sum(closes[-60:]) / 60 if len(closes) >= 60 else None
            last = closes[-1] if closes else None
            hi5 = max(closes[-5:]) if len(closes) >= 5 else None
            lo5 = min(closes[-5:]) if len(closes) >= 5 else None
            vol_ma20 = sum(vols[-20:]) / 20 if len(vols) >= 20 else None
            return {"MA20": ma20, "MA60": ma60, "LAST": last, "HI5": hi5, "LO5": lo5, "VOL_MA20": vol_ma20}
        except Exception:
            return {}
    def minute_summary(min_rows):
        try:
            last60 = min_rows[-60:] if min_rows and len(min_rows) > 60 else (min_rows or [])
            prices = []
            for x in last60:
                v = x.get("close") or x.get("价格") or x.get("最新价")
                if v is not None:
                    prices.append(float(v))
            if not prices:
                return {}
            return {"LAST": prices[-1], "AVG": sum(prices) / len(prices), "HI": max(prices), "LO": min(prices)}
        except Exception:
            return {}
    lines = []
    lines.append("# 角色")
    lines.append("你是一名资深A股短线策略分析师，精通龙头战法与题材炒作，行事风格果断坚决，严格遵循“顺势而为”法则，核心在于精准把握市场的“势”，并据此制定切实可行的交易计划。")
    lines.append(
        "请根据个股信息{{individual}}、市场总貌数据{{szse}} 、沪 A 股上市公司的实时行情数据{{sh_spot}}、上海证券交易所-每日概况{{sse}}、深 A 股上市公司的实时行情数据{{sza_spot}}、深交所股票行业成交数据 {{sz_ind}},深圳证券交易所-市场总貌-证券类别统计 {{szfss}},上交所每日概况基础数据{{shmr}}，{{base_info}}、市场行情{{market_info}}，以及最新分时成交{{latest_buy}},单日k线信息{{stock_k}},强势股、同花顺热股TOP100股票{{stock_s_hot}},{{index_min}},股票日资金流入、流向{{stock_data_flow}},股票分时行情{{stock_min}},热门概念{{stock_concept}},股票股本信息{{stock_share}},指数实时行情{{index_current}},股票实时行情{{stock_current}},指数行情{{index_k}},股票资金流向-分时{{stock_min_flow}} 对{{stock_name}}这个股票按照下面的要求进行分析"
    )
    lines.append("## 技能")
    lines.append("### 技能 1: 大盘分析")
    lines.append("### 技能 2: 板块分析")
    lines.append("### 技能 3: 个股分析")
    lines.append("## 限制:")
    lines.append("- 只进行股票相关分析，拒绝回答与股票分析无关的话题。")
    lines.append("- 所输出的内容必须按照给定的格式和要求进行组织，不能偏离框架。")
    lines.append("- 分析过程必须保持客观、理性，不带任何个人情绪。")
    lines.append("输出要求：在每个技能段内先给出推理链（R1风格，逐步推理要点），再给出结论与计划；严格使用中文与指定小节标题，不得省略任何条目。")
    lines.append("数据：")
    ind = data.get('individual') or {}
    ind_min = {k: ind.get(k) for k in ['代码','名称','最新价','涨跌幅','MA20','MA60','突破','放量']}
    lines.append(f"individual={dump(ind_min)}")
    lines.append(f"szse={dump(data.get('szse'))}")
    lines.append(f"sh_spot={dump(data.get('sh_spot'))}")
    lines.append(f"sse={dump(data.get('sse'))}")
    lines.append(f"sza_spot={dump(data.get('sza_spot'))}")
    lines.append(f"sz_ind={dump(data.get('sz_ind'))}")
    lines.append(f"szfss={dump(data.get('szfss'))}")
    lines.append(f"shmr={dump(data.get('shmr'))}")
    lines.append(f"base_info={dump(data.get('base_info'))}")
    lines.append(f"market_info={dump(data.get('market_info'))}")
    lines.append(f"latest_buy={dump(data.get('latest_buy'))}")
    lines.append(f"stock_k_summary={dump(kline_summary(data.get('stock_k') or []))}")
    lines.append(f"stock_s_hot_top={dump(take_fields((data.get('stock_s_hot') or []), ['代码','名称'], 5))}")
    lines.append(f"index_min_summary={dump(data.get('index_min'))}")
    lines.append(f"stock_data_flow_top={dump(take_fields((data.get('stock_data_flow') or []), ['日期','主力净流入','超大单净流入'], 5))}")
    lines.append(f"stock_min_summary={dump(minute_summary(data.get('stock_min') or []))}")
    sc = data.get('stock_concept') or {}
    concept_names = (sc.get('list') or [])[:10]
    lines.append(f"stock_concept_top={dump(concept_names)}")
    share = data.get('stock_share') or []
    share_min = take_fields(share, ['总股本','流通股'], 1)
    lines.append(f"stock_share_min={dump(share_min)}")
    idx_cur = data.get('index_current') or {}
    idx_cur_min = {k: v for k, v in idx_cur.items()}
    lines.append(f"index_current_min={dump(idx_cur_min)}")
    stk_cur = data.get('stock_current') or {}
    stk_cur_min = {k: stk_cur.get(k) for k in ['代码','名称','最新价','涨跌幅','成交额','换手率']}
    lines.append(f"stock_current_min={dump(stk_cur_min)}")
    lines.append(f"index_k_summary={{'sh_last': {dump((data.get('index_k') or {}).get('sh', [])[-1:] )}, 'cy_last': {dump((data.get('index_k') or {}).get('cy', [])[-1:] )}}}")
    lines.append(f"stock_min_flow={dump(data.get('stock_min_flow'))}")
    lines.append(f"zt_pool_top={dump(take_fields((data.get('zt_pool') or []), ['代码','名称','连板数'], 5))}")
    lines.append(f"lhb_inst_top={dump(take_fields((data.get('lhb_inst') or []), ['股票代码','股票简称','机构名称','净买入'], 5))}")
    lines.append(f"lhb_stats_top={dump(take_fields((data.get('lhb_stats') or []), ['上榜营业部','买入金额','卖出金额'], 5))}")
    lines.append(f"stock_name={dump(data.get('stock_name'))}")
    return "\n".join(lines)
