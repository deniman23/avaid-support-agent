#!/usr/bin/env python3
"""Register Ollama model in Dify tenant (run inside docker-api-1)."""
import os
import sys

sys.path.insert(0, "/app/api")
import app as dify_app
from services.model_provider_service import ModelProviderService

TENANT = os.environ["DIFY_TENANT_ID"]
MODEL = os.environ.get("SUPPORT_LLM_MODEL", "qwen3:8b")
PROVIDER = "langgenius/ollama/ollama"
CREDS = {
    "base_url": "http://ollama:11434",
    "mode": "chat",
    "context_size": "32768",
    "max_tokens": "4096",
    "vision_support": "false",
    "function_call_support": "true",
    "stream_function_calling": "true",
}

with dify_app.app.app_context():
    s = ModelProviderService()
    s.validate_model_credentials(TENANT, PROVIDER, "llm", MODEL, CREDS)
    try:
        s.create_model_credential(TENANT, PROVIDER, "llm", MODEL, CREDS, f"Qwen {MODEL}")
        print(f"created credential for {MODEL}")
    except Exception as e:
        if "already" in str(e).lower() or "exist" in str(e).lower():
            print(f"credential exists for {MODEL}")
        else:
            raise
    print("OK:", MODEL)
