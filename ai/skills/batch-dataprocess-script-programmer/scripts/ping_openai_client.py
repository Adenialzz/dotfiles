#!/usr/bin/env python3

import argparse
import json
import os
import sys
from pathlib import Path


CONFIG_PATH = Path(__file__).resolve().parent.parent / "references" / "llm_client.json"


def load_client_configs():
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_args():
    client_configs = load_client_configs()
    parser = argparse.ArgumentParser(
        description=(
            "Send a minimal OpenAI-compatible chat completion request to verify client "
            "configuration and endpoint availability."
        )
    )
    parser.add_argument(
        "--client",
        required=True,
        choices=sorted(client_configs),
        help="Preset client name from references/llm_client.json",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Request timeout in seconds",
    )
    args = parser.parse_args()

    preset = client_configs[args.client]
    args.base_url = preset.get("base_url")
    args.model = preset.get("model")
    args.api_key_env = preset.get("env_key")

    missing_fields = []
    if not args.base_url:
        missing_fields.append("base_url")
    if not args.model:
        missing_fields.append("model")
    if not args.api_key_env:
        missing_fields.append("env_key")
    if missing_fields:
        parser.error(
            f"client {args.client!r} is missing required config fields: "
            + ", ".join(missing_fields)
        )

    return args


def main():
    args = parse_args()

    api_key = os.getenv(args.api_key_env)
    if not api_key:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {
                        "type": "missing_api_key",
                        "message": (
                            f"Environment variable {args.api_key_env!r} is not set or empty."
                        ),
                    },
                },
                ensure_ascii=False,
            )
        )
        return 1

    try:
        from openai import OpenAI
    except ImportError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {
                        "type": "missing_dependency",
                        "message": "Package 'openai' is required. Try: uv run --with openai ...",
                        "detail": str(exc),
                    },
                },
                ensure_ascii=False,
            )
        )
        return 1

    client = OpenAI(
        api_key=api_key,
        base_url=args.base_url,
        timeout=args.timeout,
    )

    try:
        response = client.chat.completions.create(
            model=args.model,
            messages=[{"role": "user", "content": "Reply with the single word pong."}],
            max_tokens=16,
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                    "client": args.client,
                },
                ensure_ascii=False,
            )
        )
        return 1

    choice = response.choices[0] if response.choices else None
    message = getattr(choice, "message", None)
    content = getattr(message, "content", None)

    print(
        json.dumps(
            {
                "ok": True,
                "client": args.client,
                "response": {
                    "id": response.id,
                    "model": response.model,
                    "content": content,
                    "finish_reason": getattr(choice, "finish_reason", None),
                    "usage": response.usage.model_dump() if response.usage else None,
                },
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
