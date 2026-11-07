"""配置加载：优先环境变量，其次仓库根目录的 .env（无第三方依赖）。"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass


def _load_dotenv(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)  # 真实环境变量优先，便于 CI/服务器注入


@dataclass
class Config:
    base_url: str
    api_key: str
    model: str
    timeout: int
    session_id: str = ""

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key and not self.api_key.startswith("sk-xxxx"))

    def masked(self) -> str:
        key = self.api_key or ""
        return f"{key[:4]}***{key[-4:]}" if len(key) > 8 else "(未配置)"


def _find_project_env(start: str) -> str:
    """从 demo 目录向上找 .env；组长约定 Key 放项目根目录（含 .git 的那层），优先级最高。"""
    start = os.path.abspath(start)
    candidates = [start]
    up = start
    for _ in range(4):
        up = os.path.dirname(up)
        candidates.append(up)
    proj_root = next((d for d in candidates if os.path.isdir(os.path.join(d, ".git"))), None)
    ordered = ([os.path.join(proj_root, ".env")] if proj_root else []) + [
        os.path.join(d, ".env") for d in candidates
    ]
    for path in ordered:
        if os.path.isfile(path):
            return path
    return os.path.join(start, ".env")


def load_config(root: str) -> Config:
    _load_dotenv(_find_project_env(root))
    # Key 兼容三种命名：本项目 LLM_API_KEY / 组长模板 DEEPSEEK_API_KEY / OPENAI_API_KEY
    api_key = (
        os.environ.get("LLM_API_KEY")
        or os.environ.get("DEEPSEEK_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or ""
    )
    base_url = os.environ.get("LLM_BASE_URL", "").rstrip("/")
    model = os.environ.get("LLM_MODEL", "")
    if not base_url and api_key:  # 只给了 DeepSeek Key 时自动补官方地址
        base_url = "https://api.deepseek.com/v1"
        model = model or "deepseek-chat"
    # 部分网关（如 OpenCode Go）要求稳定的会话 ID 才能做路由与缓存，
    # 一个进程 = 一个会话；换成别的厂商时这个头被忽略，不影响。
    session = os.environ.get("LLM_SESSION_ID") or f"med-agent-{uuid.uuid4().hex[:16]}"
    return Config(
        base_url=base_url,
        api_key=api_key,
        model=model or "deepseek-chat",
        timeout=int(os.environ.get("LLM_TIMEOUT", "60")),
        session_id=session,
    )
