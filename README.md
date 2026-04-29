# 🧠 NemoDuo

**A hybrid multi-agent research system powered by NVIDIA Nemotron 3.**

Nemotron 3 **Super** (120B) acts as the strategic **Planner** — reasoning deeply, decomposing queries into subtasks, and synthesizing final answers. Nemotron 3 **Nano 4B** runs **locally via Ollama** as the fast **Executor** — handling web search, document reading, and summarization.

This architecture directly mirrors the edge+cloud deployment pattern Nemotron 3 was designed for.

```
User Query
    │
    ▼
┌─────────────────────────────────┐
│   Orchestrator                  │
│   Routes · Coordinates · Logs   │
└────────────┬────────────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
┌──────────────┐  ┌──────────────┐
│   PLANNER    │  │   EXECUTOR   │
│ Nemotron 3   │──│ Nemotron 3   │
│ Super (API)  │◀─│ Nano (Local) │
└──────────────┘  └──────────────┘
       │                │
       │    ┌───────────┤
       │    ▼           ▼
       │  Web Search  Doc Reader
       │  Summarizer  Tool Calls
       ▼
Final Answer + Citations + Metrics
```

---

## ✨ Features

- **Reasoning budget control** — dial Planner thinking depth from 256 to 8192 tokens
- **Live agent stream** — watch Super and Nano "talk" in real time in the UI
- **Metrics dashboard** — tokens used, reasoning tokens, latency, estimated API cost per run
- **No LangChain** — clean custom agent loop, easy to read and extend
- **One-command setup** via Docker Compose
- **Free web search** via DuckDuckGo (no API key needed), optional Serper

---

## 🚀 Quickstart

### 1. Clone & configure

```bash
git clone https://github.com/yourusername/nemoDuo.git
cd nemoDuo
cp .env.example .env
# Edit .env — add your NVIDIA_API_KEY
```

### 2. Pull Nano locally via Ollama

```bash
# Install Ollama: https://ollama.com
ollama pull nemotron3-nano-4b
```

### 3. Run with Docker Compose

```bash
docker compose up --build
```

Open [http://localhost:8501](http://localhost:8501)

### Or run locally without Docker

```bash
pip install -r requirements.txt
streamlit run ui/app.py
```

---

## ⚙️ Configuration

| Variable | Default | Description |
|---|---|---|
| `NVIDIA_API_KEY` | — | Your NVIDIA NIM API key |
| `PLANNER_MODEL` | `nvidia/nemotron-3-super-120b-a12b` | Super model via NIM |
| `EXECUTOR_MODEL` | `nemotron3-nano-4b` | Nano model via Ollama |
| `REASONING_BUDGET` | `2048` | Planner thinking tokens |
| `MAX_SUBTASKS` | `5` | Max tasks Nano executes per query |
| `SERPER_API_KEY` | — | Optional: use Serper instead of DuckDuckGo |

---

## 🏗️ Project Structure

```
nemoDuo/
├── agents/
│   ├── planner.py          # Super via NVIDIA NIM
│   ├── executor.py         # Nano 4B via Ollama
│   └── orchestrator.py     # Coordinates both agents
├── tools/
│   ├── web_search.py       # DuckDuckGo / Serper
│   ├── doc_reader.py       # URL + PDF ingestion
│   └── summarizer.py       # Nano-powered summarizer
├── core/
│   ├── config.py           # Typed config from .env
│   ├── context_manager.py  # Shared 1M-token context window
│   └── metrics.py          # Token + cost + latency logger
├── ui/
│   └── app.py              # Streamlit dashboard
├── examples/
│   └── sample_queries.md
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 🤖 How the Agents Collaborate

1. **Planner (Super)** receives the query and uses its reasoning budget to produce a structured JSON plan — a list of ordered subtasks with types: `search`, `summarize`, `read_url`, `extract`

2. **Executor (Nano)** runs locally and executes each subtask sequentially — searching the web, reading pages, summarizing content — returning structured results

3. **Planner (Super)** synthesizes all results into a comprehensive, cited final answer

4. **Metrics** are logged to SQLite and surfaced in the sidebar

---

## 📊 Reasoning Budget

The `REASONING_BUDGET` controls how many tokens Nemotron 3 Super spends thinking before responding. This is one of Nemotron 3's key features — inference-time reasoning budget control.

| Budget | Use Case |
|---|---|
| 256–512 | Fast, low-cost queries |
| 2048 | Balanced (default) |
| 4096–8192 | Deep research, complex multi-step reasoning |

---

## 🗺️ Roadmap

- [ ] Streaming token output from Nano
- [ ] PDF upload support in UI
- [ ] Parallel subtask execution
- [ ] Comparison mode: Duo vs Solo (Super only) side-by-side
- [ ] Jetson Orin Nano deployment guide

---

## 📄 License

MIT

---

Built with [Nemotron 3](https://developer.nvidia.com/nemotron) · [NVIDIA NIM](https://developer.nvidia.com/nim) · [Ollama](https://ollama.com) · [Streamlit](https://streamlit.io)
