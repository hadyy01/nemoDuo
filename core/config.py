"""
core/config.py
Central configuration — loads from .env and exposes typed settings.
"""

import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Config(BaseModel):
    # NVIDIA NIM (Planner - Super)
    nvidia_api_key: str = os.getenv("NVIDIA_API_KEY", "")
    nvidia_base_url: str = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    planner_model: str = os.getenv("PLANNER_MODEL", "nvidia/nemotron-3-super-120b-a12b")

    # Ollama (Executor - Nano 4B)
    executor_model: str = os.getenv("EXECUTOR_MODEL", "nemotron3-nano-4b")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Reasoning budget
    reasoning_budget: int = int(os.getenv("REASONING_BUDGET", "2048"))

    # Search
    serper_api_key: str = os.getenv("SERPER_API_KEY", "")

    # Limits
    max_subtasks: int = int(os.getenv("MAX_SUBTASKS", "5"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "1024"))

    # Metrics
    metrics_db_path: str = os.getenv("METRICS_DB_PATH", "./data/metrics.db")


config = Config()
