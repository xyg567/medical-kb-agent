# 医疗项目

医学科研智能体 · 医疗问答（知识库）方向（RAG 线）

## 一、目录就四大类

```
D:\medproject\
│
├── code\                    ←【代码】
│   ├── week1_demo\          第 1 周 demo（双击根目录 演示.cmd 就能跑）
│   └── kb_agent\            第 2 周起的知识库 Agent 知识库 Agent（W2 起写 RAG）
│
├── data\                    ←【医学资料】W3 开始放指南/说明书 txt
│
├── docs\                    ←【一切文档】
│   ├── 第1周任务清单.md      组长的考卷：任务、验收 4 条、周报格式
│   ├── 学习路线_W1-W8.md     8 周路线：W2 手写 RAG 全链路
│   ├── ENV.md               环境/踩坑全记录（403、402、400、pandas、GBK…）
│   ├── 第一周作业_….docx     学习笔记版作业
│   └── 脚本\                 一次性工具脚本
│
├── env\                     ←【环境】
│   ├── .venv\               Python 3.12.13 + 167 个包
│   ├── uv-cache\            下载缓存（可整删）
│   ├── uv.exe               装包工具
│   ├── requirements.txt         组长版依赖（第 1 周 3 个包）
│   ├── requirements-full.txt    完整依赖（整个项目）
│   └── requirements.lock.txt    精确版本锁定
│
├── .env                     大模型 Key（根目录，组长约定的位置）
├── 演示.cmd                 双击 = 固定演示
└── 提问.cmd                 双击 = 自由提问
```

其余都是程序自用的：`.git\`、`.vscode\`、`.env.example`、`.gitignore`。**日常只需要碰 `code\`、`docs\`、两个 .cmd。**

## 二、组长要求 vs 现状（对账表）

| 组长的要求（docs\第1周任务清单.md） | 现状 | 状态 |
|---|---|---|
| demo 放 `code\week1_demo\` | demo 本体已搬入 | ✅ |
| Key 放根目录 `.env` | 已在根目录 `.env`，程序自动找到 | ✅ |
| 大模型调一次 | OpenCode Go 通道实测可用（OpenAI 兼容） | ✅ |
| demo 工具 = **本地文档检索** | 现有工具是 PubMed + 计算器 | ❌ 待补 |
| 环境 = **conda + Python 3.11** | 现为 env\.venv（3.12.13） | ❌ 版本不符 |
| `data\` 放医学 txt | 空的 | ❌ 检索工具要用 |
| 代码推 GitHub | 未建仓库未推送 | ❌ 待办 |
| 周报（Word 四块）周日 11/8 交 | 未写（材料已齐，可起草） | ❌ 待写 |

**验收 4 条**：① `python -V`=3.11.x ② demo 能回答本地文档问题并说出出处 ③ 代码在 GitHub ④ 周报已发。

## 三、怎么跑

```powershell
cd D:\medproject
.\env\.venv\Scripts\python.exe code\week1_demo\main.py --selftest   # 自检（不花额度）
.\演示.cmd                                                           # 双击演示
```

装包（三个参数缺一不可，原因见 docs\ENV.md）：

```powershell
$env:TMP="D:\medproject\env\tmp"; $env:TEMP=$env:TMP
.\env\uv.exe pip install --cache-dir env\uv-cache --python env\.venv\Scripts\python.exe --default-index https://pypi.org/simple 包名
```

## 四、环境状态

| 工具 | 状态 |
|---|---|
| Python venv | ✅ env\.venv（3.12.13 / 167 包，2026-11-05 重建验证） |
| conda 3.11 | ❌ 组长验收口径要 conda，未装（装则放 D:\miniconda3） |
| Git | ✅ 2.53（仓库已 init，首次提交=组长） |
| VS Code | ✅ 1.121，解释器已指向 env\.venv |

## 五、本周任务与路线

- 本周：`docs\第1周任务清单.md`（截止周日 11/8 周报）
- W2–W8：`docs\学习路线_W1-W8.md`（RAG 全链路 → 语料 → 检索优化 → 引用/拒答 → 评测 → 接口 → 文档）
- 统一接口 JSON 契约已定（见学习路线文末）
