# 第一周 · 模块零：最小可运行科研 Agent demo

> 医学科研智能体培养计划 · 第一阶段（共享基础）· 全员必修
> 交付内容：一个"能调用工具的大模型最小 Agent" + 统一中间结果格式 + 工程规范样例

## 1. 这是什么

一个约 670 行的 Python 工程，用标准库实现了 Agent 的最小闭环：

```
user_query
   │
   ├─▶ LLM(messages, tools) ──没有 tool_calls──▶ 最终回答
   │            │
   │            └──有 tool_calls──▶ 执行工具 ──▶ 结果写回 messages ──┐
   └───────────────────────── 回到 LLM ◀────────────────────────────┘
```

对应 `Agent = 规划 + 工具 + 记忆 + 反思`：

| 要素 | 在本工程中的落点 |
|---|---|
| 规划 | `llm.py` 输出 tool_calls（调哪个工具、传什么参数） |
| 工具 | `tools.py`：`pubmed_search` / `calculator` / `export_csv` |
| 记忆 | `core.py` 里的 `messages` 列表（含历史工具结果） |
| 反思 | 工具报错原文回灌 + `MAX_STEPS` 兜底 + trace 留痕复盘 |

## 2. 快速开始

本机统一环境：`D:\medproject\env\.venv`（Python 3.12.13），详见 `docs\ENV.md`。

```bash
cd D:\medproject
.\env\.venv\Scripts\python.exe code\week1_demo\main.py --selftest    # 只测工具，不调大模型（无网络也能跑）
.\env\.venv\Scripts\python.exe code\week1_demo\main.py --offline "检索 PD-1 与肠道菌群的文献，并算一下 (120-15)/120*100"
```

若已用 cmd 激活过环境（`call env\.venv\Scripts\activate.bat`），把上面的全路径换成 `python main.py ...` 即可。
本 demo 只用标准库，所以其实**任何 3.10+ 的 Python 都能跑**，venv 只是为了让后续模块共用。

在线模式（真实大模型）：

```bash
# Key 已放在项目根目录 .env（组长约定的位置），改模型就改它
.\env\.venv\Scripts\python.exe main.py "帮我查一下 PD-1 抑制剂和肠道菌群的研究进展，导出 CSV"
```

> **OpenCode Go 用户注意**：Go 订阅不能用 `https://opencode.ai/zen/v1`——那是预付费余额通道，
> 会返回 402 Insufficient funds 或 429 FreeUsageLimitError。必须用 Go 专用端点，且带会话头
> （`llm.py` 已自动生成）：
>
> ```
> LLM_BASE_URL=https://opencode.ai/inference/go/openai/v1
> LLM_MODEL=deepseek-v4.1-flash
> ```
>
> 实测：同一把 Key 走 Go 端点返回 `"billing_source":"go"`；走 `/zen/v1` 报 402。缺 `x-opencode-session` 头会直接 400。

任意 OpenAI 兼容接口均可（DeepSeek / 通义 / 智谱 / Kimi / OpenAI）。未配置 Key 时自动降级为离线 planner，不会崩。

## 3. 目录结构

```
code\week1_demo/
├── main.py                 # CLI：--selftest / --offline / --json
├── agent/
│   ├── config.py           # .env 加载、Key 脱敏
│   ├── llm.py              # OpenAI 兼容客户端 + 离线规则 planner
│   ├── tools.py            # 3 个工具 + 白名单安全求值
│   ├── core.py             # Agent 主循环（规划→执行→观察→再决策）
│   └── trace.py            # 运行轨迹 JSON/JSONL 落盘
├── data/fixtures_pubmed.json   # 断网时的示例文献（PMID 为 DEMO 编号）
├── schema/trace.schema.json    # 统一中间结果格式（团队对接用）
├── runs/                   # 每次运行的 trace 与导出文件（已 gitignore）
├── .env.example
└── .gitignore
```

## 4. 三个工具

| 工具 | 作用 | 关键设计 |
|---|---|---|
| `pubmed_search` | 走 NCBI E-utilities（esearch + esummary）检索文献 | 超时 8s；网络失败自动回落本地 fixture，并在返回值里标 `source`，绝不让模型"以为"拿到真数据 |
| `calculator` | 算术求值 | 用 `ast` 白名单，不用 `eval`；已实测拦截 `__import__('os').system(...)` 注入 |
| `export_csv` | 结果导出 CSV 给 Excel/R | `utf-8-sig` 编码，Excel 打开中文不乱码 |

## 5. 统一中间结果格式

每次运行落两份文件到 `runs/`：`<run_id>.json`（最终态）与 `<run_id>.jsonl`（逐步追加）。
字段定义见 `schema/trace.schema.json`，核心是 `steps[]`：

```
llm_call  → {index, type, latency_ms, result_summary}
tool_call → {index, type, name, arguments}
tool_result → {index, type, name, ok, result_summary, latency_ms}
```

四个模块联调时，只要大家都吐这个结构，编排层就能统一渲染"这个答案是怎么来的"。

## 6. 已知限制（第一周不掩盖）

1. **离线 planner 没有语言能力**：它只做关键词→工具的映射，用来证明链路通，不代表模型效果。
2. **在线模式未在本机实测**：当前环境没有可用 API Key，代码路径按 OpenAI 规范写好，但需要你填 Key 后自测一次。
3. PubMed 未加重试与限流（NCBI 建议 ≤3 req/s、需带 `tool`/`email` 参数），模块一实现时要补。
4. 没有向量库、没有 PDF 解析、没有多轮对话压缩——这些属于模块一/模块三。
5. `export_csv` 只接受扁平行，嵌套结构未做展开。

## 7. 下一步

- 补齐在线模式实测截图与一次真实的 5 轮对话 trace；
- 把 `pubmed_search` 升级为"检索式构建 + 去重（DOI/标题归一化）"；
- 给 `trace.schema.json` 加 `tokens_in/tokens_out/cost` 字段，便于算成本。
