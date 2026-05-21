#!/usr/bin/env python3
"""Register Ollama embedding model + tenant default (run in docker-api-1)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, "/app/api")

from app_factory import create_app
from services.model_provider_service import ModelProviderService

TENANT = os.environ.get("DIFY_TENANT_ID", "11aad9d2-e6a0-41fc-b8a1-5bf10ab4518f")
PROVIDER = "langgenius/ollama/ollama"
EMBED_MODEL = os.environ.get("SUPPORT_EMBED_MODEL", "nomic-embed-text")
CREDS = {
    "base_url": "http://ollama:11434",
    "mode": "chat",
    "context_size": "8192",
    "max_tokens": "8192",
    "vision_support": "false",
    "function_call_support": "false",
    "stream_function_calling": "false",
}


def main() -> int:
    _, app = create_app()
    with app.app_context():
        s = ModelProviderService()
        s.validate_model_credentials(TENANT, PROVIDER, "text-embedding", EMBED_MODEL, CREDS)
        try:
            s.create_model_credential(
                TENANT, PROVIDER, "text-embedding", EMBED_MODEL, CREDS, f"Ollama embed {EMBED_MODEL}"
            )
            print(f"created embedding credential: {EMBED_MODEL}")
        except Exception as e:
            if "already" in str(e).lower() or "exist" in str(e).lower():
                print(f"embedding credential exists: {EMBED_MODEL}")
            else:
                raise
        s.update_default_model_of_model_type(TENANT, "text-embedding", PROVIDER, EMBED_MODEL)
        print(f"default text-embedding: {PROVIDER} / {EMBED_MODEL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
