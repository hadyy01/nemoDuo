"""
tools/web_search.py
Web search tool using DuckDuckGo (no API key required).
Optionally falls back to Serper if SERPER_API_KEY is set.
"""

import requests
from duckduckgo_search import DDGS
from core.config import config


class WebSearchTool:
    def search(self, query: str, max_results: int = 5) -> str:
        """Search the web and return formatted results string."""
        if config.serper_api_key:
            return self._serper_search(query, max_results)
        return self._ddg_search(query, max_results)

    def _ddg_search(self, query: str, max_results: int) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return "No results found."
            lines = []
            for r in results:
                lines.append(f"Title: {r.get('title', '')}")
                lines.append(f"URL: {r.get('href', '')}")
                lines.append(f"Snippet: {r.get('body', '')}")
                lines.append("---")
            return "\n".join(lines)
        except Exception as e:
            return f"Search error: {e}"

    def _serper_search(self, query: str, max_results: int) -> str:
        try:
            response = requests.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": config.serper_api_key,
                    "Content-Type": "application/json",
                },
                json={"q": query, "num": max_results},
                timeout=10,
            )
            data = response.json()
            lines = []
            for r in data.get("organic", []):
                lines.append(f"Title: {r.get('title', '')}")
                lines.append(f"URL: {r.get('link', '')}")
                lines.append(f"Snippet: {r.get('snippet', '')}")
                lines.append("---")
            return "\n".join(lines) or "No results found."
        except Exception as e:
            return f"Serper search error: {e}"
