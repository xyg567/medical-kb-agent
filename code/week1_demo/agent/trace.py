"""运行轨迹记录：每次运行落一个 JSON（最终态）+ 一个 JSONL（逐步追加），
字段遵循 schema/trace.schema.json，便于后续做模块联调和评测。
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class Trace:
    def __init__(self, root: str) -> None:
        self.run_id = str(uuid.uuid4())
        self.started_at = now_iso()
        self.mode = "offline"
        self.model = "rule-based-planner"
        self.user_query = ""
        self.steps: list[dict] = []
        self.final_answer = ""
        self.status = "error"
        self.error = ""
        self.finished_at = ""
        self._dir = os.path.join(root, "runs")
        os.makedirs(self._dir, exist_ok=True)
        self._jsonl = os.path.join(self._dir, f"{self.run_id}.jsonl")

    # --- 写入步骤
    def llm_call(self, latency_ms: int, note: str = "") -> None:
        self._append({"type": "llm_call", "latency_ms": latency_ms, "result_summary": note})

    def tool_call(self, name: str, arguments: dict) -> None:
        self._append({"type": "tool_call", "name": name, "arguments": arguments})

    def tool_result(self, name: str, payload: dict, latency_ms: int) -> None:
        summary = payload.get("note") or payload.get("error") or payload.get("source") or "ok"
        self._append(
            {"type": "tool_result", "name": name, "ok": bool(payload.get("ok")), "result_summary": summary, "latency_ms": latency_ms}
        )

    def _append(self, step: dict) -> None:
        step = {"index": len(self.steps), **step}
        self.steps.append(step)
        with open(self._jsonl, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(step, ensure_ascii=False) + "\n")

    # --- 收尾
    def finish(self, status: str, answer: str, error: str = "") -> dict:
        self.status, self.final_answer, self.error = status, answer, error
        self.finished_at = now_iso()
        payload = {
            "trace_schema_version": "1.0",
            "run_id": self.run_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "mode": self.mode,
            "model": self.model,
            "user_query": self.user_query,
            "steps": self.steps,
            "final_answer": answer,
            "status": status,
        }
        if error:
            payload["error"] = error
        with open(os.path.join(self._dir, f"{self.run_id}.json"), "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        return payload


def timeit() -> float:
    return time.perf_counter()


def elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)
