"""
tools/summarizer.py
Nano-powered summarizer — uses the local Nano 4B model via Ollama
to condense long text into key points.
"""

import time
import httpx


class SummarizerTool:
    def __init__(self, ollama_base_url: str, model: str):
        self.base_url = ollama_base_url
        self.model = model

    def summarize(self, text: str, max_points: int = 5) -> tuple[str, int, float]:
        """
        Summarize text into bullet points using Nano.
        Returns (summary, token_count, latency_ms).
        """
        prompt = (
            f"Summarize the following into {max_points} clear, concise bullet points. "
            f"Include key facts and any relevant URLs:\n\n{text[:4000]}"
        )

        start = time.time()
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "options": {"num_predict": 512, "temperature": 0.1},
                    }
                )
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            return f"Summarizer error: {e}", 0, 0.0

        latency_ms = (time.time() - start) * 1000
        content = data["message"]["content"]
        tokens = data.get("eval_count", len(content) // 4)
        return content, tokens, latency_ms
