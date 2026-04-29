"""
core/context_manager.py
Manages the shared context window passed between Planner and Executor.
Nemotron 3 supports up to 1M tokens — we keep a rolling buffer and
track token usage to avoid overflow.
"""

from dataclasses import dataclass, field
from typing import Literal

Role = Literal["planner", "executor", "tool", "system"]


@dataclass
class ContextEntry:
    role: Role
    content: str
    token_estimate: int = 0

    def __post_init__(self):
        # rough estimate: 1 token ≈ 4 chars
        if self.token_estimate == 0:
            self.token_estimate = max(1, len(self.content) // 4)


class ContextManager:
    """
    Rolling context buffer shared between Planner and Executor.
    Automatically trims oldest entries when approaching token limit.
    """

    def __init__(self, max_tokens: int = 128_000):
        self.max_tokens = max_tokens
        self._entries: list[ContextEntry] = []

    @property
    def total_tokens(self) -> int:
        return sum(e.token_estimate for e in self._entries)

    def add(self, role: Role, content: str):
        entry = ContextEntry(role=role, content=content)
        self._entries.append(entry)
        self._trim()

    def _trim(self):
        """Drop oldest entries (keeping system messages) when over budget."""
        while self.total_tokens > self.max_tokens and len(self._entries) > 1:
            # never drop index 0 if it's a system message
            drop_idx = 1 if self._entries[0].role == "system" else 0
            self._entries.pop(drop_idx)

    def get_messages(self) -> list[dict]:
        """Return entries as OpenAI-compatible message list."""
        role_map = {
            "planner": "assistant",
            "executor": "user",
            "tool": "user",
            "system": "system",
        }
        return [
            {"role": role_map[e.role], "content": e.content}
            for e in self._entries
        ]

    def get_summary(self) -> str:
        """Compact summary for display in the Streamlit UI."""
        lines = []
        for e in self._entries:
            preview = e.content[:120].replace("\n", " ")
            lines.append(f"[{e.role.upper()}] {preview}...")
        return "\n".join(lines)

    def clear(self):
        self._entries.clear()
