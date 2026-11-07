"""LLM 接入层：同一套内部消息格式，两种后端。

1. OpenAICompatLLM —— 任何 OpenAI 兼容的 /chat/completions 接口（DeepSeek / 通义 / 智谱 / Kimi / OpenAI），
   只用标准库 urllib，避免为了第一周 demo 背一堆依赖。
2. OfflinePlanner —— 无 API Key / 无网络时的规则化替身：同样输出 tool_calls，
   用来证明"规划→调用→观察→再决策"这条链路本身是通的。它不产生自然语言智能，只做链路验证。

内部消息格式即 OpenAI 格式（role / content / tool_calls / tool_call_id），
这样在线与离线共用同一份对话历史，Agent 主循环不需要分支。
"""

from __future__ import annotations

import ast
import json
import re
import urllib.request

from .config import Config

Message = dict
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) med-research-agent/0.1"


# ---------------------------------------------------------------- 在线：OpenAI 兼容
class OpenAICompatLLM:
    name = "openai-compat"

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg

    def complete(self, messages: list[Message], tools: list[dict]) -> Message:
        body = {
            "model": self.cfg.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.2,
        }
        req = urllib.request.Request(
            f"{self.cfg.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.cfg.api_key}",
                # 很多网关（Cloudflare 后面）会直接 403 掉 python-urllib 的默认 UA，
                # 实测 opencode.ai 就是如此：不带 UA 得 403，带上才进到真实接口。
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
                # OpenCode Go 要求稳定会话 ID，缺失会直接 400 MissingSessionID
                "x-opencode-session": self.cfg.session_id or "med-agent-default",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.cfg.timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        msg = payload["choices"][0]["message"]
        calls = []
        for call in msg.get("tool_calls") or []:
            fn = call.get("function", {})
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            calls.append({"id": call.get("id", ""), "name": fn.get("name", ""), "arguments": args})
        return {"content": msg.get("content") or "", "tool_calls": calls}


# ---------------------------------------------------------------- 离线：规则化替身
_TERM_MAP = [
    ("免疫检查点", "immune checkpoint inhibitor"),
    ("PD-1", "PD-1 inhibitor"),
    ("肠道菌群", "gut microbiome"),
    ("微生物", "microbiome"),
    ("肺结节", "pulmonary nodule"),
    ("乳腺癌", "breast cancer"),
    ("肝癌", "hepatocellular carcinoma"),
    ("问卷", "questionnaire"),
    ("生存分析", "survival analysis"),
]

_SEARCH_HINTS = ("文献", "检索", "查一下", "查查", "pubmed", "综述", "研究进展", "paper", "有哪些研究")
_CALC_HINTS = ("计算", "算一下", "算出", "多少", "占比", "百分比", "样本量", "平均")
_ARITH = re.compile(r"[\(\d][\d\.\s\+\-\*/\(\)%]{2,}")


def _balanced(expr: str) -> str | None:
    """从候选串里裁出一段可被 ast 解析的算术表达式（从右往左逐字修剪）。"""
    candidate = expr.strip().strip("*/+- ")
    for _ in range(len(candidate)):
        if not candidate:
            return None
        try:
            ast.parse(candidate, mode="eval")
            return candidate
        except SyntaxError:
            candidate = candidate[:-1].rstrip("*/+- ")
    return None


class OfflinePlanner:
    name = "rule-based-planner"

    def complete(self, messages: list[Message], tools: list[dict]) -> Message:
        query = next((m["content"] for m in messages if m.get("role") == "user"), "")
        tool_msgs = [m for m in messages if m.get("role") == "tool"]

        if tool_msgs:  # 第二轮：把工具结果组织成最终回答
            return {"content": self._compose(tool_msgs), "tool_calls": []}

        calls = []
        if any(h in query for h in _SEARCH_HINTS):
            calls.append(
                {
                    "id": "call_search_1",
                    "name": "pubmed_search",
                    "arguments": {"query": self._build_query(query), "retmax": 5},
                }
            )
        m = _ARITH.search(query)
        if m and (any(h in query for h in _CALC_HINTS) or len(calls) == 0):
            expr = _balanced(m.group(0))
            if expr and any(op in expr for op in "+-*/"):
                calls.append({"id": "call_calc_1", "name": "calculator", "arguments": {"expression": expr}})
        if not calls:
            return {
                "content": (
                    "（离线模式）这个问题不需要调用工具，但我只能做链路演示，无法生成真正的自然语言分析。"
                    "请配置 .env 中的 API Key 后使用在线模式。"
                ),
                "tool_calls": [],
            }
        return {"content": "", "tool_calls": calls}

    @staticmethod
    def _build_query(query: str) -> str:
        terms = [en for zh, en in _TERM_MAP if zh in query]
        return " AND ".join(terms) if terms else query

    @staticmethod
    def _compose(tool_msgs: list[Message]) -> str:
        lines, idx = [], 0
        for msg in tool_msgs:
            try:
                payload = json.loads(msg.get("content") or "{}")
            except json.JSONDecodeError:
                continue
            name = msg.get("name", "")
            if name == "pubmed_search" and payload.get("records"):
                note = f"（数据来源：{payload.get('source')}）"
                lines.append(f"检索到 {payload.get('count')} 条相关文献{note}：")
                for rec in payload["records"]:
                    idx += 1
                    authors = ", ".join(rec.get("authors", [])[:3])
                    lines.append(
                        f"[{idx}] {rec.get('title')} — {rec.get('journal')}, {rec.get('year')}; 作者：{authors}; PMID: {rec.get('pmid')}"
                    )
            elif name == "calculator" and payload.get("ok"):
                lines.append(f"计算结果：{payload.get('expression')} = {payload.get('value')}")
            elif not payload.get("ok", True):
                lines.append(f"工具 {name} 执行失败：{payload.get('error')}")
        lines.append("")
        lines.append(
            "小结：以上结果为工具直接返回的元数据，未做语义筛选；"
            "正式文献调研还需要按纳入/排除标准做二次筛选，并对结论做原文核对。"
        )
        return "\n".join(lines)
