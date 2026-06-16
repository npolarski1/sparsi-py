import structlog
import time
from typing import Any, Dict, Optional

class Reporter:
    def __init__(self, logger: Optional[Any] = None):
        self.logger = logger or structlog.get_logger("dagor.reporter")

    def engine_started(self, graph_name: str, run_id: str) -> None:
        self.logger.info("engine.started", graph=graph_name, run_id=run_id)

    def engine_finished(self, graph_name: str, run_id: str, duration_ms: float, error: Optional[Exception] = None) -> None:
        if error:
            self.logger.error("engine.failed", graph=graph_name, run_id=run_id, duration_ms=duration_ms, error=str(error))
        else:
            self.logger.info("engine.finished", graph=graph_name, run_id=run_id, duration_ms=duration_ms)

    def vertex_started(self, vertex_name: str, run_id: str, operator_name: str, inputs: Dict[str, Any]) -> None:
        self.logger.info("vertex.started", vertex=vertex_name, run_id=run_id, operator=operator_name, inputs=inputs)

    def vertex_finished(self, vertex_name: str, run_id: str, operator_name: str, outputs: Dict[str, Any], duration_ms: float) -> None:
        self.logger.info("vertex.finished", vertex=vertex_name, run_id=run_id, operator=operator_name, outputs=outputs, duration_ms=duration_ms)

    def vertex_skipped(self, vertex_name: str, run_id: str, reason: str) -> None:
        self.logger.info("vertex.skipped", vertex=vertex_name, run_id=run_id, reason=reason)

    def vertex_failed(self, vertex_name: str, run_id: str, operator_name: str, error: Exception, duration_ms: float) -> None:
        self.logger.error("vertex.failed", vertex=vertex_name, run_id=run_id, operator=operator_name, error=str(error), duration_ms=duration_ms)
