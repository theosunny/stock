def build_report(
    stock_name,
    individual,
    szse,
    sh_spot,
    sse,
    sza_spot,
    sz_ind,
    szfss,
    shmr,
    base_info,
    market_info,
    latest_buy,
    stock_k,
    stock_s_hot,
    index_min,
    stock_data_flow,
    stock_min,
    stock_concept,
    stock_share,
    index_current,
    stock_current,
    index_k,
    stock_min_flow,
    market_rating,
    board_result,
    stock_result,
    zt_pool,
    lhb_inst,
    lhb_stats,
    llm_rich=None,
):
    lines = []
    lines.append("# 角色")
    lines.append("你是一名资深A股短线策略分析师，精通龙头战法与题材炒作，行事风格果断坚决，严格遵循“顺势而为”法则，核心在于精准把握市场的“势”，并据此制定切实可行的交易计划。")
    lines.append("## 技能")
    lines.append("### 技能 1: 大盘分析")
    lines.append(f"评级：{market_rating['评级']}")
    lines.append(f"指数趋势：{market_rating['指数']}")
    lines.append(f"市场量能：{market_rating['量能']}")
    lines.append(f"市场情绪：{market_rating['情绪']}")
    lines.append("推理链（R1风格要点）：")
    lines.append(f"- 多空排列：上证MA20≥MA60、创指MA20≥MA60 → {('是' if (market_rating['指数'].get('sh_ma20') and market_rating['指数'].get('sh_ma60') and market_rating['指数']['sh_ma20']>=market_rating['指数']['sh_ma60']) else '否')} / {('是' if (market_rating['指数'].get('cy_ma20') and market_rating['指数'].get('cy_ma60') and market_rating['指数']['cy_ma20']>=market_rating['指数']['cy_ma60']) else '否')}" )
    lines.append(f"- 量能阈值：{market_rating['量能']} 与阈值5e11对比 → {('充足' if market_rating['量能']>5e11 else '一般')}" )
    lines.append(f"- 情绪结构：上涨{market_rating['情绪']['up']}、下跌{market_rating['情绪']['down']}、涨停{market_rating['情绪']['zt']}、跌停{market_rating['情绪']['dt']}" )
    lines.append(f"结论：{market_rating['结论']}")
    lines.append("### 技能 2: 板块分析")
    lines.append(f"板块列表：{board_result['板块']}")
    lines.append(f"强度：{board_result['强度']}，持续性：{board_result['持续性']}，梯队：{board_result['梯队']}")
    lines.append("推理链（R1风格要点）：")
    lines.append(f"- 概念覆盖数量：{len(board_result['板块'])}，行业强度TOP样本：{len(board_result.get('行业强度TOP', []))}")
    lines.append(f"- 梯队与持续性判定：{board_result['持续性']} / {board_result['梯队']}")
    lines.append(f"结论：{board_result['结论']}")
    lines.append("### 技能 3: 个股分析")
    lines.append(f"个股信息：{individual}")
    lines.append("次日（T+1）交易计划（基于预期管理）：")
    lines.append(f"- 次日开盘情况：{stock_result['计划'].get('次日开盘')}")
    lines.append(f"- 市场信号解读：{stock_result['计划'].get('市场信号')}")
    lines.append("推理链（R1风格要点）：")
    lines.append(f"- 技术面：突破={stock_result['individual']['突破']}，放量={stock_result['individual']['放量']}，MA20={stock_result['individual']['MA20']}，MA60={stock_result['individual']['MA60']}")
    lines.append(f"- 资金与行为：涨停池命中、龙虎榜命中将在下方支撑数据列示")
    lines.append("- 具体操作策略：")
    lines.append(f"  - 激进型：{stock_result['计划'].get('操作策略', {}).get('激进型', '')}")
    lines.append(f"  - 稳健型：{stock_result['计划'].get('操作策略', {}).get('稳健型', '')}")
    lines.append("- 符合/超预期（高开>3%）：强势确认，资金认可。")
    lines.append("  - 激进型：集合竞价高开且量能充足，可直接轻仓介入。")
    lines.append("  - 稳健型：开盘后分时线不回补缺口，或回踩分时均线后快速拉起时加仓。")
    lines.append("- 低于预期（平开或低开）：强势被证伪，不及格。")
    lines.append("  - 坚决放弃！这证明之前的强势是假的。持有者应考虑竞价卖出，未持有者取消关注。")
    lines.append("风险控制：")
    lines.append(f"- {stock_result['风险']}")
    lines.append("## 限制:")
    lines.append("- 只进行股票相关分析，拒绝回答与股票分析无关的话题。")
    lines.append("- 所输出的内容必须按照给定的格式和要求进行组织，不能偏离框架。")
    lines.append("- 分析过程必须保持客观、理性，不带任何个人情绪。")
    lines.append("打板支撑")
    lines.append(str({"涨停池": zt_pool[:10] if isinstance(zt_pool, list) else zt_pool, "龙虎榜机构": lhb_inst[:10] if isinstance(lhb_inst, list) else lhb_inst, "营业上榜统计": lhb_stats[:10] if isinstance(lhb_stats, list) else lhb_stats}))
    code = individual.get("代码", "")
    def _has_code(lst, keys=("代码", "股票代码", "symbol")):
        try:
            for it in lst or []:
                for k in keys:
                    v = it.get(k)
                    if v and str(v).endswith(str(code)):
                        return True
        except Exception:
            return False
        return False
    zt_hit = _has_code(zt_pool)
    lhb_hit = _has_code(lhb_inst)
    board_kind = board_result.get("结论", {}).get("类别")
    board_adv = board_result.get("结论", {}).get("建议")
    market_level = market_rating.get("评级")
    market_conc = market_rating.get("结论")
    plan = stock_result.get("计划", {})
    def _score():
        ms = 80 if market_level == "绿灯" else (60 if market_level == "黄灯" else 30)
        bs = 80 if board_kind == "主线板块" else (50 if board_kind == "支线轮动" else 20)
        zs = 70 if zt_hit else 40
        ls = 70 if lhb_hit else 40
        return round(0.35*ms + 0.35*bs + 0.15*zs + 0.15*ls)
    support_score = _score()
    support_label = "强支撑" if support_score >= 70 else ("一般支撑" if support_score >= 50 else "弱支撑")
    lines.append("推演结论")
    lines.append(str({
        "大盘": {"评级": market_level, "结论": market_conc},
        "板块": {"类别": board_kind, "建议": board_adv},
        "打板信号": {"涨停池命中": zt_hit, "龙虎榜命中": lhb_hit},
        "打板支撑评分": {"分数": support_score, "等级": support_label},
        "次日计划": plan,
    }))
    return "\n".join(lines)
