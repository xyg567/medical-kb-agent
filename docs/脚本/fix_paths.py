# 一次性脚本：重组目录后，把所有引用路径替换到位（2026-11-05）
#   week1_module0 -> code\week1_demo
#   .venv         -> env\.venv
#   .uv-cache     -> env\uv-cache
#   tools\uv.exe  -> env\uv.exe
#   ENV.md        -> docs\ENV.md
#   根 .env（Key 按组长约定）

import os

ROOT = r"D:\medproject"

def read(p, enc="utf-8"):
    with open(p, encoding=enc) as fh:
        return fh.read()

def write(p, text, enc="utf-8"):
    if enc == "ascii":
        with open(p, "w", encoding="ascii", newline="") as fh:
            fh.write(text)
    else:
        with open(p, "w", encoding="utf-8", newline="") as fh:  # 不写 BOM
            fh.write(text)

def apply(path, pairs, enc="utf-8"):
    text = read(path, enc)
    for old, new in pairs:
        text = text.replace(old, new)
    write(path, text, enc)
    print("done", path)

# ---------- .vscode（JSON 里要双反斜杠） ----------
vs_pairs = [
    ("week1_module0", "code\\\\week1_demo"),
    (".venv", "env\\\\.venv"),
]
for rf in ("settings.json", "tasks.json", "launch.json"):
    apply(os.path.join(ROOT, ".vscode", rf), vs_pairs)

# ---------- 根 .gitignore ----------
apply(os.path.join(ROOT, ".gitignore"), [
    (".venv/", "env/.venv/"),
    (".uv-cache/", "env/uv-cache/"),
    (".tmp/", "env/tmp/"),
    ("tools/*.exe", "env/uv.exe"),
    ("week1_module0/runs/", "code/week1_demo/runs/"),
])

# ---------- docs\ENV.md ----------
apply(os.path.join(ROOT, "docs", "ENV.md"), [
    ("配置文件 | `week1_module0\\.env`（已 gitignore）", "配置文件 | 项目根目录 `.env`（已 gitignore）"),
    ("week1_module0", "code\\week1_demo"),
    (".uv-cache", "env\\uv-cache"),
    ("tools\\uv.exe", "env\\uv.exe"),
    (".venv\\Scripts", "env\\.venv\\Scripts"),
    ("D:\\medproject\\.venv", "D:\\medproject\\env\\.venv"),
    ("-r requirements.txt", "-r env\\requirements-full.txt"),
    ('医疗项目\\.tmp"', '医疗项目\\env\\tmp"'),
    ("venv .venv --python 3.12", "venv env\\.venv --python 3.12"),
    ("('.venv': venv)", "('env\\.venv': venv)"),
    ("`\\.venv`", "`env\\.venv`"),
])

# ---------- code\week1_demo\README.md ----------
apply(os.path.join(ROOT, "code", "week1_demo", "README.md"), [
    ("D:\\medproject\\.venv", "D:\\medproject\\env\\.venv"),
    ("week1_module0", "code\\week1_demo"),
    (".\\.venv\\Scripts\\python.exe", ".\\env\\.venv\\Scripts\\python.exe"),
    ("call .venv\\Scripts\\activate.bat", "call env\\.venv\\Scripts\\activate.bat"),
    ("详见上层目录 `ENV.md`", "详见 `docs\\ENV.md`"),
    ("copy .env.example .env    # 填入 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL", "# Key 已放在项目根目录 .env（组长约定的位置），改模型就改它"),
])

# ---------- 两个双击启动器（纯 ASCII） ----------
demo_cmd = (
    "@echo off\r\n"
    "chcp 65001 >nul\r\n"
    "set PYTHONUTF8=1\r\n"
    'cd /d "%~dp0code\\week1_demo"\r\n'
    '"..\\..\\env\\.venv\\Scripts\\python.exe" demo_question.py\r\n'
    "echo.\r\n"
    "pause\r\n"
)
ask_cmd = (
    "@echo off\r\n"
    "chcp 65001 >nul\r\n"
    "set PYTHONUTF8=1\r\n"
    'cd /d "%~dp0code\\week1_demo"\r\n'
    '"..\\..\\env\\.venv\\Scripts\\python.exe" ask.py\r\n'
    "echo.\r\n"
    "pause\r\n"
)
write(os.path.join(ROOT, "演示.cmd"), demo_cmd, "ascii")
write(os.path.join(ROOT, "提问.cmd"), ask_cmd, "ascii")
print("done 演示.cmd / 提问.cmd")

# ---------- 校验 ----------
import json  # noqa: E402
for rf in ("settings.json", "tasks.json", "launch.json"):
    json.load(open(os.path.join(ROOT, ".vscode", rf), encoding="utf-8"))
    print("json OK", rf)
