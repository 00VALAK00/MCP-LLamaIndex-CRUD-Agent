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
    def get_config(is_docker: bool) -> dict:
        """Get Ollama configuration as a dictionary"""
        return {
            "model": os.getenv("OLLAMA_MODEL", "qwen3:latest"),
            "base_url": os.getenv("OLLAMA_BASE_URL_LOCAL") if not is_docker else os.getenv("OLLAMA_BASE_URL_DOCKER"),
            "base_url": os.getenv("OLLAMA_BASE_URL_LOCAL"),
            "context_window": os.getenv("OLLAMA_CONTEXT_WINDOW"),
            "max_tokens": os.getenv("OLLAMA_MAX_TOKENS"),
            "temperature": os.getenv("OLLAMA_TEMPERATURE"),
            "request_timeout": os.getenv("OLLAMA_REQUEST_TIMEOUT"),
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
    
