from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import threading

@dataclass
class ReasoningEntry:
    op: str
    run_id: str
    inputs: Dict[str, Any]
    output: Any
    reasoning: str

class ReasoningLog:
    def __init__(self):
        self._entries: List[ReasoningEntry] = []
        self._lock = threading.Lock()

    def record(self, op: str, run_id: str, inputs: Dict[str, Any], output: Any, reasoning: str):
        with self._lock:
            self._entries.append(ReasoningEntry(
                op=op,
                run_id=run_id,
                inputs=inputs,
                output=output,
                reasoning=reasoning
            ))

    def entries(self) -> List[ReasoningEntry]:
        with self._lock:
            return list(self._entries)

def get_reasoning_log(ctx: Any) -> Optional[ReasoningLog]:
    if isinstance(ctx, dict):
        return ctx.get("reasoning_log")
    return getattr(ctx, "reasoning_log", None)

def record_reasoning(ctx: Any, op: str, inputs: Dict[str, Any], output: Any, reasoning: str):
    log = get_reasoning_log(ctx)
    if log:
        from dagor import get_run_id
        run_id = get_run_id() or "unknown"
        log.record(op, run_id, inputs, output, reasoning)
