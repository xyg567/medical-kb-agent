"""双击「提问.cmd」时运行的交互式提问。"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

print("=" * 58)
print("  医学科研 Agent · 交互提问")
print("  直接回车 = 使用默认问题")
print("=" * 58)
try:
    query = input("\n请输入你的问题：").strip()
except (EOFError, KeyboardInterrupt):
    query = ""
if not query:
    query = "PD-1 和肠道菌群有什么关系"

print()
code = subprocess.call([sys.executable, os.path.join(HERE, "main.py"), query], cwd=HERE)
sys.exit(code)
