"""工具集：Agent 可以调用的外部能力。

设计原则（第一周模块零）：
1. 每个工具只做一件事，输入输出都是可 JSON 序列化的 dict；
2. 工具本身不依赖大模型，可以单独用命令行测试；
3. 网络不可用时自动降级到本地 fixture，并在返回值里显式标注 source，避免"静默幻觉"。
"""

from __future__ import annotations

import ast
import csv
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# ---------------------------------------------------------------- 工具声明
# OpenAI / DeepSeek 等接口通用的 function calling 描述格式
TOOL_SPECS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "pubmed_search",
            "description": "按主题词在 PubMed 检索文献，返回标题、期刊、年份、作者、PMID。用于文献调研。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "英文检索式，支持 AND/OR 与 MeSH 词，例如 'gut microbiome AND PD-1 inhibitor'"},
                    "retmax": {"type": "integer", "description": "返回条数，1-20，默认 5"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算四则/幂运算表达式，用于样本量、百分比、均值等数值计算。只接受数字与 + - * / ( ) ** %。",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "如 '(120-15)/120*100'"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "export_csv",
            "description": "把一组同结构记录导出为 CSV 文件（落盘到 runs/ 目录），用于把检索结果交给 Excel/R 继续处理。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "文件名，如 'pubmed_hits.csv'"},
                    "columns": {"type": "array", "items": {"type": "string"}, "description": "列名顺序"},
                    "rows": {"type": "array", "items": {"type": "object"}, "description": "记录数组，键名与 columns 对应"},
                },
                "required": ["filename", "columns", "rows"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "local_doc_search",
            "description": "在本机资料库（data/docs 下的医学指南与科普文本）中检索与问题最相关的段落，返回原文与出处（文件名+chunk_id）。用户问本地资料、指南条目时必须调用它，不得凭记忆作答。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "中文自然语言问题，如 'TACE 的适应症是什么'"},
                    "top_k": {"type": "integer", "description": "返回段落数，1-10，默认 3"},
                },
                "required": ["query"],
            },
        },
    },
]


# ---------------------------------------------------------------- 工具实现
def pubmed_search(query: str, retmax: int = 5) -> dict[str, Any]:
    """检索 PubMed；网络异常时回落到本地 fixture。"""
    retmax = max(1, min(int(retmax or 5), 20))
    try:
        ids = _esearch(query, retmax)
        records = _esummary(ids) if ids else []
        if records:
            return {"ok": True, "source": "pubmed-live", "query": query, "count": len(records), "records": records}
        return {"ok": True, "source": "pubmed-live", "query": query, "count": 0, "records": [], "note": "未命中文献"}
    except Exception as exc:  # 网络/限流/解析失败统一降级
        records = _fixture_search(query, retmax)
        return {
            "ok": True,
            "source": "offline-fixture",
            "query": query,
            "count": len(records),
            "records": records,
            "note": f"PubMed 不可用（{type(exc).__name__}），已使用本地示例数据，PMID 为 DEMO 编号，不可直接引用",
        }


def _get(url: str, timeout: int = 8) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "week1-agent-demo/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _esearch(query: str, retmax: int) -> list[str]:
    url = f"{EUTILS}/esearch.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "term": query, "retmode": "json", "retmax": retmax, "sort": "relevance"}
    )
    payload = json.loads(_get(url).decode("utf-8"))
    return payload.get("esearchresult", {}).get("idlist", [])


def _esummary(ids: list[str]) -> list[dict[str, Any]]:
    url = f"{EUTILS}/esummary.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}
    )
    payload = json.loads(_get(url).decode("utf-8")).get("result", {})
    out = []
    for pmid in ids:
        item = payload.get(pmid)
        if not item:
            continue
        out.append(
            {
                "pmid": pmid,
                "title": (item.get("title") or "").strip(),
                "journal": item.get("fulljournalname") or item.get("source") or "",
                "year": (item.get("pubdate") or "")[:4],
                "authors": [a.get("name", "") for a in item.get("authors", [])][:5],
                "doi": next((x.get("value") for x in item.get("articleids", []) if x.get("idtype") == "doi"), ""),
            }
        )
    return out


def _fixture_search(query: str, retmax: int) -> list[dict[str, Any]]:
    path = os.path.join(DATA_DIR, "fixtures_pubmed.json")
    with open(path, encoding="utf-8") as fh:
        records = json.load(fh)
    terms = [t for t in query.lower().replace(" and ", " ").split() if len(t) > 2]
    scored = []
    for rec in records:
        blob = (rec["title"] + " " + rec.get("journal", "")).lower()
        score = sum(1 for t in terms if t in blob)
        scored.append((score, rec))
    scored.sort(key=lambda x: -x[0])
    picked = [r for s, r in scored if s > 0][:retmax] or [r for _, r in scored][:retmax]
    return picked


_ALLOWED_BIN = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod)
_ALLOWED_UNARY = (ast.UAdd, ast.USub)


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, _ALLOWED_BIN):
        left, right = _eval_node(node.left), _eval_node(node.right)
        if isinstance(node.op, ast.Div) and right == 0:
            raise ZeroDivisionError("除数为 0")
        return {
            ast.Add: lambda: left + right,
            ast.Sub: lambda: left - right,
            ast.Mult: lambda: left * right,
            ast.Div: lambda: left / right,
            ast.Pow: lambda: left**right,
            ast.Mod: lambda: left % right,
        }[type(node.op)]()
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, _ALLOWED_UNARY):
        val = _eval_node(node.operand)
        return -val if isinstance(node.op, ast.USub) else val
    raise ValueError(f"不支持的表达式节点：{type(node).__name__}（只允许数字与四则/幂/取模）")


def calculator(expression: str) -> dict[str, Any]:
    """安全的算术求值：用 ast 白名单解析，绝不使用 eval。"""
    expr = (expression or "").strip()
    if not expr:
        return {"ok": False, "error": "表达式为空"}
    try:
        value = _eval_node(ast.parse(expr, mode="eval"))
        return {"ok": True, "expression": expr, "value": value}
    except Exception as exc:
        return {"ok": False, "expression": expr, "error": f"{type(exc).__name__}: {exc}"}


def export_csv(filename: str, columns: list[str], rows: list[dict[str, Any]]) -> dict[str, Any]:
    runs = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs")
    os.makedirs(runs, exist_ok=True)
    safe = os.path.basename(filename or "export.csv")
    if not safe.lower().endswith(".csv"):
        safe += ".csv"
    path = os.path.join(runs, safe)
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:  # utf-8-sig 让 Excel 正确识别中文
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})
    return {"ok": True, "path": path, "rows": len(rows), "created_at": datetime.now().isoformat(timespec="seconds")}


# ---------------------------------------------------------------- 本地文档检索
DOCS_DIR = os.path.join(DATA_DIR, "docs")
_CHUNK_SIZE = 160    # 每块字符数（去空白后）
_CHUNK_OVERLAP = 30  # 相邻块重叠，避免答案正好被切断


def _iter_doc_files() -> list[str]:
    if not os.path.isdir(DOCS_DIR):
        return []
    return [
        os.path.join(DOCS_DIR, name)
        for name in sorted(os.listdir(DOCS_DIR))
        if name.lower().endswith((".txt", ".md"))
    ]


def _load_chunks() -> list[dict[str, Any]]:
    """把资料库切成带出处的块：chunk_id = 文件名#块号，这是'引用可追溯到原文'的关键。"""
    chunks: list[dict[str, Any]] = []
    step = _CHUNK_SIZE - _CHUNK_OVERLAP
    for path in _iter_doc_files():
        fname = os.path.basename(path)
        with open(path, encoding="utf-8") as fh:
            text = re.sub(r"\s+", "", fh.read())
        for i in range(0, len(text), step):
            seg = text[i:i + _CHUNK_SIZE]
            chunks.append(
                {
                    "chunk_id": f"{fname}#{i // step}",
                    "file": fname,
                    "chunk_index": i // step,
                    "char_range": [i, i + len(seg)],
                    "text": seg,
                }
            )
            if i + _CHUNK_SIZE >= len(text):
                break
    return chunks


def _bigrams(s: str) -> set[str]:
    """字符二元组集合：对中英混排都有效，且不依赖任何分词库。"""
    if len(s) < 2:
        return {s} if s else set()
    return {s[i:i + 2] for i in range(len(s) - 1)}


def local_doc_search(query: str, top_k: int = 3) -> dict[str, Any]:
    """最小版检索：切块 → 二元组重叠打分 → top-k。它就是第二周手写 RAG 的检索端雏形
    （W2 会把'二元组打分'换成 embedding + 向量库，但返回结构和出处约定保持不变）。"""
    top_k = max(1, min(int(top_k or 3), 10))
    chunks = _load_chunks()
    if not chunks:
        return {"ok": False, "source": "local-docs", "query": query,
                "error": f"资料目录为空或不存在：{DOCS_DIR}"}
    q = _bigrams((query or "").lower())
    scored = [(len(q & _bigrams((c["file"] + c["text"]).lower())), c) for c in chunks]
    scored.sort(key=lambda x: -x[0])
    hits = [dict(c, score=s) for s, c in scored if s > 0][:top_k]
    if not hits:
        return {"ok": True, "source": "local-docs", "query": query, "count": 0, "passages": [],
                "note": "本地资料中没有相关段落，回答必须说明'资料未提及'，禁止编造"}
    return {"ok": True, "source": "local-docs", "query": query, "count": len(hits), "passages": hits,
            "note": "每条含 chunk_id，回答必须在引用处标注出处"}


# ---------------------------------------------------------------- 分发
_DISPATCH = {
    "pubmed_search": lambda a: pubmed_search(a.get("query", ""), a.get("retmax", 5)),
    "calculator": lambda a: calculator(a.get("expression", "")),
    "export_csv": lambda a: export_csv(a.get("filename", "export.csv"), a.get("columns", []), a.get("rows", [])),
    "local_doc_search": lambda a: local_doc_search(a.get("query", ""), a.get("top_k", 3)),
}


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    fn = _DISPATCH.get(name)
    if fn is None:
        return {"ok": False, "error": f"未知工具：{name}"}
    try:
        return fn(arguments or {})
    except Exception as exc:  # 工具异常不能让整个 Agent 崩掉
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
