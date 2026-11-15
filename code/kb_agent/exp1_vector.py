# -*- coding: utf-8 -*-
"""exp1_vector.py — 亲眼看看"语义相似度"长什么样。

三句话,两两算余弦相似度:
  A 糖尿病的典型症状是多饮多尿
  B 血糖升高、口渴、多尿
  C 今天天气真好,适合出去玩

预期:A-B 高(意思近),A-C / B-C 低(意思远)。
这就是 embedding 的全部意义:把"意思"变成可计算的数字。
"""
from sentence_transformers import SentenceTransformer

print("首次运行会从 HuggingFace 下载 bge-small-zh-v1.5(约 100MB),请耐心…")
model = SentenceTransformer("BAAI/bge-small-zh-v1.5")

texts = [
    "糖尿病的典型症状是多饮多尿",
    "血糖升高、口渴、多尿",
    "今天天气真好,适合出去玩",
]
vecs = model.encode(texts, normalize_embeddings=True)  # 归一化后,点积=余弦相似度

def cos(i, j):
    return float(vecs[i] @ vecs[j])

print(f"\nA: {texts[0]}")
print(f"B: {texts[1]}")
print(f"C: {texts[2]}\n")
print(f"A-B 相似度: {cos(0, 1):.4f}   ← 都在讲糖尿病症状,应该高")
print(f"A-C 相似度: {cos(0, 2):.4f}   ← 医学 vs 天气,应该低")
print(f"B-C 相似度: {cos(1, 2):.4f}   ← 同上")
print(f"\n向量维度: {len(vecs[0])}(BAAI/bge-small-zh-v1.5 输出 512 维)")
