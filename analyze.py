import os
import sys
import runpy

def main():
    if len(sys.argv) < 2:
        print("用法: python analyze.py <股票代码> [--stock_name 名称]")
        sys.exit(1)
    code = sys.argv[1]
    name = None
    if "--stock_name" in sys.argv:
        idx = sys.argv.index("--stock_name")
        if idx + 1 < len(sys.argv):
            name = sys.argv[idx + 1]
    args = [
        "app",
        code,
        "--stock_name",
        name or code,
        "--use_llm",
        "--llm_model",
        os.environ.get("LLM_MODEL", "deepseek-reasoner"),
        "--source",
        "em",
        "--strict_realtime",
    ]
    sys.argv = args
    runpy.run_module("src.app", run_name="__main__")

if __name__ == "__main__":
    main()
