"""
agents/executor.py
Nemotron 3 Nano 4B (via Ollama, running locally) — the fast Executor agent.

Responsibilities:
- Receive subtasks from the Planner
- Execute: web search, URL reading, summarization, extraction
- Return structured results back to the Orchestrator
"""

import time
import httpx
import json
from core.config import config
from tools.web_search import WebSearchTool
from tools.doc_reader import DocReaderTool
from tools.summarizer import SummarizerTool


EXECUTOR_SYSTEM_PROMPT = """You are the Executor — a fast, efficient agent powered by Nemotron 3 Nano 4B running locally.

You receive a single focused subtask from the Planner agent and must complete it precisely.
Be concise and factual. Include source URLs in your response where applicable.
Do not add unnecessary commentary. Return only what was asked.
"""


class ExecutorAgent:
    def __init__(self):
        self.base_url = config.ollama_base_url
        self.model = config.executor_model
        self.search_tool = WebSearchTool()
        self.doc_tool = DocReaderTool()
        self.summarizer = SummarizerTool(ollama_base_url=self.base_url, model=self.model)

    def _chat(self, messages: list[dict]) -> tuple[str, int, float]:
        """Raw call to Ollama's OpenAI-compatible endpoint."""
        start = time.time()
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "num_predict": config.max_tokens,
                        "temperature": 0.1,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.time() - start) * 1000
        content = data["message"]["content"]
        tokens = data.get("eval_count", len(content) // 4)
        return content, tokens, latency_ms

    def run_subtask(self, subtask: dict) -> dict:
        """
        Execute a single subtask from the Planner.
        Returns result dict with result text, tokens, latency.
        """
        task_type = subtask.get("type", "search")
        instruction = subtask.get("instruction", "")
        subtask_id = subtask.get("id", 0)

        result_text = ""
        tokens = 0
        latency_ms = 0.0

        if task_type == "search":
            raw_results = self.search_tool.search(instruction)
            # Let Nano summarize the search snippets
            prompt = (
                f"Summarize these search results for the query: '{instruction}'\n\n"
                f"{raw_results}\n\n"
                "Be concise. Include source URLs."
            )
            messages = [
                {"role": "system", "content": EXECUTOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            result_text, tokens, latency_ms = self._chat(messages)

        elif task_type == "read_url":
            content = self.doc_tool.read_url(instruction)
            prompt = (
                f"Extract the key information from this page content:\n\n"
                f"{content[:3000]}\n\n"
                "Be concise and factual."
            )
            messages = [
                {"role": "system", "content": EXECUTOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            result_text, tokens, latency_ms = self._chat(messages)

        elif task_type == "summarize":
            result_text, tokens, latency_ms = self.summarizer.summarize(instruction)

        elif task_type == "extract":
            messages = [
                {"role": "system", "content": EXECUTOR_SYSTEM_PROMPT},
                {"role": "user", "content": instruction}
            ]
            result_text, tokens, latency_ms = self._chat(messages)

        else:
            result_text = f"Unknown task type: {task_type}"

        return {
            "subtask_id": subtask_id,
            "type": task_type,
            "instruction": instruction,
            "result": result_text,
            "tokens": tokens,
            "latency_ms": latency_ms,
        }
