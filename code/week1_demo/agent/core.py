"""Agent 主循环（第一周最小闭环）。

    user_query
        │
        ├─▶ LLM(messages, tools) ──无 tool_calls──▶ 最终回答
        │            │
        │            └──有 tool_calls──▶ 执行工具 ──▶ 结果写回 messages ──┐
        └────────────────────────────── 回到 LLM ◀───────────────────────┘

对应"Agent = 规划 + 工具 + 记忆 + 反思"：
- 规划：LLM 决定调哪个工具、传什么参数；
- 工具：tools.py 里的确定性函数；
- 记忆：messages 列表充当短期记忆，工具结果留在上下文里；
- 反思：工具失败/返回空时把错误原样回灌，让 LLM 有第二次机会（本 demo 用 max_steps 兜底）。
"""

from __future__ import annotations

import json
from typing import Any

from . import tools
from .trace import Trace, elapsed_ms, timeit

SYSTEM_PROMPT = """你是一个医学科研助手，运行在一个可调用工具的 Agent 框架里。

工作原则：
1. 需要文献时调用 pubmed_search，不要凭记忆编造文献、作者或 PMID；
2. 需要数值计算时调用 calculator，不要口算；
3. 需要把结果交给 Excel/R 时调用 export_csv；
4. 回答必须区分"工具返回的事实"和"你的推断"，并标注数据来源；
5. 无法确定的内容直接说明不确定，禁止虚构。
"""

MAX_STEPS = 6


class Agent:
    def __init__(self, llm, trace: Trace) -> None:
        self.llm = llm
        self.trace = trace

    def run(self, user_query: str) -> dict[str, Any]:
        self.trace.user_query = user_query
        self.trace.mode = "online" if self.llm.name != "rule-based-planner" else "offline"
        self.trace.model = getattr(self.llm, "cfg", None).model if hasattr(self.llm, "cfg") else self.llm.name

        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query},
        ]

        for step in range(MAX_STEPS):
            t0 = timeit()
            try:
                reply = self.llm.complete(messages, tools.TOOL_SPECS)
            except Exception as exc:
                self.trace.llm_call(elapsed_ms(t0), note=f"{type(exc).__name__}: {exc}")
                self.trace.finish("error", "", f"LLM 调用失败：{type(exc).__name__}: {exc}")
                return {"answer": "", "trace": self.trace}
            self.trace.llm_call(elapsed_ms(t0), note=f"tool_calls={len(reply.get('tool_calls') or [])}")

            calls = reply.get("tool_calls") or []
            if not calls:
                answer = reply.get("content", "")
                self.trace.finish("success", answer)
                return {"answer": answer, "trace": self.trace}

            # 把 assistant 的工具意图写回上下文（记忆）
            messages.append(
                {
                    "role": "assistant",
                    "content": reply.get("content", ""),
                    "tool_calls": [
                        {
                            "id": c["id"],
                            "type": "function",
                            "function": {"name": c["name"], "arguments": json.dumps(c["arguments"], ensure_ascii=False)},
                        }
                        for c in calls
                    ],
                }
            )

            for call in calls:
                self.trace.tool_call(call["name"], call["arguments"])
                t1 = timeit()
                payload = tools.call_tool(call["name"], call["arguments"])
                self.trace.tool_result(call["name"], payload, elapsed_ms(t1))
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "name": call["name"],
                        "content": json.dumps(payload, ensure_ascii=False),
                    }
                )

        self.trace.finish("max_steps_exceeded", "", f"超过最大步数 {MAX_STEPS} 仍未收敛")
        return {"answer": "", "trace": self.trace}
