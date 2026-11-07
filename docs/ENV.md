# 开发环境说明（D:\medproject）

> 建立时间：2026-11-05　｜　解释器：Python 3.12.13（uv 管理）　｜　虚拟环境：`D:\medproject\env\.venv`

## 1. 为什么是“项目内 venv”而不是全局安装

所有依赖都装在 `D:\medproject\env\.venv`，不污染系统 Python，也不依赖 conda：

- 换项目/换机器只管拷贝或重建 `.venv`，不会互相顶版本；
- 卸载 = 删掉 `.venv` 目录，零残留；
- VS Code 只需要把解释器指向 `env\.venv\Scripts\python.exe`（已在 `.vscode/settings.json` 预设）。

**注意：你机器上的 `python` / `pip` / `conda` 都不在 PATH 里**（`py` 启动器可用，`py` 指向 3.13）。所以下面所有命令都写全路径或先激活环境。

## 2. 三条命令开始工作

**推荐方式（实测可用，不碰系统策略）——直接用解释器全路径：**

```powershell
cd D:\medproject
.\env\.venv\Scripts\python.exe code\week1_demo\main.py --selftest
```

**需要 `python` 这个命令时，用 cmd 激活**（实测通过）：

```bat
cd /d D:\medproject
call env\.venv\Scripts\activate.bat
python --version        :: 3.12.13
python code\week1_demo\main.py --selftest
deactivate
```

> ⚠️ **PowerShell 里 `Activate.ps1` 会被系统拦**：本机实测即使 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`（已设置）仍报
> “cannot be loaded. The file ... is not digitally signed”，属于 Windows 11 家庭版的脚本管控，与 PowerShell 策略无关。
> 所以**不要**在 PowerShell 里 dot-source 激活脚本：
> - 用上面的 `activate.bat`（cmd / Windows Terminal 的 cmd 配置）；
> - 或者只用 `D:\medproject\env\.venv\Scripts\python.exe` 全路径；
> - VS Code 的 Python 扩展自己会注入环境变量（不依赖 `Activate.ps1`），选了解释器就能正常运行。

## 3. 以后怎么装新包（三个参数都必须带）

```powershell
cd D:\medproject
$env:TMP = "D:\medproject\env\tmp"; $env:TEMP = $env:TMP      # 必须：否则 uv 在系统临时目录被拒绝访问
.\env\uv.exe pip install `
  --cache-dir "D:\medproject\env\uv-cache" `                  # 必须：D:\uv_cache 已损坏且不可写
  --python "env\.venv\Scripts\python.exe" `
  --default-index https://pypi.org/simple `              # 必须：全局 uv.toml 配的中科大镜像返回 403
  包名

.\env\uv.exe pip list --cache-dir "D:\medproject\env\uv-cache" --python "env\.venv\Scripts\python.exe"   # 看已装了什么
```

三个“必须”的原因见第 7 节。`env\uv.exe` 是从用户目录复制进项目的（64.7 MB），整个工具链都在项目里，拷走就能用。

## 4. 已安装的包（167 个，1.7 GB）

| 类别 | 包与版本 |
|---|---|
| 网络与 LLM | requests 2.34、openai 3.45、python-dotenv 1.2、tenacity 9.2 |
| 数据与统计 | pandas **2.3.3**、numpy 2.5、scipy 1.18、scikit-learn 1.9、statsmodels 0.15、lifelines 0.30、pingouin 0.7、openpyxl 3.1、xlsxwriter 3.3 |
| 绘图 | matplotlib 3.11、seaborn 0.13、plotly 7.1 |
| 文档解析/生成 | pymupdf 2.1、pdfplumber 0.11、beautifulsoup4 4.15、lxml 6.1、python-docx 1.2、python-pptx 1.0 |
| 知识库 | chromadb 1.5、onnxruntime 1.31、tokenizers 0.23 |
| 桌面端 | PySide6 6.12（含 WebEngine）、shiboken6 6.12 |
| 医学影像 | pydicom 3.0、opencv 5.0 |
| 姿态估计 | mediapipe 1.2.2 |
| 交互开发 | ipykernel 7.4（VS Code 的 Jupyter 靠它） |

完整版本锁定：`requirements.lock.txt`（167 行，可直接复现）。

## 5. 重建环境（换电脑 / 环境损坏时）

```powershell
cd D:\medproject
$env:TMP = "D:\medproject\env\tmp"; $env:TEMP = $env:TMP
.\env\uv.exe venv .venv --cache-dir "D:\medproject\env\uv-cache" --python 3.12
.\env\uv.exe pip install --cache-dir "D:\medproject\env\uv-cache" --python "env\.venv\Scripts\python.exe" --default-index https://pypi.org/simple -r env\requirements-full.txt
```

## 6. 尚未安装

| 包 | 用途 | 什么时候装 |
|---|---|---|
| `vtk` / `itk` / `nnunet` | 三维渲染、配准、自动分割 | 分到影像方向时（体积大、对中文路径敏感） |
| `faiss-cpu` | 更快的向量检索 | chromadb 不够用时 |
| `torch`（CUDA 版） | embedding / 分割模型推理 | 你的 RTX 5060 驱动 610.47 支持 cu128+，需要时单独装（约 2.5 GB） |

## 7. 已知坑（都实际踩过）

1. **镜像源 403**：`C:\Users\许家豪\AppData\Roaming\uv\uv.toml` 把源设成中科大镜像，实测 403。必须加 `--default-index https://pypi.org/simple`。
2. **缓存目录损坏**：`D:\uv_cache\sdists-v9\.git` 拒绝访问（os error 5），uv 直接崩。已改用项目内 `D:\medproject\env\uv-cache`，可用 `--cache-dir` 指定。
3. **系统临时目录拒绝访问**：uv 解包时在 `C:\Users\...\AppData\Local\Temp` 被拒绝，必须把 `TMP`/`TEMP` 指到项目内 `.tmp`。
4. **pip 装包卡死**：`.venv` 里的 pip 联网装包长时间无输出（阿里云、官方源都试过），所以统一用 uv；`pip list` 之类本地命令可用。
5. **pandas 不能上 3.x**：statsmodels / pingouin / lifelines 都不支持 pandas 3，已锁 `>=2.2,<3`。第一次装成 3.1 导致卸载时连锁失败，最后重建了整个环境。
6. **`Activate.ps1` 被系统拦**：PowerShell 无法 dot-source（见第 2 节），用 `activate.bat` 或解释器全路径。
7. **`import fitz` 已弃用**：pymupdf 2.x 写 `import pymupdf`。
8. **中文路径**：项目在 `D:\medproject`、用户名中文。纯 Python 包无影响；装 VTK/CUDA 版 torch 若报编码错误，先挪到 `D:\medproject`。
9. **PATH 里没有 python**：教程里的 `python xxx.py` 要写成 `py xxx.py` 或 `env\.venv\Scripts\python.exe xxx.py`。

## 8. 还差什么

- [ ] **大模型 API Key**（模块零验收第 2 条必需）：申请后写进 `code\week1_demo\.env`，模板见 `.env.example`
- [ ] 可选：把 `D:\微软下载储存地\Microsoft VS Code\bin` 加进用户 PATH，终端里就能用 `code .` 打开项目
- [ ] 可选：把 `D:\medproject\env\.venv\Scripts` 加进用户 PATH（不推荐，容易和系统 Python 混淆）

## 9. VS Code（已装，1.121.0）

| 项 | 值 |
|---|---|
| 安装位置 | `D:\微软下载储存地\Microsoft VS Code`（非默认路径，所以 `where code` 找不到） |
| CLI | `D:\微软下载储存地\Microsoft VS Code\bin\code.cmd` |
| 已装关键扩展 | ms-python.python、ms-python.vscode-pylance、ms-python.debugpy、ms-toolsai.jupyter、ms-python.vscode-python-envs、中文语言包 |
| 解释器 | 已写入 `.vscode/settings.json`：`D:\medproject\env\.venv\Scripts\python.exe` |
| 快捷键 | `Ctrl+Shift+B` 跑「工具自检」；`F5` 选「调试：离线 Agent demo」 |

打开项目：

```powershell
& "D:\微软下载储存地\Microsoft VS Code\bin\code.cmd" "D:\medproject"
```

打开后若右下角提示选择解释器，选 `Python 3.12.13 ('env\.venv': venv)` 即可；状态栏应显示 `.venv`。

## 10. 大模型接入：OpenCode Go（已跑通）

| 项 | 值 |
|---|---|
| 专用端点 | `https://opencode.ai/inference/go/openai/v1` |
| 模型 | `deepseek-v4.1-flash`（Go 套餐内，月额度约 $100 ≈ 21 万次请求） |
| 必需请求头 | `x-opencode-session`（缺失直接 400）、非通用 SDK 的 `User-Agent` |
| 配置文件 | 项目根目录 `.env`（已 gitignore） |
| 实测 | 一次问答：3 次 PubMed 检索 + 2 次补充检索 + 最终回答，`"billing_source":"go"` |

**踩过的三个坑（顺序即排查过程）**：

1. 无 User-Agent → Cloudflare **403**（不是 Key 的问题）
2. 用 `/zen/v1` 端点 → Go 订阅不生效，付费模型 **402**、免费模型 **429**
3. 用 Go 端点但不带会话头 → **400 MissingSessionID**

三处都已在 `agent/llm.py` 与 `agent/config.py` 里固化，换机器不用再调。

⚠️ Key 曾在聊天中出现，建议期限后到 Console 重置一次。

