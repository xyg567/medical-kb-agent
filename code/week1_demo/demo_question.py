"""双击「演示.cmd」时运行的固定演示。"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
QUERY = "帮我查一下 PD-1 抑制剂和肠道菌群的研究进展"

print("=" * 58)
print("  演示：模型自己决定调用哪个工具")
print("  问题：" + QUERY)
print("=" * 58)

code = subprocess.call([sys.executable, os.path.join(HERE, "main.py"), QUERY], cwd=HERE)
print("\n运行记录已保存到 week1_module0\\runs\\")
sys.exit(code)
