"""CLI 入口。

用法（在 week1_module0 目录下）：
    python main.py "帮我检索 PD-1 抑制剂与肠道菌群相关的文献，并保存结果"
    python main.py --offline "检索 PD-1 与肠道菌群的文献"
    python main.py --selftest          # 不起大模型，只测三个工具
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# Windows 控制台在重定向/管道下默认用 GBK 编码，模型输出里一旦出现 "CD8⁺" 这类字符就会抛
# UnicodeEncodeError 把整个回答吞掉。这里统一改成"遇到编不出的字符就替换"，保证永远有输出。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:  # 非文件流（如被包装过）时忽略
        pass


from agent import tools  # noqa: E402
from agent.config import load_config  # noqa: E402
from agent.core import Agent  # noqa: E402
from agent.llm import OfflinePlanner, OpenAICompatLLM  # noqa: E402
from agent.trace import Trace  # noqa: E402


def selftest() -> int:
    print("== 工具自检（不经过大模型）==")
    calc = tools.call_tool("calculator", {"expression": "(120-15)/120*100"})
    print("calculator:", json.dumps(calc, ensure_ascii=False))
    hits = tools.call_tool("pubmed_search", {"query": "PD-1 inhibitor AND gut microbiome", "retmax": 3})
    print("pubmed_search:", json.dumps({k: hits[k] for k in ("ok", "source", "count")}, ensure_ascii=False))
    if hits.get("records"):
        csv_out = tools.call_tool(
            "export_csv",
            {
                "filename": "selftest_hits.csv",
                "columns": ["pmid", "title", "journal", "year"],
                "rows": hits["records"],
            },
        )
        print("export_csv:", json.dumps(csv_out, ensure_ascii=False))
    bad = tools.call_tool("calculator", {"expression": "__import__('os').system('dir')"})
    print("calculator(注入用例):", json.dumps(bad, ensure_ascii=False))
    doc = tools.call_tool("local_doc_search", {"query": "TACE 介入治疗的适应症", "top_k": 2})
    print("local_doc_search:", json.dumps(
        {
            "ok": doc.get("ok"),
            "source": doc.get("source"),
            "count": doc.get("count"),
            "top_chunk": doc["passages"][0]["chunk_id"] if doc.get("passages") else None,
        },
        ensure_ascii=False,
    ))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="第一周·模块零 最小科研 Agent demo")
    parser.add_argument("query", nargs="?", help="用自然语言描述任务")
    parser.add_argument("--offline", action="store_true", help="强制使用规则化 planner，不需要 API Key")
    parser.add_argument("--selftest", action="store_true", help="只跑工具自检")
    parser.add_argument("--json", action="store_true", help="额外打印完整 trace JSON")
    args = parser.parse_args()

    if args.selftest:
        return selftest()
    if not args.query:
        parser.print_help()
        return 2

    cfg = load_config(ROOT)
    if args.offline:
        llm = OfflinePlanner()
        print("[模式] offline / rule-based-planner（未调用大模型）")
    elif cfg.configured:
        llm = OpenAICompatLLM(cfg)
        print(f"[模式] online / {cfg.model} @ {cfg.base_url} / key={cfg.masked()}")
    else:
        llm = OfflinePlanner()
        print("[模式] offline / rule-based-planner（未检测到可用 API Key，自动降级）")

    trace = Trace(ROOT)
    agent = Agent(llm, trace)
    result = agent.run(args.query)

    print("\n== 最终回答 ==")
    print(result["answer"] or f"[未产出回答] status={trace.status} error={trace.error}")
    print(f"\n== 轨迹 ==\nrun_id={trace.run_id}\nstatus={trace.status}\n文件: runs/{trace.run_id}.json")

    if args.json:
        print(json.dumps(
            {
                "run_id": trace.run_id,
                "status": trace.status,
                "steps": trace.steps,
            },
            ensure_ascii=False,
            indent=2,
        ))
    return 0 if trace.status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
