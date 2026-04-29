"""
tools/doc_reader.py
Reads content from URLs or local PDF files.
"""

import requests
from bs4 import BeautifulSoup


class DocReaderTool:
    def read_url(self, url: str, max_chars: int = 5000) -> str:
        """Fetch and extract readable text from a URL."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; NemoDuo/1.0)"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove scripts, styles, nav
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            # Clean blank lines
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            return "\n".join(lines)[:max_chars]
        except Exception as e:
            return f"Could not read URL {url}: {e}"

    def read_pdf(self, path: str, max_chars: int = 5000) -> str:
        """Extract text from a local PDF file."""
        try:
            import PyPDF2
            text = []
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text() or "")
            return "\n".join(text)[:max_chars]
        except Exception as e:
            return f"Could not read PDF {path}: {e}"
