import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
import sys
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load environment variables from .env.docker if it exists
env_file = Path.cwd() / ".env.docker"
logger.info(f"env_file: {env_file}")
if env_file.exists():
    load_dotenv(env_file)

class OllamaConfig:
    """Ollama configuration from environment variables"""
    
    @staticmethod
    def get_config() -> dict:
        """Get Ollama configuration as a dictionary"""
        return {
            "model": os.getenv("OLLAMA_MODEL", "qwen3:latest"),
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434"),
            "context_window": int(os.getenv("OLLAMA_CONTEXT_WINDOW", "10000")),
            "max_tokens": int(os.getenv("OLLAMA_MAX_TOKENS", "2500")),
            "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.6")),
            "request_timeout": float(os.getenv("OLLAMA_REQUEST_TIMEOUT", "120.0")),
        }


class DatabaseConfig:
    """Database configuration from environment variables"""
    
    @staticmethod
    def get_config() -> dict:
        """Get database configuration as a dictionary"""
        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "testdb"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "password"),
        }
