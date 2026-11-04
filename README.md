# 医疗项目

医学科研智能体 · 医疗问答（知识库）方向

## 目录结构

```
D:\医疗项目\
├── code\
│   ├── week1_demo\     第1周最小 Agent demo（工具 = 本地文档检索）
│   └── kb_agent\       正式的知识库问答 Agent（第2周起）
├── data\               指南、说明书等原始资料（不入 Git）
├── docs\               周报、学习笔记、接口文档
├── env\                依赖清单
├── .env                密钥（自己建，不入 Git）
└── README.md
```

## 环境要求

| 工具 | 状态 | 说明 |
|---|---|---|
| Miniconda | 待安装 | Python 3.11 环境 |
| Git | 已装 2.53.0 | 身份已配置 |
| Node.js | 已装 v24.14.0 | 智能体组联调用，本周可暂不动 |
| VS Code | 建议安装 | 写代码 |

## 快速开始

```bash
conda create -n kb python=3.11 -y
conda activate kb
pip install -r env/requirements.txt
```

## 本周任务

见 `docs\第1周任务清单.md`。

## 学习路线

见 `docs\学习路线_W1-W8.md`。
