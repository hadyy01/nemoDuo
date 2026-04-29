"""
core/metrics.py
Logs token throughput, reasoning tokens, latency, and estimated cost per run.
Stores to SQLite so the Streamlit dashboard can query it.
"""

import sqlite3
import time
import os
from dataclasses import dataclass, field
from typing import Optional
from core.config import config


@dataclass
class RunMetrics:
    query: str
    planner_tokens: int = 0
    executor_tokens: int = 0
    reasoning_tokens: int = 0
    planner_latency_ms: float = 0.0
    executor_latency_ms: float = 0.0
    subtask_count: int = 0
    timestamp: float = field(default_factory=time.time)

    # Rough cost estimate — NIM pricing as of 2025
    # Super: ~$0.54 / 1M tokens | Nano local: ~$0
    SUPER_COST_PER_1M = 0.54

    @property
    def total_tokens(self) -> int:
        return self.planner_tokens + self.executor_tokens

    @property
    def estimated_cost_usd(self) -> float:
        return (self.planner_tokens / 1_000_000) * self.SUPER_COST_PER_1M

    @property
    def total_latency_ms(self) -> float:
        return self.planner_latency_ms + self.executor_latency_ms


class MetricsLogger:
    def __init__(self, db_path: str = config.metrics_db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    query TEXT,
                    planner_tokens INTEGER,
                    executor_tokens INTEGER,
                    reasoning_tokens INTEGER,
                    planner_latency_ms REAL,
                    executor_latency_ms REAL,
                    subtask_count INTEGER,
                    estimated_cost_usd REAL
                )
            """)

    def log(self, m: RunMetrics):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO runs (
                    timestamp, query, planner_tokens, executor_tokens,
                    reasoning_tokens, planner_latency_ms, executor_latency_ms,
                    subtask_count, estimated_cost_usd
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                m.timestamp, m.query, m.planner_tokens, m.executor_tokens,
                m.reasoning_tokens, m.planner_latency_ms, m.executor_latency_ms,
                m.subtask_count, m.estimated_cost_usd
            ))

    def get_recent(self, limit: int = 20) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM runs ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
