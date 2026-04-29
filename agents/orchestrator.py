"""
agents/orchestrator.py
The Orchestrator — coordinates Planner and Executor, streams progress,
and logs metrics.
"""

from typing import Generator
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from core.context_manager import ContextManager
from core.metrics import MetricsLogger, RunMetrics


class Orchestrator:
    def __init__(self):
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.logger = MetricsLogger()

    def run(self, query: str) -> Generator[dict, None, None]:
        """
        Run the full NemoDuo pipeline.
        Yields progress events so the Streamlit UI can stream them live.

        Event types:
            status   — status message string
            plan     — subtasks list from Planner
            subtask  — result of a single Executor subtask
            answer   — final synthesized answer
            metrics  — RunMetrics summary
        """
        ctx = ContextManager()
        metrics = RunMetrics(query=query)

        # ── Step 1: Planner decomposes the query ──────────────────────────
        yield {"type": "status", "data": "🧠 Planner (Super) is reasoning about your query..."}

        decompose_result = self.planner.decompose(query, ctx)
        plan = decompose_result["plan"]
        subtasks = plan.get("subtasks", [])[:5]  # cap at 5

        metrics.planner_tokens += decompose_result["tokens_used"]
        metrics.reasoning_tokens += decompose_result["reasoning_tokens"]
        metrics.planner_latency_ms += decompose_result["latency_ms"]
        metrics.subtask_count = len(subtasks)

        yield {
            "type": "plan",
            "data": {
                "reasoning": plan.get("reasoning", ""),
                "subtasks": subtasks,
            }
        }

        # ── Step 2: Executor runs each subtask ────────────────────────────
        results = []
        for subtask in subtasks:
            yield {
                "type": "status",
                "data": f"⚡ Executor (Nano) running subtask {subtask['id']}: {subtask['instruction'][:60]}..."
            }

            result = self.executor.run_subtask(subtask)
            results.append(result)

            metrics.executor_tokens += result["tokens"]
            metrics.executor_latency_ms += result["latency_ms"]

            yield {"type": "subtask", "data": result}

        # ── Step 3: Planner synthesizes final answer ───────────────────────
        yield {"type": "status", "data": "📝 Planner (Super) synthesizing final answer..."}

        synthesis = self.planner.synthesize(query, results, ctx)
        metrics.planner_tokens += synthesis["tokens_used"]
        metrics.planner_latency_ms += synthesis["latency_ms"]

        yield {"type": "answer", "data": synthesis["answer"]}

        # ── Step 4: Log metrics ────────────────────────────────────────────
        self.logger.log(metrics)

        yield {
            "type": "metrics",
            "data": {
                "planner_tokens": metrics.planner_tokens,
                "executor_tokens": metrics.executor_tokens,
                "reasoning_tokens": metrics.reasoning_tokens,
                "total_tokens": metrics.total_tokens,
                "planner_latency_ms": round(metrics.planner_latency_ms),
                "executor_latency_ms": round(metrics.executor_latency_ms),
                "total_latency_ms": round(metrics.total_latency_ms),
                "subtask_count": metrics.subtask_count,
                "estimated_cost_usd": round(metrics.estimated_cost_usd, 6),
            }
        }
