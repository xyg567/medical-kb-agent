# -*- coding: utf-8 -*-
"""mini_rag.py — 手写 100 行 RAG(第二周产出)

不用任何框架:切分/向量/检索/回答全是自己拼的。
流程:读本地医学文档 → 切块 → 每块变向量 → 问题变向量 → 找最像的3块
     → 有把握就把原文塞给大模型回答;没把握就老实说"资料未提及"。

用法:
    python mini_rag.py "TACE 的适应症是什么"
    python mini_rag.py "阿司匹林能治脱发吗"      ← 测试拒答
"""
import os
import sys

# ---------------- 第 0 段:路径与配置 ----------------
ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(ROOT, '..', 'week1_demo', 'data', 'docs')   # 复用 W1 的两份医学资料
sys.path.insert(0, os.path.join(ROOT, '..', 'week1_demo'))          # 借用 W1 的 .env/大模型连接代码

from agent.config import load_config          # noqa: E402  读 API Key
from agent.llm import OpenAICompatLLM         # noqa: E402  W1 写好的大模型客户端,直接复用

CHUNK_SIZE = 160      # 每块多少字(和 W1 local_doc_search 一样)
CHUNK_OVERLAP = 30    # 相邻块重叠,防止答案正好被切断
TOP_K = 3             # 找最像的 3 块
MIN_SCORE = 0.35      # 相似度低于它 = 语料里没有,要拒答


# ---------------- 第 1 段:切块 ----------------
def chunk_docs():
    """读 DOCS_DIR 下所有 .md/.txt,每份切成若干块。
    返回列表,每块是一个 dict:{"text": 原文, "chunk_id": "文件名#块号"}
    """
    chunks = []
    for name in sorted(os.listdir(DOCS_DIR)):
        if not name.lower().endswith(('.md', '.txt')):
            continue
        with open(os.path.join(DOCS_DIR, name), encoding='utf-8') as fh:
            text = ''.join(fh.read().split())          # 去掉空白,让块更紧凑
        step = CHUNK_SIZE - CHUNK_OVERLAP
        for i in range(0, len(text), step):
            seg = text[i:i + CHUNK_SIZE]
            chunks.append({"text": seg, "chunk_id": f"{name}#{i // step}"})
            if i + CHUNK_SIZE >= len(text):
                break
    return chunks


# ---------------- 第 2 段:余弦相似度 ----------------
def cosine(a, b):
    """两个向量的余弦相似度。向量已经归一化(encode 时 normalize=True),
    所以点积本身就是余弦:对应位置相乘再全加起来。"""
    return sum(x * y for x, y in zip(a, b))


# ---------------- 第 3 段:找最像的 k 块 ----------------
def search(query_vec, doc_vecs, chunks, k=TOP_K):
    """算 query 和每一块的相似度,返回 [(分数, 块), ...] 从高到低取前 k 个。"""
    scored = []
    for vec, chunk in zip(doc_vecs, chunks):
        scored.append((cosine(query_vec, vec), chunk))
    scored.sort(key=lambda x: -x[0])       # 分数高的排前面
    return scored[:k]


# ---------------- 第 4 段:拼提示词 ----------------
PROMPT = """你是医学科研助手。只依据下面编号的资料段落回答问题,并在引用处标注 [编号]。
资料里没有的内容,直接回答"资料未提及",禁止编造。

资料:
{passages}

问题:{question}
回答:"""


# ---------------- 第 5 段:主流程装配 ----------------
def answer_question(question, model, chunks, doc_vecs, llm):
    """完整流程:问题变向量 → 检索 → 看分数够不够 → 够就拼 prompt 调大模型,不够就拒答。"""
    q_vec = model.encode([question], normalize_embeddings=True)[0]
    hits = search(q_vec, doc_vecs, chunks)

    top_score, top_chunk = hits[0]
    if top_score < MIN_SCORE:              # 语料里没有相关内容 → 拒答,不编造
        return (f"资料未提及(最高相似度 {top_score:.2f},低于阈值 {MIN_SCORE}。\n"
                f"本知识库只覆盖:乳腺癌科普、CSCO 肝癌指南节选。")

    passages = "\n".join(
        f"[{i+1}] ({h[1]['chunk_id']}) {h[1]['text']}"
        for i, h in enumerate(hits)
    )
    prompt = PROMPT.format(passages=passages, question=question)
    reply = llm.complete([{"role": "user", "content": prompt}], tools=[])
    return reply.get("content", "")


# ---------------- 第 6 段:入口 ----------------
def main():
    question = sys.argv[1] if len(sys.argv) > 1 else "TACE 的适应症是什么"
    print("[1/4] 加载 embedding 模型(已缓存,秒开)...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("BAAI/bge-small-zh-v1.5")

    print("[2/4] 读取本地医学文档并切块...")
    chunks = chunk_docs()
    print(f"      共 {len(chunks)} 块")

    print("[3/4] 给每块算向量...")
    texts = [c["text"] for c in chunks]
    doc_vecs = model.encode(texts, normalize_embeddings=True)

    print("[4/4] 检索并回答...")
    cfg = load_config(os.path.join(ROOT, '..', 'week1_demo'))
    llm = OpenAICompatLLM(cfg) if cfg.configured else None
    answer = answer_question(question, model, chunks, doc_vecs, llm)
    print("\n=== 回答 ===")
    print(answer)


if __name__ == "__main__":
    main()
