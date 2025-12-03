import argparse
import os
from datetime import datetime, timedelta
from src.datasource import (
    fetch_market_snapshot,
    fetch_stock_spot,
    fetch_stock_kline,
    fetch_index_kline,
    fetch_concepts_for_stock,
    fetch_stock_minute,
    fetch_stock_fund_flow_day,
    fetch_stock_share_info,
    fetch_hot_rank_top,
    fetch_index_spot,
    fetch_industry_strength,
    fetch_limit_up_today,
    fetch_lhb_institution,
    fetch_lhb_business_stats,
)
from src.analysis import analyze_market, analyze_board, analyze_stock
from src.report import build_report
from src.llm_client import call_llm
from src.prompt import build_system, build_user

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("code")
    parser.add_argument("--stock_name", default="")
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--use_llm", action="store_true")
    parser.add_argument("--llm_model", default="", help="override LLM model, e.g., deepseek-reasoner")
    parser.add_argument("--strict_realtime", action="store_true")
    parser.add_argument("--source", choices=["em", "sina", "tencent", "ak_em", "ak_spot"], default=None)
    parser.add_argument("--llm_rich", action="store_true")
    args = parser.parse_args()
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=args.days)).strftime("%Y%m%d")
    if args.llm_model:
        os.environ["LLM_MODEL"] = args.llm_model
    market = fetch_market_snapshot()
    index_sh = fetch_index_kline("000001", start, end)
    index_cy = fetch_index_kline("399006", start, end)
    stock_spot = fetch_stock_spot(args.code, source=args.source)
    stock_k = fetch_stock_kline(args.code, start, end)
    concepts = fetch_concepts_for_stock(args.code)
    stock_min = fetch_stock_minute(args.code)
    stock_flow_day = fetch_stock_fund_flow_day(args.code)
    stock_share = fetch_stock_share_info(args.code)
    hot_rank = fetch_hot_rank_top()
    idx_spot = fetch_index_spot()
    ind_strength = fetch_industry_strength()
    zt_pool = fetch_limit_up_today()
    lhb_inst = fetch_lhb_institution()
    lhb_stats = fetch_lhb_business_stats()
    market_rating = analyze_market(market, index_sh, index_cy)
    if args.strict_realtime:
        today = datetime.now().strftime("%Y-%m-%d")
        spot_ts = stock_spot.get("时间")
        min_ts = None
        try:
            if isinstance(stock_min, list) and stock_min:
                last_min = stock_min[-1]
                mt = last_min.get("时间") or last_min.get("time")
                if mt:
                    min_ts = str(mt)
        except Exception:
            pass
        if (stock_spot.get("最新价") is None) or (spot_ts and not str(spot_ts).startswith(today)):
            if not (min_ts and str(min_ts).startswith(today)):
                print("实时行情不可用或非今日数据，请检查网络或交易时段")
    src_used = args.source or "auto"
    board_result = analyze_board(args.code, concepts, market)
    stock_result = analyze_stock(args.code, stock_spot, stock_k, concepts)
    # enrich prompt data compactly
    top_n = 10 if args.llm_rich else 5
    # derived labels for market_info
    mv = market.get("market_info", {})
    up = mv.get("up") or 0
    down = mv.get("down") or 0
    zt = mv.get("zt") or 0
    dt = mv.get("dt") or 0
    amt = mv.get("amount") or 0.0
    mv["up_ratio"] = (up/(up+down) if (up+down)>0 else 0)
    mv["zt_dt_ratio"] = (zt/(dt or 1))
    mv["amount_label"] = ("充足" if amt>5e11 else "一般")
    report_data = dict(
        stock_name=args.stock_name or stock_spot.get("名称", args.code),
        individual=stock_result["individual"],
        szse=market.get("szse", {}),
        sh_spot=market.get("sh_spot", {}),
        sse=market.get("sse", {}),
        sza_spot=market.get("sza_spot", {}),
        sz_ind=market.get("sz_ind", {}),
        szfss=market.get("szfss", {}),
        shmr=market.get("shmr", {}),
        base_info=stock_result.get("base_info", {}),
        market_info=mv,
        latest_buy=stock_result.get("latest_buy", {}),
        stock_k=stock_k,
        stock_s_hot=market.get("stock_s_hot", {}),
        index_min=idx_spot,
        stock_data_flow=stock_flow_day[:top_n] if isinstance(stock_flow_day, list) else stock_flow_day,
        stock_min=stock_min,
        stock_concept={"list": concepts[:top_n]},
        stock_share=stock_share[:1] if isinstance(stock_share, list) else stock_share,
        index_current={"sh": index_sh[-1] if index_sh else {}, "cy": index_cy[-1] if index_cy else {}},
        stock_current=stock_spot,
        index_k={"sh": index_sh, "cy": index_cy},
        stock_min_flow={},
        market_rating=market_rating,
        board_result={**board_result, "行业强度TOP": ind_strength[:top_n] if isinstance(ind_strength, list) else ind_strength},
        stock_result=stock_result,
        zt_pool=zt_pool[:top_n] if isinstance(zt_pool, list) else zt_pool,
        lhb_inst=lhb_inst[:top_n] if isinstance(lhb_inst, list) else lhb_inst,
        lhb_stats=lhb_stats[:top_n] if isinstance(lhb_stats, list) else lhb_stats,
        llm_rich=args.llm_rich,
    )
    if args.use_llm:
        system = build_system()
        user = build_user(report_data)
        llm_out = call_llm(system, user)
        if llm_out:
            print(f"生成方式: DeepSeek {os.environ.get('LLM_MODEL', '')}")
            print(f"实时源: {src_used}")
            print(llm_out)
            try:
                os.makedirs("outputs", exist_ok=True)
                fn = os.path.join("outputs", f"{args.code}_{(args.stock_name or args.code)}.md")
                with open(fn, "w", encoding="utf-8") as f:
                    f.write(llm_out)
            except Exception:
                pass
        else:
            print("生成方式: 本地分析")
            print(f"实时源: {src_used}")
            text = build_report(**report_data)
            print(text)
            try:
                os.makedirs("outputs", exist_ok=True)
                fn = os.path.join("outputs", f"{args.code}_{(args.stock_name or args.code)}.md")
                with open(fn, "w", encoding="utf-8") as f:
                    f.write(text)
            except Exception:
                pass
    else:
        print("生成方式: 本地分析")
        print(f"实时源: {src_used}")
        text = build_report(**report_data)
        print(text)
        try:
            os.makedirs("outputs", exist_ok=True)
            fn = os.path.join("outputs", f"{args.code}_{(args.stock_name or args.code)}.md")
            with open(fn, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass

if __name__ == "__main__":
    main()
