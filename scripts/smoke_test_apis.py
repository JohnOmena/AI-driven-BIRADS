"""Smoke test de conectividade APIs antes de iniciar T12."""
import os
import sys
import time
import yaml
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.translation.client import create_client


def main():
    cfg = yaml.safe_load(Path("configs/models.yaml").read_text(encoding="utf-8"))

    tests = [
        ("deepseek-v3",                  "Hi, respond in one word."),
        ("gemini-2.5-flash",             "Hi, respond in one word."),
        ("gemini-2.5-flash-no-thinking", "Hi, respond in one word."),
        ("gpt-4o-mini",                  "Hi, respond in one word."),
    ]

    print("Smoke test de conectividade:")
    print("=" * 60)

    for name, prompt in tests:
        if name not in cfg["models"]:
            print(f"\n[{name}] CONFIG AUSENTE em models.yaml")
            continue
        api_key = os.environ.get(cfg["models"][name]["env_key"])
        if not api_key:
            print(f"\n[{name}] API KEY AUSENTE -- pulando")
            continue
        try:
            t0 = time.time()
            client = create_client(name, cfg["models"][name])
            response = client.generate(prompt, temperature=0)
            elapsed = time.time() - t0
            print(f"\n[{name}] OK em {elapsed:.2f}s")
            print(f"  Resposta: {response[:60]!r}")
            print(f"  Tokens in/out: {client.total_input_tokens}/{client.total_output_tokens}")
            print(f"  Custo:    ${client.total_cost_usd:.6f}")
        except Exception as e:
            print(f"\n[{name}] FALHA: {type(e).__name__}: {str(e)[:200]}")


if __name__ == "__main__":
    main()
