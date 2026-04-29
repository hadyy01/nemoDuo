"""
agents/planner.py
Nemotron 3 Super (via NVIDIA NIM API) — the strategic Planner agent.

Responsibilities:
- Decompose the user query into ordered subtasks
- Synthesize Executor results into a final cited answer
- Manage reasoning depth via budget token control
"""

import time
import json
from openai import OpenAI
from core.config import config
from core.context_manager import ContextManager


PLANNER_SYSTEM_PROMPT = """You are the Planner — a strategic reasoning agent powered by Nemotron 3 Super.

Your role in the NemoDuo system:
1. Receive a research query from the user
2. Break it down into clear, ordered subtasks for the Executor agent (Nemotron 3 Nano running locally)
3. After the Executor returns results, synthesize a comprehensive answer with citations

When decomposing tasks, output ONLY a JSON object in this format:
{
  "reasoning": "<your internal reasoning about the query>",
  "subtasks": [
    {"id": 1, "type": "search", "instruction": "<what to search for>"},
    {"id": 2, "type": "summarize", "instruction": "<what to summarize from result 1>"},
    {"id": 3, "type": "search", "instruction": "<follow-up search>"}
  ]
}

Task types available to Executor: search | summarize | read_url | extract

Keep subtasks focused. Maximum 5 subtasks per query.
"""

SYNTHESIS_PROMPT = """You are now synthesizing the final answer.

You have the original query and the Executor's results for each subtask.
Produce a comprehensive, well-structured research answer with:
- Clear sections
- Inline citations referencing the source URLs where applicable
- A brief conclusion

Be thorough but concise. Prioritize accuracy over length.
"""


class PlannerAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=config.nvidia_api_key,
            base_url=config.nvidia_base_url,
        )
        self.model = config.planner_model
        self.reasoning_budget = config.reasoning_budget

    def decompose(self, query: str, ctx: ContextManager) -> dict:
        """
        Break query into subtasks for the Executor.
        Returns parsed JSON with subtasks list.
        """
        ctx.add("system", PLANNER_SYSTEM_PROMPT)
        ctx.add("executor", f"Research query: {query}")

        start = time.time()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=ctx.get_messages(),
            max_tokens=config.max_tokens,
            temperature=0.2,
            extra_body={
                "thinking": {"type": "enabled", "budget_tokens": self.reasoning_budget}
            },
        )

        latency_ms = (time.time() - start) * 1000
        raw = response.choices[0].message.content.strip()

        # Parse reasoning tokens if available
        reasoning_tokens = 0
        if hasattr(response, "usage") and hasattr(response.usage, "completion_tokens_details"):
            details = response.usage.completion_tokens_details
            reasoning_tokens = getattr(details, "reasoning_tokens", 0)

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        try:
            plan = json.loads(raw.strip())
        except json.JSONDecodeError:
            # Fallback: treat as single search task
            plan = {
                "reasoning": "Could not parse structured plan.",
                "subtasks": [{"id": 1, "type": "search", "instruction": query}]
            }

        ctx.add("planner", json.dumps(plan, indent=2))

        return {
            "plan": plan,
            "tokens_used": response.usage.total_tokens if response.usage else 0,
            "reasoning_tokens": reasoning_tokens,
            "latency_ms": latency_ms,
        }

    def synthesize(self, query: str, results: list[dict], ctx: ContextManager) -> dict:
        """
        Synthesize Executor results into a final research answer.
        """
        results_text = "\n\n".join([
            f"### Subtask {r['subtask_id']}: {r['instruction']}\n{r['result']}"
            for r in results
        ])

        messages = [
            {"role": "system", "content": SYNTHESIS_PROMPT},
            {"role": "user", "content": f"Original query: {query}\n\n---\n\n{results_text}"}
        ]

        start = time.time()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=config.max_tokens * 2,
            temperature=0.3,
            extra_body={
                "thinking": {"type": "enabled", "budget_tokens": self.reasoning_budget // 2}
            },
        )

        latency_ms = (time.time() - start) * 1000
        answer = response.choices[0].message.content.strip()

        return {
            "answer": answer,
            "tokens_used": response.usage.total_tokens if response.usage else 0,
            "latency_ms": latency_ms,
        }
